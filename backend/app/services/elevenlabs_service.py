"""
ElevenLabs Real-time Voice Conversation Service
Handles WebSocket communication with ElevenLabs ConvAI API for real-time voice AI
Based on neo-interview implementation
"""

import asyncio
import base64
import json
import time
from typing import Dict, Optional, Callable, Any, List

import websockets
from websockets.exceptions import ConnectionClosed

from app.config import settings


class ElevenLabsVoiceHandler:
    """Handles WebSocket communication with ElevenLabs ConvAI"""
    
    WEBSOCKET_URL = "wss://api.elevenlabs.io/v1/convai/conversation"
    SIGNED_URL_ENDPOINT = "https://api.elevenlabs.io/v1/convai/conversation/get-signed-url"
    
    def __init__(self, api_key: str, agent_id: str, dynamic_variables: Dict[str, str] = None):
        self.api_key = api_key
        self.agent_id = agent_id
        self.websocket_url = f"{self.WEBSOCKET_URL}?agent_id={agent_id}"
        self.websocket = None
        self.is_connected = False
        self._conversation_ready = False
        self._init_sent = False  # Track if we've sent init message
        
        # Dynamic variables for personalizing the agent (issues list, user name, etc.)
        self.dynamic_variables = dynamic_variables or {}
        
        # Callback registry
        self.response_callbacks: Dict[str, Callable] = {}
        
        # Audio buffering
        self._pcm_buffer = bytearray()
        self._flush_bytes = 3200  # Flush every 3200 bytes (~100ms at 16kHz)
        self._last_flush = time.time()
        self._pending_audio_before_ready: List[bytes] = []
        
        # Payload format cache
        self._successful_payload_format: Optional[int] = None
    
    async def _get_signed_url(self) -> Optional[str]:
        """Get a signed URL from ElevenLabs API for secure connection.
        
        Try to pass dynamic variables here to ensure they're available
        BEFORE the conversation starts.
        """
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                # Try POST with dynamic variables in body
                post_data = {}
                if self.dynamic_variables:
                    post_data["dynamic_variables"] = self.dynamic_variables
                    print(f"[ElevenLabs] Passing dynamic variables to signed URL endpoint...")
                
                # First try with POST to include dynamic variables
                if post_data:
                    response = await client.post(
                        self.SIGNED_URL_ENDPOINT,
                        params={"agent_id": self.agent_id},
                        headers={"xi-api-key": self.api_key, "Content-Type": "application/json"},
                        json=post_data
                    )
                    if response.status_code == 200:
                        data = response.json()
                        signed_url = data.get("signed_url")
                        print(f"[ElevenLabs] Got signed URL with dynamic vars (POST)")
                        return signed_url
                    else:
                        print(f"[ElevenLabs] POST failed ({response.status_code}), trying GET...")
                
                # Fall back to GET
                response = await client.get(
                    self.SIGNED_URL_ENDPOINT,
                    params={"agent_id": self.agent_id},
                    headers={"xi-api-key": self.api_key}
                )
                if response.status_code == 200:
                    data = response.json()
                    signed_url = data.get("signed_url")
                    print(f"[ElevenLabs] Got signed URL (valid for 15 min)")
                    return signed_url
                else:
                    print(f"[ElevenLabs] Failed to get signed URL: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            print(f"[ElevenLabs] Error getting signed URL: {e}")
            return None
    
    async def connect(self) -> bool:
        """Connect to ElevenLabs WebSocket using signed URL"""
        if self.is_connected and self.websocket:
            return True
        
        try:
            # Get signed URL first (more secure and reliable)
            signed_url = await self._get_signed_url()
            
            if signed_url:
                # Use signed URL - no need for API key in headers
                connection_url = signed_url
                headers = {}
                print(f"[ElevenLabs] Connecting with signed URL...")
            else:
                # Fall back to direct connection with API key
                connection_url = self.websocket_url
                headers = {"xi-api-key": self.api_key}
                print(f"[ElevenLabs] Falling back to direct connection...")
            
            # Try newer websockets API first, fall back to older
            try:
                if headers:
                    self.websocket = await websockets.connect(
                        connection_url,
                        extra_headers=headers,
                        max_size=None,
                    )
                else:
                    self.websocket = await websockets.connect(
                        connection_url,
                        max_size=None,
                    )
            except TypeError:
                # Fall back to older websockets API
                header_list = list(headers.items()) if headers else []
                self.websocket = await websockets.connect(
                    connection_url,
                    additional_headers=header_list,
                    max_size=None,
                )
            
            self.is_connected = True
            self._init_sent = False
            print(f"[ElevenLabs] Connected successfully")
            
            # Send dynamic variables IMMEDIATELY after connection, before any audio
            if self.dynamic_variables:
                await self._send_init_with_dynamic_variables()
            
            # Start listening for responses
            asyncio.create_task(self._listen())
            return True
            
        except Exception as e:
            print(f"[ElevenLabs] Connection failed: {e}")
            self.is_connected = False
            return False
    
    async def _send_init_with_dynamic_variables(self):
        """Send conversation initialization with dynamic variables.
        
        According to ElevenLabs docs, the message structure should have
        dynamic_variables at the ROOT level.
        
        NOTE: conversation_config_override for prompt is NOT allowed unless
        enabled in the agent dashboard. So we only send dynamic_variables
        and rely on the agent's system prompt having {{issues_list}} placeholder.
        """
        if self._init_sent:
            return
        
        try:
            # CORRECT FORMAT per ElevenLabs docs:
            # dynamic_variables at ROOT level (no conversation_config_override
            # because it's blocked by policy)
            init_message = {
                "type": "conversation_initiation_client_data",
                "dynamic_variables": self.dynamic_variables
            }
            
            message_json = json.dumps(init_message)
            print(f"[ElevenLabs] Sending init with dynamic_variables only (no override)")
            print(f"[ElevenLabs] Dynamic vars: {list(self.dynamic_variables.keys())}")
            
            if 'issues_list' in self.dynamic_variables:
                issues = self.dynamic_variables['issues_list']
                print(f"[ElevenLabs] issues_list value:\n{issues}")
            
            await self.websocket.send(message_json)
            self._init_sent = True
            print(f"[ElevenLabs] ✅ Dynamic variables sent at root level")
        except Exception as e:
            print(f"[ElevenLabs] Error sending init: {e}")
            import traceback
            traceback.print_exc()
    
    async def disconnect(self):
        """Disconnect from ElevenLabs"""
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception:
                pass
        self.is_connected = False
        self._conversation_ready = False
        print("[ElevenLabs] Disconnected")
    
    async def _listen(self):
        """Listen for messages from ElevenLabs"""
        if not self.websocket:
            return
        
        try:
            async for raw in self.websocket:
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    print(f"[ElevenLabs] Non-JSON frame: {raw[:60] if isinstance(raw, str) else type(raw)}")
                    continue
                
                await self._handle_event(data)
                
        except ConnectionClosed as cc:
            print(f"[ElevenLabs] Socket closed: code={cc.code}")
        except Exception as e:
            print(f"[ElevenLabs] Listener error: {e}")
        finally:
            self.is_connected = False
    
    async def _handle_event(self, data: dict):
        """Handle incoming events from ElevenLabs"""
        try:
            evt_type = data.get("type")
            
            # Log ALL events for debugging
            if evt_type not in ("audio", "ping"):  # Skip noisy audio/ping logs
                print(f"[ElevenLabs] 📨 Event type: {evt_type}")
                if evt_type == "error":
                    print(f"[ElevenLabs] ❌ ERROR from ElevenLabs: {data}")
                if evt_type == "conversation_initiation_metadata":
                    print(f"[ElevenLabs] 📋 Full metadata: {json.dumps(data, indent=2)[:500]}")
            
            # Conversation initiation
            if evt_type == "conversation_initiation_metadata":
                conversation_id = data.get("conversation_id") or data.get("conversationId") or data.get("id")
                print(f"[ElevenLabs] Conversation started: {conversation_id}")
                
                # Check if dynamic variables were acknowledged
                if "dynamic_variables" in str(data):
                    print(f"[ElevenLabs] ✅ Dynamic variables appear in metadata!")
                else:
                    print(f"[ElevenLabs] ⚠️ Dynamic variables NOT in metadata response")
                
                await self._notify("status", data)
                
                if not self._conversation_ready:
                    self._conversation_ready = True
                    # Flush any pending audio
                    if self._pending_audio_before_ready:
                        print(f"[ElevenLabs] Flushing {len(self._pending_audio_before_ready)} buffered audio chunks")
                        for buf in self._pending_audio_before_ready:
                            self._pcm_buffer.extend(buf)
                        self._pending_audio_before_ready.clear()
                        await self.flush()
                return
            
            # Audio response - check multiple possible formats
            audio_b64 = None
            if "audio_event" in data:
                ev = data["audio_event"]
                audio_b64 = ev.get("audio_base64") or ev.get("audio") or ev.get("audio_base_64")
            elif "audio_base64" in data:
                audio_b64 = data["audio_base64"]
            elif "audio" in data and isinstance(data["audio"], str):
                audio_b64 = data["audio"]
            
            if audio_b64:
                try:
                    pcm = base64.b64decode(audio_b64)
                    print(f"[ElevenLabs] 🎵 Audio received: {len(pcm)} bytes")
                    await self._notify("audio_response", pcm)
                except Exception as e:
                    print(f"[ElevenLabs] Audio decode error: {e}")
            
            # Text response
            if "agent_response_event" in data:
                text = data["agent_response_event"].get("agent_response") or \
                       data["agent_response_event"].get("text")
                if text:
                    print(f"[ElevenLabs] 🤖 Agent says: {text[:100]}...")
                    await self._notify("text_response", text)
            elif isinstance(data.get("text"), str):
                print(f"[ElevenLabs] 🤖 Agent says (alt): {data['text'][:100]}...")
                await self._notify("text_response", data["text"])
            
            # Ping - respond to keep connection alive
            if evt_type == "ping":
                await self._notify("ping", data)
            
            # User transcript - check multiple formats
            user_text = None
            if "user_transcript" in data:
                user_text = data["user_transcript"]
            elif "user_transcription_event" in data:
                user_text = data["user_transcription_event"].get("user_transcript") or data["user_transcription_event"].get("text")
            elif evt_type == "user_transcript":
                user_text = data.get("text") or data.get("transcript")
            
            if user_text:
                print(f"[ElevenLabs] 👤 User said: {user_text}")
                await self._notify("user_transcript", user_text)
            
            # Tool calls (like end_call) - handle various formats
            if "tool_call" in data:
                await self._notify("tool_call", data["tool_call"])
            elif "tool_calls" in data:
                for tool_call in data["tool_calls"]:
                    await self._notify("tool_call", tool_call)
            elif "function_call" in data:
                await self._notify("tool_call", data["function_call"])
            elif "function_calls" in data:
                for func_call in data["function_calls"]:
                    await self._notify("tool_call", func_call)
            # Check for tool calls nested in agent response events
            elif "agent_response_event" in data:
                agent_event = data["agent_response_event"]
                if "tool_call" in agent_event:
                    await self._notify("tool_call", agent_event["tool_call"])
                elif "tool_calls" in agent_event:
                    for tool_call in agent_event["tool_calls"]:
                        await self._notify("tool_call", tool_call)
            
            # Errors
            if "error" in data:
                await self._notify("error", data["error"])
                
        except Exception as e:
            print(f"[ElevenLabs] Event handling error: {e}")
    
    async def start_conversation(self) -> bool:
        """Start the conversation (wait for initiation metadata)"""
        if not self.is_connected and not await self.connect():
            return False
        
        # Wait for conversation ready (server sends initiation metadata)
        start = time.time()
        timeout = 5.0
        while time.time() - start < timeout:
            if self._conversation_ready:
                print("[ElevenLabs] Conversation ready")
                return True
            await asyncio.sleep(0.05)
        
        print("[ElevenLabs] Conversation initiation timeout")
        return False
    
    async def queue_pcm(self, pcm16: bytes):
        """Queue PCM audio for sending to ElevenLabs"""
        if not self.is_connected or not pcm16:
            return
        
        # Buffer audio before conversation is ready
        if not self._conversation_ready:
            self._pending_audio_before_ready.append(pcm16)
            if len(self._pending_audio_before_ready) > 10:
                self._pending_audio_before_ready.pop(0)
            return
        
        # Add to buffer
        self._pcm_buffer.extend(pcm16)
        
        # Flush when buffer is large enough or time threshold
        buffer_size = len(self._pcm_buffer)
        time_since_flush = time.time() - self._last_flush
        
        if buffer_size >= self._flush_bytes or time_since_flush > 0.1:
            await self.flush()
    
    async def flush(self):
        """Flush audio buffer to ElevenLabs"""
        if not self._pcm_buffer:
            return
        
        chunk = bytes(self._pcm_buffer)
        self._pcm_buffer.clear()
        await self._send_chunk(chunk)
        self._last_flush = time.time()
    
    async def _send_chunk(self, pcm16: bytes):
        """Send audio chunk to ElevenLabs"""
        if not (self.websocket and self.is_connected):
            return
        
        if not pcm16 or len(pcm16) == 0:
            return
        
        try:
            # Ensure even byte length
            if len(pcm16) % 2 != 0:
                pcm16 = pcm16 + b'\x00'
            
            b64 = base64.b64encode(pcm16).decode("utf-8")
            
            # Payload variants (ordered by most common first)
            variants = [
                {"user_audio_chunk": b64},
                {"type": "user_audio_chunk", "user_audio_chunk": b64},
                {"audio_base64": b64},
                {"type": "audio", "audio_base64": b64},
            ]
            
            # Use cached format if available
            if self._successful_payload_format is not None:
                try:
                    payload = variants[self._successful_payload_format]
                    await self.websocket.send(json.dumps(payload))
                    return
                except Exception:
                    self._successful_payload_format = None
            
            # Try each variant
            for idx, payload in enumerate(variants):
                try:
                    await self.websocket.send(json.dumps(payload))
                    self._successful_payload_format = idx
                    print(f"[ElevenLabs] Sent {len(pcm16)} bytes using format #{idx}")
                    return
                except Exception:
                    if idx == len(variants) - 1:
                        raise
                    continue
                    
        except Exception as e:
            # Handle graceful close
            if "1000" in str(e):
                print(f"[ElevenLabs] Connection closed gracefully")
                self.is_connected = False
                return
            
            print(f"[ElevenLabs] Send error: {e}")
            self.is_connected = False
    
    def register_callback(self, event: str, cb: Callable):
        """Register a callback for an event type"""
        self.response_callbacks[event] = cb
    
    async def _notify(self, event: str, payload: Any):
        """Notify registered callbacks"""
        cb = self.response_callbacks.get(event)
        if not cb:
            return
        
        try:
            if asyncio.iscoroutinefunction(cb):
                await cb(payload)
            else:
                cb(payload)
        except Exception as e:
            print(f"[ElevenLabs] Callback error for {event}: {e}")
    
    def is_ready(self) -> bool:
        """Check if handler is ready"""
        return self.is_connected and self.websocket is not None


class JitsiElevenLabsBridge:
    """Bridge between Jitsi audio and ElevenLabs conversation"""
    
    def __init__(self, api_key: str = None, agent_id: str = None, dynamic_variables: Dict[str, str] = None):
        self.api_key = api_key or settings.ELEVENLABS_API_KEY
        self.agent_id = agent_id or getattr(settings, 'ELEVENLABS_AGENT_ID', '')
        self.dynamic_variables = dynamic_variables or {}
        self.handler = ElevenLabsVoiceHandler(self.api_key, self.agent_id, self.dynamic_variables)
        self._started = False
    
    def set_dynamic_variables(self, variables: Dict[str, str]):
        """Set dynamic variables (call before initialize)"""
        self.dynamic_variables = variables
        self.handler.dynamic_variables = variables
    
    async def initialize(self) -> bool:
        """Initialize the bridge"""
        return await self.handler.connect()
    
    async def process_audio_chunk(self, pcm16: bytes):
        """Process audio from Jitsi"""
        if not self._started:
            return
        await self.handler.queue_pcm(pcm16)
    
    def register_audio_callback(self, cb: Callable):
        """Register callback for AI audio responses"""
        self.handler.register_callback("audio_response", cb)
    
    def register_text_callback(self, cb: Callable):
        """Register callback for AI text responses"""
        self.handler.register_callback("text_response", cb)
    
    def register_error_callback(self, cb: Callable):
        """Register callback for errors"""
        self.handler.register_callback("error", cb)
    
    def register_tool_callback(self, cb: Callable):
        """Register callback for tool calls (like end_call)"""
        self.handler.register_callback("tool_call", cb)
    
    def register_user_transcript_callback(self, cb: Callable):
        """Register callback for user transcripts"""
        self.handler.register_callback("user_transcript", cb)
    
    async def start_conversation(self) -> bool:
        """Start the conversation"""
        if not self._started:
            self._started = await self.handler.start_conversation()
        return self._started
    
    def has_started(self) -> bool:
        """Check if conversation has started"""
        return self._started
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.handler.flush()
        await self.handler.disconnect()
    
    def is_ready(self) -> bool:
        """Check if bridge is ready"""
        return self.handler.is_ready()


# Legacy compatibility - keep the old service for TTS-only use cases
class ElevenLabsTTSService:
    """Text-to-Speech service (for non-realtime use cases)"""
    
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.voice_id = settings.ELEVENLABS_VOICE_ID
        self.base_url = "https://api.elevenlabs.io/v1"
    
    async def generate_speech(self, text: str) -> bytes:
        """Generate speech from text (HTTP API)"""
        import httpx
        
        url = f"{self.base_url}/text-to-speech/{self.voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.content


# Singleton instances
elevenlabs_tts_service = ElevenLabsTTSService()
