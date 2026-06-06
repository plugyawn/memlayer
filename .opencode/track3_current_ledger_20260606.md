# Track 3 Current Ledger - 2026-06-06

This is the current-only ledger for the active LocoProp-M / PR287-tail work.
Do not use broad historical `.opencode` run clutter as live context unless a run
is explicitly named here.

## Active Boundary

- Current hypothesis family: simple Track 3 Muon + LocoProp-M prefix, then
  PR287-style late scheduling.
- Current question: can we preserve the early/mid LocoProp advantage and avoid
  the post-2500 slope starvation?
- Do not repeat: plain oldtail `h3075,p1.10` suffixes from 2400. They reproduce
  the same slope and do not create a sub-3.28 path.

## Prime Pod

- pod_id: `6f66430b6a1a444bbe1f503b4f73caaf`
- name: `oc-main-track3-coldpulse-h100-20260605-2145`
- provider: `datacrunch`
- gpu: `H100 80GB HBM3` / H100 SXM5-class
- price: `$3.25/hr`
- ip: `31.22.104.57`
- ssh known_hosts: `.opencode/prime_known_hosts_coldpulse`
- Prime list status as of final check: zero active pods.
- final state: pod terminated after WR checkpoint builder and state diffs
  completed; minimal logs/diffs pulled locally.

## Completed Diagnostic Run

### `wr_source_seed3710_ckpt2000_2400_h100`

Status: completed successfully, rc `0`; pod later terminated.

Purpose:

- Build exact current-record WR-source checkpoints for seed `3710`, no
  LocoProp hooks.
- Save:
  - `/root/.cache/track3_checkpoints/wr_source_seed3710_step2000.pt`
  - `/root/.cache/track3_checkpoints/wr_source_seed3710_step2400.pt`
- Compare those against the cold-pulse checkpoints with
  `tools/analyze_track3_state_diff.py`.

Settings:

```text
source=records/track_3_optimization/results/20260509_contra_soft_muon/03c36e81-e2e5-4916-bf16-0141999b1dbb.txt
seed=3710
train_steps=2400
schedule_steps=3105
checkpoint_steps=2000,2400
```

Verification:

```text
WR_SAVE_CHECKPOINT=/root/.cache/track3_checkpoints/wr_source_seed3710_step{step}.pt
WR_SAVE_CHECKPOINT_STEPS=2000,2400
```

Result:

```text
2000 3.43533
2125 3.41192
2250 3.38738
2375 3.36583
2400 3.36072
```

Artifacts pulled locally:

```text
.opencode/current_track3_ledger_20260606_logs/wr_source_seed3710_ckpt2000_2400_h100.log
.opencode/current_track3_ledger_20260606_logs/wr_source_seed3710_ckpt2000_2400_h100.status
.opencode/current_track3_ledger_20260606_logs/wr_source_seed3710_ckpt2000_2400_h100_train_gpt_wr_record_resume.py
.opencode/current_track3_ledger_20260606_logs/state_diff_ours_cold_vs_wr_step2000.md
.opencode/current_track3_ledger_20260606_logs/state_diff_ours_cold_vs_wr_step2400.md
```

### `track3_truepost3000_post-true-k10-lr2e4-active-poscos_103924`

Status: stopped early and pod terminated after artifacts were pulled.

Purpose:

- Test whether the clean true-post `K=10`, `inner_lr=2e-4` LocoProp-M active
  result from the short 1800 screen survives under a proper 3000-step suffix.
- This was launched from the same seed `3710` step `1600` checkpoint as the
  successful 1800 screen.

Settings:

```text
TRACK3_TRAIN_STEPS=3000
TRACK3_LOCOM_ACTIVE_WINDOWS=0:3000
TRACK3_LOCOM_END_STEP=3000
K=10
inner_lr=2e-4
true_post_grad=1
require_loss_decrease=1
min_cos_desc=0.0
sample_tokens=1024
```

Result:

```text
1600 3.48241
1625 3.49295
1650 3.49193
```

Comparison against the short 1800 screen:

```text
short 1800 screen:
1600 3.48241
1625 3.45139
1650 3.43530
1800 3.40452

proper 3000 schedule:
1600 3.48241
1625 3.49295
1650 3.49193
```

Artifacts pulled locally:

