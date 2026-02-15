import { ToneMode, Audience, ContentInput, WriterOutput } from '../src/types';
// Tests using global Jest describe/it/expect

describe('Writer Agent Types', () => {
  it('should have correct ToneMode values', () => {
    expect(ToneMode.StrategicBridge).toBe('StrategicBridge');
    expect(ToneMode.Institutional).toBe('Institutional');
    expect(ToneMode.PortfolioAmplifier).toBe('PortfolioAmplifier');
    expect(ToneMode.TechnicalAnalyst).toBe('TechnicalAnalyst');
  });

  it('should have correct Audience values', () => {
    expect(Audience.Public).toBe('Public');
    expect(Audience.Internal).toBe('Internal');
    expect(Audience.LP).toBe('LP');
  });

  it('should support typed ContentInput', () => {
    const input: ContentInput = {
      rawText: 'Some raw text',
      source: 'Notion',
      metadata: { author: 'Steven' }
    };
    expect(input.rawText).toBe('Some raw text');
    expect(input.source).toBe('Notion');
    expect(input.metadata?.author).toBe('Steven');
  });

  it('should support typed WriterOutput', () => {
    const output: WriterOutput = {
      content: 'Polished content',
      toneUsed: ToneMode.StrategicBridge,
      metadata: { confidence: 0.9 }
    };
    expect(output.content).toBe('Polished content');
    expect(output.toneUsed).toBe(ToneMode.StrategicBridge);
    expect(output.metadata?.confidence).toBe(0.9);
  });
});
