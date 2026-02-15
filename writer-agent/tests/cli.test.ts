import { run } from '../src/cli';
import * as fs from 'fs';
import { WriterAgent } from '../src/WriterAgent';
import { OutputFormat, Audience, ToneMode } from '../src/types';

jest.mock('fs');
jest.mock('../src/WriterAgent');

describe('CLI Handler', () => {
  const mockProcess = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
    (WriterAgent as jest.Mock).mockImplementation(() => ({
      process: mockProcess
    }));
    (fs.existsSync as jest.Mock).mockReturnValue(true);
    (fs.readFileSync as jest.Mock).mockReturnValue('mock content');
    mockProcess.mockResolvedValue('Generated Content');
  });

  test('should process valid input correctly', async () => {
    const args = ['input.txt', 'LinkedIn', 'Public', 'Steven Xu'];
    const result = await run(args);
    
    expect(fs.existsSync).toHaveBeenCalled();
    expect(fs.readFileSync).toHaveBeenCalled();
    expect(WriterAgent).toHaveBeenCalled();
    expect(mockProcess).toHaveBeenCalledWith(
      'mock content',
      'LinkedIn',
      Audience.Public,
      ToneMode.StrategicBridge
    );
    expect(result).toBe('Generated Content');
  });

  test('should throw error if arguments are missing', async () => {
    await expect(run(['input.txt'])).rejects.toThrow('Usage:');
  });

  test('should throw error if input file does not exist', async () => {
    (fs.existsSync as jest.Mock).mockReturnValue(false);
    await expect(run(['missing.txt', 'LinkedIn'])).rejects.toThrow('Input file not found');
  });

  test('should throw error for invalid format', async () => {
    await expect(run(['input.txt', 'InvalidFormat'])).rejects.toThrow('Invalid format');
  });

  test('should support internal memo format', async () => {
    const args = ['input.txt', 'InternalMemo', 'Internal'];
    await run(args);
    expect(mockProcess).toHaveBeenCalledWith(
      'mock content',
      'Memo',
      Audience.Internal,
      undefined
    );
  });
  
  test('should handle tone mapping correctly', async () => {
      // Test different tone mappings
      await run(['input.txt', 'LinkedIn', 'Public', 'INP Institutional']);
      expect(mockProcess).toHaveBeenCalledWith(expect.any(String), expect.any(String), expect.any(String), ToneMode.Institutional);
      
      mockProcess.mockClear();
      await run(['input.txt', 'LinkedIn', 'Public', 'Portfolio Amplifier']);
      expect(mockProcess).toHaveBeenCalledWith(expect.any(String), expect.any(String), expect.any(String), ToneMode.PortfolioAmplifier);
  });
});
