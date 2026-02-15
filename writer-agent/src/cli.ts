import fs from 'fs';
import path from 'path';
import { WriterAgent } from './WriterAgent';
import { Audience, ToneMode } from './types';

// Map CLI format argument to WriterAgent intent
const formatMap: Record<string, 'Update' | 'LinkedIn' | 'Memo'> = {
  'update': 'Update',
  'linkedin': 'LinkedIn',
  'memo': 'Memo'
};

const audienceMap: Record<string, Audience> = {
  'public': Audience.Public,
  'internal': Audience.Internal,
  'lp': Audience.LP
};

const toneMap: Record<string, ToneMode> = {
  'strategic': ToneMode.StrategicBridge,
  'institutional': ToneMode.Institutional,
  'amplifier': ToneMode.PortfolioAmplifier,
  'technical': ToneMode.TechnicalAnalyst
};

function parseArgs(args: string[]): Record<string, string> {
  const options: Record<string, string> = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--')) {
      const key = args[i].substring(2);
      // Check if next arg exists and is not a flag
      if (i + 1 < args.length && !args[i + 1].startsWith('--')) {
        options[key] = args[i + 1];
        i++; // Skip the value
      } else {
        // Flag without value (boolean true, stored as 'true')
        options[key] = 'true';
      }
    }
  }
  return options;
}

async function main() {
  const options = parseArgs(process.argv.slice(2));

  if (!options.input || !options.format) {
    console.log('Usage: node cli.js --input <file> --format <update|linkedin|memo> [--audience <public|internal|lp>] [--tone <strategic|institutional|amplifier|technical>]');
    process.exit(1);
  }

  const inputPath = path.resolve(process.cwd(), options.input);
  if (!fs.existsSync(inputPath)) {
    console.error(`Error: Input file not found at ${inputPath}`);
    process.exit(1);
  }

  const text = fs.readFileSync(inputPath, 'utf-8');

  const formatKey = options.format.toLowerCase();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const format = (formatMap as any)[formatKey];
  if (!format) {
    console.error(`Error: Invalid format "${options.format}". Must be one of: update, linkedin, memo`);
    process.exit(1);
  }

  const audienceKey = (options.audience || 'public').toLowerCase();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const audience = (audienceMap as any)[audienceKey];
  if (!audience) {
    console.error(`Error: Invalid audience "${options.audience}". Must be one of: public, internal, lp`);
    process.exit(1);
  }

  let tone: ToneMode | undefined;
  if (options.tone) {
    const toneKey = options.tone.toLowerCase();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const mappedTone = (toneMap as any)[toneKey];
    if (!mappedTone) {
      console.error(`Error: Invalid tone "${options.tone}". Must be one of: strategic, institutional, amplifier, technical`);
      process.exit(1);
    }
    tone = mappedTone;
  }

  const agent = new WriterAgent();

  try {
    const result = await agent.process(text, format, audience, tone);
    console.log(result);
  } catch (error) {
    console.error('Error processing content:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

export { main, parseArgs }; // Export for testing
