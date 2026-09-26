# Kev Skills

**English** | [한국어](README.ko.md)

Agent Skills for using [Kev](https://github.com/jaredpalmer/kev/) in Codex and
Claude Code. The `kev-local` skill uses an already-running local Kev server for
file selection and repeated classification of logs or text during implementation
and debugging. It skips calls when direct reading costs less context and time.

Use it to:

- Classify multiple failure logs and identify what to investigate next.
- Judge whether documents or code are relevant to the current task.
- Choose a reading order among files retrieved by local search.

Run the Kev server and model separately, and keep the server running while using
the skill.

## Prerequisites

- Codex or Claude Code.
- Git and Node.js/npm with `npx` to install the skill.
- Python 3.9 or later to run the helper.
- A local Kev server accessible from the coding agent.

Installing the Kev server itself requires Python 3.12 or later and
[uv](https://docs.astral.sh/uv/). This setup assumes the server and coding agent
run in the same local environment.

## Quick Start

### 1. Start Kev

If Kev is already running at `http://127.0.0.1:8009`, continue to the next step.
Otherwise, follow the [Kev quick start](https://github.com/jaredpalmer/kev/#quick-start)
and start the server in a separate terminal:

```bash
git clone https://github.com/jaredpalmer/kev.git
cd kev
uv sync --extra serve
KEV_DTYPE=bf16 uv run --extra serve python -m kev.serve \
  --run jaredpalmer/kev-4b --port 8009
```

The first run takes time to download and load the model. See the
[Kev documentation](https://github.com/jaredpalmer/kev/) for model choices and
hardware-specific setup.

### 2. Install the Skill

Open another terminal, change to **the project where you want to use the skill**,
and run the command for your agent.

Codex:

```bash
npx skills add violetstair/kev-skills --skill kev-local --agent codex -y
```

Claude Code:

```bash
npx skills add violetstair/kev-skills --skill kev-local --agent claude-code -y
```

Use `--agent codex claude-code` to install for both agents. Add `-g` to make the
skill available across projects. Private repositories require Git credentials
with access to the repository. With SSH authentication, you can use
`git@github.com:violetstair/kev-skills.git` as the source instead. The skill is
installed from Git; `kev-skills` does not need to be published to the npm registry.

### 3. Use It in Your Agent

Open a Codex or Claude Code session in the target project and request your task.
Restart the agent if the installed skill is not visible.

Example for Codex:

```text
$kev-local

Choose a reading order for the documents and code needed to change payment
retries, inspect the selected evidence, and implement the change. Read all
required specifications.
```

Example for Claude Code:

```text
/kev-local Classify these test failure logs and choose what to investigate first.
Check the classifications against the original logs before fixing the failures.
```

The agent can also select the skill during an ordinary implementation or debugging
request. To check whether it actually used Kev, add:

```text
Tell me whether you actually called Kev and what judgment it helped with.
If you skipped it or it failed, explain why.
```

### 4. Check Connectivity and Inference

Run these commands from the project root to verify the helper directly. Set
`KEV_SKILL_DIR` to the installed skill directory. These are the
[skills CLI default paths](https://github.com/vercel-labs/skills#supported-agents);
use the path shown by your installation if it differs.

| Agent | Project installation | Global installation |
| --- | --- | --- |
| Codex | `.agents/skills/kev-local` | `~/.codex/skills/kev-local` |
| Claude Code | `.claude/skills/kev-local` | `~/.claude/skills/kev-local` |

For a project-level Codex installation:

```bash
KEV_SKILL_DIR=".agents/skills/kev-local"
python3 "$KEV_SKILL_DIR/scripts/kev_local.py" --pretty check
python3 "$KEV_SKILL_DIR/scripts/kev_local.py" --pretty ask \
  --request "$KEV_SKILL_DIR/examples/decision.json"
```

For a global Codex installation, use
`KEV_SKILL_DIR="$HOME/.codex/skills/kev-local"`. Use the corresponding Claude Code
path for that agent. Some installations keep a shared copy under
`~/.agents/skills/kev-local` and link agent-specific paths to it; follow your
installation output when setting `KEV_SKILL_DIR`.

- `check` reports connectivity and loaded model metadata. A successful response
  has `mode: "live_health"` and `loaded_model` fields including `run`, `base`, and `device`.
- `ask` performs inference using the example JSON. A successful response has
  `mode: "live_api"`, `answers`, HTTP round-trip time in `http_ms`, and server
  inference time in `server_latency_ms`.

Run both commands: a successful `check` alone does not test inference.
`kev-latest` is an API alias; the server's `--run` option selects the actual model.

## Use Kev Throughout a Project

Merge [AGENTS.snippet.md](AGENTS.snippet.md) into your project's Codex `AGENTS.md`
or Claude Code `CLAUDE.md` to provide the usage conditions. Installing the skill
does not modify those instruction files automatically.

The skill and snippet tell the agent to use Kev at these implementation and
debugging steps without waiting for an explicit skill mention:

- After local search finds four or more plausible unread files, use `rank` before
  reading all their contents. This matches the default `top-k=3`.
- When repeatedly classifying logs or text items using the same categories, use
  `ask` with explicit criteria.

**Skip Kev when direct reading is cheaper.** A few short excerpts or evidence
already read can cost less context and time to inspect directly than to package
into a request and interpret afterward. Automatic selection does not guarantee
a call for every task. The agent also skips calls or resumes ordinary investigation
when:

- Deterministic code can handle the task, such as exact search or file existence.
- The number of rankable candidates is at most `top-k`, which defaults to three.
- The server is unavailable, a request times out, or the response is invalid.

The coding agent still implements changes and runs tests. Kev helps select evidence;
required specifications and original evidence remain part of the investigation.

### Where to Configure Codex Automatic Selection

The exact key is **`allow_implicit_invocation`**. `allow_implict_invocation` is a
misspelling. Set it under `policy` in the skill's `agents/openai.yaml` file:

| Location | Configuration file |
| --- | --- |
| Source in this repository | [`skills/kev-local/agents/openai.yaml`](skills/kev-local/agents/openai.yaml) |
| Project-level Codex installation | `.agents/skills/kev-local/agents/openai.yaml` |
| Any other installation | `<installed-skill-directory>/agents/openai.yaml` |

```yaml
policy:
  allow_implicit_invocation: true
```

This repository already sets it to `true`. Preserve other fields, such as
`interface`, when checking or editing the policy. This setting belongs in
`agents/openai.yaml`, not in `AGENTS.md`, the `SKILL.md` frontmatter, or Codex's
`config.toml`.

The flag permits automatic selection. The skill's `description` and applicable
project instructions help the agent decide when to use it; the flag does not force
a call on every task. See the [official Codex skill documentation](https://learn.chatgpt.com/docs/build-skills).

### Claude Code Settings and Instruction Files

Claude Code controls automatic selection through `disable-model-invocation` in
the `SKILL.md` YAML frontmatter. Leaving it unset, as this skill does, uses the
default `false` and allows automatic selection. Setting it to `true` makes the
skill explicit-only. The `agents/openai.yaml` policy is for Codex.
See the [official Claude skill documentation](https://code.claude.com/docs/en/skills).

Check your instruction filenames too. Codex uses the plural `AGENTS.md` by default.
For Claude Code, put the snippet in `CLAUDE.md`, or import an `AGENTS.md` in the
same directory with this line:

```markdown
@AGENTS.md
```

Direct `AGENTS.md` loading in Claude Code depends on its version and project
instruction settings. The import lets you share instructions when using both
files. See [Claude's instruction file documentation](https://code.claude.com/docs/en/memory#share-one-file-with-other-coding-tools).

### Apply Changes to an Installed Skill

Editing the source repository may not update an existing installation. After
pushing changes, run the installation command again and open a fresh agent session.
Keep `-g` if the original installation was global. To use local changes before
pushing, run this from the target project:

```bash
npx skills add /absolute/path/to/kev-skills --skill kev-local --agent codex claude-code -y
```

Also update any older snippet you copied into the project's instruction files.

## Use the Helper Directly

These examples use `KEV_SKILL_DIR` from the quick start. The helper uses only the
Python standard library and needs no additional packages.

### Ask Typed Questions: `ask`

Copy the [example request](skills/kev-local/examples/decision.json). Put the
evidence in `state` and the questions and criteria in `questions`.

| Question type | Purpose |
| --- | --- |
| `noul` | Estimate the probability that a proposition is true |
| `choice` | Select from named alternatives |
| `score` | Evaluate against ordered levels starting at zero |

```bash
python3 "$KEV_SKILL_DIR/scripts/kev_local.py" --pretty ask --request request.json
```

`ask --request -` reads JSON from standard input. `ask --raw` includes the full API
response. See [decision patterns](skills/kev-local/references/decision-patterns.md)
for request formats and interpretation.

### Choose a File Reading Order: `rank`

From the project root, save candidate paths one per line and rank them. This
example searches Markdown documents under `docs` for payment retry evidence.
Adjust the directory and terms for your project. Searching requires `rg`.

```bash
rg -l --glob '*.md' 'retry|idempotency' docs > /tmp/kev-candidates.txt
python3 "$KEV_SKILL_DIR/scripts/kev_local.py" rank \
  --root . --files-from /tmp/kev-candidates.txt \
  --query 'Find constraints and evidence for implementing payment retries' --top-k 3
```

`suggested_paths` gives the suggested reading order. `review_required` marks
candidates needing further inspection. `deferred_paths` remain candidates to
revisit as needed. Use `--required docs/payment-spec.md` with a real path to keep
a required document in the result.

By default, rank evaluates up to 12 candidates sequentially using excerpts of up
to 2,400 characters per file. Narrow the search first if there are more candidates.
Required documents and candidates needing review are retained, so the result can
contain more than `top-k` files.

## Connection Settings and Troubleshooting

The default server URL is `http://127.0.0.1:8009`. For another port, put
`--base-url` before the subcommand:

```bash
python3 "$KEV_SKILL_DIR/scripts/kev_local.py" \
  --base-url http://127.0.0.1:8010 --pretty check
```

You can also set `KEV_BASE_URL`. The coding agent must inherit that environment
variable for the helper it launches to use it.

| Symptom | What to check |
| --- | --- |
| Skill is not visible | Check the target agent and project/global installation path, then start a new session. |
| Server is running but no calls occur | Check the installed automatic-selection policy, active `AGENTS.md`/`CLAUDE.md`, file-selection/classification triggers, and direct-reading skip condition. Explicit invocation can help distinguish selection from connectivity issues. |
| `skipped_small_set` | The candidate count is at most `top-k`; skipping inference is expected. |
| `local_connection_failed_or_timed_out` | Check the URL, model loading status, and the agent's local network access. |
| Works in a terminal but fails in the agent | Check sandbox loopback restrictions and allow the specific helper command's local access if needed. |
| `check` works but `ask` fails | Inspect the server logs and error. To diagnose slow inference, increase the timeout as shown below. |

```bash
python3 "$KEV_SKILL_DIR/scripts/kev_local.py" --timeout 60 --pretty ask \
  --request "$KEV_SKILL_DIR/examples/decision.json"
```

The default HTTP timeout is 15 seconds. Rank also has a separate client budget,
`--budget-seconds 15`; check both when diagnosing slow inference. A client timeout
does not cancel inference already running on the server.

The helper permits HTTP requests only to `127.0.0.1` and `localhost`. In a remote
environment or separate container, `localhost` refers to that environment, so the
agent must be able to reach Kev at the same address. On failure, the agent resumes
ordinary investigation. The helper does not start a server or switch to hosted
inference automatically.

## Related Documentation

- [Kev repository](https://github.com/jaredpalmer/kev/): models, server setup, and API.
- [Skill instructions](skills/kev-local/SKILL.md): triggers and workflow.
- [Decision patterns](skills/kev-local/references/decision-patterns.md): request/response formats and examples.
- [skills CLI](https://github.com/vercel-labs/skills): installation options and skill management.
