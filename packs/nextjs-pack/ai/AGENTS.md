# Next.js pack AI rules

Follow the conventions declared by nextjs-pack:

- App Router only for new routes; never extend pages/.
- Server Components by default; fetch server-side with declared caching.
- Durable mutations run in Server Actions / route handlers with server-side validation, authorization, and cache revalidation.
- Never expose secrets to the client.
- Run type-check, lint, and tests before claiming completion.
