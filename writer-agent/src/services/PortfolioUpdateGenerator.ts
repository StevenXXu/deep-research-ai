import { ContentInput, Audience } from '../types';
import { ConfidentialityService } from './ConfidentialityService';

export class PortfolioUpdateGenerator {
  /**
   * Generates a Portfolio Update document.
   * 
   * @param input The content input.
   * @param confidentiality The confidentiality service to use for redaction.
   * @param audience The target audience for the update.
   * @returns The generated portfolio update string.
   */
  generate(input: ContentInput, confidentiality: ConfidentialityService, audience: Audience = Audience.Public): string {
    const header = 'PORTFOLIO UPDATE';
    let content = input.rawText;

    // Redact sensitive data if audience is Public
    if (audience === Audience.Public) {
        content = confidentiality.redact(content, Audience.Public);
    } else {
        // Still use confidentiality service for other audiences if necessary (e.g. Internal might have different rules later)
        content = confidentiality.redact(content, audience);
    }
    
    return `${header}\n\n${content}`;
  }
}
