"""
Voice WebSocket Endpoint for StandupAI
Handles real-time voice conversations during standups using ElevenLabs ConvAI
"""

import asyncio
import json
import math
import time
from typing import Dict, Optional

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.config import settings
from app.services.elevenlabs_service import JitsiElevenLabsBridge
from app.services.standup_summary_service import standup_summary_service


class StandupVoiceSession:
    """Manages a voice session for a standup meeting"""
    
    def __init__(self, standup_id: str, websocket: WebSocket, team_id: str = None, slack_channel_id: str = None):
        self.standup_id = standup_id
        self.websocket = websocket
        self.bridge: Optional[JitsiElevenLabsBridge] = None
        self.is_active = False
        
        # Standup configuration
        self.team_id = team_id
        self.slack_channel_id = slack_channel_id
        
        # VAD (Voice Activity Detection) tracking
        self._pre_start_chunks = 0
        self._rms_accum = 0.0
        self._rms_samples = 0
        self._conversation_started = False
        
        # Session timing
        self._start_time: Optional[float] = None
        self._max_duration_minutes: Optional[int] = 30  # Default 30 min max
        
        # Transcripts
        self.user_transcripts: list = []
        self.agent_transcripts: list = []
    
    async def initialize(self, agent_id: str = None) -> bool:
        """Initialize the voice session - creates bridge but defers connection until start_agent"""
        import logging
        logger = logging.getLogger("voice.session")
        
        try:
            logger.info(f"[VoiceSession {self.standup_id}] Initializing with agent_id: {agent_id}")
            
            # Store agent_id for later use when connecting
            self._agent_id = agent_id or getattr(settings, 'ELEVENLABS_AGENT_ID', '')
            
            # Create ElevenLabs bridge (but don't connect yet - wait for issues context)
            self.bridge = JitsiElevenLabsBridge(
                api_key=settings.ELEVENLABS_API_KEY,
                agent_id=self._agent_id
            )
            
            # Register callbacks
            self.bridge.register_audio_callback(self._on_audio_response)
            self.bridge.register_text_callback(self._on_text_response)
            self.bridge.register_error_callback(self._on_error)
            self.bridge.register_tool_callback(self._on_tool_call)
            self.bridge.register_user_transcript_callback(self._on_user_transcript)
            
            self.is_active = True
            logger.info(f"[VoiceSession {self.standup_id}] Callbacks registered, waiting for user to join meeting...")
            
            # DON'T CONNECT YET - Wait for user_joined which triggers start_agent
            # This allows us to fetch issues and pass them as dynamic variables
            await self.websocket.send_json({
                "type": "status",
                "message": "AI ready - waiting for you to join the meeting...",
                "status": "ready",
                "started": False
            })
            
            return True
            
        except Exception as e:
            logger.error(f"[VoiceSession {self.standup_id}] Initialization error: {e}")
            await self.websocket.send_json({
                "type": "error",
                "message": f"Initialization failed: {str(e)}"
            })
            return False
    
    async def start_agent(self, issues_context: list = None) -> bool:
        """Start the AI agent conversation - called when user joins meeting
        
        Args:
            issues_context: Optional list of issues to discuss (passed from frontend)
        """
        import logging
        logger = logging.getLogger("voice.session")
        
        if not self.bridge or self._conversation_started:
            return False
        
        logger.info(f"[VoiceSession {self.standup_id}] User joined meeting, starting agent...")
        
        # Store issues context for summary processing
        self.issues_context = issues_context or []
        
        # If no issues passed but we have team_id, try to fetch from Linear
        if not self.issues_context and self.team_id:
            try:
                logger.info(f"[VoiceSession {self.standup_id}] Fetching issues from Linear for team {self.team_id}")
                from app.services.linear_service import linear_service
                issues = await linear_service.get_team_issues(self.team_id, active_only=True)
                self.issues_context = issues or []
                logger.info(f"[VoiceSession {self.standup_id}] Fetched {len(self.issues_context)} issues from Linear")
            except Exception as e:
                logger.warning(f"[VoiceSession {self.standup_id}] Could not fetch issues: {e}")
                self.issues_context = []
        
        # Format issues for the agent as dynamic variables
        if self.issues_context:
            issues_list = []
            for issue in self.issues_context:
                # Handle both dict and object formats
                if isinstance(issue, dict):
                    identifier = issue.get('identifier', 'UNKNOWN')
                    title = issue.get('title', 'No title')
                    assignee = issue.get('assignee', {})
                    assignee_name = assignee.get('name', 'Unassigned') if isinstance(assignee, dict) else 'Unassigned'
                else:
                    identifier = getattr(issue, 'identifier', 'UNKNOWN')
                    title = getattr(issue, 'title', 'No title')
                    assignee_name = getattr(getattr(issue, 'assignee', None), 'name', 'Unassigned')
                
                # Use explicit labeled format for better LLM parsing
                issues_list.append(f"ID: {identifier} | TITLE: {title} | ASSIGNEE: {assignee_name}")
            
            issues_text = "\n".join(issues_list)
            logger.info(f"[VoiceSession {self.standup_id}] Setting issues context for agent:\n{issues_text}")
            
            # Set dynamic variables on the bridge
            self.bridge.set_dynamic_variables({
                "issues_list": issues_text,
                "issues_count": str(len(self.issues_context)),
                "team_id": self.team_id or "Unknown"
            })
        else:
            logger.info(f"[VoiceSession {self.standup_id}] No issues to set for agent")
        
        # NOW connect to ElevenLabs (with dynamic variables already set)
        logger.info(f"[VoiceSession {self.standup_id}] Connecting to ElevenLabs...")
        if not await self.bridge.initialize():
            logger.error(f"[VoiceSession {self.standup_id}] Failed to connect to ElevenLabs")
            await self.websocket.send_json({
                "type": "error",
                "message": "Failed to connect to voice AI service"
            })
            return False
        
        ok = await self.bridge.start_conversation()
        if ok:
            self._start_time = time.time()
            self._conversation_started = True
            logger.info(f"[VoiceSession {self.standup_id}] Agent started successfully!")
            
            await self.websocket.send_json({
                "type": "status",
                "message": "AI Agent started! Listening...",
                "status": "started",
                "started": True,
                "reason": "user_joined",
                "issues_count": len(self.issues_context)
            })
            return True
        else:
            logger.error(f"[VoiceSession {self.standup_id}] Failed to start agent")
            return False
    
    async def process_audio(self, audio_data: bytes):
        """Process incoming audio from the user"""
        if not self.is_active or not self.bridge:
            return
        
        try:
            # If conversation hasn't started, check VAD
            if not self.bridge.has_started():
                speech, rms = self._is_speech(audio_data, return_rms=True)
                self._pre_start_chunks += 1
                self._rms_accum += rms
                self._rms_samples += 1
                avg_rms = self._rms_accum / self._rms_samples if self._rms_samples else 0
                
                # Start conditions
                vad_threshold = 0.002
                should_start = (
                    speech or
                    (self._pre_start_chunks >= 30 and avg_rms > 0.008) or
                    self._pre_start_chunks >= 100  # Auto-start after ~3s
                )
                
                if should_start:
                    ok = await self.bridge.start_conversation()
                    if ok:
                        self._start_time = time.time()
                        self._conversation_started = True
                        
                        reason = "speech" if speech else ("avg_rms" if avg_rms > 0.008 else "auto")
                        await self.websocket.send_json({
                            "type": "status",
                            "message": "Conversation started",
                            "status": "started",
                            "started": True,
                            "reason": reason
                        })
                        print(f"[VoiceSession {self.standup_id}] Conversation started: {reason}")
                
                if not self.bridge.has_started():
                    return
            
            # Forward audio to ElevenLabs
            await self.bridge.process_audio_chunk(audio_data)
            
        except Exception as e:
            print(f"[VoiceSession {self.standup_id}] Audio processing error: {e}")
    
    def _is_speech(self, pcm16: bytes, return_rms: bool = False):
        """Simple energy-based VAD"""
        if not pcm16:
            return (False, 0.0) if return_rms else False
        
        sample_count = len(pcm16) // 2
        if sample_count == 0:
            return (False, 0.0) if return_rms else False
        
        total = 0.0
        step = 4
        limit = sample_count - (sample_count % step)
        
        for i in range(0, limit, step):
            lo = pcm16[2 * i]
            hi = pcm16[2 * i + 1]
            val = (hi << 8) | lo
            if val & 0x8000:
                val = -((~val & 0xFFFF) + 1)
            total += (val * val)
        
        used = limit // step if step else sample_count
        if used == 0:
            return (False, 0.0) if return_rms else False
        
        rms = math.sqrt(total / used) / 32768.0
        is_speech = rms > 0.002  # Threshold
        
        return (is_speech, rms) if return_rms else is_speech
    
    async def _on_audio_response(self, audio_data: bytes):
        """Handle AI audio response"""
        if not self.is_active:
            return
        
        try:
            print(f"[VoiceSession {self.standup_id}] 🔊 Sending {len(audio_data)} bytes audio to frontend")
            # Send audio bytes to client
            await self.websocket.send_bytes(audio_data)
            
            # Also send metadata
            await self.websocket.send_json({
                "type": "audio_response",
                "size": len(audio_data),
                "timestamp": time.time()
            })
        except (WebSocketDisconnect, RuntimeError) as e:
            print(f"[VoiceSession {self.standup_id}] Client disconnected during audio send")
            self.is_active = False
        except Exception as e:
            print(f"[VoiceSession {self.standup_id}] Error sending audio: {e}")
    
    async def _on_text_response(self, text: str):
        """Handle AI text response"""
        if not self.is_active:
            return
        
        self.agent_transcripts.append({
            "text": text,
            "timestamp": time.time()
        })
        
        try:
            await self.websocket.send_json({
                "type": "agent_transcript",
                "text": text,
                "timestamp": time.time()
            })
        except Exception as e:
            print(f"[VoiceSession {self.standup_id}] Error sending text: {e}")
    
    async def _on_user_transcript(self, text: str):
        """Handle user transcript from ElevenLabs STT"""
        if not self.is_active:
            return
        
        print(f"[VoiceSession {self.standup_id}] 📝 User transcript: {text}")
        
        self.user_transcripts.append({
            "text": text,
            "timestamp": time.time()
        })
        
        print(f"[VoiceSession {self.standup_id}] Total user transcripts: {len(self.user_transcripts)}")
        
        try:
            await self.websocket.send_json({
                "type": "user_transcript",
                "text": text,
                "timestamp": time.time()
            })
        except Exception as e:
            print(f"[VoiceSession {self.standup_id}] Error sending user transcript: {e}")
    
    async def _on_error(self, error: str):
        """Handle errors from ElevenLabs"""
        try:
            await self.websocket.send_json({
                "type": "error",
                "message": f"Voice AI error: {error}",
                "timestamp": time.time()
            })
        except Exception as e:
            print(f"[VoiceSession {self.standup_id}] Error sending error: {e}")
    
    async def _on_tool_call(self, tool_data: dict):
        """Handle tool calls from AI (like end_call)"""
        tool_name = tool_data.get("name") or tool_data.get("tool_name")
        
        if tool_name == "end_call":
            print(f"[VoiceSession {self.standup_id}] AI requested to end call")
            await self._end_session("ai_requested")
    
    async def _end_session(self, reason: str = "unknown"):
        """End the voice session and process summary"""
        import logging
        from starlette.websockets import WebSocketState
        logger = logging.getLogger("voice.session")
        
        if not self.is_active:
            logger.info(f"[VoiceSession {self.standup_id}] Session already inactive, skipping end")
            return
        
        logger.info(f"[VoiceSession {self.standup_id}] Ending session: {reason}")
        logger.info(f"[VoiceSession {self.standup_id}] User transcripts: {len(self.user_transcripts)}, Agent transcripts: {len(self.agent_transcripts)}")
        logger.info(f"[VoiceSession {self.standup_id}] Conversation started: {self._conversation_started}, Team ID: {self.team_id}, Slack: {self.slack_channel_id}")
        
        duration = time.time() - self._start_time if self._start_time else 0
        
        # Helper to check if WebSocket is still open
        def ws_is_open():
            try:
                return self.websocket.client_state == WebSocketState.CONNECTED
            except:
                return False
        
        # Process summary if we have transcripts and configuration
        summary_result = None
        if (self.user_transcripts or self.agent_transcripts) and self._conversation_started:
            try:
                logger.info(f"[VoiceSession {self.standup_id}] Starting summary processing...")
                logger.info(f"[VoiceSession {self.standup_id}] User transcripts: {len(self.user_transcripts)}")
                logger.info(f"[VoiceSession {self.standup_id}] Agent transcripts: {len(self.agent_transcripts)}")
                logger.info(f"[VoiceSession {self.standup_id}] Issues context: {len(getattr(self, 'issues_context', []))}")
                
                # Log sample transcripts for debugging
                if self.user_transcripts:
                    logger.info(f"[VoiceSession {self.standup_id}] User said: {[t.get('text', '')[:50] for t in self.user_transcripts[:3]]}")
                if self.agent_transcripts:
                    logger.info(f"[VoiceSession {self.standup_id}] Agent said: {[t.get('text', '')[:50] for t in self.agent_transcripts[:3]]}")
                
                # Only send status if WebSocket is still open
                if ws_is_open():
                    try:
                        await self.websocket.send_json({
                            "type": "status",
                            "message": "Processing standup summary...",
                            "status": "processing_summary"
                        })
                    except Exception:
                        pass  # Continue processing even if we can't send status
                
                summary_result = await standup_summary_service.process_session_end(
                    standup_id=self.standup_id,
                    user_transcripts=self.user_transcripts,
                    agent_transcripts=self.agent_transcripts,
                    team_id=self.team_id or "",
                    slack_channel_id=self.slack_channel_id or "",
                    issues_discussed=getattr(self, 'issues_context', None)
                )
                
                logger.info(f"[VoiceSession {self.standup_id}] Summary processed successfully!")
                logger.info(f"[VoiceSession {self.standup_id}] - Updates: {summary_result.total_updates}")
                logger.info(f"[VoiceSession {self.standup_id}] - Linear comments: {summary_result.linear_comments_posted}")
                logger.info(f"[VoiceSession {self.standup_id}] - Escalations: {len(summary_result.escalations_created)}")
                logger.info(f"[VoiceSession {self.standup_id}] - Slack posted: {summary_result.slack_posted}")
                if summary_result.errors:
                    logger.warning(f"[VoiceSession {self.standup_id}] - Errors: {summary_result.errors}")
                
            except Exception as e:
                logger.error(f"[VoiceSession {self.standup_id}] Summary processing error: {e}", exc_info=True)
                summary_result = None
        else:
            logger.info(f"[VoiceSession {self.standup_id}] Skipping summary: no transcripts or conversation not started")
        
        # Only try to send response if WebSocket is still open
        if ws_is_open():
            try:
                response = {
                    "type": "session_ended",
                    "reason": reason,
                    "duration_seconds": duration,
                    "user_transcripts": self.user_transcripts,
                    "agent_transcripts": self.agent_transcripts,
                    "timestamp": time.time()
                }
                
                # Include summary if available
                if summary_result:
                    response["summary"] = {
                        "processed": True,
                        "total_updates": summary_result.total_updates,
                        "linear_comments_posted": summary_result.linear_comments_posted,
                        "escalations_created": summary_result.escalations_created,
                        "slack_posted": summary_result.slack_posted,
                        "summary_text": summary_result.summary_text,
                        "issue_updates": summary_result.issue_updates,
                        "errors": summary_result.errors
                    }
                
                await self.websocket.send_json(response)
                logger.info(f"[VoiceSession {self.standup_id}] Session ended response sent to client")
            except Exception as e:
                logger.info(f"[VoiceSession {self.standup_id}] Could not send session_ended (client disconnected): {e}")
        else:
            logger.info(f"[VoiceSession {self.standup_id}] WebSocket already closed, skipping response send")
        
        self.is_active = False
    
    async def cleanup(self):
        """Cleanup session resources"""
        self.is_active = False
        
        if self.bridge:
            await self.bridge.cleanup()
        
        print(f"[VoiceSession {self.standup_id}] Cleaned up")
    
    def get_transcripts(self) -> dict:
        """Get all transcripts from the session"""
        return {
            "user": self.user_transcripts,
            "agent": self.agent_transcripts
        }