```text
.opencode/current_track3_ledger_20260606_logs/truepost3000_848672/
```

Read:

- The true-post local solve did not explode under the 3000 schedule.
- The logged corrections remained small and uncapped, but the base Muon step was
  much larger than in the short screen:

```text
3000-schedule step 1600 base_step ~= 1.293
3000-schedule step 1625 base_step ~= 1.270
logged corr_norm range at 1625 ~= 1e-3 to 2e-2
```

- So the exact local-solve correction that moved validation loss in the 1800
  screen was effectively diluted by the hot 3000-schedule Muon step.
- This rules out a naive "just extend the clean K10 true-post screen to 3000"
  path.
- The next version, if funded, needs a relative-scale rule such as correction
  normalized to a fixed fraction of the base Muon step, a colder/handoff window,
  or layer-restricted stronger true-post corrections. Repeating this exact
  `2e-4` all-layer active run under the hot 3000 schedule is ruled out.

## Closed Current Runs

Local text logs:

```text
.opencode/current_track3_ledger_20260606_logs/track3_red1600_coldp110_rewarm2125_2400_seed3710.log
.opencode/current_track3_ledger_20260606_logs/track3_red2400_h3075p110_nolocom_seed3710.log
.opencode/current_track3_ledger_20260606_logs/track3_red2400_matchcold_rewarm2500_2875_seed3710.log
.opencode/current_track3_ledger_20260606_logs/track3_red2000_true_rewarm050_2125_2400_seed3710.log
.opencode/current_track3_ledger_20260606_logs/track3_red1600_coldtail1800_h3075p110_seed3710.log
```

### `track3_red1600_coldp110_rewarm2125_2400_seed3710`

Status: closed by gate at step 2750.

Settings:

- resume: `track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt`
- LocoProp-M active window: `0:1800`
- LocoProp-M: all MLP layers, `K=4`, `inner_lr=0.1`, `cap=0.20`, `sample_tokens=1024`, `mbs=16`
- schedule: linear prefix, switch at 2000 to PR287 `h3075,p1.10`, blend at
  2125-2400 toward WR-like `h3105,p1.20`

Key losses:

```text
2000 3.41926
2025 3.40098
2125 3.37699
2400 3.34381
2500 3.33487
2625 3.32440
2750 3.31539
```

Interpretation:

- The cold-pulse / oldtail drop reproduced exactly: `3.37699 @2125`, matching
  oldtail `~3.37700`.
- It beat the WR/record reference through roughly 2500.
- It became slope-starved after 2500 and missed the 2750 gate by `0.00039`.
- This confirms the oldtail phenomenon is reproducible from the new red
  checkpoint, but it still does not solve the terminal descent problem.

Available remote checkpoints:

```text
step2000.pt
step2125.pt
step2250.pt
step2400.pt
step2500.pt
step2625.pt
step2750.pt
```

Remote checkpoint prefix:

```text
/root/.cache/track3_checkpoints/track3_red1600_coldp110_rewarm2125_2400_seed3710_
```

### `track3_red2400_h3075p110_nolocom_seed3710`

Status: closed / no longer running.

Settings:

- resume: current run `step2400.pt`
- LocoProp disabled
- schedule: PR287 `h3075,p1.10`

Key losses:

```text
2400 3.34377
2500 3.33484
2625 3.32436
2750 3.31536
2800 3.31205
2825 3.31069
```

Interpretation:

- This is effectively identical to the parent run after 2400.
- The speed is much faster because LocoProp is disabled, but the optimizer path
  is the already-known oldtail/no-LocoProp suffix.
- Treat as a redundancy confirmation, not a live lead.

Available remote checkpoints:

```text
step2500.pt
step2625.pt
step2750.pt
step2800.pt
```

Remote checkpoint prefix:

```text
/root/.cache/track3_checkpoints/track3_red2400_h3075p110_nolocom_seed3710_seed3710_
```

## Reference Curves Still Allowed

Use only these references unless a new plot/table is explicitly refreshed.

