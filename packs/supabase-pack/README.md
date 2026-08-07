# Supabase pack

Living context for Supabase backends: Row Level Security, versioned migrations, realtime, and auth.

## Included contexts

- `ctx-supabase-rls` — RLS on every table with reviewed policies (hardened-mandate, block).
- `ctx-supabase-migrations` — versioned migrations, no hand-edited schema (block).
- `ctx-supabase-realtime` — scoped, cleaned-up subscriptions (warn).

## Extends

- `typescript-pack@^1`
- `security-pack@^1`

## Provenance

- Author: OpenCraft Backend · License: MIT · Source: https://github.com/Lelianto/opencraft-skills
