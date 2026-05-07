# NEXUS Emergency Deployment Checklist
**Status: May 7, 2026 — Infrastructure Down**

## What Just Broke
- ❌ Railway backend (credits exhausted)
- ❌ Supabase database (paused + RLS vulnerability)
- ❌ Vercel frontend (build config error — **FIXED**)

## What's Fixed
- ✅ Frontend Vercel build (`vercel.json` root directory corrected)
- → Vercel will auto-rebuild in ~30s

---

## Step-by-Step Recovery (30 mins)

### 1️⃣ Unpause Supabase (1 min)
1. Go to https://app.supabase.com → Projects
2. Click your `nexus project` (ID: `lntdsbshrndsb0jbxjfh`)
3. See "Project paused" banner
4. Click **"Restore project"** button
5. Wait 30 seconds for it to restart

### 2️⃣ Enable RLS Security (2 mins)
1. In Supabase dashboard, go to **SQL Editor**
2. Click **"+ New query"**
3. Copy all SQL from `supabase_rls_fix.sql` (in this repo)
4. **Paste** into the SQL editor
5. Click **"Run"** (blue button)
6. Should say "Success"

**Why:** Fixes the "Table publicly accessible" security issue. Your documents table is now read-protected.

### 3️⃣ Deploy FastAPI Backend to Fly.io (15 mins)

#### Install Fly CLI (one-time)
```bash
# Windows: https://fly.io/docs/hands-on/install-flyctl/
# macOS: brew install flyctl
# Linux: curl -L https://fly.io/install.sh | sh
```

#### Deploy NEXUS
```bash
fly launch
# Answer prompts:
#   - App name: nexus-backend
#   - Region: iad (US Virginia)
#   - Copy configuration from existing app? → No
#   - Would you like to set up a Postgresql database? → No
#   - Deploy now? → Yes

# Wait ~2 min for build + deploy
```

#### Add Environment Variables
```bash
fly secrets set \
  GROQ_API_KEY="your-groq-key-here" \
  SUPABASE_URL="your-supabase-url" \
  SUPABASE_KEY="your-supabase-anon-key"
```

#### Redeploy with secrets
```bash
fly deploy
```

When done, you'll get a URL like: `https://nexus-backend.fly.dev`

### 4️⃣ Update Vercel Environment (2 mins)
1. Go to https://vercel.com/dashboard
2. Click **nexus** project
3. Click **Settings** → **Environment Variables**
4. Update `NEXT_PUBLIC_API_URL`:
   - **Old value:** (from Railway, broken)
   - **New value:** `https://nexus-backend.fly.dev`
5. Click **Save**
6. Go to **Deployments** → trigger **Redeploy** on latest commit

Vercel will rebuild and deploy with the new backend URL.

### 5️⃣ Test End-to-End (5 mins)
1. Visit https://nexus.skay.dev (or whatever your Vercel URL is)
2. Click **[Try Demo]**
3. Ask a question in the chat
4. Should see:
   - ✅ Response streaming from backend
   - ✅ Confidence bar animating
   - ✅ Source cards appearing
   - ✅ Contradiction badge (if contradictions exist)

---

## If Something Fails

### Vercel build still failing after fix?
```bash
# Make sure the fix was pushed
git log --oneline | head -5
# Should see: "fix: correct vercel.json root directory..."

# If not, push again:
git push origin $(git rev-parse --abbrev-ref HEAD)
```

### Fly.io deploy fails?
```bash
# Check logs
fly logs

# If out of space:
fly scale count 1  # Scale down to 1 instance

# If still broken:
fly destroy nexus-backend  # Delete and start over
fly launch
```

### Supabase RLS SQL error?
- Check the SQL editor for the error message
- Most common: wrong table name or columns
- Verify your documents table exists: go to **Table Editor** in Supabase

### Backend can't reach Supabase?
```bash
fly secrets set SUPABASE_URL="https://xxx.supabase.co"
fly secrets set SUPABASE_KEY="your-actual-anon-key"
fly deploy
```

Check logs: `fly logs`

---

## Final State (After All Steps)

| Component | Status | URL |
|-----------|--------|-----|
| **Frontend** | ✅ Live | https://nexus.skay.dev |
| **Backend** | ✅ Live | https://nexus-backend.fly.dev |
| **Database** | ✅ Live + Secure | Supabase (restored + RLS enabled) |

Your NEXUS demo should now:
- Load documents without errors
- Stream responses from Groq
- Detect contradictions
- Show confidence scores
- Attribute sources

---

## Free Tier Status
- **Fly.io:** Free tier (256MB RAM) — OK for this load
- **Supabase:** Free tier restored (pauses after 7 days of inactivity again)
- **Vercel:** Free tier — fine
- **Groq:** Free tier — 30 requests/min (plenty)

**Pro tip:** Set a calendar reminder in 6 days to do something with Supabase to keep it active (e.g., ask the demo one question).

---

## Questions?
Check:
- `fly status` — see if backend is healthy
- `fly logs` — see backend logs
- Supabase dashboard → Logs → see if queries are coming through
- Vercel dashboard → Deployments → see if frontend built successfully
