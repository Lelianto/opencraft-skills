# Supabase pack AI rules

- Enable RLS and write explicit policies for every table; client filtering is not authorization.
- Never use the service role key in the client.
- Schema changes are versioned migrations; destructive changes are approved separately.
- Use generated database types.
