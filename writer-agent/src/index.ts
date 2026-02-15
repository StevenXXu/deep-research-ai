import { WriterAgent } from './WriterAgent';
import { OutputFormat, Audience } from './types';
import * as fs from 'fs';
import * as path from 'path';

async function main() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.log('Usage: node dist/index.js <input-file> <format> [source] [audience]');
    console.log('Formats: LinkedIn, PortfolioUpdate, InternalMemo');
    console.log('Audience: Public, Internal, LP (optional)');
    process.exit(1);
  }

  const [inputFile, formatStr, source = 'CLI', audienceStr] = args;

  // Validate format
  if (!Object.values(OutputFormat).includes(formatStr as OutputFormat)) {
    console.error(`Invalid format: ${formatStr}`);
    console.error(`Available formats: ${Object.values(OutputFormat).join(', ')}`);
    process.exit(1);
  }

  const format = formatStr as OutputFormat;
  
  // Determine Intent and Default Audience
  let intent: 'LinkedIn' | 'Update' | 'Memo';
  let defaultAudience: Audience = Audience.Public;

  switch (format) {
    case OutputFormat.LinkedIn:
      intent = 'LinkedIn';
      defaultAudience = Audience.Public;
      break;
    case OutputFormat.PortfolioUpdate:
      intent = 'Update';
      defaultAudience = Audience.Public;
      break;
    case OutputFormat.InternalMemo:
      intent = 'Memo';
      defaultAudience = Audience.Internal;
      break;
    default:
      console.error(`Unsupported format: ${format}`);
      process.exit(1);
  }

  // Override audience if provided
  let audience: Audience = defaultAudience;
  if (audienceStr && Object.values(Audience).includes(audienceStr as Audience)) {
    audience = audienceStr as Audience;
  }

  try {
    const rawInput = fs.readFileSync(path.resolve(inputFile), 'utf-8');
    
    console.log('Initializing Writer Agent...');
    const agent = new WriterAgent();
    
    console.log(`Running generation for ${format} (Intent: ${intent}, Audience: ${audience})...`);
    // agent.process(text, intent, audience, tone?)
    const output = await agent.process(rawInput, intent, audience);
    
    console.log('\n--- GENERATED OUTPUT ---\n');
    console.log(output);
    console.log('\n------------------------\n');
    
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

export { WriterAgent };
