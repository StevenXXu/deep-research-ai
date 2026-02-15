import * as fs from 'fs';
import * as path from 'path';
import { WriterAgent } from './WriterAgent';
import { OutputFormat, Audience, ToneMode } from './types';

export async function run(args: string[]): Promise<string> {
  if (args.length < 2) {
    throw new Error('Usage: node dist/cli.js <input-file> <format> [audience] [tone]\n' +
      'Formats: LinkedIn, PortfolioUpdate, InternalMemo\n' +
      'Audience: Public, Internal, LP (default: Public)\n' +
      'Tone: Steven Xu, INP Institutional, Portfolio Amplifier, Technical/Analyst (optional)');
  }

  const [inputFile, formatStr, audienceStr, toneStr] = args;

  // Validate Input File
  const absolutePath = path.resolve(process.cwd(), inputFile);
  if (!fs.existsSync(absolutePath)) {
    throw new Error(`Error: Input file not found at ${absolutePath}`);
  }

  // Validate Format
  if (!Object.values(OutputFormat).includes(formatStr as OutputFormat)) {
    throw new Error(`Error: Invalid format "${formatStr}". Supported: ${Object.values(OutputFormat).join(', ')}`);
  }
  const format = formatStr as OutputFormat;

  // Validate Audience
  let audience: Audience = Audience.Public;
  if (audienceStr) {
    if (Object.values(Audience).includes(audienceStr as Audience)) {
      audience = audienceStr as Audience;
    } else {
      throw new Error(`Error: Invalid audience "${audienceStr}". Supported: ${Object.values(Audience).join(', ')}`);
    }
  }

  // Validate Tone
  let tone: ToneMode | undefined;
  if (toneStr) {
    if (Object.values(ToneMode).includes(toneStr as ToneMode)) {
      tone = toneStr as ToneMode;
    } else {
       const lower = toneStr.toLowerCase();
       if (lower.includes('steven')) tone = ToneMode.StrategicBridge;
       else if (lower.includes('institutional')) tone = ToneMode.Institutional;
       else if (lower.includes('amplifier')) tone = ToneMode.PortfolioAmplifier;
       else if (lower.includes('technical') || lower.includes('analyst')) tone = ToneMode.TechnicalAnalyst;
       else {
         throw new Error(`Error: Invalid tone "${toneStr}". Supported: ${Object.values(ToneMode).join(', ')}`);
       }
    }
  }

  const rawInput = fs.readFileSync(absolutePath, 'utf-8');
  const agent = new WriterAgent();
  
  let intent: 'Update' | 'LinkedIn' | 'Memo';
  switch (format) {
      case OutputFormat.LinkedIn: intent = 'LinkedIn'; break;
      case OutputFormat.PortfolioUpdate: intent = 'Update'; break;
      case OutputFormat.InternalMemo: intent = 'Memo'; break;
      default: throw new Error('Unknown format mapping');
  }

  return await agent.process(rawInput, intent, audience, tone);
}

if (require.main === module) {
  run(process.argv.slice(2))
    .then(console.log)
    .catch((err) => {
      console.error(err.message);
      process.exit(1);
    });
}
