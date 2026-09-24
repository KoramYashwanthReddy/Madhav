import { webApiClient } from '../api/client';
import { VoiceState } from '../types';

// Declare Web Speech API types for TypeScript compatibility
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
    SpeechGrammarList: any;
    webkitSpeechGrammarList: any;
  }
}

export interface RecognitionCallbacks {
  onStateChange?: (state: VoiceState) => void;
  onInterimResult?: (transcript: string) => void;
  onFinalResult?: (transcript: string) => void;
  onError?: (errorMessage: string, isPermissionDenied?: boolean) => void;
  onEnd?: () => void;
  onAudioLevel?: (level: number) => void; // 0.0 to 1.0 real volume level
}

export interface SynthesisCallbacks {
  onStart?: () => void;
  onEnd?: () => void;
  onPause?: () => void;
  onResume?: () => void;
  onError?: (error: string) => void;
}

export class SpeechRecognitionService {
  private recognition: any = null;
  private mediaStream: MediaStream | null = null;
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private animFrameId: number | null = null;
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];

  private isListening = false;
  private useFallbackSTT = false;
  private currentLanguage = 'en-US';

  public isSupported(): boolean {
    return (
      typeof window !== 'undefined' &&
      !!(window.SpeechRecognition || window.webkitSpeechRecognition || (navigator.mediaDevices && navigator.mediaDevices.getUserMedia))
    );
  }

  public isNativeSTTAvailable(): boolean {
    return typeof window !== 'undefined' && !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  }

  public async requestMicrophonePermission(): Promise<boolean> {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      return false;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Stop tracks immediately after verifying permission
      stream.getTracks().forEach((track) => track.stop());
      return true;
    } catch {
      return false;
    }
  }

  public startListening(language = 'en-US', callbacks: RecognitionCallbacks = {}): void {
    if (this.isListening) {
      this.stopListening();
    }

    this.currentLanguage = language;
    this.isListening = true;
    callbacks.onStateChange?.('listening');

    // Attempt Native Browser Web Speech API first
    const SpeechRecognitionClass = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognitionClass) {
      try {
        this.recognition = new SpeechRecognitionClass();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = language;

        let fullTranscript = '';

        this.recognition.onstart = () => {
          this.startAudioLevelAnalysis(callbacks.onAudioLevel);
        };

        this.recognition.onresult = (event: any) => {
          let interimTranscript = '';
          let finalTranscript = '';

          for (let i = event.resultIndex; i < event.results.length; ++i) {
            const result = event.results[i];
            const transcriptText = result[0].transcript;
            if (result.isFinal) {
              finalTranscript += transcriptText;
            } else {
              interimTranscript += transcriptText;
            }
          }

          if (interimTranscript) {
            callbacks.onInterimResult?.(interimTranscript);
          }

          if (finalTranscript) {
            fullTranscript += (fullTranscript ? ' ' : '') + finalTranscript;
            callbacks.onFinalResult?.(fullTranscript);
          }
        };

        this.recognition.onerror = (event: any) => {
          const errorType = event.error;
          if (errorType === 'not-allowed' || errorType === 'service-not-allowed') {
            callbacks.onStateChange?.('permission_denied');
            callbacks.onError?.('Microphone access denied. Please grant permission in browser settings.', true);
          } else if (errorType === 'no-speech') {
            // Silence - clean end without crash
          } else {
            callbacks.onStateChange?.('error');
            callbacks.onError?.(`Speech recognition error: ${errorType}`);
          }
          this.cleanup();
        };

        this.recognition.onend = () => {
          this.cleanup();
          callbacks.onEnd?.();
        };

        this.recognition.start();
        return;
      } catch (e: any) {
        console.warn('Native SpeechRecognition failed, attempting MediaRecorder fallback', e);
      }
    }

    // Fallback using MediaRecorder & Module 26 Backend Transcribe API
    this.startFallbackRecording(callbacks);
  }

  private async startFallbackRecording(callbacks: RecognitionCallbacks): Promise<void> {
    try {
      this.useFallbackSTT = true;
      this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.startAudioLevelAnalysis(callbacks.onAudioLevel);

      this.audioChunks = [];
      this.mediaRecorder = new MediaRecorder(this.mediaStream);

      this.mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          this.audioChunks.push(e.data);
        }
      };

      this.mediaRecorder.onstop = async () => {
        callbacks.onStateChange?.('processing');
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        const arrayBuffer = await audioBlob.arrayBuffer();
        const bytes = new Uint8Array(arrayBuffer);

        // Convert to hex string for backend API
        let hex = '';
        for (let i = 0; i < bytes.length; i++) {
          hex += bytes[i].toString(16).padStart(2, '0');
        }

        try {
          const langCode = this.currentLanguage.split('-')[0] || 'en';
          const res = await webApiClient.transcribeAudioHex(hex, langCode);
          if (res.text) {
            callbacks.onFinalResult?.(res.text);
          } else {
            callbacks.onError?.('No speech detected in recorded audio.');
          }
        } catch {
          callbacks.onError?.('Failed to process recorded audio on backend.');
        } finally {
          this.cleanup();
          callbacks.onEnd?.();
        }
      };

      this.mediaRecorder.start();
    } catch {
      callbacks.onStateChange?.('permission_denied');
      callbacks.onError?.('Microphone permission requested but denied.', true);
      this.cleanup();
    }
  }

  private async startAudioLevelAnalysis(onAudioLevel?: (level: number) => void): Promise<void> {
    if (!onAudioLevel) return;
    try {
      if (!this.mediaStream) {
        this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      }
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtx) return;

      this.audioContext = new AudioCtx();
      const source = this.audioContext.createMediaStreamSource(this.mediaStream);
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 64;
      source.connect(this.analyser);

      const bufferLength = this.analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const updateLevel = () => {
        if (!this.analyser || !this.isListening) return;
        this.analyser.getByteFrequencyData(dataArray);

        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
          sum += dataArray[i];
        }
        const avg = sum / bufferLength;
        const normalized = Math.min(1.0, avg / 128.0);
        onAudioLevel(normalized);

        this.animFrameId = requestAnimationFrame(updateLevel);
      };

      updateLevel();
    } catch {
      // Ignore visualization errors gracefully
    }
  }

  public stopListening(): void {
    this.isListening = false;
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch {
        // ignore
      }
    }
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      try {
        this.mediaRecorder.stop();
      } catch {
        // ignore
      }
    }
  }

  public cancelListening(): void {
    this.isListening = false;
    if (this.recognition) {
      try {
        this.recognition.abort();
      } catch {
        // ignore
      }
    }
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      try {
        this.mediaRecorder.stop();
      } catch {
        // ignore
      }
    }
    this.cleanup();
  }

  private cleanup(): void {
    this.isListening = false;
    if (this.animFrameId) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }
    if (this.audioContext) {
      try {
        this.audioContext.close();
      } catch {
        // ignore
      }
      this.audioContext = null;
    }
    this.analyser = null;
  }
}

