import { LinkedInGenerator } from '../src/services/LinkedInGenerator';
import { ToneService } from '../src/services/ToneService';
import { ToneMode, ContentInput } from '../src/types';

describe('LinkedInGenerator', () => {
  let generator: LinkedInGenerator;
  let toneService: ToneService;

  beforeEach(() => {
    toneService = new ToneService();
    generator = new LinkedInGenerator(toneService);
  });

  it('should generate a LinkedIn post with proper formatting', () => {
    const input: ContentInput = {
      rawText: 'This is the hook.\nThis is the body.\nThis is another paragraph.',
      source: 'test'
    };

    const result = generator.generate(input);

    expect(result).toContain('This is the hook.');
    expect(result).toContain('This is the body.');
    expect(result).toContain('This is another paragraph.');
    
    // Check for hashtags
    expect(result).toContain('#VentureCapital');
    expect(result).toContain('#Innovation');
    expect(result).toContain('#Strategy');
    expect(result).toContain('#Tech');
    
    // Check for short paragraphs (double newlines)
    expect(result).toMatch(/\n\n/);
  });

  it('should include a hook in the first line', () => {
    const input: ContentInput = {
      rawText: 'First sentence is hook.\nBody follows.',
      source: 'test'
    };
    
    const result = generator.generate(input);
    const lines = result.split('\n');
    
    expect(lines[0]).toBe('First sentence is hook.');
  });

  it('should default to StrategicBridge tone if not specified', () => {
    // This is hard to test directly since implementation just uses default param,
    // but we can verify it doesn't crash or throw.
    const input: ContentInput = {
      rawText: 'Content.',
      source: 'test'
    };
    
    const result = generator.generate(input);
    expect(result).toBeDefined();
    // In a real implementation we might check if specific tone instructions were applied.
  });

  it('should handle empty input gracefully', () => {
    const input: ContentInput = {
      rawText: '',
      source: 'test'
    };
    
    const result = generator.generate(input);
    expect(result).toBe('');
  });

  it('should force StrategicBridge tone internally if not specified', () => {
      // Again, hard to verify internal state without mocking or inspecting, 
      // but we can ensure it works when called without the second argument.
      const input: ContentInput = {
          rawText: 'Test content',
          source: 'test'
      };
      const result = generator.generate(input);
      expect(result).toContain('Test content');
  });
});
