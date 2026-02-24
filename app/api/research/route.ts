import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { url, email } = body;

    if (!url || !email) return NextResponse.json({ error: "URL and Email required" }, { status: 400 });

    // FORWARD TO LOCAL PYTHON BACKEND (via Tunnel)
    const BACKEND_URL = "https://good-chicken-pay.loca.lt/research";
    
    console.log(`[API] Forwarding to: ${BACKEND_URL}`);
    
    // We send the request to the Python backend
    // Fire and forget is tricky with HTTP, so we'll await a quick acknowledgement
    try {
        const response = await fetch(BACKEND_URL, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Bypass-Tunnel-Reminder': 'true' // Bypass Localtunnel warning
            },
            body: JSON.stringify({ url, email })
        });
        
        if (!response.ok) {
            throw new Error(`Backend responded with ${response.status}`);
        }
        
        const data = await response.json();
        return NextResponse.json(data);
        
    } catch (err: any) {
        console.error(`[API] Proxy Error: ${err.message}`);
        return NextResponse.json({ error: "Backend unavailable. Is the tunnel running?" }, { status: 502 });
    }
}
/*
    // Path to the bundled script (Inside the repo now)
    // const scriptPath = path.resolve(process.cwd(), 'backend/research_writer.py');
    // ...
*/
