import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { url, email } = body;

    if (!url || !email) return NextResponse.json({ error: "URL and Email required" }, { status: 400 });

    // FORWARD TO LOCAL PYTHON BACKEND (via Tunnel)
    // Ngrok or Localtunnel URL
    const BACKEND_URL = "https://tough-dots-admire.loca.lt/research";
    
    console.log(`[API] Forwarding to: ${BACKEND_URL}`);
    
    try {
        const response = await fetch(BACKEND_URL, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Bypass-Tunnel-Reminder': 'true'
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
        return NextResponse.json({ error: "Backend unavailable. Tunnel might be down." }, { status: 502 });
    }

  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
