import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const formData = await req.formData();
    const url = formData.get("url") as string;
    const email = formData.get("email") as string;
    const file = formData.get("file") as File | null;

    if (!url || !email) {
      return NextResponse.json({ error: "URL and Email required" }, { status: 400 });
    }

    // FORWARD TO LOCAL PYTHON BACKEND (via Tunnel)
    // Updated: 2026-02-28
    const TUNNEL_URL = "https://tasty-crabs-sing.loca.lt";
    const BACKEND_ENDPOINT = `${TUNNEL_URL}/research-upload`;

    const backendForm = new FormData();
    backendForm.append("url", url as string);
    backendForm.append("email", email as string);
    if (file) backendForm.append("file", file);

    try {
      console.log(`[PROXY] Forwarding to ${BACKEND_ENDPOINT}...`);
      
      const response = await fetch(BACKEND_ENDPOINT, {
        method: 'POST',
        // 'Bypass-Tunnel-Reminder' is critical for loca.lt to avoid the "Click to Continue" page blocking the API
        headers: {
          'Bypass-Tunnel-Reminder': 'true' 
        },
        body: backendForm
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
