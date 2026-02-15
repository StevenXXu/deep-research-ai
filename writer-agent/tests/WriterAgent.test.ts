import { WriterAgent } from '../src/WriterAgent';
import { Audience, ToneMode } from '../src/types';

describe('WriterAgent Orchestrator', () => {
  let agent: WriterAgent;

  beforeEach(() => {
    agent = new WriterAgent();
  });

  test('should initialize correctly', () => {
    expect(agent).toBeDefined();
  });

  test('should generate LinkedIn content successfully', async () => {
    const input = 'This is a test input about AI trends.';
    // LinkedIn intent, Audience Public (default for LinkedIn usually), Tone Optional
    const output = await agent.process(input, 'LinkedIn', Audience.Public);
    
    expect(output).toBeDefined();
    expect(output).toContain('AI trends');
    expect(output).toContain('#'); // LinkedIn tags
  });

  test('should generate Portfolio Update (Public) with redaction', async () => {
    const input = 'Portfolio company X raised $10M in Series A.';
    const output = await agent.process(input, 'Update', Audience.Public);
    
    expect(output).toBeDefined();
    expect(output).toContain('PORTFOLIO UPDATE');
    // Expect dollar amount to be redacted
    expect(output).not.toContain('$10M');
    expect(output).toContain('[REDACTED]');
    // Expect general text to remain
    expect(output).toContain('Portfolio company X raised');
  });

  test('should generate Portfolio Update (Internal) WITHOUT redaction', async () => {
    const input = 'Portfolio company X raised $10M in Series A.';
    const output = await agent.process(input, 'Update', Audience.Internal);
    
    expect(output).toBeDefined();
    expect(output).toContain('PORTFOLIO UPDATE');
    // Expect dollar amount to REMAIN
    expect(output).toContain('$10M');
  });

  test('should generate Internal Memo (Internal) without redaction', async () => {
    const input = 'Portfolio company X raised $10M.';
    const output = await agent.process(input, 'Memo', Audience.Internal);
    
    expect(output).toBeDefined();
    expect(output).toContain('MEMORANDUM');
    // Expect dollar amount to be present (Internal)
    expect(output).toContain('$10M');
  });

  test('should generate Internal Memo (Public) WITH redaction (Edge Case)', async () => {
    // If we ask for a Memo but for Public audience, it should redact.
    const input = 'Portfolio company X raised $10M.';
    const output = await agent.process(input, 'Memo', Audience.Public);
    
    expect(output).toBeDefined();
    expect(output).toContain('MEMORANDUM');
    // Expect dollar amount to be REDACTED
    expect(output).not.toContain('$10M');
    expect(output).toContain('[REDACTED]');
  });

  test('should handle unsupported intent gracefully', async () => {
    await expect(agent.process('input', 'Unknown' as any, Audience.Public)).rejects.toThrow();
  });

  test('should accept ToneMode', async () => {
    const input = 'Test content';
    // Just verifying it runs without error when tone is provided
    const output = await agent.process(input, 'LinkedIn', Audience.Public, ToneMode.Institutional);
    expect(output).toBeDefined();
  });
});
