import { ContentInput, ToneMode } from '../types';

export class LinkedInGenerator {
  /**
   * Generates a LinkedIn post in the Steven Xu style.
   * 
   * @param input The content input to generate from.
   * @param toneMode The tone mode to use (defaults to StrategicBridge).
   * @returns The generated LinkedIn post string.
   */
  generate(input: ContentInput, toneMode?: ToneMode): string {
    // Force ToneMode to Steven Xu - Strategic Bridge internally if not specified
    const mode = toneMode || ToneMode.StrategicBridge;

    // Apply specific formatting (short paragraphs, hook in first line)
    // 1. Identify hook (first sentence/line)
    const rawText = input.rawText;
    if (!rawText || rawText.trim().length === 0) {
      return '';
    }

    const lines = rawText.split('\n').map(line => line.trim()).filter(line => line.length > 0);
    const hook = lines[0];
    const body = lines.slice(1);

    // 2. Format body into short paragraphs
    // Ensure spacing between paragraphs (double newlines)
    const formattedBody = body.join('\n\n');

    // 3. Add hashtags (simulated)
    const hashtags = ['#VentureCapital', '#Innovation', '#Strategy', '#Tech'];
    const hashtagString = hashtags.join(' ');

    // 4. Construct output
    // Hook + double newline + Body + double newline + Hashtags
    let output = `${hook}\n\n${formattedBody}`;
    
    // Add hashtags at the end
    output += `\n\n${hashtagString}`;

    return output;
  }
}
