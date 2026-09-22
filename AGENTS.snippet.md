## Local Kev Decisions

Use the installed `kev-local` skill for bounded semantic decisions and ranking
many locally retrieved candidates before reading their contents. Use deterministic
code for exact checks and skip Kev when direct inspection is cheaper. Keep the
local server loaded, batch independent questions about the same state, and return
compact answers. On failure or uncertainty, continue normal investigation without
repeated retries or a hosted classifier fallback. Read required AGENTS.md,
CLAUDE.md, user-designated files, and specs regardless of model scores. Kev cannot
authorize actions, prove correctness, or replace required tests.