export class SpeechSynthesisService {
  private activeUtterance: SpeechSynthesisUtterance | null = null;
  private currentSpokenText = '';

  public isSupported(): boolean {
    return typeof window !== 'undefined' && 'speechSynthesis' in window;
  }

  public getVoices(): Promise<SpeechSynthesisVoice[]> {
    return new Promise((resolve) => {
      if (!this.isSupported()) {
        resolve([]);
        return;
      }

      let voices = window.speechSynthesis.getVoices();
      if (voices.length > 0) {
        resolve(voices);
        return;
      }

      window.speechSynthesis.onvoiceschanged = () => {
        voices = window.speechSynthesis.getVoices();
        resolve(voices);
      };

      // Fallback timeout in case voiceschanged event doesn't trigger
      setTimeout(() => {
        resolve(window.speechSynthesis.getVoices());
      }, 500);
    });
  }

  public async speak(
    text: string,
    options: {
      voiceName?: string;
      rate?: number;
      lang?: string;
    } = {},
    callbacks: SynthesisCallbacks = {}
  ): Promise<void> {
    if (!text.trim()) return;

    // Clean html formatting or extra raw markdown symbols if present for natural speech
    const cleanText = text
      .replace(/```[\s\S]*?```/g, 'Code block omitted.')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/[*_#~]/g, '')
      .trim();

    if (!cleanText) return;

    this.stop(); // Stop any currently playing audio immediately

    if (this.isSupported()) {
      try {
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.rate = options.rate || 1.0;
        utterance.lang = options.lang || 'en-US';

        if (options.voiceName) {
          const voices = window.speechSynthesis.getVoices();
          const foundVoice = voices.find((v) => v.name === options.voiceName || v.voiceURI === options.voiceName);
          if (foundVoice) {
            utterance.voice = foundVoice;
          }
        }

        utterance.onstart = () => {
          this.currentSpokenText = cleanText;
          callbacks.onStart?.();
        };

        utterance.onend = () => {
          this.activeUtterance = null;
          this.currentSpokenText = '';
          callbacks.onEnd?.();
        };

        utterance.onerror = (e: any) => {
          this.activeUtterance = null;
          this.currentSpokenText = '';
          callbacks.onError?.(e?.error || 'Speech synthesis failed.');
        };

        utterance.onpause = () => {
          callbacks.onPause?.();
        };

        utterance.onresume = () => {
          callbacks.onResume?.();
        };

        this.activeUtterance = utterance;
        window.speechSynthesis.speak(utterance);
        return;
      } catch (e: any) {
        console.warn('SpeechSynthesis API failed, attempting backend TTS fallback', e);
      }
    }

    // Fallback: Request backend synthesis from Module 26 Speech API
    try {
      callbacks.onStart?.();
      const res = await webApiClient.synthesizeSpeech(cleanText, options.voiceName || 'mock_voice_en_female');
      if (res && res.audio_bytes_hex) {
        // Mock fallback simulation timing
        setTimeout(() => {
          callbacks.onEnd?.();
        }, Math.min(6000, Math.max(1500, cleanText.length * 50)));
      } else {
        callbacks.onEnd?.();
      }
    } catch (e: any) {
      callbacks.onError?.('Speech output unavailable.');
    }
  }

  public pause(): void {
    if (this.isSupported() && window.speechSynthesis.speaking) {
      window.speechSynthesis.pause();
    }
  }

  public resume(): void {
    if (this.isSupported() && window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
    }
  }

  public stop(): void {
    if (this.isSupported()) {
      try {
        window.speechSynthesis.cancel();
      } catch {
        // ignore
      }
    }
    this.activeUtterance = null;
    this.currentSpokenText = '';
  }

  public isSpeaking(): boolean {
    return this.isSupported() && window.speechSynthesis.speaking;
  }

  public isPaused(): boolean {
    return this.isSupported() && window.speechSynthesis.paused;
  }

  public getCurrentSpokenText(): string {
    return this.currentSpokenText;
  }
}

export const speechRecognitionService = new SpeechRecognitionService();
export const speechSynthesisService = new SpeechSynthesisService();
