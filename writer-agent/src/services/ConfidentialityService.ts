import { Audience } from '../types';

export class ConfidentialityService {
  /**
   * Redacts sensitive information based on the audience.
   * @param text The text to process.
   * @param audience The target audience.
   * @returns The redacted text.
   */
  redact(text: string, audience: Audience): string {
    if (audience === Audience.Internal) {
      return text;
    }

    if (audience === Audience.LP) {
      // For now, preserve all data for LP
      return text;
    }

    if (audience === Audience.Public) {
      return this.redactPublic(text);
    }

    return text;
  }

  private redactPublic(text: string): string {
    let redacted = text;

    // Redact specific keywords (case-insensitive)
    const keywords = ['Revenue', 'Cap Table'];
    keywords.forEach(keyword => {
      const regex = new RegExp(keyword, 'gi');
      redacted = redacted.replace(regex, '[REDACTED]');
    });

    // Redact currency amounts (e.g., $1M, $500k, $100,000)
    // Simple regex: $ followed by digits, optionally commas/periods, and optional suffix (k, m, b, t)
    const currencyRegex = /\$(\d{1,3}(?:,\d{3})*|(\d+))(\.\d+)?([kKmMbBtT])?\b/g;
    redacted = redacted.replace(currencyRegex, '[REDACTED]');

    return redacted;
  }
}
