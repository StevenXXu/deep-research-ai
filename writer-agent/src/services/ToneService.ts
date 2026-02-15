import { ToneMode } from '../types';
import { ToneProfile } from './ToneProfile';
import { StrategicBridgeProfile } from './profiles/StrategicBridge';
import { InstitutionalProfile } from './profiles/Institutional';
import { PortfolioAmplifierProfile } from './profiles/PortfolioAmplifier';
import { TechnicalAnalystProfile } from './profiles/TechnicalAnalyst';

export class ToneService {
  private profiles: Map<ToneMode, ToneProfile>;

  constructor() {
    this.profiles = new Map<ToneMode, ToneProfile>([
      [ToneMode.StrategicBridge, StrategicBridgeProfile],
      [ToneMode.Institutional, InstitutionalProfile],
      [ToneMode.PortfolioAmplifier, PortfolioAmplifierProfile],
      [ToneMode.TechnicalAnalyst, TechnicalAnalystProfile]
    ]);
  }

  getProfile(mode: ToneMode): ToneProfile {
    const profile = this.profiles.get(mode);
    if (!profile) {
      throw new Error(`Tone profile for mode '${mode}' not found.`);
    }
    return profile;
  }

  getInstructions(mode: ToneMode): string {
    const profile = this.getProfile(mode);
    return `TONE INSTRUCTIONS:
${profile.systemInstruction}
Description: ${profile.description}
Vocabulary: ${profile.vocabulary.join(', ')}
Constraints:
- ${profile.constraints.join('\n- ')}`;
  }
}
