import { ToneService } from '../src/services/ToneService';
import { ToneMode } from '../src/types';
import { ToneProfile } from '../src/services/ToneProfile';

describe('ToneService', () => {
  let toneService: ToneService;

  beforeEach(() => {
    toneService = new ToneService();
  });

  it('should retrieve the StrategicBridge profile correctly', () => {
    const profile = toneService.getProfile(ToneMode.StrategicBridge);
    expect(profile).toBeDefined();
    expect(profile.mode).toBe(ToneMode.StrategicBridge);
    expect(profile.description).toContain('Insightful');
  });

  it('should retrieve the Institutional profile correctly', () => {
    const profile = toneService.getProfile(ToneMode.Institutional);
    expect(profile).toBeDefined();
    expect(profile.mode).toBe(ToneMode.Institutional);
    expect(profile.description).toContain('Formal');
  });

  it('should retrieve the PortfolioAmplifier profile correctly', () => {
    const profile = toneService.getProfile(ToneMode.PortfolioAmplifier);
    expect(profile).toBeDefined();
    expect(profile.mode).toBe(ToneMode.PortfolioAmplifier);
    expect(profile.description).toContain('Celebratory');
  });

  it('should retrieve the TechnicalAnalyst profile correctly', () => {
    const profile = toneService.getProfile(ToneMode.TechnicalAnalyst);
    expect(profile).toBeDefined();
    expect(profile.mode).toBe(ToneMode.TechnicalAnalyst);
    expect(profile.description).toContain('Deep');
  });

  it('should format instructions correctly', () => {
    const instructions = toneService.getInstructions(ToneMode.StrategicBridge);
    expect(instructions).toContain('TONE INSTRUCTIONS:');
    expect(instructions).toContain('Steven Xu');
    expect(instructions).toContain('Constraints:');
  });

  it('should throw error for invalid tone mode', () => {
    // Cast to any to bypass type checking for this test
    expect(() => toneService.getProfile('InvalidMode' as ToneMode)).toThrow();
  });
});
