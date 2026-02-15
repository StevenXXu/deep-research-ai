import { parseArgs } from '../src/cli';

describe('CLI Argument Parser', () => {
  it('should parse valid arguments correctly', () => {
    const args = ['--input', 'test.txt', '--format', 'update', '--audience', 'internal'];
    const options = parseArgs(args);
    
    expect(options.input).toBe('test.txt');
    expect(options.format).toBe('update');
    expect(options.audience).toBe('internal');
  });

  it('should handle optional arguments missing', () => {
    const args = ['--input', 'file.txt', '--format', 'memo'];
    const options = parseArgs(args);
    
    expect(options.input).toBe('file.txt');
    expect(options.format).toBe('memo');
    expect(options.audience).toBeUndefined();
  });

  it('should handle flags at end of string', () => {
    const args = ['--format', 'linkedin', '--input', 'test.txt'];
    const options = parseArgs(args);
    
    expect(options.input).toBe('test.txt');
    expect(options.format).toBe('linkedin');
  });
  
  it('should ignore non-flag arguments not following a flag', () => {
     // This parser is simple and might not handle positional args well if mixed, 
     // but for our strict usage:
     const args = ['random', '--input', 'test.txt']; 
     const options = parseArgs(args);
     expect(options.input).toBe('test.txt');
  });
});
