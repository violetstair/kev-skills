## Local Kev Decisions

During implementation and debugging, use the installed `kev-local` skill and the
running local Kev server first, without waiting for an explicit user request at
these steps:

- After local search finds four or more plausible unread file candidates, use
  `rank` before reading all their contents (the default `top-k` is three).
- When repeatedly classifying logs or text items into known categories, use `ask`
  with explicit criteria.

For these judgments, call Kev before making the judgment in the main coding model
or requesting another model. Do not bypass Kev because direct reading or another
model seems cheaper or faster, even for short excerpts. Use deterministic code for
exact checks; skip inference when no semantic judgment is needed or rankable
candidates are at most `top-k`. Keep the local server loaded and batch independent
questions about the same state. On failure or uncertainty, report the reason and
continue normal investigation without repeated retries or a hosted classifier
fallback. Read required AGENTS.md, CLAUDE.md, user-designated files, and specs
regardless of scores. The coding agent writes code and runs required tests; Kev
helps choose evidence and cannot authorize actions or prove correctness.
