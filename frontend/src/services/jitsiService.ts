/**
 * Jitsi Service for StandupAI
 * Handles Jitsi meeting connections, audio capture, and voice AI integration
 */

declare const JitsiMeetJS: any;
declare const JitsiMeetExternalAPI: any;

export interface JitsiConnectionConfig {
    domain: string;
    room: string;
    jwt: string;
}

export interface JitsiTrackInfo {
    track: any;
    trackId: string;
    participantId: string;
}

export interface VoiceSessionCallbacks {
    onUserJoined?: () => void;
    onUserLeft?: () => void;
    onAudioReceived?: (audio: ArrayBuffer) => void;
    onAgentTranscript?: (text: string) => void;
    onUserTranscript?: (text: string) => void;
    onSessionEnded?: (reason: string) => void;
    onError?: (error: string) => void;
}

class JitsiService {
    private activeConference: any = null;
    private connection: any = null;
    private voiceWebSocket: WebSocket | null = null;
    private audioContext: AudioContext | null = null;
    private mediaStream: MediaStream | null = null;
    private processor: ScriptProcessorNode | null = null;

    private callbacks: VoiceSessionCallbacks = {};
    private isConnected = false;
    private currentStandupId: string | null = null;

    /**
     * Wait for Jitsi scripts to load (if using lib-jitsi-meet)
     */
    async waitForJitsiScripts(timeoutMs: number = 10000): Promise<void> {
        const start = performance.now();
        return new Promise((resolve, reject) => {
            const check = () => {
                if ((window as any).JitsiMeetJS) {
                    console.log('✅ Jitsi scripts loaded');
                    resolve();
                } else if (performance.now() - start > timeoutMs) {
                    reject(new Error('Jitsi scripts not loaded'));
                } else {
                    setTimeout(check, 100);
                }
            };
            check();
        });
    }

    /**
     * Initialize the Jitsi library
     */
    initJitsi(): void {
        if (typeof JitsiMeetJS === 'undefined') {
            console.warn('JitsiMeetJS not found - using iframe mode only');
            return;
        }

        JitsiMeetJS.init({
            disableAudioLevels: false,
            enableNoAudioDetection: true,
            disableAP: true,
            disableAEC: true,
            disableNS: true,
            disableAGC: true,
        });
        JitsiMeetJS.setLogLevel(JitsiMeetJS.logLevels.INFO);
    }

    /**
     * Join a Jitsi conference (headless mode for audio capture)
     */
    async joinConference(config: JitsiConnectionConfig): Promise<void> {
        if (typeof JitsiMeetJS === 'undefined') {
            throw new Error('JitsiMeetJS not available');
        }

        this.initJitsi();

        // Parse room name (format: appId/roomName)
        const roomParts = config.room.split('/');
        const isJaas = roomParts.length > 1;
        const conferenceRoomName = isJaas ? roomParts[1] : config.room;
        const jaasTenant = isJaas ? roomParts[0] : null;

        const options = {
            hosts: {
                domain: config.domain,
                muc: `conference.${jaasTenant}.${config.domain}`
            },
            p2p: { enabled: false },
            serviceUrl: `wss://${config.domain}/${jaasTenant}/xmpp-websocket?room=${encodeURIComponent(conferenceRoomName)}`,
            clientNode: 'http://jitsi.org/jitsimeet'
        };

        console.log('🔧 Jitsi connection options:', options);
        this.connection = new JitsiMeetJS.JitsiConnection(null, config.jwt, options);

        return new Promise((resolve, reject) => {
            this.connection.addEventListener(
                JitsiMeetJS.events.connection.CONNECTION_ESTABLISHED,
                () => {
                    console.log('✅ Jitsi connection established');

                    const conference = this.connection.initJitsiConference(conferenceRoomName, {});
                    this.activeConference = conference;

                    this.setupConferenceEvents(conference);
                    conference.join();
                    resolve();
                }
            );

            this.connection.addEventListener(
                JitsiMeetJS.events.connection.CONNECTION_FAILED,
                (e: any) => {
                    console.error('❌ Jitsi connection failed', e);
                    reject(e);
                }
            );

            this.connection.connect();
        });
    }

