export enum ToneMode {
  StrategicBridge = 'StrategicBridge',
  Institutional = 'Institutional',
  PortfolioAmplifier = 'PortfolioAmplifier',
  TechnicalAnalyst = 'TechnicalAnalyst'
}

export enum Audience {
  Public = 'Public',
  Internal = 'Internal',
  LP = 'LP'
}

export interface ContentInput {
  rawText: string;
  source: string;
  metadata?: Record<string, unknown>;
}

export interface WriterOutput {
  content: string;
  metadata?: Record<string, unknown>;
  toneUsed: ToneMode;
}
