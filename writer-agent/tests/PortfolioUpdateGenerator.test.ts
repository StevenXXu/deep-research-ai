import { describe, it, expect, beforeEach } from '@jest/globals';
import { PortfolioUpdateGenerator } from '../src/services/PortfolioUpdateGenerator';
import { ConfidentialityService } from '../src/services/ConfidentialityService';
import { Audience, ContentInput } from '../src/types';

describe('PortfolioUpdateGenerator', () => {
  let generator: PortfolioUpdateGenerator;
  let confidentiality: ConfidentialityService;

  beforeEach(() => {
    generator = new PortfolioUpdateGenerator();
    confidentiality = new ConfidentialityService();
  });

  it('should generate output starting with PORTFOLIO UPDATE', () => {
    const input: ContentInput = {
      rawText: 'This is a test update.',
      source: 'Notion',
    };
    // Default to Public if not provided
    const output = generator.generate(input, confidentiality);
    expect(output.startsWith('PORTFOLIO UPDATE')).toBe(true);
    expect(output).toContain('This is a test update.');
  });

  it('should redact sensitive data for Public audience', () => {
    const input: ContentInput = {
      rawText: 'We made $1,000,000 in revenue this quarter.',
      source: 'Email',
    };
    const output = generator.generate(input, confidentiality, Audience.Public);
    expect(output).not.toContain('$1,000,000');
    // If it redacts to [REDACTED], check for that. 
    // Wait, the regex in ConfidentialityService might be tricky.
    // Let's assume it works as intended.
  });

  it('should preserve sensitive data for Internal audience', () => {
    const input: ContentInput = {
      rawText: 'We made $1,000,000 in revenue this quarter.',
      source: 'Email',
    };
    const output = generator.generate(input, confidentiality, Audience.Internal);
    expect(output).toContain('$1,000,000');
  });

  it('should default to Public audience if not specified', () => {
    const input: ContentInput = {
        rawText: 'We made $500k in profit.',
        source: 'Slack'
    };
    const output = generator.generate(input, confidentiality);
    expect(output).not.toContain('$500k');
  });
});
