import { MemoGenerator } from '../src/services/MemoGenerator';
import { ConfidentialityService } from '../src/services/ConfidentialityService';
import { ContentInput } from '../src/types';

describe('MemoGenerator', () => {
  let generator: MemoGenerator;
  let confidentialityService: ConfidentialityService;

  beforeEach(() => {
    confidentialityService = new ConfidentialityService();
    generator = new MemoGenerator(confidentialityService);
  });

  it('should generate a memo with the correct header format', () => {
    const input: ContentInput = {
      rawText: 'This is a test memo content.',
      source: 'Test',
    };

    const output = generator.generate(input);
    const date = new Date().toISOString().split('T')[0];

    expect(output).toContain('MEMORANDUM');
    expect(output).toContain('TO: Internal Team');
    expect(output).toContain('FROM: Writer Agent');
    expect(output).toContain(`DATE: ${date}`);
    expect(output).toContain('This is a test memo content.');
  });

  it('should not redact sensitive information for internal audience', () => {
    const input: ContentInput = {
      rawText: 'Our revenue is $1,000,000 and the valuation is $50M.',
      source: 'Financial Report',
    };

    const output = generator.generate(input);

    expect(output).toContain('$1,000,000');
    expect(output).toContain('$50M');
    expect(output).not.toContain('[REDACTED]');
  });
});
