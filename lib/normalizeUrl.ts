export function normalizeUrl(input: string): string {
  const raw = (input || "").trim();
  if (!raw) return raw;

  // Already has a scheme
  if (/^https?:\/\//i.test(raw)) return raw;

  // Handle protocol-relative URLs
  if (raw.startsWith("//")) return `https:${raw}`;

  // If it looks like a domain (contains a dot) or starts with www., assume https.
  const looksLikeDomain = raw.startsWith("www.") || /\.[a-z]{2,}(\b|\/|:)/i.test(raw);
  if (looksLikeDomain) return `https://${raw}`;

  return raw;
}