```text
WR source n=30 mean:
2500 3.34377
2625 3.32395
2750 3.30654
2875 3.29183
3000 3.28096

record h3075 mean:
2500 3.34077
2625 3.32131
2750 3.30442
2875 3.29056
3000 3.28106

lead stop1600 + PR287:
2500 3.34646
2625 3.32907
2750 3.31391
2800 3.30849
2875 3.30185
3000 3.29374

old cd500 -> softmerge p1.10:
2500 3.33600
2625 3.32538
2750 3.31640
2800 3.31303
2875 3.30907
3000 3.30405
```

## Current Conclusion

The recoverable edge is before or around 2500, not after 2800. The current
cold-pulse run produces the desired mid-run drop, but after 2500 it descends
too slowly relative to WR-like schedules. Oldtail/no-LocoProp suffixes from 2400
are now ruled out as a useful next experiment.

Important scheduler finding:

- The intended `2125->2400` rewarm in
  `track3_red1600_coldp110_rewarm2125_2400_seed3710` likely did **not** execute.
- In the generated scheduler, once `TRACK3_LR_AFTER_SWITCH=pr287` is active,
  `set_hparams()` returns from the PR287 branch before applying
  `TRACK3_LR_BLEND_TARGET`.
- This explains why the "rewarmed" main line and the explicit
  `h3075,p1.10` no-LocoProp suffix were numerically identical after 2400.
- Consequence: the right next probe is not another oldtail suffix, but a
  run that implements the cold pulse and true rewarm without the switch/blend
  short-circuit.

If launching one more probe from this pod, it should be genuinely different:

1. start from `step2400` or `step2500`;
2. keep WR-like late LR levels instead of repeating `h3075,p1.10`;
3. test a localized post-2500 slope fix, not another oldtail replay.

## 2400 Pathology Read

The failure is not that the LocoProp/cold-pulse state is bad at `2400`.
At `2400-2500` it is competitive or ahead. The failure is that the state is
slope-starved after the cold drop and reacts badly to restoring WR-like late LR.

Slope table, loss decrease per interval:

```text
run                    2000-2125  2125-2250  2250-2375  2375-2500  2500-2625  2625-2750
ours cold-pulse          0.04227     0.01694     0.01328     0.01190     0.01047     0.00901
WR source mean           0.02418     0.02408     0.02181     0.02135     0.01982     0.01741
record h3075 mean        0.02422     0.02392     0.02154     0.02111     0.01946     0.01689
```

Position relative to references:

```text
step  ours cold-pulse  vs WR source  vs record h3075
2500  3.33487          -0.00890      -0.00590
2625  3.32440          +0.00045      +0.00309
2750  3.31539          +0.00885      +0.01097
```

What this means:

- The `2000->2125` improvement is real and much steeper than WR. It looks like
  a cold-settling / validation-loss pull-down.
- The slope after that drops by roughly half while the WR/record references keep
  a nearly steady late descent.
- The explicit no-LocoProp h3075 suffix from `2400` is numerically identical to
  the parent line, so active LocoProp is not the post-2400 cause.
- The true rewarm probe reproduced the cold drop through `2125`, then stalled
  immediately (`2125->2250` only `0.00601`), so the cold-pulse state cannot
  absorb full WR-like LR right after the drop.
- The delayed rewarm probe matched the cold line through `2500`, then also lost
  slope by `2625`. Restoring WR LR later is not a simple fix.

Current best diagnosis:

```text
LocoProp/cold scheduling buys validation loss early, but it leaves the run in a
trajectory/optimizer-state regime with low usable late velocity. WR reaches
similar losses with a hotter state that still converts late LR into descent.
```

This is not settled as weight-state versus optimizer-state without a matched
WR/record checkpoint. Current local/remote artifacts include our cold-pulse
checkpoints, but no matched WR-source or record checkpoint at `2400/2500`.
The next true diagnostic is to recover or generate a WR/reference checkpoint at
the same seed/step and run `tools/analyze_track3_state_diff.py`.

## Matched WR State-Diff Result

We generated the missing WR-source seed `3710` checkpoints at `2000` and `2400`
and compared them with the cold-pulse checkpoints.

Important caveat: this compares simple Track 3 Muon + LocoProp/cold scheduling
against the current-record WR substrate. It is still useful because the user
question is exactly why our state fails relative to WR, but it is not a tiny
same-optimizer perturbation comparison.

At `2400`, ours has lower validation loss but very different parameter and
optimizer geometry:

