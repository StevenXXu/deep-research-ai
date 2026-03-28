import { NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

export async function POST(req: Request) {
  try {
    const { userId } = await auth();
    const body = await req.json();
    const { type, message, email } = body;

    if (!message) {
      return NextResponse.json({ error: "Message is required" }, { status: 400 });
    }

    const resendApiKey = process.env.RESEND_API_KEY;
    if (!resendApiKey) {
      return NextResponse.json({ error: "Resend API key missing on server" }, { status: 500 });
    }

    const safeMessage = message.replace(/\n/g, '<br/>');

    const htmlContent = `
      <h2>New SoloAnalyst Feedback</h2>
      <p><strong>Type:</strong> ${type || 'Feedback'}</p>
      <p><strong>User ID:</strong> ${userId || 'Anonymous'}</p>
      <p><strong>User Email (Client Provided):</strong> ${email || 'Not provided'}</p>
      <br/>
      <p><strong>Message:</strong></p>
      <div style="background-color: #f4f4f5; padding: 12px; border-radius: 8px;">
        <p>${safeMessage}</p>
      </div>
    `;

    // Try to send email
    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${resendApiKey}`
      },
      body: JSON.stringify({
        from: 'SoloAnalyst Feedback <onboarding@resend.dev>',
        to: ['steve.x.xu@gmail.com', 'stevexxu@outlook.com'],
        subject: `[SoloAnalyst] New ${type || 'Feedback'} Report`,
        html: htmlContent
      })
    });

    if (!res.ok) {
      const text = await res.text();
      console.error("Resend API Error:", text);
      return NextResponse.json({ error: "Failed to send email via Resend" }, { status: 500 });
    }

    return NextResponse.json({ success: true });
  } catch (e: any) {
    console.error("Feedback route error:", e);
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}