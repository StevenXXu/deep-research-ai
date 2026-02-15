
import { describe, it, expect } from 'vitest';
import { PortfolioUpdateGenerator } from './portfolio-update';
import { ConfidentialityService } from '../services/confidentiality';
import { ContentInput, Audience, ToneMode } from '../types';

describe('PortfolioUpdateGenerator', () => {
  const generator = new PortfolioUpdateGenerator();
  const confidentialityService = new ConfidentialityService();

  const mockInput: ContentInput = {
    id: '123',
    source: 'Notion',
    rawText: 'We achieved $10M revenue and closed a $50M Series B at $200M valuation.',
    timestamp: new Date(),
    metadata: {}
  };

  it('starts with PORTFOLIO UPDATE header', () => {
    const result = generator.generate(mockInput, confidentialityService, 'Internal');
    expect(result).toContain('PORTFOLIO UPDATE');
  });

  it('preserves content for Internal audience', () => {
    const result = generator.generate(mockInput, confidentialityService, 'Internal');
    expect(result).toContain('$10M');
    expect(result).toContain('$50M');
    expect(result).toContain('$200M');
  });

  it('redacts sensitive data for Public audience', () => {
    const result = generator.generate(mockInput, confidentialityService, 'Public');
    expect(result).toContain('[REDACTED]');
    expect(result).not.toContain('$10M');
    expect(result).not.toContain('$50M');
    expect(result).not.toContain('$200M');
  });

  it('includes the audience in the header', () => {
    const result = generator.generate(mockInput, confidentialityService, 'Public');
    expect(result).toContain('Audience: Public');
  });
});