```text
loss:
  ours cold-pulse: 3.34381
  WR source seed3710: 3.36072

model bucket norms:
  attention:   ours 525       WR 7655
  mlp_fc:      ours 657       WR 5765
  mlp_proj:    ours 337       WR 3669
  output_proj: ours 810       WR 5341
  embed:       ours 60804     WR 76511

optimizer norms:
  opt0 floating_norm: ours 2.93e6   WR 7.78e6
  opt1 floating_norm: ours 2.72e3   WR 1.35e7
  opt1 float tensors: ours 144      WR 324
```

Top tensor diffs are dominated by attention `v` and `proj` weights, with near
zero cosine against WR tensors. This is not "same state, wrong LR." The
LocoProp/cold path reaches a better validation number by `2400` while staying
in a much smaller-matrix/simple-optimizer parameterization; the WR path is
building a much hotter/larger-norm state that still converts late LR into
descent.

At `2000`, the same pattern is already present:

```text
loss:
  ours cold-pulse: 3.41926
  WR source seed3710: 3.43533

model bucket norms:
  attention:   ours 544       WR 6818
  mlp_fc:      ours 681       WR 5245
  mlp_proj:    ours 350       WR 3317
  output_proj: ours 805       WR 4808

optimizer norms:
  opt0 floating_norm: ours 9.83e6   WR 1.01e7
  opt1 floating_norm: ours 2.46e3   WR 2.98e7
```

Updated diagnosis:

```text
The LocoProp/cold trajectory is a validation-loss shortcut, not a delayed WR
trajectory. By the time it looks best, it has not built the WR optimizer/matrix
state that supports the final steep descent. When we rewarm it, we are not
restoring a missing scalar; we are asking a different state to tolerate WR
late-tail energy.
```

Refined substrate read:

```text
This is not "LocoProp state + wrong scalar LR" anymore. It is "simple Muon
plus a capped local MLP correction reached lower validation loss using a
different parameter/optimizer geometry than the WR stack."
```

The source-code delta supports that interpretation:

- Simple Track 3 base uses plain Muon with one momentum tensor per matrix,
  explicit matrix weight decay, and no NorMuon/Soft/Contra/SOAP state:
  `update = muon_update(p.grad, state["momentum"])`,
  `p.mul_(1 - lr * weight_decay)`, then `p.add_(update, -lr)`.
- The WR source uses:
  - Contra-Muon until normal by step `2000`;
  - Soft-Muon transition `2500 -> 3010`;
  - NorMuon-style second-moment state for every Muon matrix;
  - SOAP state on `mlp_plus_v` with `V_SOAP_BLEND=0.95`;
  - a `u/w` floor with `TARGET_UW=0.3825`;
  - no ordinary Muon weight-decay shrink in the Muon step, because the `u/w`
    target replaces that role.

This explains why the state diff is so large even at `2000`, before the visible
`2400` failure. The WR tail is not just hotter LR. It is a late optimizer
machine with persistent row/column/second-moment state and update-floor
behavior. The LocoProp/cold path is cheaper and lower-loss in the mid-run, but
it does not accumulate that machine.

The local LocoProp logs also look like a capped geometric perturbation, not a
clean global descent correction:

- At `1600`, some layer corrections are accepted with negative `cos_desc`, and
  several are cap-scaled.
- At `1750`, one logged correction has `corr_norm=2.908e+02` and is scaled by
  `6.672e-04`.

That does not make the correction useless: the `2000 -> 2125` drop is real.
But it suggests the benefit is a state/path effect, not an ordinary learning
rate boost and not a stable late Newton step.

Consequence:

- More oldtail from `2400` is ruled out.
- Late LocoProp re-on from `2400` was already neutral/worse.
- A simple LR rewarm is unlikely to work unless it also rebuilds the missing
  late optimizer geometry gradually.
- The next principled test would need either:
  - compose LocoProp prefix with the WR substrate from much earlier and verify it
    survives the `900-1600` phase, or
  - add a non-scalar late optimizer bridge that grows the Muon/WR matrix-state
    geometry without shocking validation.

Most discriminating next tests, if GPUs are resumed:

1. Same WR substrate from the start, but add LocoProp only in the proven
   prefix/cold window, with no accept/reject gate first. This tests whether the
   WR optimizer machinery can coexist with the LocoProp state effect if it is
   present before the late tail is built.