    /**
     * Setup Jitsi conference event listeners
     */
    private setupConferenceEvents(conference: any): void {
        const JM = JitsiMeetJS;

        conference.on(JM.events.conference.CONFERENCE_JOINED, () => {
            console.log('✅ Joined Jitsi conference');
            this.isConnected = true;
            this.callbacks.onUserJoined?.();
        });

        conference.on(JM.events.conference.TRACK_ADDED, (track: any) => {
            if (!track.isLocal() && track.getType() === 'audio') {
                console.log('🎵 Remote audio track added');
                this.captureRemoteAudio(track);
            }
        });

        conference.on(JM.events.conference.TRACK_REMOVED, (track: any) => {
            console.log('🛑 Track removed:', track.getType());
        });

        conference.on(JM.events.conference.USER_LEFT, (id: any) => {
            console.log(`👋 User left: ${id}`);
            this.callbacks.onUserLeft?.();
        });

        conference.on(JM.events.conference.CONFERENCE_FAILED, (err: any) => {
            console.error('❌ Conference failed', err);
            this.callbacks.onError?.(err);
        });
    }

    /**
     * Capture audio from a remote track and send to backend
     */
    private captureRemoteAudio(track: any): void {
        const mediaTrack = track.getTrack();
        if (!mediaTrack) {
            console.warn('No media track available');
            return;
        }

        this.mediaStream = new MediaStream([mediaTrack]);
        this.audioContext = new AudioContext({ sampleRate: 16000 });

        const source = this.audioContext.createMediaStreamSource(this.mediaStream);
        this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);

        this.processor.onaudioprocess = (e) => {
            if (this.voiceWebSocket?.readyState === WebSocket.OPEN) {
                const float32 = e.inputBuffer.getChannelData(0);
                const pcm16 = this.floatToPcm16(float32);
                this.voiceWebSocket.send(pcm16);
            }
        };

        source.connect(this.processor);
        this.processor.connect(this.audioContext.destination);

