# Wellspring — Future Architecture Specification

**Status:** Draft / planning spec
**Scope:** Dagster → Supabase migration, Next.js SSG (pnpm), FastAPI with LLM generation + session auth, and the song-convert form flow.

This document describes target-state architecture for four components that currently exist in simpler form. Each section states the current state, the target state, the interface contract between components, and open decisions that need to be made explicitly before implementation (marked with 🔶).

---

## 0. System overview

```
                    ┌─────────────────────────────┐
                    │         Supabase            │
                    │   (Postgres + Auth + RLS)   │
                    └──────────────┬───────────────┘
                                   │
                 writes ┌──────────┴──────────┐ reads (build-time)
                         │                     │
              ┌──────────▼─────────┐  ┌────────▼─────────┐
              │  Dagster pipeline  │  │  Next.js (SSG)   │
              │  (src/music_data)  │  │  pnpm, output:   │
              │  IOManager →       │  │  export          │
              │  Supabase writer   │  └────────┬─────────┘
              └─────────────────────┘           │ build-time only
                                                 │
                                   ┌─────────────▼─────────────┐
                                   │   web/app/convert/page.tsx │
                                   │   (client component)       │
                                   └─────────────┬───────────────┘
                                                 │ fetch (runtime, with session cookie)
                                                 │
                                   ┌─────────────▼─────────────┐
                                   │   FastAPI (src/api)        │
                                   │   - /auth/* (Supabase Auth)│
                                   │   - /convert (LLM-backed)  │
                                   │   - reads/writes Supabase  │
                                   └─────────────┬───────────────┘
                                                 │
                                   ┌─────────────▼─────────────┐
                                   │   LLM provider (Anthropic) │
                                   └─────────────────────────────┘
```

Two independent data paths into the same Supabase database:
1. **Build-time path:** Dagster writes rows → Next.js reads rows at `next build` → static HTML.
2. **Request-time path:** user submits a song via the convert form → FastAPI authenticates the session, calls the LLM, writes the result to Supabase, returns it → page renders it client-side, no rebuild involved.

---

## 1. Dagster → Supabase

### 1.1 Current state

- Dagster project at `src/music_data/` (`assets.py`, `resources.py`, `definitions.py`).
- Output IO manager: a JSON file IO manager. Each asset materialization writes `data/song/{song_id}.json` to disk.
- No database involved. `data/` is the only source of truth, and it's read directly by Next.js at build time via `fs`.

### 1.2 Target state

- Replace the JSON file IO manager with a **Supabase-writing IO manager** (or per-asset I/O inside the asset body — see 🔶 below).
- Dagster writes structured rows into Supabase tables instead of JSON blobs on disk.
- `data/song/*.json` becomes legacy. It can be kept temporarily as a migration fallback or removed once the cutover is verified.

### 1.3 Schema (Supabase / Postgres)

Minimum viable schema to support both the static song/term/vocab pages and the convert flow:

```sql
-- songs
create table songs (
  song_id      text primary key,
  title        text not null,
  artist       text,
  data         jsonb not null,        -- the full structured payload (lyrics, segments, etc.)
  source       text not null default 'pipeline',  -- 'pipeline' | 'convert'
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);

-- terms (vocab entries)
create table terms (
  term_id      text primary key,
  term         text not null,
  definition   text not null,
  data         jsonb not null,
  created_at   timestamptz not null default now()
);

-- song_terms (join table — which terms appear in which songs)
create table song_terms (
  song_id text references songs(song_id) on delete cascade,
  term_id text references terms(term_id) on delete cascade,
  primary key (song_id, term_id)
);
```

Using a `jsonb data` column alongside explicit columns lets you keep the existing JSON shape your Dagster assets already produce (minimal rewrite of the asset logic itself) while still having queryable columns (`title`, `artist`, `source`) for listing/filtering pages like the vocab index.

🔶 **Open decision:** is the `data` jsonb blob the long-term shape, or do you want to fully normalize (separate columns/tables per field)? Keeping `jsonb` is the lower-effort migration; normalizing is better if you'll eventually query into the structure (e.g. "all songs containing term X") beyond what the `song_terms` join table already covers.

### 1.4 IO Manager implementation sketch