2. From the simple+LocoProp `2000` or `2125` checkpoint, switch to the WR Muon
   step while initializing the missing WR state from current gradients and
   ramping `u/w`/SOAP/Soft over hundreds of steps. This tests whether the
   terminal slope is recoverable by rebuilding optimizer geometry, not scalar
   LR.
3. A matched no-LocoProp simple-Muon cold-schedule control with the same
   oldtail pulse. This isolates how much of the `2000 -> 2125` drop is
   scheduler/settling versus LocoProp-created state.

## Recent Diagnostic Runs

### `track3_red1600_coldtail1800_h3075p110_seed3710`

Status: stopped manually at 1675 as redundant with the older end1800/h3075
family.

Settings:

- resume: `track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt`
- LocoProp-M active window: `0:1800`, same prefix window as the red run.
- schedule: linear until 1800, then PR287 `h3075,p1.10`; no rewarm.
- purpose: move the reproducible cold-pulse descent earlier. The prior runs
  showed rewarming after 2125 and after 2500 hurt, so this tests whether the
  climb is to get the cold descent earlier rather than repair it later.
- gates: `2000<=3.415`, `2125<=3.380`, `2400<=3.338`,
  `2500<=3.330`, `2625<=3.316`.
- local launch script:
  `.opencode/prime_scripts/from1600_coldtail1800_h3075p110.sh`

Remote log paths:

```text
/root/prime_track3_logs/track3_red1600_coldtail1800_h3075p110_seed3710.log
/root/prime_track3_logs/track3_red1600_coldtail1800_h3075p110_seed3710.status
/root/prime_track3_logs/track3_red1600_coldtail1800_h3075p110_seed3710.watcher.log
```

Live evidence:

```text
1600 3.48241
1625 3.48041
1650 3.47522
1675 3.47046
active LocoProp prefix step_avg around 4.6s/step
```

Read:

- Startup is consistent with the known red prefix.
- User correctly flagged that this is too close to prior work. The exact
  `switch=1800,p=1.10` tuple may not be identical, but the family was already
  explored:
  - old-tail replacement from the same checkpoint: LocoProp active through
    1800, switch at 2000 to PR287 `h3075,p1.10`;
  - `cd500-end1800-pr2873075` lanes;
  - h3075 `1800->2000` blend lanes with late LR bumps.
- Stopped before the slow LocoProp prefix spent more compute.

### `track3_red2400_matchcold_rewarm2500_2875_seed3710`

Status: stopped by watcher at 2625; not a candidate.

Settings:

- resume: `track3_red1600_coldp110_rewarm2125_2400_seed3710_step2400.pt`
- LocoProp-M after resume: disabled; checkpoint already contains prefix
  LocoProp-M/cold-pulse state.
- schedule: direct PR287 `h3105,p1.20`
- cold-match multiplier:
  `TRACK3_LR_BUMP_WINDOWS=2400:2400:2500:2875:0.50`
- interpretation of multiplier: h3105/p1.20 is roughly 2x h3075/p1.10 in
  this region, so `0.50` approximately matches the old cold LR through 2500;
  it then fades to full WR-like LR by 2875.
- purpose: preserve the cold-pulse descent through the observed useful window,
  then test whether gradual late rewarm fixes post-2500 slope starvation.
- gates: `2500<=3.3365`, `2625<=3.3235`, `2750<=3.3120`,
  `2875<=3.2960`.
- local launch script:
  `.opencode/prime_scripts/suffix_from2400_matchcold_rewarm2500_2875.sh`

Remote log paths:

```text
/root/prime_track3_logs/track3_red2400_matchcold_rewarm2500_2875_seed3710.log
/root/prime_track3_logs/track3_red2400_matchcold_rewarm2500_2875_seed3710.status
/root/prime_track3_logs/track3_red2400_matchcold_rewarm2500_2875_seed3710.watcher.log
```

Live evidence:

```text
2400 3.34377
2425 3.34167
2450 3.33899
2475 3.33728
2500 3.33492  gate passed <= 3.33650
2525 3.33330
2550 3.33171
2575 3.33018
2600 3.32922
2625 3.32780  gate failed > 3.32350
```

Read:

- Through 2500, this preserves the cold-line behavior instead of repeating the
  failed early rewarm.
