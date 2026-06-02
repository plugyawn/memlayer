# Track 3 LocoProp-M PR Confirmation Audit

Date: 2026-06-02

Branch: `codex/wr-fresh-20260526`

Durable evidence ledger: `.opencode/track3_loco_experiments_20260531.md`

## Objective Gates

Requested objective:

1. Confirm a PR with `n=8` runs.
2. Prefer hitting target around `3000` steps or lower.
3. If the `3100` path is encouraging, try `3000`.
4. If `3000` looks encouraging, continue monitoring and scale parallel runs toward `n=8`.
5. After the `2800` checkpoint is available, launch suffix runs to find a path to `3.28` at `3100` or below, preferably `3030` or below.

## Current Evidence

### Exact checkpoint replay

The seed2900 step-2500 checkpoint replay is faithful.

| path | result | verdict |
| --- | ---: | --- |
| exact replay from step 2500 to step 3000 | `3.29350 @3000` | misses target by about `0.0135` |

The exact replay proves the checkpoint and resume machinery are good enough to trust suffix tests. It also proves the current path does not reach `3.28` near `3000`.

### Full 3000 fanout

The full 3000 fanout briefly looked promising at step `1500`, then faded by `1625-1750`.

| gate | observation | verdict |
| --- | --- | --- |
| `1500` | mature seeds were about `0.003-0.0045` better than old lead | encouraging but not decisive |
| `1625` | most of the lead vanished | persistence failure |
| `1750` | sampled mature seeds were at parity or worse than old lead | stop condition hit |

The fanout was stopped to save H100 time. This is not an `n=8` below-3000 confirmation.

### Step-2500 suffix array

Suffix tests from the saved checkpoint did not find a late landing fix.

| suffix | key result | verdict |
| --- | --- | --- |
| `3030/power0.50/cap0.20` | `3.38188 @2525`, `3.38922 @2550` | immediately unstable/worse |
| `3030/pr287-switch/cap0.20` | tracked exact through `2900` without benefit | no improvement |
| `3030/pr287-switch/cap0.50` | `3.34941 @2525` | worse |
| `3030/pr287-switch3125/noloco` | `3.34291 @2550`, worse than exact | worse |
| `3030/pr287-tail3125/noloco` | matched through `2800`, then `3.30765 @2825`, `3.30602 @2850`, `3.30385 @2875` | post-switch slope worse |
| `3030/pr287tail3125+loco2800/cap0.20` | matched through `2800`, then `3.30775 @2825` | LocoProp re-on worsened immediately |

The suffix array satisfies the requested exploration condition, but it did not produce a candidate.

## Resource State

Modal:

- `modal container list`: no active containers.
- `modal app list`: all owned Track 3 apps from the wave are stopped with `0` tasks.

Prime:

- `prime pods list` could not be verified from available env files; the CLI returned `API key unauthorized`.
- No Prime pods were launched or terminated in this audit.

## Decision

Do not launch another `n=8` wave for this exact primitive/schedule. The current evidence contradicts the confirmation goal:

- No run reached `3.28` near `3000`.
- The best exact replay is `3.29350 @3000`.
- The only broad fanout signal faded before it reached the decisive late regime.
- Every tested suffix either tracked exact or worsened.

The goal remains unachieved. A future launch should require a materially different mechanism aimed at the late-slope collapse after roughly `2800`, not another replay of the same LocoProp-M + PR287/no-late schedule.
