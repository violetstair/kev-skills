# Kev Skills

[English](README.md) | **한국어**

[Kev](https://github.com/jaredpalmer/kev/)를 Codex와 Claude Code 작업에 활용하기 위한
Agent Skills입니다. 현재 제공하는 `kev-local` 스킬은 구현·디버깅 중 파일 선별과
로그·텍스트의 반복 분류를 로컬에서 실행 중인 Kev에 맡깁니다. 직접 읽는 편이
문맥 사용량과 시간 면에서 저렴하면 호출을 생략합니다.

다음과 같은 작업에 사용할 수 있습니다.

- 여러 실패 로그를 원인별로 분류하고 다음에 조사할 대상을 선택하기
- 문서나 코드가 현재 작업과 관련 있는지 판단하기
- 검색으로 찾은 여러 파일 중 먼저 읽을 파일의 순서를 정하기

Kev 서버와 모델은 별도로 실행해야 합니다. 스킬을 사용하는 동안 서버를 켜 두세요.

## 준비 사항

- Codex 또는 Claude Code
- 스킬 설치에 사용할 Git과 Node.js/npm의 `npx`
- 스킬 도우미를 실행할 Python 3.9 이상
- 코딩 에이전트에서 접근할 수 있는 로컬 Kev 서버

Kev 서버를 새로 설치한다면 Python 3.12 이상과 [uv](https://docs.astral.sh/uv/)가
필요합니다. 서버와 코딩 에이전트는 같은 로컬 환경에서 실행하는 구성을 기준으로 합니다.

## 빠른 시작

### 1. Kev 서버 실행

이미 Kev가 `http://127.0.0.1:8009`에서 실행 중이면 다음 단계로 이동하세요.
처음 사용하는 경우 [Kev 공식 설치 안내](https://github.com/jaredpalmer/kev/#quick-start)에
따라 별도 터미널에서 서버를 실행합니다.

```bash
git clone https://github.com/jaredpalmer/kev.git
cd kev
uv sync --extra serve
KEV_DTYPE=bf16 uv run --extra serve python -m kev.serve \
  --run jaredpalmer/kev-4b --port 8009
```

최초 실행에는 모델 다운로드와 로딩 시간이 필요합니다. 사용할 모델과 하드웨어별
실행 방법은 [Kev 문서](https://github.com/jaredpalmer/kev/)를 참고하세요.

### 2. 스킬 설치

새 터미널을 열고 **스킬을 사용할 프로젝트 디렉터리**로 이동한 다음,
사용하는 에이전트에 맞는 명령을 실행합니다.

Codex:

```bash
npx skills add violetstair/kev-skills --skill kev-local --agent codex -y
```

Claude Code:

```bash
npx skills add violetstair/kev-skills --skill kev-local --agent claude-code -y
```

두 에이전트에 함께 설치하려면 `--agent codex claude-code`를 사용합니다.
모든 프로젝트에서 사용하려면 설치 명령에 `-g`를 추가하세요.
비공개 저장소를 설치할 때는 해당 저장소에 접근할 수 있는 Git 인증이 필요합니다.
SSH 인증을 사용한다면 저장소 주소를 `git@github.com:violetstair/kev-skills.git`로
지정할 수도 있습니다. 스킬은 Git 저장소에서 설치하므로 npm 레지스트리에
`kev-skills`를 등록하거나 공개할 필요가 없습니다.

### 3. 에이전트에서 사용

스킬을 설치한 프로젝트에서 Codex 또는 Claude Code 세션을 열고 작업을 요청합니다.
설치한 스킬이 보이지 않으면 에이전트를 다시 시작하세요.

Codex 요청 예시:

```text
$kev-local

결제 재시도 수정에 필요한 문서와 코드 후보의 읽기 순서를 정하고,
선택한 근거를 확인한 뒤 구현해줘. 필수 명세는 모두 읽어줘.
```

Claude Code 요청 예시:

```text
/kev-local 여러 테스트 실패 로그를 원인별로 분류하고, 먼저 조사할 대상을 골라줘.
분류 결과를 원본 로그와 대조한 뒤 수정해줘.
```

일반 작업 요청에서도 에이전트가 스킬을 자동으로 선택할 수 있습니다. 사용 여부를
확인하고 싶다면 요청에 다음 문장을 덧붙이세요.

```text
Kev를 실제로 호출했는지, 호출했다면 어떤 판단에 사용했는지 알려줘.
생략하거나 실패했다면 그 이유도 알려줘.
```

### 4. 연결과 실제 추론 확인

직접 동작을 확인하려면 프로젝트 루트에서 아래 명령을 실행합니다.
`KEV_SKILL_DIR`에는 설치 위치를 지정하세요.
아래는 [skills CLI의 기본 경로](https://github.com/vercel-labs/skills#supported-agents)이며,
설치 결과에 다른 위치가 표시되면 그 경로를 사용합니다.

| 설치 대상 | 프로젝트 설치 경로 | 전역 설치 경로 |
| --- | --- | --- |
| Codex | `.agents/skills/kev-local` | `~/.codex/skills/kev-local` |
| Claude Code | `.claude/skills/kev-local` | `~/.claude/skills/kev-local` |

다음은 Codex 프로젝트 설치 기준입니다.

```bash
KEV_SKILL_DIR=".agents/skills/kev-local"
python3 "$KEV_SKILL_DIR/scripts/kev_local.py" --pretty check
python3 "$KEV_SKILL_DIR/scripts/kev_local.py" --pretty ask \
  --request "$KEV_SKILL_DIR/examples/decision.json"
```

전역 Codex 설치라면 첫 줄을 `KEV_SKILL_DIR="$HOME/.codex/skills/kev-local"`로
바꾸세요. Claude Code도 표의 설치 위치에 맞게 지정합니다.
설치 방식에 따라 공용 원본이 `~/.agents/skills/kev-local`에 있고 에이전트별 경로가
심볼릭 링크일 수 있습니다. `KEV_SKILL_DIR`은 실제 설치 결과의 경로를 사용하세요.

- `check`: 연결 상태와 로딩된 모델을 조회합니다. 성공하면 `mode: "live_health"`와
  `loaded_model`의 `run`, `base`, `device`를 확인할 수 있습니다.
- `ask`: 예제 JSON으로 실제 추론을 요청합니다. 성공하면 `mode: "live_api"`,
  `answers`, HTTP 왕복 시간 `http_ms`, 서버 추론 시간 `server_latency_ms`를 반환합니다.

`check` 성공 후 `ask`까지 확인해야 실제 추론이 가능한지 알 수 있습니다.
`kev-latest`는 API 별칭이며, 실제 모델은 Kev 서버의 `--run`으로 선택합니다.

## 프로젝트에서 지속적으로 활용하기

프로젝트의 Codex `AGENTS.md` 또는 Claude Code `CLAUDE.md`에
[AGENTS.snippet.md](AGENTS.snippet.md)의 지침을 병합하면 Kev를 사용할 작업 조건을
에이전트에 전달할 수 있습니다. 스킬 설치는 이 파일들을 자동으로 수정하지 않습니다.

현재 스킬과 snippet은 구현·디버깅 중 다음 단계에서 사용자가 스킬을 명시하지 않아도
Kev를 사용하도록 안내합니다.

- 로컬 검색으로 아직 읽지 않은 관련 후보 파일을 4개 이상 찾았다면, 본문을 모두
  읽기 전에 `rank`로 읽기 순서를 정합니다. 기본 `top-k=3`에 맞춘 조건입니다.
- 여러 로그나 텍스트를 같은 기준으로 반복 분류해야 한다면 `ask`를 사용합니다.

**직접 읽는 것이 저렴하면 생략합니다.** 짧은 발췌 몇 개이거나 이미 읽은 근거라면,
요청을 만들고 결과를 해석하는 것보다 직접 확인하는 편이 문맥과 시간을 덜 쓸 수
있습니다. 자동 선택은 모든 작업에서의 호출을 보장하지 않으며, 다음 경우에도
생략하거나 일반 조사로 돌아갑니다.

- 정확한 문자열 검색, 파일 존재 확인 등 일반 코드로 처리할 수 있는 작업
- `rank`에서 평가 가능한 후보 수가 `top-k` 이하인 경우: 기본값은 3개
- 서버 연결 실패, 시간 초과, 유효하지 않은 응답

코드 구현과 테스트는 코딩 에이전트가 수행합니다. Kev의 판단 결과는 확인할 근거를
선택하는 데 사용하며, 필수 명세와 원본 증거는 결과와 관계없이 확인합니다.

### Codex 자동 선택 설정 위치

정확한 키 이름은 **`allow_implicit_invocation`**입니다.
`allow_implict_invocation`은 오타입니다. 이 설정은 스킬 디렉터리 안의
`agents/openai.yaml`에서 `policy` 아래에 둡니다.

| 대상 | 설정 파일 |
| --- | --- |
| 이 저장소의 원본 | [`skills/kev-local/agents/openai.yaml`](skills/kev-local/agents/openai.yaml) |
| Codex 프로젝트 설치 | `.agents/skills/kev-local/agents/openai.yaml` |
| 다른 설치 위치 | `<실제 스킬 설치 경로>/agents/openai.yaml` |

```yaml
policy:
  allow_implicit_invocation: true
```

현재 저장소에는 이미 `true`로 설정되어 있습니다. 기존 `interface` 등 다른 항목을
유지하면서 `policy` 항목을 확인하세요. `AGENTS.md`, `SKILL.md`의 YAML 헤더,
또는 Codex의 `config.toml`에 넣는 설정이 아닙니다.

`true`는 모델이 스킬을 자동으로 선택할 수 있게 허용합니다. 실제 선택에는 스킬의
`description`과 적용되는 프로젝트 지침이 함께 영향을 주며, 모든 작업에서 호출을
강제하지는 않습니다. [공식 Codex 스킬 문서](https://learn.chatgpt.com/docs/build-skills)

### Claude Code 설정과 지침 파일

Claude Code의 자동 선택은 `SKILL.md` YAML 헤더의 `disable-model-invocation`으로
제어합니다. 이 스킬처럼 생략하면 기본값이 `false`이므로 자동 선택이 가능합니다.
`true`를 추가하면 명시 호출 전용이 됩니다. `agents/openai.yaml`의 설정은 Codex용입니다.
[공식 Claude 스킬 문서](https://code.claude.com/docs/en/skills)

지침 파일명도 확인하세요. Codex의 기본 파일명은 복수형인 `AGENTS.md`입니다.
Claude Code에서는 `CLAUDE.md`에 snippet을 넣거나, 같은 디렉터리의 `AGENTS.md`를
다음 한 줄로 가져올 수 있습니다.

```markdown
@AGENTS.md
```

Claude Code의 `AGENTS.md` 자동 로딩은 버전과 프로젝트 지침 설정에 따라 다르므로,
`CLAUDE.md`와 함께 사용하는 경우 위 import로 공유할 수 있습니다.
[Claude 지침 파일 문서](https://code.claude.com/docs/en/memory#share-one-file-with-other-coding-tools)

### 변경 사항을 설치된 스킬에 반영하기

저장소 원본을 수정해도 기존 설치본은 자동으로 갱신되지 않을 수 있습니다.
원격 저장소에 push한 뒤 같은 설치 명령을 다시 실행하고 새 에이전트 세션을 여세요.
전역 설치였다면 `-g`도 유지합니다. push 전에 로컬 변경을 사용하려면 대상 프로젝트에서:

```bash
npx skills add /absolute/path/to/kev-skills --skill kev-local --agent codex claude-code -y
```

이전에 프로젝트 지침에 붙여 넣은 snippet도 새 내용으로 갱신하세요.

## 도우미를 직접 사용하는 방법

아래 예시는 빠른 시작에서 설정한 `KEV_SKILL_DIR`을 사용합니다.
도우미는 Python 표준 라이브러리만 사용하므로 별도 패키지 설치가 필요하지 않습니다.

### 질문하기: `ask`

[예제 요청](skills/kev-local/examples/decision.json)을 복사한 뒤 `state`에 판단할
내용을, `questions`에 질문과 선택 기준을 작성합니다.

| 질문 유형 | 용도 |
| --- | --- |
| `noul` | 특정 명제가 참일 확률 판단 |
| `choice` | 주어진 선택지 중 하나 선택 |
| `score` | 0부터 시작하는 순서형 기준으로 평가 |

```bash
python3 "$KEV_SKILL_DIR/scripts/kev_local.py" --pretty ask --request request.json
```

`ask --request -`는 표준 입력에서 JSON을 읽고, `ask --raw`는 전체 API 응답을
포함합니다. 요청 형식과 결과 해석은
[판단 패턴 안내](skills/kev-local/references/decision-patterns.md)를 참고하세요.

### 파일 읽기 순서 정하기: `rank`

프로젝트 루트에서 관련 후보 경로를 한 줄씩 파일로 저장한 뒤 평가합니다.
다음은 `docs` 디렉터리에서 결제 재시도 관련 Markdown 문서를 찾는 예시입니다.
디렉터리와 검색어는 실제 프로젝트에 맞게 바꾸세요. 검색에는 `rg`가 필요합니다.

```bash
rg -l --glob '*.md' 'retry|idempotency|재시도' docs > /tmp/kev-candidates.txt
python3 "$KEV_SKILL_DIR/scripts/kev_local.py" rank \
  --root . --files-from /tmp/kev-candidates.txt \
  --query '결제 재시도 구현에 필요한 제약과 근거' --top-k 3
```

`suggested_paths`는 권장 읽기 순서이고, `review_required`는 추가 확인이 필요한
후보를 나타냅니다. `deferred_paths`도 필요하면 다시 확인해야 하는 후보입니다.
필수 문서는 `--required docs/payment-spec.md`처럼 실제 경로를 지정할 수 있습니다.

기본값으로 최대 12개 후보를 파일당 2,400자까지 발췌해 순차 평가합니다. 후보가 많으면
검색 범위를 먼저 좁히세요. 필수 문서나 추가 확인이 필요한 후보가 유지되므로
결과는 `top-k`보다 많을 수 있습니다.

## 연결 설정과 문제 해결

기본 서버 주소는 `http://127.0.0.1:8009`입니다. 다른 포트에서 실행 중이라면
`--base-url`을 서브명령 앞에 지정합니다.

```bash
python3 "$KEV_SKILL_DIR/scripts/kev_local.py" \
  --base-url http://127.0.0.1:8010 --pretty check
```

`KEV_BASE_URL` 환경 변수로도 설정할 수 있습니다. 에이전트가 실행하는 도우미에도
적용하려면 해당 환경 변수가 에이전트 실행 환경에 전달되어야 합니다.

| 증상 | 확인 방법 |
| --- | --- |
| 스킬이 보이지 않음 | 설치 대상 에이전트와 프로젝트·전역 설치 위치를 확인하고 세션을 다시 시작합니다. |
| 서버는 켜져 있지만 호출이 없음 | 설치본의 자동 선택 설정, 적용되는 `AGENTS.md`/`CLAUDE.md`, 파일 선별·반복 분류 조건과 직접 읽기 생략 조건을 확인합니다. 진단 시 명시 호출로 연결 문제와 구분할 수 있습니다. |
| `skipped_small_set` | 후보 수가 `top-k` 이하라 호출을 생략한 정상 결과입니다. |
| `local_connection_failed_or_timed_out` | 서버 주소, 모델 로딩 상태, 에이전트의 로컬 네트워크 접근 권한을 확인합니다. |
| 터미널에서는 성공하지만 에이전트에서는 실패 | 샌드박스의 loopback 통신 제한을 확인하고, 필요한 도우미 명령의 로컬 접근을 허용합니다. |
| `check`는 성공하지만 `ask`는 실패 | 서버 로그와 오류를 확인합니다. 추론 지연이 의심되면 아래처럼 시간 제한을 늘려 진단합니다. |

```bash
python3 "$KEV_SKILL_DIR/scripts/kev_local.py" --timeout 60 --pretty ask \
  --request "$KEV_SKILL_DIR/examples/decision.json"
```

기본 HTTP 시간 제한은 15초입니다. `rank`에는 별도로 전체 클라이언트 예산
`--budget-seconds 15`가 있으므로 긴 추론을 진단할 때는 두 설정을 함께 확인하세요.
클라이언트의 시간 초과는 이미 서버에서 진행 중인 추론을 취소하지 않습니다.

도우미는 HTTP의 `127.0.0.1`과 `localhost`만 허용합니다. 원격 환경이나 별도 컨테이너의
`localhost`는 사용자 컴퓨터를 가리키지 않으므로, 에이전트에서 같은 주소로 Kev에
접근할 수 있어야 합니다. 실패 시 에이전트는 일반 조사로 복귀하며, 도우미가 서버를
자동 실행하거나 외부 추론 서비스로 전환하지 않습니다.

## 관련 문서

- [Kev 공식 저장소](https://github.com/jaredpalmer/kev/): 모델 설치, 서버 실행, API 안내
- [스킬 사용 지침](skills/kev-local/SKILL.md): 호출 조건과 작업 흐름
- [판단 패턴 안내](skills/kev-local/references/decision-patterns.md): 요청·응답 형식과 활용 예시
- [skills CLI](https://github.com/vercel-labs/skills): 설치 옵션과 스킬 관리
