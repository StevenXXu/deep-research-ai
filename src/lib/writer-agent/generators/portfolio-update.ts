
import { ContentInput, Audience } from '../types';
import { ConfidentialityService } from '../services/confidentiality';

export class PortfolioUpdateGenerator {
  generate(input: ContentInput, confidentialityService: ConfidentialityService, audience: Audience): string {
    const rawContent = input.rawText;
    
    // Apply confidentiality redaction based on audience
    const safeContent = confidentialityService.process(rawContent, audience);

    // Format the output
    const timestamp = new Date().toLocaleDateString();
    
    return `PORTFOLIO UPDATE
Date: ${timestamp}
Audience: ${audience}

${safeContent}`;
  }
}