- The delayed rewarm still hurts relative to the old h3075 cold suffix by
  `2625` (`3.32780` versus roughly `3.3244`).
- Rewarming h3105/p1.20 from the cold-pulse path is not currently fixing the
  post-2500 slope. The evidence now points toward moving the cold-pulse benefit
  earlier, not trying to rescue it later.

### `track3_red2000_true_rewarm050_2125_2400_seed3710`

Status: stopped manually at 2325; not a candidate.

Settings:

- resume: `track3_red1600_coldp110_rewarm2125_2400_seed3710_step2000.pt`
- LocoProp-M after resume: disabled; checkpoint already contains prefix
  LocoProp-M state.
- schedule: direct PR287 `h3105,p1.20`
- cold pulse: `TRACK3_LR_BUMP_WINDOWS=2000:2000:2125:2400:0.50`
- interpretation of multiplier: `0.50` through 2125, fades to `1.00` by
  2400, stays `1.00` afterward.
- purpose: test the intended cold-pulse-then-true-rewarm behavior that the
  prior switch/blend setup did not actually run.
- gates: `2400<=3.345`, `2500<=3.337`, `2625<=3.323`, `2750<=3.312`.
- local launch script:
  `.opencode/prime_scripts/suffix_from2000_true_rewarm050_2125_2400.sh`
- watcher note: initial script used `python` and failed because the pod only has
  `python3`; first replacement watcher attached to a transient PID and exited
  before seeing gates; watcher3 is attached to live train PID `8930` as PID
  `9381`. The local script was patched to use `python3`.

First live evidence:

```text
2000 3.41921
2025 3.40159
2050 3.39309
2075 3.38742
2100 3.38195
2125 3.37789
2150 3.37458
2175 3.37326
2200 3.37186
2225 3.37244
2250 3.37188
2275 3.37074
2300 3.37099
2325 3.37126
startup step_avg around 1330ms/step, much faster than active LocoProp path
```

Read:

- `2125=3.37789` is close to the old cold-pulse target (`~3.37699`), so the
  cold part is roughly reproduced.
- The rewarm after 2125 is too early/aggressive. The line stalls immediately
  after the cold drop instead of following the old cold descent through
  2200-2400.
- This implies the recoverable edge is in the cold-pulse phase itself, around
  `2000-2125` and possibly through `2400-2500`; full WR-like LR should not be
  restored that early.

Remote log paths:

```text
/root/prime_track3_logs/track3_red2000_true_rewarm050_2125_2400_seed3710.log
/root/prime_track3_logs/track3_red2000_true_rewarm050_2125_2400_seed3710.status
/root/prime_track3_logs/track3_red2000_true_rewarm050_2125_2400_seed3710.watcher.log
/root/prime_track3_logs/track3_red2000_true_rewarm050_2125_2400_seed3710.watcher2.log
/root/prime_track3_logs/track3_red2000_true_rewarm050_2125_2400_seed3710.watcher3.log
```

## Cleanup State

- Prime pod `6f66430b6a1a444bbe1f503b4f73caaf` was terminated after artifact
  pull.
- `prime pods list` showed zero active pods after termination.
- Large remote checkpoint files were not pulled locally; only logs, generated
  script, and state-diff Markdown artifacts were preserved locally.

## 2026-06-06 Sample Size Probe: `sample_tokens=2048`

Status: pod terminated externally before the 2125 gate; no active Prime pods
remain.

Pod:

```text
727008a819364d429bced3a1df8a3866
oc-main-track3-sample2048-h100-20260606-0655
datacrunch H100_80GB SXM5 spot, $1.14/hr
```

Settings:

- resume: `track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt`
- LocoProp-M active window: `0:1800`
- cap: `0.20`
- K: `4`
- changed knob: `TRACK3_LOCOM_SAMPLE_TOKENS=2048`
- schedule: linear/cd500 prefix, then h3075/p1.10 PR287-like cold tail from
  2000; same generator caveat as before where the recorded blend target is
  short-circuited by `TRACK3_LR_AFTER_SWITCH=pr287`.

Recovered live evidence:

```text
1600 3.48241
1625 3.48033
1650 3.47430
1675 3.47036
1700 3.46684
1725 3.46230
1750 3.46070
1775 3.45626
1800 3.44940
1825 3.44622
1850 3.44347
1875 3.43841
1900 3.43419
```

