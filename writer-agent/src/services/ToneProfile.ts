import { ToneMode } from '../types';

export interface ToneProfile {
  mode: ToneMode;
  description: string;
  vocabulary: string[];
  constraints: string[];
  systemInstruction: string;
}