```python
# src/music_data/resources.py
import json
from dagster import IOManager, io_manager
from supabase import create_client, Client

class SupabaseIOManager(IOManager):
    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)

    def handle_output(self, context, obj):
        # obj is expected to be a dict matching the `songs` row shape
        song_id = context.asset_key.path[-1]
        self.client.table("songs").upsert({
            "song_id": song_id,
            "title": obj["title"],
            "artist": obj.get("artist"),
            "data": obj,
            "source": "pipeline",
        }).execute()

    def load_input(self, context):
        song_id = context.asset_key.path[-1]
        res = self.client.table("songs").select("*").eq("song_id", song_id).single().execute()
        return res.data

@io_manager(config_schema={"url": str, "key": str})
def supabase_io_manager(init_context):
    return SupabaseIOManager(
        url=init_context.resource_config["url"],
        key=init_context.resource_config["key"],
    )
```

```python
# src/music_data/definitions.py
from dagster import Definitions
from .resources import supabase_io_manager
from . import assets

defs = Definitions(
    assets=[...],
    resources={
        "io_manager": supabase_io_manager.configured({
            "url": {"env": "SUPABASE_URL"},
            "key": {"env": "SUPABASE_SERVICE_ROLE_KEY"},
        }),
    },
)
```

🔶 **Open decision:** Dagster writes should use the Supabase **service role key** (bypasses Row Level Security), since the pipeline is a trusted backend process, not a user session. Make sure this key is never exposed to FastAPI's public-facing auth paths or to the frontend — it's pipeline-only, stored as a Dagster deployment secret.

### 1.5 Migration steps (in order)

1. Create the Supabase project and run the schema above.
2. Add `supabase-py` (or raw `psycopg`/`sqlalchemy`) to `pyproject.toml`.
3. Implement `SupabaseIOManager`, point Dagster definitions at it via env-configured resource.
4. Run a one-off backfill script that reads existing `data/song/*.json` and `data/term/*.json` and upserts them into Supabase (this is the actual "migration" — moving historical data, not just future writes).
5. Verify Dagster materializations write correctly (spot-check rows in Supabase dashboard or `select` query).
6. Cut Next.js build-time data fetching over to Supabase queries (see Section 2).
7. Remove the JSON file IO manager and `data/` directory once both paths are confirmed working end-to-end for at least one full rebuild cycle.

---

## 2. Next.js static site generation (pnpm)

### 2.1 Current state

- `web/` scaffolded with `bun create next-app`, using `bun.lock`.
- `output: "export"` in `next.config.ts`.
- Static pages read from `data/song/*.json` / `data/term/*.json` via `fs` in `generateStaticParams()`.

### 2.2 Target state: switch package manager to pnpm

```bash
cd web
rm -rf node_modules bun.lock
corepack enable pnpm        # or: npm install -g pnpm
pnpm import                 # optional: converts bun.lock/package-lock.json -> pnpm-lock.yaml if one exists
pnpm install
```

`package.json` scripts (unchanged in content, just invoked via `pnpm`):

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  }
}
```

Commands going forward:

```bash
pnpm dev
pnpm build      # emits web/out/ due to output: "export"
pnpm start
```

If you use a CI/build host (Vercel, GitHub Actions, etc.), make sure its package-manager detection picks pnpm — Vercel auto-detects from `pnpm-lock.yaml`; for GitHub Actions, use `pnpm/action-setup` before `pnpm install`.

🔶 **Open decision:** any reason for the bun → pnpm switch beyond preference (e.g. team standardization, a dependency that doesn't resolve well under Bun)? Worth noting in case something currently relies on Bun-specific behavior (e.g. `Bun.serve`, `bun:test`) — a vanilla `create-next-app` scaffold shouldn't, but worth a quick check of `package.json` for anything Bun-specific before swapping.

### 2.3 Target state: data source swap (fs → Supabase)

```ts
// web/lib/supabase.ts
import { createClient } from "@supabase/supabase-js";

export const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!   // read-only, public-safe key — build time only needs read access
);
```

```ts
// web/app/song/[song_id]/page.tsx
import { supabase } from "@/lib/supabase";

export async function generateStaticParams() {
  const { data, error } = await supabase.from("songs").select("song_id");
  if (error) throw error;
  return data.map((row) => ({ song_id: row.song_id }));
}

