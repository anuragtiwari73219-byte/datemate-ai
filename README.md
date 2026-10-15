# DateMate AI — Agentic Dating Simulator

A consent-based prototype in which profile agents simulate respectful first-date conversations and produce explainable, heuristic compatibility rankings.

## Features
- 25 fictional demo personas for immediate demo; they are clearly not real people.
- Individual profile pages with interests, stated values, profile links, and analysis.
- Add a participant with official LinkedIn + Instagram URLs and self-reported information, requiring explicit consent confirmation.
- Agent-to-agent first-date simulation.
- Per-person rankings with reasons.
- Optional Groq LLM generation when `GROQ_API_KEY` is configured; deterministic local demo dialogue works without a key.

## Run locally
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```
Open http://127.0.0.1:8000

For LLM-generated analysis and dialogue, set `GROQ_API_KEY` in your environment before starting the server. Never commit API keys.

## Deploy to Render
1. Push this folder to a public GitHub repository.
2. In Render, create a new Web Service from the repo.
3. Render can use `render.yaml`; build command: `pip install -r requirements.txt`; start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`.
4. Add `GROQ_API_KEY` as a secret environment variable if using Groq.

## Important limits
- This prototype intentionally does not scrape LinkedIn or Instagram. Enter only participant-authorized profile URLs and self-reported details. It stores the links as references; it does not fetch or parse social network pages.
- Demo personas are fictional, not 25 real people. Do not present them as real profiles or as proof of having sourced real participants.
- The heuristic fit score is not scientifically validated and is not a prediction of attraction.
- No real messages are sent. All dates are simulations; the participants decide for themselves.
- Production use needs authentication, durable storage, consent records, privacy controls, rate limiting, and review of platform terms and applicable law.
