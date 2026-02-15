/**
 * Supported tone modes for content generation.
 */
export enum ToneMode {
  StrategicBridge = 'StrategicBridge',
  Institutional = 'Institutional',
  PortfolioAmplifier = 'PortfolioAmplifier',
  TechnicalAnalyst = 'TechnicalAnalyst'
}

/**
 * Target audience for the content.
 */
export enum Audience {
  Public = 'Public',
  Internal = 'Internal',
  LP = 'LP'
}

/**
 * Structure for input content to be processed.
 */
export interface ContentInput {
  rawText: string;
  source: string;
  metadata?: Record<string, unknown>;
}

/**
 * Structure for the final output content.
 */
export interface WriterOutput {
  content: string;
  metadata?: Record<string, unknown>;
  toneUsed: ToneMode;
}