async function getSong(song_id: string) {
  const { data, error } = await supabase
    .from("songs")
    .select("*")
    .eq("song_id", song_id)
    .single();
  if (error) throw error;
  return data;
}

export default async function SongPage({ params }: { params: { song_id: string } }) {
  const song = await getSong(params.song_id);
  return <SongView data={song.data} title={song.title} />;
}
```

Same pattern for `term/[term_id]/page.tsx` and the `vocab/page.tsx` listing (the latter just does a `select` over all `terms` rows, no params needed since it's a single static page, not a dynamic route).

### 2.4 Build-time environment requirements

```
# web/.env.local (and equivalent CI/build secrets)
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...              # safe to expose; RLS restricts what it can read
NEXT_PUBLIC_API_URL=https://api.yourapp.com   # for the client-side /convert fetch
```

The build environment needs outbound network access to Supabase. If building via Vercel this is automatic; if via a sandboxed CI runner, confirm egress isn't blocked.

🔶 **Open decision:** rebuild trigger. Static export means new pipeline data only shows up after the next `pnpm build`. Decide whether rebuilds are manual, on a schedule (e.g. nightly via cron/GitHub Actions), or triggered by a Supabase webhook / Dagster sensor hitting a deploy hook (e.g. Vercel's deploy hook URL) after a successful pipeline run. The last option is the cleanest "data flows through automatically" setup but requires wiring Dagster → deploy hook.

---

## 3. FastAPI: LLM-backed `/convert` + session auth

### 3.1 Current state

- No `src/api/` yet.
- Planned: `/convert` endpoint, synchronous, checks if input is a valid song and runs conversion.

### 3.2 Target state: LLM-backed generation

```python
# src/api/routers/convert.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from anthropic import Anthropic
from ..auth import get_current_user  # see 3.3
from ..db import get_supabase_client

router = APIRouter()
llm = Anthropic()  # reads ANTHROPIC_API_KEY from env

class ConvertRequest(BaseModel):
    input: str

class ConvertResponse(BaseModel):
    song_id: str
    title: str
    data: dict

@router.post("/convert", response_model=ConvertResponse)
def convert_song(req: ConvertRequest, user=Depends(get_current_user)):
    validity = check_is_song(req.input)          # cheap heuristic / lookup check first
    if not validity.is_song:
        raise HTTPException(status_code=422, detail="Not a recognized song")

    song_data = generate_song_data_via_llm(req.input)  # LLM call, see below
    song_id = slugify(song_data["title"])

    db = get_supabase_client()
    db.table("songs").upsert({
        "song_id": song_id,
        "title": song_data["title"],
        "artist": song_data.get("artist"),
        "data": song_data,
        "source": "convert",
    }).execute()

    return ConvertResponse(song_id=song_id, title=song_data["title"], data=song_data)


def generate_song_data_via_llm(raw_input: str) -> dict:
    response = llm.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": f"Given this song input: {raw_input}\n\nReturn ONLY valid JSON matching this schema: {{...}}"
        }],
    )
    text = response.content[0].text
    return json.loads(text)
```

🔶 **Open decision:** what exactly does "check if it's a song" mean — a cheap regex/lookup (e.g. against a known song database or MusicBrainz-style API), or is it itself an LLM call? If it's LLM-based validation followed by LLM-based generation, that's two model calls per submission; worth knowing for latency/cost planning even though you've said the whole thing should stay fast (seconds).

🔶 **Open decision:** LLM output reliability. Asking the model to "return only valid JSON" is a starting point, not a guarantee — plan for a `try/except json.JSONDecodeError` with either a retry or Anthropic's structured-output/tool-use pattern (defining a tool schema and forcing a `tool_use` block) for stronger guarantees than prompting alone.

### 3.3 Target state: session-persisting authentication

Since Supabase already ships an Auth product, the lowest-effort path is using **Supabase Auth** rather than rolling your own session system — FastAPI just verifies the JWT Supabase issues.

**Flow:**
1. Frontend uses `@supabase/supabase-js`'s auth methods (`signInWithOtp`, `signInWithPassword`, OAuth, etc.) directly — Supabase handles issuing a session JWT and refresh token, stored client-side (Supabase's JS client manages this in browser storage for you).
2. On each request to FastAPI, the frontend attaches the Supabase access token: `Authorization: Bearer <token>`.
3. FastAPI verifies the JWT against Supabase's public JWKS (or shared secret, depending on your Supabase project's JWT signing config) and extracts the user.

```python
# src/api/auth.py
from fastapi import Depends, HTTPException, Header
import jwt
import os

