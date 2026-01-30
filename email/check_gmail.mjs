import { ImapFlow } from 'imapflow';
import { simpleParser } from 'mailparser';
import dotenv from 'dotenv';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// Load local, uncommitted secrets if present (works even for Scheduled Task / service contexts)
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config({ path: path.join(__dirname, '.env') });

// Keep output clean (do not leak debug logs into summaries)
process.env.IMAPFLOW_LOG_LEVEL = process.env.IMAPFLOW_LOG_LEVEL || 'silent';

const user = process.env.JOY_GMAIL_USER || 'joyai8009@gmail.com';
const pass = process.env.JOY_GMAIL_APP_PASSWORD;

if (!pass) {
  console.log('Missing credentials: please set environment variable JOY_GMAIL_APP_PASSWORD (Gmail App Password).');
  console.log('Also set JOY_GMAIL_USER (optional; defaults to joyai8009@gmail.com).');
  process.exit(2);
}

const client = new ImapFlow({
  host: 'imap.gmail.com',
  port: 993,
  secure: true,
  auth: { user, pass }
});

function fmtDate(d) {
  try { return new Date(d).toLocaleString('en-AU', { timeZone: 'Australia/Sydney' }); } catch { return String(d); }
}

function clip(s, n = 160) {
  if (!s) return '';
  const t = String(s).replace(/\s+/g, ' ').trim();
  return t.length > n ? t.slice(0, n - 1) + '…' : t;
}

let lock;
try {
  await client.connect();
  lock = await client.getMailboxLock('INBOX');

  // Search unseen messages
  const unseen = await client.search({ seen: false });

  if (!unseen || unseen.length === 0) {
    console.log('No new mail.');
    process.exit(0);
  }

  // Fetch newest first
  const uids = unseen.slice(-20).reverse();

  console.log(`Unread: ${unseen.length} (showing up to ${uids.length})`);

  for await (const msg of client.fetch(uids, { uid: true, envelope: true, source: true, flags: true, internalDate: true }, { uid: true })) {
    const env = msg.envelope || {};
    const from = (env.from && env.from[0]) ? `${env.from[0].name || env.from[0].address || ''}${env.from[0].name && env.from[0].address ? ' <' + env.from[0].address + '>' : ''}` : '';
    const subject = env.subject || '(no subject)';
    const when = msg.internalDate ? fmtDate(msg.internalDate) : '';

    let snippet = '';
    try {
      const parsed = await simpleParser(msg.source);
      snippet = clip(parsed.text || parsed.html || '');
    } catch {
      snippet = '';
    }

    console.log('\n---');
    console.log(`From: ${from}`);
    console.log(`Subject: ${subject}`);
    console.log(`Time: ${when}`);
    if (snippet) console.log(`Snippet: ${snippet}`);
    console.log('Suggested next step: (triage)');
  }
} finally {
  try { if (lock) lock.release(); } catch {}
  try { await client.logout(); } catch {}
}