# Active sessions tracking
active_voice_sessions: Dict[str, StandupVoiceSession] = {}


async def handle_voice_websocket(
    websocket: WebSocket, 
    standup_id: str, 
    agent_id: str = None,
    team_id: str = None,
    slack_channel_id: str = None
):
    """Handle voice WebSocket connection for a standup"""
    await websocket.accept()
    
    print(f"[Voice] New connection for standup: {standup_id}")
    
    # Create session with configuration
    session = StandupVoiceSession(
        standup_id=standup_id, 
        websocket=websocket,
        team_id=team_id,
        slack_channel_id=slack_channel_id
    )
    active_voice_sessions[standup_id] = session
    
    try:
        # Initialize voice session
        if not await session.initialize(agent_id):
            print(f"[Voice] Failed to initialize session for {standup_id}")
            return
        
        # Main message loop
        while session.is_active:
            try:
                message = await websocket.receive()
                
                if "bytes" in message:
                    # Audio data from client
                    audio_data = message["bytes"]
                    await session.process_audio(audio_data)
                    
                elif "text" in message:
                    # JSON message
                    try:
                        data = json.loads(message["text"])
                        msg_type = data.get("type")
                        
                        if msg_type == "ping":
                            await websocket.send_json({"type": "pong"})
                        elif msg_type == "stop":
                            await session._end_session("user_stopped")
                            break
                        elif msg_type == "user_joined":
                            # User joined the Jitsi meeting - start the agent now
                            # Optionally receive issues context from frontend
                            issues_context = data.get("issues", [])
                            print(f"[Voice] User joined meeting, starting agent for {standup_id} with {len(issues_context)} issues")
                            await session.start_agent(issues_context=issues_context)
                        elif msg_type == "force_start":
                            if session.bridge and not session.bridge.has_started():
                                ok = await session.bridge.start_conversation()
                                await websocket.send_json({
                                    "type": "status",
                                    "status": "started" if ok else "error",
                                    "started": ok,
                                    "reason": "force"
                                })
                        elif msg_type == "get_transcripts":
                            await websocket.send_json({
                                "type": "transcripts",
                                "data": session.get_transcripts()
                            })
                                
                    except json.JSONDecodeError:
                        pass
                        
                elif message.get("type") == "websocket.disconnect":
                    break
                    
            except WebSocketDisconnect:
                print(f"[Voice] WebSocket disconnected for {standup_id}")
                break
            except RuntimeError as e:
                if "disconnect" in str(e).lower():
                    break
                print(f"[Voice] Runtime error for {standup_id}: {e}")
                break
            except Exception as e:
                print(f"[Voice] Error in message loop for {standup_id}: {e}")
                break
    
    except Exception as e:
        print(f"[Voice] Session error for {standup_id}: {e}")
    
    finally:
        # CRITICAL: Call _end_session BEFORE cleanup to trigger post-call processing
        # This ensures summary generation, Linear updates, and Slack notifications happen
        if session.is_active and session._conversation_started:
            print(f"[Voice] WebSocket disconnected, triggering session end processing for {standup_id}")
            try:
                await session._end_session("websocket_disconnect")
            except Exception as e:
                print(f"[Voice] Error in session end processing: {e}")
        
        # Cleanup
        await session.cleanup()
        if standup_id in active_voice_sessions:
            del active_voice_sessions[standup_id]
        print(f"[Voice] Session ended for {standup_id}")


def get_active_voice_session_count() -> int:
    """Get count of active voice sessions"""
    return len(active_voice_sessions)


def get_voice_session_status(standup_id: str) -> Optional[dict]:
    """Get status of a voice session"""
    session = active_voice_sessions.get(standup_id)
    if not session:
        return None
    
    return {
        "active": session.is_active,
        "started": session._conversation_started,
        "duration": time.time() - session._start_time if session._start_time else 0
    }