SUPABASE_JWT_SECRET = os.environ["SUPABASE_JWT_SECRET"]

def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ")
    try:
        payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return {"id": payload["sub"], "email": payload.get("email")}
```

```python
# src/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import convert

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourapp.com", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(convert.router)
```

**Frontend session handling:**

```ts
// web/lib/supabase-client.ts (browser-side client, distinct from build-time server client)
import { createClient } from "@supabase/supabase-js";

export const supabaseClient = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);
```

```tsx
// web/app/convert/page.tsx (relevant excerpt)
const { data: { session } } = await supabaseClient.auth.getSession();

const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/convert`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${session?.access_token}`,
  },
  body: JSON.stringify({ input }),
});
```

Because Supabase's JS client persists the session in browser storage and auto-refreshes the access token, "session persists" falls out of using Supabase Auth as intended — you don't need to build your own refresh-token rotation or cookie-signing logic.

🔶 **Open decision:** is the convert feature gated behind requiring login (no anonymous use), or is auth optional — e.g. anonymous users can convert but logged-in users get history/saved conversions? This changes whether `get_current_user` should raise on a missing token or treat it as `None` and proceed.

🔶 **Open decision:** Supabase offers magic-link/OTP email, password auth, and OAuth (Google, GitHub, etc.) out of the box. Worth picking which now since it affects what UI you build for the login page.

---

## 4. Form submit → FastAPI client fetch flow (full picture)

This ties Sections 2 and 3 together into the actual page behavior.

```tsx
// web/app/convert/page.tsx
"use client";
import { useState } from "react";
import { supabaseClient } from "@/lib/supabase-client";

type SongData = { title: string; artist?: string; [key: string]: unknown };

export default function ConvertPage() {
  const [input, setInput] = useState("");
  const [result, setResult] = useState<SongData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    const { data: { session } } = await supabaseClient.auth.getSession();

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/convert`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(session ? { Authorization: `Bearer ${session.access_token}` } : {}),
        },
        body: JSON.stringify({ input }),
      });

      if (!res.ok) {
        const body = await res.json();
        throw new Error(body.detail ?? "Something went wrong");
      }
      setResult(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter a song name or URL"
        />
        <button type="submit" disabled={loading || !input}>
          {loading ? "Checking…" : "Convert"}
        </button>
      </form>
      {error && <p role="alert">{error}</p>}
      {result && <SongResultView data={result} />}
    </div>
  );
}
```

This stays a Client Component, compatible with `output: "export"` — no server actions, no route handlers, just a browser-side fetch against the externally-hosted FastAPI service. Nothing here changes if/when the LLM or auth pieces in Section 3 evolve further; the contract the frontend depends on is just: `POST /convert` with `{ input }` and an optional bearer token → `{ song_id, title, data }` or a 4xx with `{ detail }`.

---

## 5. Summary of open decisions (🔶) to resolve before/during implementation

| # | Decision | Affects |
|---|---|---|
| 1 | `jsonb` blob vs. fully normalized schema | Dagster IO manager, Supabase schema |
| 2 | Service role key handling/secrecy | Dagster resource config, deployment secrets |
| 3 | Reason for bun → pnpm (check for Bun-specific code first) | `web/` scaffolding |
| 4 | Rebuild trigger mechanism (manual / scheduled / webhook-driven) | Deployment pipeline, Dagster sensors |
| 5 | "Is this a song" check: heuristic vs. LLM call | FastAPI `/convert`, latency/cost |
| 6 | LLM output reliability strategy (retry vs. tool-use schema) | FastAPI `/convert` |
| 7 | Auth required vs. optional for convert | `get_current_user` behavior, UX |
| 8 | Which Supabase Auth method(s) to support | Login UI, frontend auth flow |

None of these block writing code today — they're product/ops decisions layered on top of an architecture that already holds together end to end.