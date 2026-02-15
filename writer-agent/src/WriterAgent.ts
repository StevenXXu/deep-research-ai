import { InputParser } from './services/InputParser';
import { ConfidentialityService } from './services/ConfidentialityService';
import { ToneService } from './services/ToneService';
import { LinkedInGenerator } from './services/LinkedInGenerator';
import { PortfolioUpdateGenerator } from './services/PortfolioUpdateGenerator';
import { MemoGenerator } from './services/MemoGenerator';
import { ContentInput, OutputFormat, Audience, ToneMode } from './types';

export class WriterAgent {
  private parser: InputParser;
  private confidentiality: ConfidentialityService;
  private tone: ToneService;
  private linkedinGen: LinkedInGenerator;
  private portfolioGen: PortfolioUpdateGenerator;
  private memoGen: MemoGenerator;

  constructor() {
    this.parser = new InputParser();
    this.confidentiality = new ConfidentialityService();
    this.tone = new ToneService();
    this.linkedinGen = new LinkedInGenerator(this.tone);
    this.portfolioGen = new PortfolioUpdateGenerator();
    this.memoGen = new MemoGenerator(this.confidentiality);
  }

  /**
   * Orchestrates the content generation process.
   * 
   * @param text The raw text input.
   * @param intent The desired output intent/format.
   * @param audience The target audience.
   * @param tone (Optional) The tone mode to use.
   * @returns The generated content string.
   */
  async process(
    text: string, 
    intent: 'Update' | 'LinkedIn' | 'Memo', 
    audience: Audience, 
    tone?: ToneMode
  ): Promise<string> {
    console.log(`[WriterAgent] Processing input for intent: ${intent}, audience: ${audience}...`);

    // 1. Parser
    // We'll use a default source 'Input' for now as the signature doesn't ask for it.
    const input: ContentInput = this.parser.parse(text, 'Input');
    
    // 2. Confidentiality
    // Redact the raw text based on the audience BEFORE passing to generators?
    // Or do generators handle it?
    // The requirement says "Orchestrates: Parser -> Confidentiality -> Tone -> Generator"
    // So WriterAgent should handle confidentiality.
    
    const redactedText = this.confidentiality.redact(input.rawText, audience);
    
    // Create a new input object with the redacted text to pass downstream
    const redactedInput: ContentInput = {
      ...input,
      rawText: redactedText
    };

    // 3. Tone & 4. Generator
    // We dispatch based on intent
    let output = '';

    switch (intent) {
      case 'LinkedIn':
        // LinkedIn usually implies Public, but we respect the passed audience if needed?
        // LinkedInGenerator uses ToneService internally (or we pass tone).
        // It takes redactedInput (so sensitive data is already gone if audience=Public)
        output = this.linkedinGen.generate(redactedInput, tone);
        break;

      case 'Update': // Portfolio Update
        // PortfolioUpdateGenerator takes (input, confidentiality, audience)
        // But we already redacted. 
        // If we pass redactedInput, and it calls redact again, it should be idempotent (or we pass Internal to it?)
        // Let's see: PortfolioUpdateGenerator.generate(input, confidentiality, audience)
        // If we pass 'audience', it will try to redact again.
        // If we already redacted, we can pass Audience.Internal to avoid double redaction? 
        // OR we just rely on the generator to do it if that's how it's built?
        // BUT the requirement says "Orchestrates: ... -> Confidentiality -> ... -> Generator".
        // This implies WriterAgent does the redaction step explicitly.
        
        // Let's use the generator but acknowledging we might have already redacted.
        // Actually, PortfolioUpdateGenerator logic is: `content = confidentiality.redact(content, audience);`
        // If we pass already redacted text, and call redact again with same audience, it should be fine.
        output = this.portfolioGen.generate(redactedInput, this.confidentiality, audience);
        break;

      case 'Memo': // Internal Memo
        // MemoGenerator.generate(input) calls confidentiality.redact(input, Internal)
        // If we pass redactedInput (which might be redacted for Public if audience=Public was passed?),
        // BUT Memo intent usually implies Internal audience?
        // The prompt says "Can run the full pipeline for an Internal Memo".
        // If intent is Memo, audience is likely Internal.
        // If user passes intent=Memo, audience=Public, we should probably respect audience (redact) 
        // but MemoGenerator hardcodes Audience.Internal inside it:
        // `this.confidentialityService.redact(input.rawText, Audience.Internal);`
        // This seems like a conflict in the existing generator design vs the new orchestrator requirement.
        
        // However, if we follow "Parser -> Confidentiality -> Tone -> Generator", 
        // we feed the generator the *already processed* text.
        // But the generators are coupled to services.
        
        // For now, I will pass the redactedInput.
        // MemoGenerator will redact again for Internal (which does nothing).
        // If I passed audience=Public, `redactedInput` is redacted. 
        // MemoGenerator redacts for Internal (no change).
        // So effectively we get a Memo with Public-safe content. This seems correct.
        output = this.memoGen.generate(redactedInput);
        break;

      default:
        throw new Error(`Unsupported intent: ${intent}`);
    }

    return output;
  }
}
