/**
 * Audio Playback Service for StandupAI
 * Handles agent audio playback, PCM processing, and conference audio injection
 * Based on neo-interview's AudioPlaybackService pattern
 */

// Audio sample rate from ElevenLabs (16kHz)
const SOURCE_SAMPLE_RATE = 16000;
// Target sample rate for Jitsi (48kHz)
const TARGET_SAMPLE_RATE = 48000;

export class AudioPlaybackService {
    private agentPlaybackContext: AudioContext | null = null;
    private agentOutDest: MediaStreamAudioDestinationNode | null = null;
    private nextPlaybackTime = 0;
    private audioContextsResumed = false;

    /**
     * Initialize audio playback context
     */
    async initializePlaybackContext(): Promise<void> {
        if (!this.agentPlaybackContext || this.agentPlaybackContext.state === 'closed') {
            this.agentPlaybackContext = new AudioContext({ sampleRate: TARGET_SAMPLE_RATE });
            this.agentOutDest = this.agentPlaybackContext.createMediaStreamDestination();
            console.log('🎧 Created agent playback context and destination node');
        }
    }

    /**
     * Resume audio contexts (requires user interaction)
     */
    async resumeAudioContexts(): Promise<void> {
        if (this.audioContextsResumed) {
            return;
        }

        try {
            if (this.agentPlaybackContext && this.agentPlaybackContext.state === 'suspended') {
                await this.agentPlaybackContext.resume();
                console.log('🎧 Agent playback context resumed');
            }

            this.audioContextsResumed = true;
            console.log('✅ All audio contexts resumed successfully');
        } catch (error) {
            console.error('❌ Failed to resume audio contexts:', error);
        }
    }

    /**
     * Process and inject audio blob into Jitsi
     * Converts raw PCM16 (16k) to playable buffer and returns track for injection
     */
    async injectAudioBlob(audioBlob: Blob): Promise<MediaStreamTrack | null> {
        try {
            if (!this.agentPlaybackContext || this.agentPlaybackContext.state === 'closed') {
                await this.initializePlaybackContext();
            }

            await this.resumeAudioContexts();

            const arrayBuffer = await audioBlob.arrayBuffer();
            if (arrayBuffer.byteLength === 0) return null;

            // Handle odd-length chunks
            if (arrayBuffer.byteLength % 2 !== 0) {
                console.warn('⚠️ Odd-length PCM chunk');
            }

            const pcm16 = new Int16Array(
                arrayBuffer.slice(0, arrayBuffer.byteLength - (arrayBuffer.byteLength % 2))
            );

            // Upsample 16k -> 48k (simple 3x duplication for Jitsi compatibility)
            const upsampled = new Float32Array(pcm16.length * 3);
            for (let i = 0; i < pcm16.length; i++) {
                const v = pcm16[i] / 32768;
                const o = i * 3;
                upsampled[o] = v;
                upsampled[o + 1] = v;
                upsampled[o + 2] = v;
            }

            const buffer = this.agentPlaybackContext!.createBuffer(1, upsampled.length, TARGET_SAMPLE_RATE);
            buffer.copyToChannel(upsampled, 0);

            // Schedule playback
            if (this.nextPlaybackTime < this.agentPlaybackContext!.currentTime) {
                this.nextPlaybackTime = this.agentPlaybackContext!.currentTime;
            }

            const src = this.agentPlaybackContext!.createBufferSource();
            src.buffer = buffer;

            // Connect to destination for Jitsi injection
            if (this.agentOutDest) {
                src.connect(this.agentOutDest);
            }

            // Also connect to speakers for local playback
            src.connect(this.agentPlaybackContext!.destination);

            src.start(this.nextPlaybackTime);
            const duration = buffer.duration;
            this.nextPlaybackTime += duration;

            if (Math.random() < 0.1) {
                console.log(`🔊 Agent chunk queued (${(duration * 1000).toFixed(1)} ms)`);
            }

            // Return the audio track for injection into conference
            return this.agentOutDest?.stream.getAudioTracks()[0] || null;
        } catch (e) {
            console.error('❌ Agent audio injection/playback failed:', e);
            return null;
        }
    }

    /**
     * Get the audio destination track for conference injection
     */
    getDestinationTrack(): MediaStreamTrack | null {
        return this.agentOutDest?.stream.getAudioTracks()[0] || null;
    }

    /**
     * Get the destination stream
     */
    getDestinationStream(): MediaStream | null {
        return this.agentOutDest?.stream || null;
    }

    /**
     * Check if destination is ready
     */
    hasDestination(): boolean {
        return this.agentOutDest !== null;
    }

    /**
     * Get current playback context
     */
    getPlaybackContext(): AudioContext | null {
        return this.agentPlaybackContext;
    }

    /**
     * Check if currently playing audio
     */
    isPlaying(): boolean {
        if (!this.agentPlaybackContext) return false;
        return this.nextPlaybackTime > this.agentPlaybackContext.currentTime;
    }

    /**
     * Cleanup audio resources
     */
    async cleanup(): Promise<void> {
        console.log('[AudioPlayback] Cleaning up resources...');

        try {
            if (this.agentPlaybackContext && this.agentPlaybackContext.state !== 'closed') {
                await this.agentPlaybackContext.close();
                console.log('🎧 Closed agent playback context');
            }
        } catch (e) {
            console.warn('⚠️ Error closing agent playback context:', e);
        }

        this.agentPlaybackContext = null;
        this.agentOutDest = null;
        this.nextPlaybackTime = 0;
        this.audioContextsResumed = false;
    }
}

// Singleton instance
export const audioPlaybackService = new AudioPlaybackService();