Reference from prior 1024-token run:

```text
1750 3.45909
1800 3.44970
2000 3.41926
2025 3.40098
2125 3.37699
2400 3.34381
2500 3.33487
2625 3.32440
2750 3.31539
```

Read:

- `2048` improved some local diagnostics but did not visibly improve the loss
  trajectory before the pod disappeared.
- At `1750`, sample-2048 was worse than prior 1024 by `0.00161`.
- At `1800`, sample-2048 was better than prior 1024 by only `0.00030`, i.e.
  noise-level.
- Internal LocoProp diagnostics were cleaner at step 1600, especially layer 2,
  but still not globally safe:
  - step 1600 layer 2: `lossK=8.172e-04`, `corr_norm=1.412e-01`,
    `cos_desc=0.148`; this removed the earlier large 1024-token outlier.
  - step 1625 layers 0/1/2 were locally sane, but layer 3 already had
    `lossK > loss0` and `cos_desc=-0.035`.
  - step 1750 layer 3 still blew up: `lossK=6.691e+00`,
    `corr_norm=1.540e+02`, `cos_desc=0.810`; the norm cap was still the
    effective safety mechanism.
- Conclusion: higher sample count reduces some estimator noise, but the core
  per-layer correction pathology remains and did not produce a clear external
  win before the pod was lost.

## Next: K-Ladder Diagnostics

Prepared follow-up:

```text
.opencode/track3_locom_k_ladder_20260606.md
tools/run_track3_locom_kdiag_probe.sh
tools/analyze_locom_kdiag.py
```

Purpose:

- Test `K=1,2,4,5,8,10` from the same captured sample.
- Separate current post-feature matching approximation from a true post-gradient
  solve and a preactivation solve.
- Decide whether more LocoProp iterations make the local solve saner, or merely
  amplify the capped perturbation.

Primary profiles:

```text
post-approx-k10-alpha0
pre-k10-alpha0
post-true-k10-alpha0
post-approx-k10-fixedtime-active
pre-k10-fixedtime-active
```

Read the plan file before launching more GPU time; it contains the promotion and
kill gates.

### K-Ladder Probe Run: Prime `bb96ad929daa4016955006a0f107b7c8`

Status: completed; artifacts pulled; pod terminated. Prime reported zero
active pods after termination.

Pod:

```text
bb96ad929daa4016955006a0f107b7c8
datacrunch H100_80GB SXM5 spot, $1.14/hr
```

Profiles:

```text
post-approx-k10-alpha0
pre-k10-alpha0
post-true-k10-alpha0
```

Purpose:

- Alpha-zero diagnostics only. These profiles do not intentionally change model
  weights through the LocoProp correction.
- Decide whether `K=5-10` improves local loss/cosine/norm behavior enough to
  justify an active K10 run.

Artifacts:

```text
.opencode/current_track3_ledger_20260606_logs/kdiag_bb96/
```

Computed reports:

```text
combined_summary_v2.md
layer_details_k10_v2.md
gate_report_v2.md
gate_report_v4.md
recommendation_v3.md
recommendation_relaxed_v3.md
recommendation_v4.md
```

Summary:

```text
post-approx current path:
  k1  median loss/loss0 9.133e-01, corr_norm 3.492e-02, bad_loss 4/12
  k4  median loss/loss0 2.132e+03, corr_norm 1.030e+00, bad_loss 10/12
  k10 median loss/loss0 3.128e+04, corr_norm 1.266e+02, bad_loss 8/12

preactivation:
  k1  median loss/loss0 2.274e+00, corr_norm 7.451e-02, bad_loss 11/12
  k10 median loss/loss0 6.590e+11, corr_norm 3.918e+04, bad_loss 11/12

true post-gradient:
  k1  median loss/loss0 9.989e-01, corr_norm 4.724e-05, bad_loss 0/12
  k10 median loss/loss0 9.890e-01, corr_norm 4.685e-04, bad_loss 0/12
```

Read:

- More iterations on the existing post-approx path are not viable. `K>1`
  mostly amplifies bad layers into a cap-rescued or nonfinite correction.
