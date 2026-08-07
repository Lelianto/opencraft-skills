# Testing pack AI rules

- Write tests proportional to risk; high-risk paths need integration/E2E evidence.
- Never weaken a test, remove assertions, or skip tests to pass.
- Run the focused suite and report fresh output before claiming completion.
- Add a regression test that fails on old behavior before fixing a bug.
