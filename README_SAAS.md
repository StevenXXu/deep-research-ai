# Deep Research SaaS - Deployment Guide

## 1. Environment Setup
Rename `.env.local.example` to `.env.local` and fill in the keys.

### Where to get keys:
- **Clerk**: [dashboard.clerk.com](https://dashboard.clerk.com) -> Create App -> API Keys.
- **Supabase**: [supabase.com](https://supabase.com) -> Create Project -> Settings -> API.
- **Railway**: You already have the URL.

## 2. Database Setup
1. Go to Supabase SQL Editor.
2. Open `supabase/schema.sql`.
3. Run the query. This creates the `profiles` and `reports` tables.

## 3. Webhook Setup (Crucial)
To make sure users are created in the DB when they sign up:
1. Go to **Clerk Dashboard** -> Webhooks.
2. Add Endpoint: `https://your-vercel-url.com/api/webhooks/clerk` (For local dev, use ngrok).
3. Subscribe to `user.created`.
4. Copy the `Signing Secret` to `CLERK_WEBHOOK_SECRET` in `.env.local`.

## 4. Run Local
```bash
npm run dev
```
Visit `http://localhost:3000`.

## 5. Deploy Frontend
1. Push this repo to GitHub.
2. Import to **Vercel**.
3. Add the Environment Variables from `.env.local` to Vercel Settings.
4. Deploy!
