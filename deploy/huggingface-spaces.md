# Deploying the NEXUS backend to Hugging Face Spaces (Docker, free)

Why HF Spaces: 16 GB RAM free (the torch + MiniLM image needs ~400–700 MB at
runtime — Render's 512 MB free tier risks OOM), Docker SDK reuses this repo's
`Dockerfile` almost verbatim, and Spaces only sleep after **48 h** idle.

Supabase pgvector is external and unaffected — it stays exactly as is.

---

## 0. Prereqs (one-time)
- A Hugging Face account (free): https://huggingface.co/join
- Your existing secrets to hand: `GROQ_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`

## 1. Create the Space
1. https://huggingface.co/new-space
2. **Owner:** you · **Space name:** `nexus-backend`
3. **SDK:** **Docker** → **Blank** template
4. **Hardware:** CPU basic (free) · **Visibility:** Public

## 2. Add the Space metadata to the README the Space uses
The Space's own `README.md` (at the Space repo root) needs this YAML front-matter
so HF routes traffic to the right port:

```yaml
---
title: NEXUS Backend
emoji: 🧠
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---
```

## 3. Push this backend to the Space
The Space is a git repo. Push **only the backend** (the `nexus-frontend/` folder
is not needed on the Space). Easiest path — add the Space as a second remote:

```bash
# from the nexus repo root
git remote add space https://huggingface.co/spaces/<your-username>/nexus-backend
git push space main
```

The Space builds the `Dockerfile` automatically on push.

> If you prefer not to push the frontend folder, create a small dedicated Space
> repo containing: `Dockerfile`, `pyproject.toml`, `README.md` (with the YAML
> above), `src/`, `demo_corpus/`. Those are the only paths the image copies.

## 4. Set Space secrets + the port variable
Space → **Settings → Variables and secrets**:

| Type | Key | Value |
|---|---|---|
| Secret | `GROQ_API_KEY` | (your Groq key) |
| Secret | `SUPABASE_URL` | (your Supabase project URL) |
| Secret | `SUPABASE_KEY` | (your Supabase anon key) |
| Variable | `PORT` | `7860` |
| Variable | `ALLOWED_ORIGINS` | `https://nexussss-two.vercel.app,http://localhost:3000` |

`PORT=7860` matches `app_port: 7860`; the Dockerfile's `CMD` honors `$PORT`.
`ALLOWED_ORIGINS` is read by `config.py` → FastAPI CORS — no code change needed.

## 5. Verify the backend is live
After the build finishes, the Space serves at:
`https://<your-username>-nexus-backend.hf.space`

```bash
curl https://<your-username>-nexus-backend.hf.space/health
# → {"status":"ok","indexed_chunks":N,"llm_backend":"groq","version":"0.1.0"}
curl -X POST https://<your-username>-nexus-backend.hf.space/demo
# → loads the demo corpus
```

## 6. Point the frontend at the new backend (REQUIRED — and redeploy)
`NEXT_PUBLIC_API_URL` is inlined at **build time**, so an env change alone does
nothing until you redeploy.

1. Vercel → nexus project → **Settings → Environment Variables**
2. Set `NEXT_PUBLIC_API_URL = https://<your-username>-nexus-backend.hf.space`
3. **Deployments → Redeploy** (must rebuild, not just restart)

## 7. Smoke-test the live demo
- Open https://nexussss-two.vercel.app
- "Backend unreachable" should be gone; **Try Demo** loads the corpus and a
  query streams an answer with confidence + (where present) a contradiction.

---

## Cold-start note (the one UX gap to close next)
When the Space has been idle >48 h, the first request wakes it (~30–60 s while
the container boots + rebuilds BM25 from Supabase). Until the frontend shows a
"waking the demo backend…" state, that first hit can still read as
"Backend unreachable." Follow-up task: soften the landing health-check to retry
with a warming message instead of failing hard. (Backend `lifespan` already does
non-blocking warmup, so `/health` answers fast once the container is up.)
