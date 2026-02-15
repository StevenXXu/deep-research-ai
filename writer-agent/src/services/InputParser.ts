import { ContentInput } from '../types';

export class InputParser {
  /**
   * Parses raw string input into a structured ContentInput object.
   * Performs basic cleanup and metadata extraction.
   *
   * @param raw - The raw text content.
   * @param source - The source identifier (e.g., 'Notion', 'Email').
   * @returns A structured ContentInput object.
   */
  public parse(raw: string, source: string): ContentInput {
    // 1. Basic cleanup: trim
    const trimmedRaw = raw.trim();

    const metadata: Record<string, unknown> = {};
    const lines = trimmedRaw.split(/\r?\n/);
    const contentLines: string[] = [];
    
    let isParsingHeaders = true;
    
    // Supported header keys for metadata extraction to avoid false positives
    // More generous list? Maybe just basic ones for now.
    const knownHeaders = ['From', 'To', 'Subject', 'Date', 'Source', 'Author', 'Title'];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmedLine = line.trim();

      if (isParsingHeaders) {
        if (trimmedLine === '') {
          // If we encounter an empty line while parsing headers, 
          // allow it only if we've already found some headers (it's a separator).
          // If we haven't found any headers, an empty line at the start is just whitespace (already trimmed, but maybe internal to the block?)
          // Wait, we trimmed `raw` so leading empty lines are gone.
          // So if we see an empty line here, it MUST be a separator if headers exist, or content if no headers exist?
          if (Object.keys(metadata).length > 0) {
            isParsingHeaders = false;
            continue; // Skip the separator line
          } else {
            // No headers found yet, so this empty line is weird. 
            // Treat it as content if we decide "no headers".
            isParsingHeaders = false;
            contentLines.push(line);
            continue;
          }
        }

        const headerMatch = line.match(/^([a-zA-Z0-9-]+):\s+(.+)$/);
        if (headerMatch) {
          const key = headerMatch[1];
          const value = headerMatch[2];
          
          if (knownHeaders.includes(key)) {
            metadata[key] = value.trim();
            continue;
          }
        }
        
        // If we reach here, it's not a header line (or not a known one), so stop parsing headers
        isParsingHeaders = false;
        contentLines.push(line);
      } else {
        contentLines.push(line);
      }
    }

    // 2. Remove excess whitespace from content lines
    // Re-join and trim again to handle leading/trailing newlines in content body
    const cleanedContent = contentLines
      .join('\n')
      .trim();

    return {
      rawText: cleanedContent,
      source: source,
      metadata: Object.keys(metadata).length > 0 ? metadata : undefined,
    };
  }
}
