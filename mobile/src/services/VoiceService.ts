import { VoiceState } from '../types';
import { deviceCapabilityService } from './DeviceCapabilityService';

type VoiceStateListener = (state: VoiceState, transcript?: string) => void;

class VoiceService {
  private currentState: VoiceState = 'IDLE';
  private currentTranscript: string = '';
  private listeners: Set<VoiceStateListener> = new Set();
  private isAutoSpeakEnabled: boolean = true;
  private speechSpeed: number = 1.0;

  subscribe(listener: VoiceStateListener): () => void {
    this.listeners.add(listener);
    listener(this.currentState, this.currentTranscript);
    return () => this.listeners.delete(listener);
  }

  private setState(state: VoiceState, transcript: string = '') {
    this.currentState = state;
    this.currentTranscript = transcript;
    this.listeners.forEach((l) => l(this.currentState, this.currentTranscript));
  }

  async startListening(): Promise<boolean> {
    const perm = await deviceCapabilityService.requestPermission('SHOW_NOTIFICATION');
    if (perm !== 'supported') {
      this.setState('ERROR', 'Microphone permission denied by user.');
      return false;
    }

    this.setState('LISTENING', 'Listening for speech prompt...');
    
    // Simulate speech detection transition
    setTimeout(() => {
      if (this.currentState === 'LISTENING') {
        this.setState('TRANSCRIBING', 'What are my active tasks for today?');
      }
    }, 2000);

    return true;
  }

  stopListening(): void {
    if (this.currentState === 'LISTENING' || this.currentState === 'TRANSCRIBING') {
      this.setState('STOPPED', 'Voice capture stopped.');
    }
  }

  interruptSpeech(): void {
    if (this.currentState === 'SPEAKING') {
      this.setState('IDLE', '');
    }
  }

  setThinking(): void {
    this.setState('THINKING', 'MAX processing speech prompt...');
  }

  speakResponse(text: string): void {
    if (!this.isAutoSpeakEnabled) {
      this.setState('IDLE');
      return;
    }
    this.setState('SPEAKING', text);
    setTimeout(() => {
      if (this.currentState === 'SPEAKING') {
        this.setState('IDLE');
      }
    }, 3000);
  }

  setSpeechSettings(autoSpeak: boolean, speed: number): void {
    this.isAutoSpeakEnabled = autoSpeak;
    this.speechSpeed = speed;
  }

  getState(): VoiceState {
    return this.currentState;
  }
}

export const voiceService = new VoiceService();
