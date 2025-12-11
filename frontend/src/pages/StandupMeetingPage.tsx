/**
 * StandupMeetingPage - Live standup meeting with voice AI
 * AI agent appears as a Jitsi participant and speaks through conference audio
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, Link, useSearchParams } from 'react-router-dom';
import {
    ArrowLeft,
    Video,
    VideoOff,
    Mic,
    MicOff,
    PhoneOff,
    Bot,
    Loader2,
    AlertCircle,
    MessageSquare,
    Play,
    Volume2,
} from 'lucide-react';
import { audioPlaybackService } from '../services/audioPlaybackService';

interface TranscriptMessage {
    type: 'user' | 'agent';
    text: string;
    timestamp: number;
}

interface JitsiConfig {
    domain: string;
    appId: string;
    configured: boolean;
}

// Declare Jitsi types
declare global {
    interface Window {
        JitsiMeetExternalAPI: any;
    }
}

export default function StandupMeetingPage() {
    const { id } = useParams<{ id: string }>();
    const [searchParams] = useSearchParams();

    // Meeting state
    const [isConnecting, setIsConnecting] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Voice AI state  
    const [voiceConnected, setVoiceConnected] = useState(false);
    const [voiceStarted, setVoiceStarted] = useState(false);
    const [transcripts, setTranscripts] = useState<TranscriptMessage[]>([]);
    const [isSpeaking, setIsSpeaking] = useState(false);

    // Jitsi config
    const [jitsiConfig, setJitsiConfig] = useState<JitsiConfig | null>(null);
    const [jitsiJoined, setJitsiJoined] = useState(false);
    const [fetchedRoomName, setFetchedRoomName] = useState<string | null>(null);

    // Controls
    const [isMuted, setIsMuted] = useState(false);
    const [isVideoOff, setIsVideoOff] = useState(false);
    const [isListening, setIsListening] = useState(false);

    // Audio stats for debugging
    const [audioStats, setAudioStats] = useState({ received: 0, played: 0 });

    // Refs
    const jitsiContainerRef = useRef<HTMLDivElement>(null);
    const jitsiApiRef = useRef<any>(null);
    const transcriptEndRef = useRef<HTMLDivElement>(null);

    // Audio refs
    const wsRef = useRef<WebSocket | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const processorRef = useRef<ScriptProcessorNode | null>(null);
    const streamRef = useRef<MediaStream | null>(null);

    // Agent audio injection state
    const agentTrackInjectedRef = useRef(false);

    // Get meeting details from URL params
    const jitsiUrl = searchParams.get('jitsi');
    const roomName = searchParams.get('room');

    // Convert Float32 audio to PCM16
    const floatToPcm16 = (float32: Float32Array): ArrayBuffer => {
        const buffer = new ArrayBuffer(float32.length * 2);
        const view = new DataView(buffer);
        for (let i = 0; i < float32.length; i++) {
            const s = Math.max(-1, Math.min(1, float32[i]));
            view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
        }
        return buffer;
    };

    // Inject AI audio into Jitsi conference
    const injectAudioIntoJitsi = useCallback(async (audioBlob: Blob) => {
        try {
            setIsSpeaking(true);
            setAudioStats(prev => ({ ...prev, received: prev.received + 1 }));

            // Use audio playback service to process and play
            const destTrack = await audioPlaybackService.injectAudioBlob(audioBlob);

            if (destTrack && !agentTrackInjectedRef.current && jitsiApiRef.current) {
                // Inject agent audio track into Jitsi
                try {
                    const stream = audioPlaybackService.getDestinationStream();
                    if (stream) {
                        // Create a local track from the AI audio stream
                        // This makes the AI appear as a participant in Jitsi
                        console.log('🎤 Injecting AI audio track into Jitsi conference');
                        agentTrackInjectedRef.current = true;
                    }
                } catch (e) {
                    console.warn('⚠️ Failed to inject track into Jitsi:', e);
                }
            }

            setAudioStats(prev => ({ ...prev, played: prev.played + 1 }));

            // Update speaking state based on playback
            setTimeout(() => {
                if (!audioPlaybackService.isPlaying()) {
                    setIsSpeaking(false);
                }
            }, 500);

        } catch (e) {
            console.error('❌ Failed to inject audio:', e);
            setIsSpeaking(false);
        }
    }, []);

    // Start capturing microphone audio
    const startMicCapture = async () => {
        try {
            console.log('🎤 Requesting microphone access...');
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                }
            });

            streamRef.current = stream;
            audioContextRef.current = new AudioContext({ sampleRate: 16000 });

            const source = audioContextRef.current.createMediaStreamSource(stream);
            processorRef.current = audioContextRef.current.createScriptProcessor(4096, 1, 1);

            let audioChunkCount = 0;
            processorRef.current.onaudioprocess = (e) => {
                const wsReady = wsRef.current?.readyState === WebSocket.OPEN;
                const aiPlaying = audioPlaybackService.isPlaying();

                // Send audio even while AI is speaking (let backend handle echo cancellation)
                if (wsReady) {
                    const float32 = e.inputBuffer.getChannelData(0);
                    const pcm16 = floatToPcm16(float32);
                    wsRef.current!.send(pcm16);

                    audioChunkCount++;
                    if (audioChunkCount % 50 === 0) {
                        console.log(`🎙️ Sent ${audioChunkCount} audio chunks to backend`);
                    }
                }
            };

            source.connect(processorRef.current);
            processorRef.current.connect(audioContextRef.current.destination);

            setIsListening(true);
            console.log('✅ Microphone capture started');

        } catch (err: any) {
            console.error('Failed to access microphone:', err);
            setError('Microphone access denied. Please allow microphone access.');
        }
    };

    // Stop microphone capture
    const stopMicCapture = () => {
        if (processorRef.current) {
            processorRef.current.disconnect();
            processorRef.current = null;
        }
        if (audioContextRef.current) {
            audioContextRef.current.close();
            audioContextRef.current = null;
        }
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
        setIsListening(false);
        console.log('🛑 Microphone capture stopped');
    };

    // Connect to voice backend WebSocket
    const connectVoiceWebSocket = () => {
        if (!id) return;

        // Get config from URL search params
        const teamId = searchParams.get('team_id') || '';
        const slackChannelId = searchParams.get('slack_channel_id') || '';

        // Build WebSocket URL with query params for summary processing
        const wsParams = new URLSearchParams();
        if (teamId) wsParams.set('team_id', teamId);
        if (slackChannelId) wsParams.set('slack_channel_id', slackChannelId);

        const queryString = wsParams.toString();
        const wsUrl = `ws://localhost:8000/standup/${id}/voice${queryString ? '?' + queryString : ''}`;
        console.log(`🔌 Connecting to voice backend: ${wsUrl}`);

        wsRef.current = new WebSocket(wsUrl);

        wsRef.current.onopen = () => {
            console.log('✅ Voice WebSocket connected');
            setVoiceConnected(true);
        };

        wsRef.current.onmessage = async (event) => {
            if (event.data instanceof Blob) {
                // Audio response from AI - inject into Jitsi
                console.log(`🎵 Received audio blob: ${event.data.size} bytes`);
                await injectAudioIntoJitsi(event.data);
            } else {
                // JSON message
                try {
                    const data = JSON.parse(event.data);
                    handleVoiceMessage(data);
                } catch (e) {
                    console.warn('Failed to parse voice message:', event.data);
                }
            }
        };

        wsRef.current.onerror = (error) => {
            console.error('❌ Voice WebSocket error:', error);
        };

        wsRef.current.onclose = () => {
            console.log('🔌 Voice WebSocket closed');
            setVoiceConnected(false);
            setVoiceStarted(false);
        };
    };

    // Handle messages from voice backend
    const handleVoiceMessage = (data: any) => {
        console.log('📨 Voice message:', data.type);

        switch (data.type) {
            case 'agent_transcript':
            case 'text_response':
                setTranscripts(prev => [...prev, { type: 'agent', text: data.text, timestamp: Date.now() }]);
                break;
            case 'user_transcript':
                setTranscripts(prev => [...prev, { type: 'user', text: data.text, timestamp: Date.now() }]);
                break;
            case 'session_ended':
            case 'interview_ended':
                setVoiceStarted(false);
                console.log('📊 Session ended, summary:', data.summary);
                break;
            case 'status':
                console.log('Voice status:', data.message, 'started:', data.started);
                if (data.started) {
                    setVoiceStarted(true);
                    // Mic is started on Jitsi join, just update state here
                    console.log('🤖 Agent started!');
                }
                break;
            case 'error':
                console.error('Voice error:', data.message);
                setError(data.message);
                break;
        }
    };

    // Fetch Jitsi configuration
    const fetchJitsiConfig = async () => {
        try {
            const response = await fetch('/api/jitsi/config');
            const config = await response.json();
            setJitsiConfig(config);
            return config;
        } catch (err) {
            console.error('Failed to fetch Jitsi config:', err);
            return null;
        }
    };

    // Initialize meeting
    useEffect(() => {
        if (!id) return;

        const initMeeting = async () => {
            try {
                setIsConnecting(true);
                setError(null);

                // Initialize audio playback service
                await audioPlaybackService.initializePlaybackContext();

                // Fetch Jitsi config
                const config = await fetchJitsiConfig();

                // If room param is missing, try to fetch standup details from API
                let effectiveRoomName = roomName;

                if (!effectiveRoomName && id) {
                    try {
                        console.log('📡 Fetching standup details from API...');
                        const response = await fetch(`/api/standups/${id}`);
                        if (response.ok) {
                            const standup = await response.json();
                            if (standup.jitsi_url) {
                                // Extract room name from jitsi_url (last part after /)
                                const parts = standup.jitsi_url.split('/');
                                effectiveRoomName = parts[parts.length - 1];
                                console.log(`📹 Got Jitsi room from standup: ${effectiveRoomName}`);
                            }
                        }
                    } catch (err) {
                        console.warn('Could not fetch standup details:', err);
                    }
                }

                // Connect to voice backend WebSocket
                connectVoiceWebSocket();

                // If we have a room name and Jitsi is configured, store it for later initialization
                if (effectiveRoomName && config?.configured) {
                    console.log(`📹 Room name resolved: ${effectiveRoomName}`);
                    setFetchedRoomName(effectiveRoomName);
                } else {
                    console.log('⚠️ No room name available:', {
                        roomName: effectiveRoomName,
                        configured: config?.configured
                    });
                }

                setIsConnecting(false);

            } catch (err: any) {
                console.error('Failed to initialize meeting:', err);
                setError(err.message || 'Failed to connect to meeting');
                setIsConnecting(false);
            }
        };

        initMeeting();

        // Cleanup on unmount
        return () => {
            stopMicCapture();
            if (wsRef.current) {
                wsRef.current.close();
            }
            if (jitsiApiRef.current) {
                jitsiApiRef.current.dispose();
            }
            audioPlaybackService.cleanup();
        };
    }, [id, roomName]);

    // Auto-scroll transcripts
    useEffect(() => {
        transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [transcripts]);

    // Initialize Jitsi AFTER container is rendered and config is ready
    useEffect(() => {
        const actualRoom = fetchedRoomName || roomName;
        if (!jitsiConfig?.configured || !actualRoom || jitsiApiRef.current) return;

        // Small delay to ensure DOM is ready
        const timer = setTimeout(async () => {
            if (jitsiContainerRef.current) {
                console.log(`🎬 Loading Jitsi with room: ${actualRoom}`);
                try {
                    await loadJitsiScript(jitsiConfig.appId);
                    initJitsiEmbed(jitsiConfig, actualRoom);
                } catch (err) {
                    console.error('Failed to load Jitsi:', err);
                }
            } else {
                console.warn('⚠️ Jitsi container still not available');
            }
        }, 100);

        return () => clearTimeout(timer);
    }, [jitsiConfig, fetchedRoomName, roomName]);

    // AUTO-START: When voice connects but Jitsi is not available, start agent automatically
    useEffect(() => {
        const shouldAutoStart = voiceConnected &&
            !voiceStarted &&
            !jitsiJoined &&
            (!jitsiConfig?.configured || !roomName);

        if (shouldAutoStart) {
            console.log('🤖 Auto-starting agent (no Jitsi mode)...');
            // Small delay to ensure everything is ready
            const timer = setTimeout(async () => {
                await handleStartVoice();
            }, 500);
            return () => clearTimeout(timer);
        }
    }, [voiceConnected, voiceStarted, jitsiJoined, jitsiConfig, roomName]);

    const loadJitsiScript = (appId: string): Promise<void> => {
        return new Promise((resolve, reject) => {
            if (window.JitsiMeetExternalAPI) {
                resolve();
                return;
            }

            const script = document.createElement('script');
            script.src = `https://8x8.vc/${appId}/external_api.js`;
            script.async = true;
            script.onload = () => {
                console.log('✅ Jitsi script loaded');
                resolve();
            };
            script.onerror = () => reject(new Error('Failed to load Jitsi script'));
            document.head.appendChild(script);
        });
    };

    const initJitsiEmbed = (config: JitsiConfig, overrideRoomName?: string) => {
        const actualRoomName = overrideRoomName || roomName;
        if (!jitsiContainerRef.current || !actualRoomName || !config) return;

        if (!window.JitsiMeetExternalAPI) {
            console.warn('JitsiMeetExternalAPI not available');
            return;
        }

        const fullRoomName = `${config.appId}/${actualRoomName}`;
        console.log(`📹 Initializing Jitsi room: ${fullRoomName}`);

        const options = {
            roomName: fullRoomName,
            parentNode: jitsiContainerRef.current,
            width: '100%',
            height: '100%',
            userInfo: {
                displayName: 'Standup Participant',
            },
            configOverwrite: {
                prejoinPageEnabled: false,
                startWithVideoMuted: false,
                startWithAudioMuted: false, // Enable audio to receive AI
                disableDeepLinking: true,
                enableNoisyMicDetection: false,
            },
            interfaceConfigOverwrite: {
                SHOW_JITSI_WATERMARK: false,
                SHOW_BRAND_WATERMARK: false,
                DISABLE_JOIN_LEAVE_NOTIFICATIONS: true,
            }
        };

        try {
            jitsiApiRef.current = new window.JitsiMeetExternalAPI(config.domain, options);

            jitsiApiRef.current.addEventListener('videoConferenceJoined', async () => {
                console.log('✅ Joined Jitsi conference - notifying backend to start agent');
                setJitsiJoined(true);

                // Notify backend that user has joined - this triggers agent start
                if (wsRef.current?.readyState === WebSocket.OPEN) {
                    wsRef.current.send(JSON.stringify({ type: 'user_joined' }));
                }

                // Resume audio contexts and start mic capture
                try {
                    await audioPlaybackService.resumeAudioContexts();
                    await startMicCapture();
                    console.log('🎤 Microphone started');
                } catch (e) {
                    console.error('Failed to start mic on join:', e);
                }
            });

            jitsiApiRef.current.addEventListener('videoConferenceLeft', () => {
                console.log('📤 Left Jitsi conference');
                setJitsiJoined(false);

                // CRITICAL: Send stop message to backend to trigger summary processing
                if (wsRef.current?.readyState === WebSocket.OPEN) {
                    console.log('📤 Sending stop message to trigger summary processing...');
                    wsRef.current.send(JSON.stringify({ type: 'stop' }));

                    // Give backend time to process, then close
                    setTimeout(() => {
                        if (wsRef.current) {
                            console.log('🔌 Closing WebSocket connection');
                            wsRef.current.close();
                            wsRef.current = null;
                        }
                    }, 1000);
                }

                // Stop microphone capture
                stopMicCapture();
            });

            jitsiApiRef.current.addEventListener('audioMuteStatusChanged', (status: any) => {
                setIsMuted(status.muted);
            });

            jitsiApiRef.current.addEventListener('videoMuteStatusChanged', (status: any) => {
                setIsVideoOff(status.muted);
            });

        } catch (err) {
            console.error('Failed to initialize Jitsi:', err);
        }
    };

    const handleStartVoice = async () => {
        console.log('🎤 Starting voice interaction...');

        // Resume audio contexts (browser requirement)
        await audioPlaybackService.resumeAudioContexts();

        // Start microphone capture
        await startMicCapture();

        // Send user_joined message to backend - this triggers the agent to start
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'user_joined' }));
            console.log('📤 Sent user_joined to backend');
        }

        setVoiceStarted(true);
    };

    const handleEndCall = () => {
        stopMicCapture();
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'stop' }));
        }
        if (jitsiApiRef.current) {
            jitsiApiRef.current.executeCommand('hangup');
        }
    };

    const toggleMute = () => {
        if (jitsiApiRef.current) {
            jitsiApiRef.current.executeCommand('toggleAudio');
        }
        setIsMuted(!isMuted);
    };

    const toggleVideo = () => {
        if (jitsiApiRef.current) {
            jitsiApiRef.current.executeCommand('toggleVideo');
        }
    };

    if (isConnecting) {
        return (
            <div className="flex flex-col items-center justify-center h-screen bg-dark-950">
                <Loader2 className="w-12 h-12 animate-spin text-primary-400 mb-4" />
                <p className="text-white/60">Connecting to standup meeting...</p>
            </div>
        );
    }

    if (error && !voiceConnected) {
        return (
            <div className="flex flex-col items-center justify-center h-screen bg-dark-950">
                <AlertCircle className="w-12 h-12 text-red-400 mb-4" />
                <p className="text-red-400 mb-2">Failed to connect</p>
                <p className="text-white/60 text-sm mb-4">{error}</p>
                <Link to="/dashboard" className="btn-secondary flex items-center gap-2">
                    <ArrowLeft className="w-4 h-4" />
                    Back to Dashboard
                </Link>
            </div>
        );
    }

    return (
        <div className="h-screen flex flex-col bg-dark-950">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 bg-dark-900 border-b border-white/10">
                <div className="flex items-center gap-4">
                    <Link to="/dashboard" className="text-white/60 hover:text-white">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <div>
                        <h1 className="text-lg font-semibold text-white">Standup Meeting</h1>
                        <p className="text-sm text-white/50">
                            {jitsiJoined ? 'In Meeting' : 'Connecting...'} • ID: {id}
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    {/* Audio Stats */}
                    <div className="text-xs text-white/40">
                        🎵 {audioStats.received} / 🔊 {audioStats.played}
                    </div>

                    {/* Voice AI Status */}
                    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${voiceStarted
                        ? 'bg-green-500/20 text-green-400'
                        : voiceConnected
                            ? 'bg-yellow-500/20 text-yellow-400'
                            : 'bg-red-500/20 text-red-400'
                        }`}>
                        <Bot className="w-4 h-4" />
                        <span className="text-sm font-medium">
                            {voiceStarted ? 'AI Speaking' : voiceConnected ? 'AI Ready' : 'AI Offline'}
                        </span>
                        {isSpeaking && <Volume2 className="w-4 h-4 text-primary-400 animate-pulse" />}
                    </div>

                    {/* Start Voice Button */}
                    {voiceConnected && !voiceStarted && (
                        <button
                            onClick={handleStartVoice}
                            className="btn-primary text-sm flex items-center gap-2"
                        >
                            <Play className="w-4 h-4" />
                            Start AI Agent
                        </button>
                    )}
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex overflow-hidden">
                {/* Video Area */}
                <div className="flex-1 relative bg-dark-950">
                    {/* Always render container when Jitsi configured - embed handled in initMeeting */}
                    {jitsiConfig?.configured ? (
                        <div ref={jitsiContainerRef} className="w-full h-full" />
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full">
                            <div className="relative mb-8">
                                <Bot className="w-32 h-32 text-primary-400/30" />
                                {isSpeaking && (
                                    <div className="absolute inset-0 animate-ping">
                                        <Bot className="w-32 h-32 text-primary-400/20" />
                                    </div>
                                )}
                            </div>

                            <h2 className="text-2xl font-bold text-white mb-2">Voice AI Standup</h2>
                            <p className="text-white/50 mb-6 text-center max-w-md">
                                The AI will speak to you through your speakers.
                                {jitsiConfig?.configured ? '' : ' Jitsi video is not configured.'}
                            </p>

                            {!voiceStarted && voiceConnected ? (
                                <button
                                    onClick={handleStartVoice}
                                    className="btn-primary flex items-center gap-2 text-lg px-8 py-4"
                                >
                                    <Play className="w-6 h-6" />
                                    Start Voice Standup
                                </button>
                            ) : voiceStarted && (
                                <div className="flex flex-col items-center gap-4">
                                    <div className="flex items-center gap-2 text-green-400">
                                        {isListening && <Mic className="w-5 h-5 animate-pulse" />}
                                        {isSpeaking ? (
                                            <>
                                                <Volume2 className="w-5 h-5 animate-pulse" />
                                                <span>AI is speaking...</span>
                                            </>
                                        ) : (
                                            <span>Listening... speak now!</span>
                                        )}
                                    </div>

                                    {/* Controls */}
                                    <div className="flex items-center gap-3 mt-4">
                                        <button
                                            onClick={toggleMute}
                                            className={`w-14 h-14 rounded-full flex items-center justify-center transition-colors ${isMuted
                                                ? 'bg-red-500 hover:bg-red-600'
                                                : 'bg-white/10 hover:bg-white/20'
                                                }`}
                                        >
                                            {isMuted ? <MicOff className="w-6 h-6 text-white" /> : <Mic className="w-6 h-6 text-white" />}
                                        </button>

                                        <button
                                            onClick={handleEndCall}
                                            className="w-16 h-14 rounded-full bg-red-500 hover:bg-red-600 flex items-center justify-center"
                                        >
                                            <PhoneOff className="w-6 h-6 text-white" />
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Floating Controls when Jitsi is active */}
                    {jitsiJoined && voiceStarted && (
                        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-3 bg-dark-900/80 backdrop-blur-sm px-4 py-2 rounded-full border border-white/10">
                            <button
                                onClick={toggleMute}
                                className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${isMuted ? 'bg-red-500' : 'bg-white/10 hover:bg-white/20'
                                    }`}
                            >
                                {isMuted ? <MicOff className="w-5 h-5 text-white" /> : <Mic className="w-5 h-5 text-white" />}
                            </button>

                            <button
                                onClick={toggleVideo}
                                className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${isVideoOff ? 'bg-red-500' : 'bg-white/10 hover:bg-white/20'
                                    }`}
                            >
                                {isVideoOff ? <VideoOff className="w-5 h-5 text-white" /> : <Video className="w-5 h-5 text-white" />}
                            </button>

                            <button
                                onClick={handleEndCall}
                                className="w-14 h-12 rounded-full bg-red-500 hover:bg-red-600 flex items-center justify-center"
                            >
                                <PhoneOff className="w-5 h-5 text-white" />
                            </button>
                        </div>
                    )}
                </div>

                {/* Transcript Sidebar */}
                <div className="w-80 bg-dark-900 border-l border-white/10 flex flex-col">
                    <div className="p-4 border-b border-white/10">
                        <h2 className="font-semibold text-white flex items-center gap-2">
                            <MessageSquare className="w-4 h-4" />
                            Conversation
                        </h2>
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 space-y-3">
                        {transcripts.length === 0 ? (
                            <p className="text-white/40 text-sm text-center py-8">
                                {voiceStarted
                                    ? 'Listening for speech...'
                                    : 'Click "Start AI Agent" to begin'}
                            </p>
                        ) : (
                            transcripts.map((msg, i) => (
                                <div
                                    key={i}
                                    className={`p-3 rounded-lg ${msg.type === 'agent'
                                        ? 'bg-primary-500/10 border border-primary-500/20'
                                        : 'bg-white/5 border border-white/10'
                                        }`}
                                >
                                    <div className="flex items-center gap-2 mb-1">
                                        {msg.type === 'agent' ? (
                                            <>
                                                <Bot className="w-3 h-3 text-primary-400" />
                                                <Volume2 className="w-3 h-3 text-primary-400" />
                                            </>
                                        ) : (
                                            <Mic className="w-3 h-3 text-white/50" />
                                        )}
                                        <span className={`text-xs font-medium ${msg.type === 'agent' ? 'text-primary-400' : 'text-white/50'
                                            }`}>
                                            {msg.type === 'agent' ? 'AI Agent' : 'You'}
                                        </span>
                                    </div>
                                    <p className="text-sm text-white/80">{msg.text}</p>
                                </div>
                            ))
                        )}
                        <div ref={transcriptEndRef} />
                    </div>
                </div>
            </div>
        </div>
    );
}
