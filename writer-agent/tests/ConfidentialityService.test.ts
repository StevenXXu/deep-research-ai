import { ConfidentialityService } from '../src/services/ConfidentialityService';
import { Audience } from '../src/types';

describe('ConfidentialityService', () => {
  let service: ConfidentialityService;

  beforeEach(() => {
    service = new ConfidentialityService();
  });

  describe('Audience.Public', () => {
    it('should redact specific keywords', () => {
      const text = 'This year Revenue has increased significantly. The Cap Table is clean.';
      const result = service.redact(text, Audience.Public);
      expect(result).toBe('This year [REDACTED] has increased significantly. The [REDACTED] is clean.');
    });

    it('should redact currency amounts', () => {
      const text = 'We raised $1M at a $10M valuation. Last quarter revenue was $500k.';
      const result = service.redact(text, Audience.Public);
      expect(result).toBe('We raised [REDACTED] at a [REDACTED] valuation. Last quarter [REDACTED] was [REDACTED].');
    });

    it('should handle case insensitivity for keywords', () => {
      const text = 'REVENUE is up.';
      const result = service.redact(text, Audience.Public);
      expect(result).toBe('[REDACTED] is up.');
    });

    it('should preserve other text', () => {
      const text = 'This is a public update regarding our progress.';
      const result = service.redact(text, Audience.Public);
      expect(result).toBe('This is a public update regarding our progress.');
    });
  });

  describe('Audience.Internal', () => {
    it('should preserve all data', () => {
      const text = 'Revenue: $1M. Cap Table: sensitive.';
      const result = service.redact(text, Audience.Internal);
      expect(result).toBe('Revenue: $1M. Cap Table: sensitive.');
    });
  });

  describe('Audience.LP', () => {
    it('should preserve all data (for now)', () => {
      const text = 'Revenue: $1M. Cap Table: sensitive.';
      const result = service.redact(text, Audience.LP);
      expect(result).toBe('Revenue: $1M. Cap Table: sensitive.');
    });
  });
});
