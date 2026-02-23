import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { url, email } = body;

    if (!url || !email) return NextResponse.json({ error: "URL and Email required" }, { status: 400 });

    // Path to the bundled script (Inside the repo now)
    const scriptPath = path.resolve(process.cwd(), 'backend/research_writer.py');
    
    // Command
    const command = `python "${scriptPath}" "${url}" "${email}"`;
    
    console.log(`[SAAS-API] Triggering: ${command}`);
    
    // Fire and Forget (Async)
    exec(command, (error, stdout, stderr) => {
        if (error) {
            console.error(`[SAAS-API] Error: ${error}`);
            return;
        }
        console.log(`[SAAS-API] Success: ${stdout}`);
    });

    return NextResponse.json({ status: "started", message: "Agent dispatched. Report arriving via email soon." });

  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
