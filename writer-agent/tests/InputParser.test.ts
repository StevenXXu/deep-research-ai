import { InputParser } from '../src/services/InputParser';
import { ContentInput } from '../src/types';

describe('InputParser', () => {
  let parser: InputParser;

  beforeEach(() => {
    parser = new InputParser();
  });

  test('should parse raw text without metadata correctly', () => {
    const raw = 'This is a simple text input.';
    const source = 'Notion';
    const result = parser.parse(raw, source);

    expect(result.rawText).toBe('This is a simple text input.');
    expect(result.source).toBe(source);
    expect(result.metadata).toBeUndefined();
  });

  test('should trim excess whitespace from raw text', () => {
    const raw = '   \n  This text has extra whitespace.   \n   ';
    const source = 'PDF';
    const result = parser.parse(raw, source);

    expect(result.rawText).toBe('This text has extra whitespace.');
    expect(result.source).toBe(source);
  });

  test('should extract metadata from header-like lines at the beginning', () => {
    const raw = `From: steven@example.com
Subject: Weekly Update
Date: 2026-02-15

Here is the update content.
It spans multiple lines.`;
    const source = 'Email';
    const result = parser.parse(raw, source);

    expect(result.metadata).toEqual({
      From: 'steven@example.com',
      Subject: 'Weekly Update',
      Date: '2026-02-15'
    });
    expect(result.rawText).toBe('Here is the update content.\nIt spans multiple lines.');
  });

  test('should stop extracting metadata when a non-header line is encountered', () => {
    const raw = `Title: My Great Post
This is the content.
From: embedded@example.com
It should not be extracted as metadata.`;
    const source = 'Notion';
    const result = parser.parse(raw, source);

    expect(result.metadata).toEqual({
      Title: 'My Great Post'
    });
    // The "From:" line in content should stay
    expect(result.rawText).toBe('This is the content.\nFrom: embedded@example.com\nIt should not be extracted as metadata.');
  });

  test('should handle known headers vs content that looks like headers', () => {
      // "Note: This is content" should NOT be metadata because "Note" is not in our allowlist (unless we add it)
      // "From: me" IS metadata.
      const raw = `From: me
Note: This is actually the first line of content.`;
      const source = 'Test';
      const result = parser.parse(raw, source);

      expect(result.metadata).toEqual({
          From: 'me'
      });
      expect(result.rawText).toBe('Note: This is actually the first line of content.');
  });

  test('should handle empty input gracefully', () => {
      const raw = '   ';
      const source = 'Empty';
      const result = parser.parse(raw, source);
      
      expect(result.rawText).toBe('');
      expect(result.metadata).toBeUndefined();
  });
});
