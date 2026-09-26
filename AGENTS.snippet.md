## Local Kev Decisions

During implementation and debugging, use the installed `kev-local` skill without
waiting for an explicit user request at these steps:

- After local search finds four or more plausible unread file candidates, use
  `rank` before reading all their contents (the default `top-k` is three).
- When repeatedly classifying logs or text items into known categories, use `ask`
  with explicit criteria.

Skip Kev when direct reading costs less context and time than preparing a request
and interpreting the response, such as a few short excerpts or evidence already
read. Use deterministic code for exact checks. Keep the local server loaded and
batch independent questions about the same state. On failure or uncertainty,
continue normal investigation without repeated retries or a hosted classifier
fallback. Read required AGENTS.md, CLAUDE.md, user-designated files, and specs
regardless of scores. The coding agent writes code and runs required tests; Kev
helps choose evidence and cannot authorize actions or prove correctness.