- The corrected analyzer parses literal `inf`/`nan`; post-approx `K=10`
  contains `4` nonfinite fields in the 12-layer screen.
- The automated max-K recommendation is:
  - post-approx: dead, nonfinite correction, stable layers `1/12`;
  - post-true: scale up true local step, stable layers `12/12`, median cap
    multiplier `18.84x`;
  - pre: dead, local loss worsens, stable layers `1/12`.
- Preactivation with the same step scale is worse, not better.
- True post-gradient is numerically sane, but the correction is tiny and
  directionally weak at the tested LR; it is a stable local-solve path, not yet
  an externally useful update.
- Do not launch active `K=10` from the current post-approx or preactivation
  path. If spending again, the only credible K-path is true-post-gradient with a
  deliberate LR scale sweep.

Next GPU ladder, if funded:

```text
alpha-zero:
  post-true-k10-lr1e4-alpha0
  post-true-k10-lr2e4-alpha0
  post-true-k10-lr3e4-alpha0
  post-true-k10-lr1e3-alpha0

active only if alpha-zero passes local gates:
  post-true-k10-lr2e4-active-poscos, stop at 1800 unless tied/better
```

Rationale:

- True post-gradient at `inner_lr=1e-5` is stable but too small. Layer-wise
  multipliers needed to hit the existing `0.20 * base_step` cap are roughly
  `4x-95x`, median `18.84x`. The analyzer's scale recommendation is
  `lr@corr_min=2.134e-5`, `lr@corr_max=2.134e-4`, and
  `lr@median_cap=1.884e-4`.
- `inner_lr=2e-4` is the calibrated next scale; `3e-4` is a useful
  just-above-cap stress check rather than the first active default.
- The active profile requires local loss decrease and nonnegative cosine so it
  tests "faithful local correction" rather than another capped random-ish
  perturbation.

### True-Post K10 Scale Ladder: Prime `0357862775354f9b89186256e498af27`

Status: alpha-zero scale ladder completed; artifacts pulled. The same pod is
currently running one active `2e-4` validation screen.

Artifact directory:

```text
.opencode/current_track3_ledger_20260606_logs/kdiag_scale_035786/
```

K=10 scale read:

```text
1e-4: median loss/loss0 9.044e-01, corr_norm 4.069e-03,
      bad_loss 0/12, nonfinite 0
2e-4: median loss/loss0 8.327e-01, corr_norm 6.757e-03,
      bad_loss 0/12, nonfinite 0
3e-4: median loss/loss0 8.297e-01, corr_norm 9.128e-03,
      bad_loss 1/12, nonfinite 0
1e-3: median loss/loss0 7.789e-01, corr_norm 2.842e-02,
      bad_loss 3/12, nonfinite 0
```

Read:

- The corrected true-post local optimizer is locally meaningful once scaled up.
  This is the first K10 shape here that lowers the local objective without
  turning into nonfinite/cap-only noise.
- `2e-4` is the cleanest active candidate. `3e-4` is already edge-case; `1e-3`
  is too hot for all-layer use even though its median local objective improves
  more.
- Active screen launched:

```text
track3_kdiag_post-true-k10-lr2e4-active-poscos_095921
```

Active result:

```text
1600: 3.48241
1625: 3.45139
1650: 3.43530
1675: 3.42536
1700: 3.41809
1725: 3.41258
1750: 3.40855
1775: 3.40573
1800: 3.40452
```

Comparison:

- The old weak `pr287soft2500` family was `3.46252 @1800`; this active
  true-post run is better by `0.05800`.
- The old `B1 softmerge1600` family was `3.42141 @1800`; this active true-post
  run is better by `0.01689`.
- At `1750`, this active true-post run is `3.40855`, while the old
  `B1 softmerge1600` family was `3.43345`, a `0.02490` improvement.

Read:

- This is the first evidence that a cleaned, scaled, true-post LocoProp-M local
  solve can translate to validation loss, not just improve alpha-zero
  diagnostics.
- Corrections were not cap-only: at `1600` and `1750`, logged `scale=1.000e+00`
  for the applied layers. The effect is coming from the actual local correction
  after positive-cos/loss-decrease gating.
- The run is still very slow (`~4595ms/step` on the Prime H100 after resume), so
  this is an algorithmic screen, not a speedrun candidate yet.
