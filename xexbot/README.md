# Xexbot: Human-Like X Automation Bot

## About
Xexbot is an AI-powered bot for ethical X automation, mimicking human interactions for crypto thought leadership (e.g., @PiLord_officia). Builds trust via scam callouts, problem guides, and trends—powered by Gemini/OpenRouter. Free X API compliant, deploys serverless.

## Quick Start (Local)
1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env`, fill keys.
3. `python -m app.main` (or `uvicorn app.main:app --reload`).
4. Test: POST to `/generate-post` with JSON `{"topic": "Pi KYC fix"}`.

## Production Deploy
- **Render**: Use Dockerfile (calls build.sh/start.sh). Connect Git, set env. Auto-scales.
- **Vercel**: `vercel deploy`, uses vercel.json. Serverless, global CDN.

## Usage
- Trigger posts: `curl -X POST http://your-url/generate-post -H "Content-Type: application/json" -d '{"topic": "Trump tariffs impact on $Pi"}'`
- Monitor logs for pings/polls.

## Procedures
1. Get X API keys: developer.x.com (free tier).
2. Gemini: ai.google.dev (free tier up to 15 RPM).
3. OpenRouter: openrouter.ai (pay-as-you-go, Grok models).
4. Customize prompts in `ai_handler.py` for your niche.
5. Scale: Upgrade X tier for more posts; add Redis for prod DB.

## Troubleshooting
- Quota errors: Check X Analytics.
- AI fails: Fallback chains automatically.
- Idle timeout: Pings ensure 24/7.

Contribute? Fork & PR. Questions: DM @yourhandle.