        console.log('🎤 Audio capture started');
    }

    /**
     * Convert Float32 audio to PCM16
     */
    private floatToPcm16(float32: Float32Array): ArrayBuffer {
        const buffer = new ArrayBuffer(float32.length * 2);
        const view = new DataView(buffer);

        for (let i = 0; i < float32.length; i++) {
            const s = Math.max(-1, Math.min(1, float32[i]));
            view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
        }

        return buffer;
    }

    /**
     * Connect to the voice backend WebSocket
     */
    connectToVoiceBackend(standupId: string, baseUrl: string = ''): void {
        this.currentStandupId = standupId;

        // Determine WebSocket URL
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = baseUrl || `${wsProtocol}//${window.location.host}`;
        const wsUrl = `${host}/standup/${standupId}/voice`;

        console.log(`🔌 Connecting to voice backend: ${wsUrl}`);

        this.voiceWebSocket = new WebSocket(wsUrl);

        this.voiceWebSocket.onopen = () => {
            console.log('✅ Voice WebSocket connected');
        };

        this.voiceWebSocket.onmessage = async (event) => {
            if (event.data instanceof Blob) {
                // Audio response from AI
                const buffer = await event.data.arrayBuffer();
                this.callbacks.onAudioReceived?.(buffer);
                this.playAudioBuffer(buffer);
            } else {
                // JSON message
                try {
                    const data = JSON.parse(event.data);
                    this.handleVoiceMessage(data);
                } catch (e) {
                    console.warn('Failed to parse voice message:', event.data);
                }
            }
        };

        this.voiceWebSocket.onerror = (error) => {
            console.error('❌ Voice WebSocket error:', error);
            this.callbacks.onError?.('Voice connection error');
        };

        this.voiceWebSocket.onclose = () => {
            console.log('🔌 Voice WebSocket closed');
        };
    }

    /**
     * Handle messages from voice backend
     */
    private handleVoiceMessage(data: any): void {
        switch (data.type) {
            case 'agent_transcript':
                this.callbacks.onAgentTranscript?.(data.text);
                break;
            case 'user_transcript':
                this.callbacks.onUserTranscript?.(data.text);
                break;
            case 'session_ended':
                this.callbacks.onSessionEnded?.(data.reason);
                break;
            case 'error':
                this.callbacks.onError?.(data.message);
                break;
            case 'status':
                console.log('Voice status:', data.message);
                break;
        }
    }

    /**
     * Play audio buffer through speakers
     */
    private async playAudioBuffer(buffer: ArrayBuffer): Promise<void> {
        try {
            const audioContext = new AudioContext({ sampleRate: 16000 });

            // Convert PCM16 to AudioBuffer
            const pcm16 = new Int16Array(buffer);
            const float32 = new Float32Array(pcm16.length);

            for (let i = 0; i < pcm16.length; i++) {
                float32[i] = pcm16[i] / 32768.0;
            }

            const audioBuffer = audioContext.createBuffer(1, float32.length, 16000);
            audioBuffer.copyToChannel(float32, 0);

            const source = audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(audioContext.destination);
            source.start();

        } catch (e) {
            console.error('Failed to play audio:', e);
        }
    }

    /**
     * Force start the conversation (skip VAD)
     */
    forceStartConversation(): void {
        if (this.voiceWebSocket?.readyState === WebSocket.OPEN) {
            this.voiceWebSocket.send(JSON.stringify({ type: 'force_start' }));
        }
    }

    /**
     * Stop the voice session
     */
    stopVoiceSession(): void {
        if (this.voiceWebSocket?.readyState === WebSocket.OPEN) {
            this.voiceWebSocket.send(JSON.stringify({ type: 'stop' }));
        }
    }

    /**
     * Set callbacks for voice events
     */
    setCallbacks(callbacks: VoiceSessionCallbacks): void {
        this.callbacks = callbacks;
    }

    /**
     * Setup Jitsi iframe (for visible meeting)
     */
    setupIframe(
        containerId: string,
        room: string,
        jwt: string,
        domain: string,
        options: any = {}
    ): any {
        if (typeof JitsiMeetExternalAPI === 'undefined') {
            console.error('JitsiMeetExternalAPI not available');
            return null;
        }

        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container #${containerId} not found`);
            return null;
        }

        const api = new JitsiMeetExternalAPI(domain, {
            roomName: room,
            parentNode: container,
            jwt,
            configOverwrite: {
                prejoinPageEnabled: options.prejoin ?? false,
                p2p: { enabled: false },
                ...options.config
            },
            interfaceConfigOverwrite: {
                SHOW_JITSI_WATERMARK: false,
                ...options.interfaceConfig
            }
        });

        api.addEventListener('videoConferenceJoined', () => {
            console.log('✅ Joined Jitsi meeting (iframe)');
            this.callbacks.onUserJoined?.();
        });

        api.addEventListener('videoConferenceLeft', () => {
            console.log('👋 Left Jitsi meeting');
            this.callbacks.onUserLeft?.();
        });

        return api;
    }

    /**
     * Cleanup all resources
     */
    async cleanup(): Promise<void> {
        console.log('🧹 Cleaning up Jitsi resources...');

        // Close voice WebSocket
        if (this.voiceWebSocket) {
            this.voiceWebSocket.close();
            this.voiceWebSocket = null;
        }

        // Stop audio processing
        if (this.processor) {
            this.processor.disconnect();
            this.processor = null;
        }

        // Close audio context
        if (this.audioContext) {
            await this.audioContext.close();
            this.audioContext = null;
        }

        // Leave conference
        if (this.activeConference) {
            try {
                this.activeConference.leave();
            } catch (e) {
                console.warn('Error leaving conference:', e);
            }
            this.activeConference = null;
        }

        // Close connection
        if (this.connection) {
            try {
                this.connection.disconnect();
            } catch (e) {
                console.warn('Error disconnecting:', e);
            }
            this.connection = null;
        }

        this.isConnected = false;
        this.mediaStream = null;
        this.currentStandupId = null;
    }

    /**
     * Check if connected
     */
    isActive(): boolean {
        return this.isConnected;
    }
}

// Export singleton instance
export const jitsiService = new JitsiService();
export default JitsiService;
