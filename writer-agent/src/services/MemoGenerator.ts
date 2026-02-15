import { ContentInput, Audience } from '../types';
import { ConfidentialityService } from './ConfidentialityService';

export class MemoGenerator {
  private confidentialityService: ConfidentialityService;

  constructor(confidentialityService: ConfidentialityService) {
    this.confidentialityService = confidentialityService;
  }

  /**
   * Generates an Internal Memo document.
   * 
   * @param input The content input.
   * @returns The generated memo string.
   */
  generate(input: ContentInput): string {
    const date = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
    const header = `MEMORANDUM\nTO: Internal Team\nFROM: Writer Agent\nDATE: ${date}`;
    
    // Internal memos are for Internal audience, so we use that.
    const content = this.confidentialityService.redact(input.rawText, Audience.Internal);
    
    return `${header}\n\n${content}`;
  }
}
