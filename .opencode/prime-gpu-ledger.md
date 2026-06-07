- pod_id: 2a2e4b3be8f04d52976e522187845fc1
  name: oc-codex-track3-h100sxm-20260603-1348
  owner: current-agent
  purpose: Resume Track 3 LocoProp-M h3075/p1.10 ramp2350 + LocoProp re-on lane from seed3710 step1600 checkpoint
  gpu: 1x H100_80GB SXM5 datacrunch
  price_per_hour: 3.25
  created_at: 2026-06-03T13:48Z
  expected_stop: user requested keep alive while checkpoint-backed experiment loop remains active
  status: terminated after SSH key rejection; no workload started
  termination_policy: keep running for follow-up runs unless user asks to stop or workload fails before setup
- pod_id: d34ec95df4104fcd8176f9640bc4485f
  name: oc-codex-wr-locom-h100-20260603-1613
  owner: current-agent
  purpose: Probe current-record Track 3 WR stack plus state-decoupled c_fc LocoProp-M around 2000-2200
  gpu: 1x H100_80GB PCIe lambdalabs
  price_per_hour: 3.29
  created_at: 2026-06-03T16:13Z
  expected_stop: after narrow WR+LocoProp probe answers 2000-2200 composition question or setup fails
  status: terminated after Prime image installation error; no SSH endpoint; no workload started
  termination_policy: keep only while actively running probe; terminate on unrecoverable setup failure
- pod_id: 6d73b2cff0624ce2a3fff0eb0c60ccfd
  name: oc-codex-wr-locom-gh200-20260603-1623
  owner: current-agent
  purpose: Probe current-record Track 3 WR stack plus state-decoupled c_fc LocoProp-M around 2000-2200
  gpu: 1x GH200_96GB SXM5 lambdalabs
  price_per_hour: 2.29
  created_at: 2026-06-03T16:23Z
  expected_stop: after narrow WR+LocoProp probe answers 2000-2200 composition question or setup fails
  status: terminated after hook-based WR LocoProp probes OOMed before step 0; evidence archived at .opencode/prime_wr_locom_probe_20260603/wr_record_locom_probe_20260603.tgz
  termination_policy: keep only while actively running probe; terminate on unrecoverable setup failure
- pod_id: 6d0a7c2ed83d4b138c8b4e9dc8ac6d0d
  name: oc-codex-wrresume-b200-20260603-174534
  owner: current-agent
  purpose: Resume step1600 LocoProp-M prefix model into current-record WR Track 3 suffix, no LocoProp hooks
  gpu: 1x B200_180GB SXM6 datacrunch spot
  price_per_hour: 2.14
  created_at: 2026-06-03T17:45Z
  expected_stop: after WR-resume handoff probe reaches target, fails gates, or setup fails
  status: terminated after WR-state splice and WR+LocoProp co-train gates failed; logs archived at .opencode/prime_wr_locom_probe_20260603/
  termination_policy: keep only while actively running probe; terminate on unrecoverable setup failure
- pod_id: ab33db60b24a46b2a86625d8a0f235bf
  name: oc-codex-wr-locom-normbase-20260603-1937
  owner: current-agent
  purpose: B200 Prime WR+LocoProp normalized gated correction 250-step screen
  gpu: 1x B200_180GB SXM6 datacrunch spot
  price_per_hour: 2.14
  created_at: 2026-06-03T19:38:27Z
  expected_stop: after 250-step gated screen and artifact pull
  status: terminated after normalized LocoProp gates missed WR source; logs archived at .opencode/prime_wr_locom_probe_20260604/
  termination_policy: terminate immediately if setup fails or 250-step gate misses

- pod_id: e3ba5d547a504c658ac556065772a8c2
  name: oc-codex-recover2000-20260603-2112
  owner: current-agent
  purpose: Recover missing Track 3 LocoProp-M step-2000 checkpoint from step-1600 provenance
  gpu: GH200_96GB
  price_per_hour: $1.99
  created_at: 2026-06-03T21:12:43.592501+00:00
  expected_stop: after checkpoint recovery and verification
  status: create_failed_http400
  termination_policy: none; pod was not created

- pod_id: 3cb6b49ce0bb4d829cf00906f9ea7849
  name: oc-codex-recover2000-h100-20260603-2114
  owner: current-agent
  purpose: Build exact WR-source 2000/2400 checkpoints, then run exact-WR-state hookless aux-capture LocoProp suffix from step2000
  gpu: H100_80GB PCIe
  price_per_hour: $2.35
  created_at: 2026-06-03T21:14:15.939175+00:00
  expected_stop: after checkpoint build and queued suffix-from-2000 probe complete
  status: terminated_after_aux_suffix_probes_no_gate_bad_gated_neutral_normbase005_neutral_prime_active_pods_0
  termination_policy: terminate when recovery/probes complete unless user asks to keep

- pod_id: 47042bdc76984163a1e903a7475edd78
  name: oc-codex-wrnogate1600-h100spot-20260604-0654
  owner: current-agent
  purpose: Screen hookless aux-capture WR-stack LocoProp-M without accept/reject gates while checkpoint-builder continues on existing H100
  gpu: 1x H100_80GB SXM5 spot datacrunch
  price_per_hour: $1.14
  created_at: 2026-06-04T06:54Z
  expected_stop: after aux-capture 500-step screen and artifact pull, or immediately on setup failure/spot interruption
  status: terminated_after_aux_screen_step500_3.82600_1599ms_artifacts_pulled
  termination_policy: terminate when aux screen completes or fails unless user asks to keep
- pod_id: ca97c73f4ff24c45aeece6d3243ecbed
  name: oc-codex-locom-fused-20260604-1009
  owner: current-agent
  purpose: Prime 1x H100 SXM5 screen for hookless aux + batched LocoProp-M prep timing and convergence
  gpu: 1x H100_80GB SXM5 datacrunch
  price_per_hour: $3.25
  created_at: 2026-06-04T10:09Z
  expected_stop: keep active through fused timing screen and immediate follow-up runs unless setup fails
  status: terminated_after_normcap_queue_finished_pods_total_0
  termination_policy: terminated to avoid idle spend after user flagged budget risk
  notes:
    - exact no-Loco control from same step2000 checkpoint: 3.41121 @2125, 3.38789 @2250, 3.36546 @2375, 3.36065 @2400.
    - wr_s2000_locom_lr1e5_k10_gated_normbase020_2125_seed3710 finished 3.41234 @2125, worse than control.
    - wr_s2000_locom_lr1e5_k10_gated_normbase005_2125_seed3710 finished 3.41121 @2125, exact parity with control.
    - wr_s2000_locom_lr1e5_k10_gated_normbase010_mincos002_2125_seed3710 finished 3.41139 @2125, worse than control.

- pod_id: 8a54bb5c0f9f49fc92fc9903a2efec63
  name: oc-codex-locom-gh200-20260604-1838
  owner: current-agent
  purpose: Conservative GH200 Track 3 LocoProp-M prefix mechanism screen for normal/orthogonal/parallel/polar controls
  gpu: 1x GH200_96GB SXM5 lambdalabs
  price_per_hour: $2.29
  created_at: 2026-06-04T18:38Z
  expected_stop: after the smallest discriminating prefix ladder that fits wallet balance, or immediately on setup failure
  status: terminated_after_install_error_docker_container_start_failed_before_ssh
  termination_policy: keep only while actively syncing/running the prefix mechanism screen; terminate on setup failure or when budget gate is reached

- pod_id: 6e10ceefa3a94a6fbc5d90286000cefe
  name: oc-codex-locom-h100dc-20260604-1856
  owner: current-agent
  purpose: Conservative H100 Track 3 LocoProp-M prefix mechanism screen for normal/softpolar controls
  gpu: 1x H100_80GB SXM5 datacrunch
  price_per_hour: $3.25
  created_at: 2026-06-04T18:56Z
  expected_stop: after one short prefix gate and artifact pull, or immediately on setup failure
  status: terminated_after_softpolar_250_4.11736_orthogonal_500_3.82706_normal_500_3.82583_artifacts_pulled
  termination_policy: keep only while actively syncing/running the prefix mechanism screen; terminate on setup failure or budget gate
- pod_id: pending
  name: oc-main-locom-handoff-20260604-2013
  owner: current-agent
  purpose: Track 3 LocoProp-M WR handoff probe; Adam-only optimizer-state bridge from step 1600, gates at 1625/1750/2000+
  gpu: H100_80GB Datacrunch SXM5
  price_per_hour: $3.25
  created_at: 2026-06-04T14:43:14Z
  expected_stop: after 2125 gate or earlier if handoff flattens by 1750
  status: reconciled_inactive_after_prime_pods_list_total_0_on_20260604; handoff logs archived locally
  termination_policy: terminate after workload/failure unless user asks to keep alive

- pod_id: 17cca344b512457a8455fda1d992a939
  name: oc-main-locom-momscale-h100spot-20260604-2202
  owner: current-agent
  purpose: Conservative Track 3 LocoProp-M suffix test using recovered LocoProp step2000 model state plus WR optimizer-state momentum scaling
  gpu: 1x H100_80GB SXM5 datacrunch spot
  price_per_hour: about $1.1-$1.9 from Prime availability row ec854a
  created_at: 2026-06-04T16:32Z
  expected_stop: after one momentum-scale suffix probe reaches 2250/2400 or setup fails
  status: terminated_before_ip_or_ssh_no_workload_started
  termination_policy: keep only while actively syncing/running the suffix probe; terminate on setup failure or budget gate

- pod_id: 8dd85bfb06a442f6a35e46e97e2697e9
  name: oc-main-locom-momscale-h100stable-20260604-2212
  owner: current-agent
  purpose: Stable H100 fallback for Track 3 LocoProp-M model2000 plus WR optimizer-state momentum-scale suffix gate
  gpu: 1x H100_80GB SXM5 datacrunch
  price_per_hour: about $3.25 from Prime availability row a74def
  created_at: 2026-06-04T16:42Z
  expected_stop: after 2000 checkpoint regeneration plus one 2250/2400 suffix gate, or setup failure
  status: terminated_after_momscale050_and_fresh_state_suffix_shocked_upward_logs_pulled
  termination_policy: terminate on setup failure; if run is hot at 2400, continue only if budget allows

- pod_id: 3401f6568514409381d6060c8f754e7a
  name: oc-main-locom-gated-h100pcie-default-20260604-1815
  owner: current-agent
  purpose: Self-gated Track 3 LocoProp-M suffix from saved step-2400 checkpoint; hold 0.35 LR multiplier through 2450 then fade to full by 2750
  gpu: 1x H100_80GB PCIe massedcompute
  price_per_hour: $2.35
  created_at: 2026-06-04T18:15Z
  expected_stop: after automated 2500/2600/2750/2875 gates, target hit, setup failure, or user stop
  status: terminated_after_scheduler_only_failed_2600_and_late_locom_failed_2500_artifacts_pulled
  termination_policy: terminate immediately if setup fails or watcher reports gate failure; keep only while the gated run is actively progressing
  notes:
    - scheduler-only h3105,p1.20 hold2450/fade2750 from 2400 checkpoint reached 3.34023 @2500 then stalled to 3.33989 @2600; watcher failed 2600 gate 3.33852 and terminated.
    - late LocoProp 2400:2700 cap0.20 on the same checkpoint and schedule reached 3.34032 @2500; watcher failed stricter 2500 gate 3.34000 and terminated.
    - pod was terminated after artifacts were pulled; `prime pods list` returned empty.

- pod_id: 83bf9d642713451185bf20b9061e3953
  name: oc-main-wr-locom-overlay-20260604-2104
  owner: current-agent
  purpose: WR-stack LocoProp-M aux overlay gate through 2000 with automatic loss gates
  gpu: 1x H100_80GB SXM5 datacrunch
  price_per_hour: $3.25
  created_at: 2026-06-04T21:05:12Z
  expected_stop: after gate failure, step 2000 completion, setup failure, or artifact pull
  status: terminated_after_aux_overlay_screen_worse_by_1250_artifacts_pulled_prime_active_pods_0
  termination_policy: terminate after workload/failure unless user asks to keep alive
  notes:
    - intended run started successfully and used the H100; stopped manually after step 1250 because the mid-run signal was not positive enough to justify more spend.
    - live aux K5 inner_lr=1e-3 no-gate cap0.20 reached 3.65455 @1000 and 3.59871 @1250.
    - compared with checked-in WR source seed: +0.00213 worse @1000 and +0.00451 worse @1250.
    - compared with prior WR-source state-builder line: -0.00015 better @1000 but +0.00426 worse @1250.
    - artifacts pulled to `.opencode/prime_wr_locom_overlay_20260605/prime_track3_logs_83bf9d64_stopped1250.tgz`.

- pod_id: pending
  name: oc-main-track3-forensics-gh200-20260605-1946
  owner: current-agent
  purpose: Track 3 late-tail checkpoint forensics and narrow suffix probe; compare LocoProp/softmerge state against WR-like tail state around 2000-2800
  gpu: 1x GH200_96GB SXM5 vultr
  price_per_hour: $1.99
  created_at: 2026-06-05T19:46Z
  expected_stop: after checkpoint/state diagnostics plus at most the smallest discriminating suffix probe, or immediately on setup/create failure
  status: create_failed_payment_required_no_pod_started
  termination_policy: keep only while actively syncing/running diagnostics; terminate on setup failure or after artifacts are pulled

- pod_id: 6f66430b6a1a444bbe1f503b4f73caaf
  name: oc-main-track3-coldpulse-h100-20260605-2145
  owner: current-agent
  purpose: Track 3 LocoProp-M cold-pulse p1.10 then WR-tail rewarm probe from seed3710 step1600 checkpoint; now also building matched WR-source step2000/2400 checkpoints for state forensics
  gpu: H100 80GB SXM5 datacrunch $3.25
  price_per_hour: selected by availability id 90f5c3
  created_at: 2026-06-05T21:45:53Z
  expected_stop: after WR-source checkpoint builder completes and state-diff artifacts/logs are pulled
  status: terminated_after_wr_checkpoint_builder_and_state_diffs_pulled
  termination_policy: terminate after workload/failure unless user asks to keep alive
  notes:
    - cold-pulse run `track3_red1600_coldp110_rewarm2125_2400_seed3710` reproduced the oldtail drop at 2125 (`3.37699`) and reached `3.31539 @2750`; closed by gate.
    - redundant no-LocoProp suffix `track3_red2400_h3075p110_nolocom_seed3710` reached `3.31069 @2825`; it matched the parent suffix slope and should not be repeated.
    - remote checkpoints remain on pod under `/root/.cache/track3_checkpoints/`; see `.opencode/track3_current_ledger_20260606.md`.
    - 2026-06-06 10:58 IST: started `wr_source_seed3710_ckpt2000_2400_h100` to generate matched WR-source checkpoints for exact state comparison; verified `WR_SAVE_CHECKPOINT_STEPS=2000,2400` in live process env.
    - WR builder completed successfully: `3.43533 @2000`, `3.36072 @2400`; pulled log/status/generated script and state diffs to `.opencode/current_track3_ledger_20260606_logs/`.
    - State diff showed simple Muon+LocoProp/cold state has much smaller matrix norms than WR at 2400 (`attention 525 vs 7655`, `mlp_fc 657 vs 5765`, `mlp_proj 337 vs 3669`) and very different optimizer state (`opt1 2.72e3 over 144 float tensors vs WR 1.35e7 over 324 tensors).
    - 2026-06-06: terminated pod; `prime pods list` showed zero active pods afterward.

- pod_id: 727008a819364d429bced3a1df8a3866
  name: oc-main-track3-sample2048-h100-20260606-0655
  owner: current-agent
  purpose: Track 3 LocoProp-M cold-pulse sample_tokens=2048 p1.10 then WR-tail rewarm probe from seed3710 step1600 checkpoint
  gpu: H100 80GB (Spot) SXM5 datacrunch $1.14
  price_per_hour: selected by availability id 365368
  created_at: 2026-06-06T06:55:46Z
  expected_stop: after 2125/2400/2500 gates, setup failure, or artifact pull
  status: launched_by_launch_prime_track3_coldpulse_personal.sh_head_2724b44
  termination_policy: terminate after workload/failure unless user asks to keep alive
    - 2026-06-06: launcher SSH parsing stalled because Prime returned `root@ip -p 22`; continuing manually on `root@86.38.182.101 -p 22` for sample_tokens=2048 run.
    - 2026-06-06 07:59 UTC: Prime API reports pod status `TERMINATED`; `prime pods list` reports zero active pods. SSH timed out before artifact pull, so final remote logs/checkpoints are unavailable.
    - Last recovered live evidence: `3.44940 @1800`, `3.43419 @1900`; run was effectively tied with sample_tokens=1024 through 1800 and did not show a clear prefix improvement before pod loss.

- pod_id: 1a661182161b4f41a7be8511a9d86bdc
  name: oc-main-locom-tick-h100spot-20260607-0053
  owner: current-agent
  purpose: Guarded Track 3 LocoProp-M tick ladder from seed3710 step1600 checkpoint; prefix specificity then layer subset, optional suffix only if gates pass
  gpu: 1x H100_80GB SXM5 datacrunch spot
  price_per_hour: $1.14
  created_at: 2026-06-07T00:53Z
  expected_stop: completed and terminated after prefix-specificity decision plus artifact pull
  status: terminated_after_alpha_zero_control_matched_active_prime_active_pods_0
  termination_policy: terminate after workload/failure unless an immediate user-approved follow-up reuses the warmed pod
  notes:
    - Active K5 prefix reproduced the known healthy segment: `3.38478 @1900` to `3.37337 @2000`, drop `0.01141/100`.
    - Disabled-path no-Loco control produced `nan` validation through the compiled path, so it was stopped and replaced by same-harness `alpha=0.0` no-parameter-correction control.
    - Alpha-zero control matched active through the decision point: active `3.37337 @2000`, control `3.37338 @2000`; `1900->2000` drop/100 was `0.01141` active vs `0.01140` control.
    - Prefix decision: active LocoProp gain over no-correction was only `+0.00001 @2000`; read is schedule/checkpoint state, not applied LocoProp direction.
    - Pulled artifact archive to `.opencode/current_track3_ledger_20260607_logs/prime_track3_locom_tick_ladder_20260607T022549Z.tar.gz`.
    - Terminated pod with `--yes`; follow-up `prime pods list` showed zero active pods.

- pod_id: bb96ad929daa4016955006a0f107b7c8
  name: oc-main-track3-kdiag-h100-20260606-$(date -u +%H%M)
  owner: current-agent
  purpose: Track 3 LocoProp-M K-ladder diagnostics profiles=post-approx-k10-alpha0,pre-k10-alpha0,post-true-k10-alpha0
  gpu: H100 80GB (Spot) SXM5 datacrunch $1.14
  price_per_hour: selected by availability id ec854a
  created_at: 2026-06-06T08:20:45Z
  expected_stop: after K-ladder diagnostics, setup failure, or artifact pull
  status: terminated_after_kdiag_artifacts_pulled_prime_active_pods_0
  termination_policy: terminate after diagnostics/artifact pull unless user asks to keep alive
  notes:
    - completed alpha-zero K-ladder profiles `post-approx-k10-alpha0`, `pre-k10-alpha0`, and `post-true-k10-alpha0`.
    - artifacts pulled to `.opencode/current_track3_ledger_20260606_logs/kdiag_bb96/`.
    - current post-approx and preactivation K>1 paths blew up; true post-gradient was stable but tiny.
    - pod terminated with `--yes`; `prime pods list` returned zero active pods.

- pod_id: 29eb17f5760742a1a4bab682a23cb8ec
  name: oc-main-track3-suffixbridge-h100-20260607-0805
  owner: current-agent
  purpose: Track 3 suffix schedule bridge probes from seed3710 step2125 checkpoint, avoiding more 1600-2000 prefix replay
  gpu: 1x H100_80GB SXM5 datacrunch spot
  price_per_hour: $1.14
  created_at: 2026-06-07T08:05Z
  expected_stop: after two 2400 gates, setup failure, or artifact pull
  status: terminated_after_two_suffix_bridge_gates_failed_prime_active_pods_0
  termination_policy: terminate after workload/failure unless a lane clears the 2400 gate
  notes:
    - checkpoint source: `track3_noloco_ckpt2125_seed3710_seed3710_step2125.pt`.
    - `bump150_2250_2650` reached `3.34638 @2400`, failing the `3.33650` straight-line gate.
    - `blend_p15_2250_2650` reached `3.34595 @2400`, also failing the gate.
    - artifacts pulled to `.opencode/current_track3_ledger_20260607_logs/suffixbridge_29eb17/`.
    - terminated pod with `--yes`; follow-up `prime pods list` showed zero active pods.

- pod_id: 0357862775354f9b89186256e498af27
  name: oc-main-track3-kdiag-scale-20260606-0927
  owner: current-agent
  purpose: Track 3 LocoProp-M K-ladder diagnostics profiles=post-true-k10-lr1e4-alpha0,post-true-k10-lr2e4-alpha0,post-true-k10-lr3e4-alpha0,post-true-k10-lr1e3-alpha0
  gpu: H100 80GB (Spot) SXM5 datacrunch $1.14
  price_per_hour: selected by availability id ec854a
  created_at: 2026-06-06T09:28:22Z
  expected_stop: after K-ladder diagnostics, setup failure, or artifact pull
  status: terminated_after_true_post_scale_ladder_and_active_screen_artifacts_pulled_prime_active_pods_0
  termination_policy: terminate after diagnostics/artifact pull unless user asks to keep alive
  notes:
    - 2026-06-06: K-ladder completed and artifacts were pulled to `.opencode/current_track3_ledger_20260606_logs/kdiag_scale_035786/`.
    - 2026-06-06: launched active screen `track3_kdiag_post-true-k10-lr2e4-active-poscos_095921` from the same step1600 checkpoint, PID 6230, to test whether the clean `2e-4` local diagnostic translates to validation loss by step 1800.
    - Active screen completed: `3.48241 @1600`, `3.45139 @1625`, `3.40855 @1750`, `3.40452 @1800`; artifacts pulled to the same directory.
    - Pod terminated successfully after mapping `PRIME_KEY` to `PRIME_API_KEY`; `prime pods list` reported zero active pods.

- pod_id: 8486723dca7749a0a7603d4eca10db7b
  name: oc-main-track3-truepost3000-h100-20260606-1026
  owner: current-agent
  purpose: Extend true-post K10 LocoProp-M `2e-4` active-poscos result from seed3710 step1600 checkpoint to a proper 3000-step suffix
  gpu: H100 80GB (Spot) SXM5 datacrunch $1.14
  price_per_hour: selected by availability id ec854a
  created_at: 2026-06-06T10:26Z
  expected_stop: after 3000-step suffix completes, clear gate failure, setup failure, or artifact pull
  status: terminated_after_3000_schedule_failed_early_gate_artifacts_pulled_prime_active_pods_0
  termination_policy: terminate after workload/failure unless user asks to keep alive
  notes:
    - Prime preflight before launch: wallet `$17.882`, zero active pods, cheapest adequate H100 was spot SXM5 `$1.14/hr`.
    - Launcher created the pod and copied the step1600 checkpoint, but failed before starting training due to local shell expansion in the remote heredoc. Remote checkpoint provenance is intact.
    - Manual remote run started on `root@86.38.238.161 -p 22`, PID 2947, from commit `8f1dbd2`.
    - Run env: `post-true-k10-lr2e4-active-poscos`, `TRACK3_TRAIN_STEPS=3000`, `TRACK3_LOCOM_ACTIVE_WINDOWS=0:3000`, `TRACK3_LOCOM_END_STEP=3000`, `SCREEN_VAL_EVERY=25`.
    - Early result under the proper 3000 schedule: `3.48241 @1600`, `3.49295 @1625`, `3.49193 @1650`; stopped because it was far worse than the short 1800 screen (`3.45139 @1625`, `3.43530 @1650`).
    - Diagnostic read: correction norms remained small and uncapped, but the 3000 schedule's `base_step` was about `1.29` at 1600, so the same LocoProp correction was too small relative to the hot Muon step.
    - Artifacts pulled to `.opencode/current_track3_ledger_20260606_logs/truepost3000_848672/`; pod terminated successfully and `prime pods list` returned zero active pods.

- pod_id: c57f71bf40964f2ab874120ddd3140cd
  name: oc-main-track3-normtarget-sxm-20260606-1106
  owner: current-agent
  purpose: Track 3 LocoProp-M relative-scale diagnostics on SXM H100, starting with norm002 and reusing the warm pod for norm005 if needed
  gpu: H100 80GB SXM5 datacrunch $3.25
  price_per_hour: selected by availability id 90f5c3
  created_at: 2026-06-06T11:06:38Z
  expected_stop: after norm-target early gates answer the scale question, setup failure, or artifact pull
  status: terminated_after_locom_lr_handoff_logs_pulled_prime_active_pods_0
  termination_policy: keep warm for the immediate norm005 follow-up when norm002 misses; terminate after the queued ladder/artifact pull unless another concrete follow-up is active
  notes:
    - 2026-06-06: user corrected lifecycle policy; keep this owned SXM pod warm between adjacent runs when repo/cache/checkpoint/compile reuse saves time.
    - norm002 (`TRACK3_LOCOM_NORM_TARGET=0.02`) launched as `track3_kdiag_post-true-k10-lr2e4-active-poscos-norm002_111634`.
    - norm002 missed the early gate: `3.49340 @1625`, matching the failed raw 3000 schedule and far behind the short 1800 screen.
    - stopped only the training process, not the pod, and launched norm005 (`TRACK3_LOCOM_NORM_TARGET=0.05`) as `track3_kdiag_post-true-k10-lr2e4-active-poscos-norm005_112249`.
    - norm005 also missed the early gate: `3.49298 @1625`; correction/base normalization alone did not recover the short-screen hit under the hot 3000 schedule.
    - launched same-primitive short-schedule control on the warm pod as `track3_kdiag_post-true-k10-lr2e4-active-poscos_112755`; it reproduced the hit at `3.45139 @1625`.
    - short-schedule control completed: `3.45139 @1625`, `3.43530 @1650`, `3.40855 @1750`, `3.40573 @1775`, `3.40453 @1800`.
    - launched cold-power 3000 suffix `track3_kdiag_post-true-k10-lr2e4-active-poscos-coldp2_115017` with `TRACK3_COOLDOWN_FRAC=1.0`, `TRACK3_LR_SCHEDULE=power`, `TRACK3_LR_POWER=2.0`, no norm target, to reduce the base update itself while keeping nonzero LR past 1800.
    - coldp2 first gate matched the short schedule while staying in a 3000-step run: `3.45135 @1625`; logged base step was `~0.42` at 1600/1625 versus hot 3000 `~1.29` and short control `~0.31/0.27`.
    - coldp2 remained on the good curve through `1750`: `3.43562 @1650`, `3.42613 @1675`, `3.41883 @1700`, `3.41289 @1725`, `3.40792 @1750`.
    - coldp2 beat the short control after the old endpoint: `3.40359 @1775`, `3.39872 @1800`, then kept descending to `3.39518 @1825`, `3.39175 @1850`, `3.38819 @1875`.
    - by `2000`, coldp2 slope had tapered: `3.38477 @1900`, `3.38173 @1925`, `3.37909 @1950`, `3.37605 @1975`, `3.37337 @2000`, `3.37101 @2025`, `3.36869 @2050`, `3.36658 @2075`. Keep running, but next obvious follow-up is cold-prefix plus smoother/warmer tail, not larger LocoProp correction.
    - continued taper: `3.36425 @2100`, `3.36217 @2125`, `3.36005 @2150`; still descending but with little margin for a 3.28 by 3000 path.
    - coldp2 remained active through `2400` with sample_tokens=1024 and no LocoProp stop: `3.35803 @2175`, `3.35629 @2200`, `3.35478 @2225`, `3.35306 @2250`, `3.35149 @2275`, `3.34996 @2300`, `3.34865 @2325`, `3.34747 @2350`, `3.34629 @2375`, `3.34514 @2400`.
    - `locoprop_m_prepare step=2400` still shows local loss decrease and positive cosine for 3/4 logged layers (`tokens=1024`), but `base_step` is down to `~7.76e-02`; the observed problem is tail slope/LR starvation, not that LocoProp shut off at 1800.
    - stopped coldp2 after `3.34403 @2425` because the tail slope was still starving.
    - launched replacement `track3_kdiag_post-true-k10-lr2e4-active-poscos-coldp2-prblend1800-2200_131444` on the same warm pod: same step1600 checkpoint, same true-post K10 `inner_lr=2e-4`, `sample_tokens=1024`, LocoProp active `0:3000`, cold `power=2.0` schedule until blend start, then smooth blend `1800->2200` to PR287 `h3105,p1.20`.
    - stopped `coldp2-prblend1800-2200` after it overheated the suffix: it matched prefix (`3.39871 @1800`) but degraded after the warm blend (`3.38964 @1900`, `3.39010 @1925`, `3.39646 @2000`), with logged `base_step` rising to `~5.20e-01 @2000`.
    - launched tempered rewarm `track3_kdiag_post-true-k10-lr2e4-active-poscos-coldp2-switch2000-pr287035fade2600_135759`: cold `power=2.0` until step 2000, then PR287 `h3105,p1.20` with LR multiplier `0.35` held `2000-2200` and faded to `1.0` by 2600; same LocoProp primitive remains active `0:3000`.
    - tempered rewarm first gate matched coldp2 prefix as intended: `3.45136 @1625`; this isolates the future LR handoff.
    - stopped tempered rewarm after it spiked immediately after switch: it matched coldp2 through `3.37604 @1975`, hit `3.37335 @2000`, then worsened to `3.37638 @2025`. Logged `base_step` at switch was only `~2.89e-01`, so even a modest rewarm from the cold path perturbs the state.
    - launched direct switch-out diagnostic `track3_kdiag_post-true-k10-lr2e4-active-poscos-coldp2-locomoff1800_144346`: identical cold `power=2.0` 3000-step schedule and same LocoProp primitive, but LocoProp active only `0:1800`. This isolates whether continuing LocoProp after the good prefix causes the taper, without any LR rewarm.
    - stopped `coldp2-locomoff1800` after it matched coldp2 through `2125`: `3.38477 @1900`, `3.37338 @2000`, `3.36218 @2125`; turning LocoProp off after 1800 did not give a loss bump, but reduced step time from about `4600ms` to `4521ms`.
    - launched zero-jump suffix `track3_kdiag_post-true-k10-lr2e4-coldp2-off1800-switch2000-pr287026hold2400fade3000_153844`: LocoProp active `0:1800`, cold `power=2.0` schedule until 2000, then PR287 `h3105,p1.20` with multiplier `0.26` held `2000-2400` and faded to `1.0` by 3000. This matches cold LR at the switch (`~0.995x` at 2000) and warms slowly.
    - zero-jump suffix avoided the validation spike but did not catch coldp2: `3.37336 @2000`, `3.37244 @2025`, `3.36460 @2125`, `3.36038 @2175`; this is worse than coldp2 (`3.37337 @2000`, `3.37101 @2025`, `3.36217 @2125`, `3.35803 @2175`).
    - pulled focused SXM logs to `.opencode/current_track3_ledger_20260606_logs/normtarget_sxm_c57f/`.
    - terminated pod successfully after parsing `env.local` key-values safely; Prime `pods list` returned zero active pods.

- pod_id: 461e0ceb6a3743f98ebd2b621fba42ca
  name: oc-main-locom-kdepth-h100sxm-20260606-1837
  owner: current-agent
  purpose: Track 3 true-post LocoProp-M K-depth 1600->1800 screen: K10/K8/K5/K5-lr3e4
  gpu: H100 80GB SXM5 datacrunch $3.25
  price_per_hour: selected by availability id a74def
  created_at: 2026-06-06T18:37:54Z
  expected_stop: after the normalized LocoProp from-2000 probe answers 2125/2250 gates, or earlier if it clearly misses
  status: terminated_after_from2000_floor_and_norm002_suffix_missed_pods_total_0
  termination_policy: terminated after active suffix probes missed and artifacts were pulled
  notes:
    - K-depth screen completed. K10/K8/K5 at lr2e-4 were externally tied through 1800 (`~3.39870`), so K5 is the cheapest adequate prefix in this window.
    - Stopped K5-lr3e-4 early to prioritize controls.
    - Random same-shape/cap continuation from K5 1800 matched active continuation to 2125 (`3.36216`).
    - No-correction continuation from the same checkpoint also matched (`3.36213 @2125`), proving the post-1800 descent is not continued-LocoProp-specific.
    - Saved exact no-correction checkpoint at remote `/root/.cache/track3_checkpoints/track3_noloco_ckpt2125_seed3710_seed3710_step2125.pt`.
    - Saved cold no-correction 2400 checkpoint at remote `/root/.cache/track3_checkpoints/track3_fast_noloco_from2125_seed3710_seed3710_step2400.pt`.
    - Pulled text logs to `.opencode/current_track3_ledger_20260606_logs/kdepth_461e/`.
    - Checkpoint blobs are being pulled to `/Users/progyan/speedrun/tmp/prime_ckpt_transfer/`; terminate pod after transfer completes.
    - Hot PR287 no-correction suffix from 2125 spiked (`3.40302 @2150`, `3.41107 @2200`) and was stopped.
    - Power2 no-correction with `LR_MIN_ETA=0.08` was worse than cold by 2200/2250 and was stopped.
    - Replayed no-correction from 1800 and saved `/root/.cache/track3_checkpoints/track3_noloco_slope_seed3710_seed3710_step2000.pt`, `...step2075.pt`, and `...step2100.pt`.
    - Verified replay slope: `3.38474 @1900`, `3.37333 @2000`, `3.36655 @2075`, `3.36420 @2100`.
    - Launched fast no-LocoProp branch `track3_from2000_floor009_to2400_213135` from the 2000 checkpoint with power2 h3000 and `LR_MIN_ETA=0.09`; saves 2250/2400 checkpoints.
    - `floor009` failed the 2250 gate: `3.35514 @2250`, worse than cold `3.35305 @2250`; stopped after checkpoint save.
    - Launched `track3_from2000_norm002_locom_to2250_213950`: true-post K10 `inner_lr=2e-4`, positive-cos/loss-decrease, `NORM_TARGET=0.02`, active `2000:2250` from the same step-2000 checkpoint.
    - `norm002` first gate: `3.37101 @2025`, neutral/slightly worse than cold `3.37098`; continue only to `2125` unless it turns positive.
    - `norm002` stopped at `3.36217 @2125`, still slightly worse than no-Loco cold `3.36215`; local K10 loss/loss0 improved to median `~0.86-0.89`, but median cosine stayed `~0.004-0.009`.
    - Pulled suffix logs to `.opencode/current_track3_ledger_20260606_logs/kdepth_461e/suffix_from2000/` and generated local `.kdiag.md` / `.apply_scale.md` for the normalized run.
    - Terminated pod successfully with `PRIME_API_KEY=$PRIME_KEY`; follow-up `prime pods list` showed zero active pods.
    - Caveat: remote `1800/2000/2075/2100` checkpoint blobs were not pulled before termination. Local preserved checkpoint blobs from this pod are the later `2125` and `2400` files in `/Users/progyan/speedrun/tmp/prime_ckpt_transfer/`; the exact earlier branch blobs would need to be regenerated from the local step-1600 provenance.

- pod_id: 11341a1371174b539e4a7b7010574d14
  name: oc-main-track3-2000gate-gh200-20260607-0305
  owner: current-agent
  purpose: Track 3 post-2000 LocoProp suffix gate to 2125 from seed3710 step1600 checkpoint
  gpu: GH200 96GB SXM5 lambdalabs $2.29
  price_per_hour: selected by availability id 0f1fb9
  created_at: 2026-06-07T03:05:51Z
  expected_stop: after 2125 gate, setup failure, or artifact pull
  status: terminated_after_arm64_pytorch_wheel_mismatch_prime_active_pods_0
  termination_policy: terminate after gate/artifact pull unless a concrete follow-up is queued
  notes:
    - Provider returned an ARM64 GH200 image; setup reached pip install but `torch==2.7.1` was unavailable for the required CUDA wheel/index on ARM64.
    - Terminated owned pod manually with `prime --plain pods terminate --yes`; follow-up `prime pods list` reported zero active pods.

- pod_id: 9b33955ad0cf4275813a590ff6ebd7c8
  name: oc-main-track3-2000gate-gh200-20260607-0316
  owner: current-agent
  purpose: Track 3 post-2000 LocoProp suffix gate to 2125 from seed3710 step1600 checkpoint
  gpu: H100 80GB (Spot) SXM5 datacrunch $1.14
  price_per_hour: selected by availability id ec854a
  created_at: 2026-06-07T03:17:02Z
  expected_stop: after full 3000 suffix ladder completes, setup failure, or artifact pull
  status: terminated_after_schedule_suffix_probes_prime_active_pods_0
  termination_policy: keep warm until the queued full 3000 suffix ladder completes, then pull artifacts and terminate unless another concrete follow-up is queued
  notes:
    - Launcher synced commit `0ba916e`, copied local step1600 checkpoint to `/home/ubuntu/.cache/track3_checkpoints/`, and started `/home/ubuntu/prime_track3_2000_suffix_gate_logs/run_2000_suffix_gate.sh`.
    - User requested letting the run go through rather than stopping at the short gate. Queued `/home/ubuntu/prime_track3_2000_suffix_gate_logs/run_full_after_gate.sh`, which waits for gate `DONE` and then runs the same suffix ladder to step 3000 in `/home/ubuntu/prime_track3_2000_suffix_full_logs/`.
    - Current first lane is recreating/saving the step2000 checkpoint from the seed3710 step1600 checkpoint; early startup validated checkpoint load and training resumed at `3.48241 @1600`.
    - Step2000 checkpoint was created at `/home/ubuntu/.cache/track3_checkpoints/track3_locom_good2000_seed3710_step2000.pt`; recreated prefix was `3.37335 @2000`.
    - Short post-2000 gate completed training but failed only in manifest validation because the checker expected LocoM headers in all lane logs, so `DONE` was not written and the queued watcher waited forever.
    - Gate result at 2125: plain no-LocoProp control was best (`3.36216`); `floor111` was `3.36425`; `floor111_norm002`, `floor111_random002`, `floor111_norm005`, and `floor111_random005` were all around `3.36429-3.36430`; `ramp111` was `3.36502`.
    - Stopped stale watcher/3000 continuation and launched no-LocoProp control from the same step2000 checkpoint to 3300 in `/home/ubuntu/prime_track3_2000_nolocom3300_logs/`, but the wrapper still hardcoded `TRACK3_LR_SCHEDULE_STEPS=3000`.
    - The first 3300 extension therefore plateaued under a zero-LR tail and then crashed at step 3000 on the generated schedule assertion. It saved checkpoints at 2125/2400/2600/2800/3000 and reached `3.33456 @3000`.
    - Patched `tools/run_track3_locom_2000_suffix_probe.sh` so `TRACK3_LR_SCHEDULE_STEPS` is configurable, copied it remote, and launched the real 3300-schedule no-LocoProp control in `/home/ubuntu/prime_track3_2000_nolocom3300_real_logs/`.
    - Real 3300-schedule run is active and initially hotter/worse than the 3000-schedule continuation: `3.37335 @2000`, `3.37430 @2025`, `3.37307 @2050`, `3.37137 @2075`, `3.36882 @2100`, `3.36667 @2125`, `3.35982 @2200`, `3.35808 @2225`, `3.35198 @2300`; step time after warmup is about `1265ms`.
    - Real 3300-schedule run reached the first saved suffix checkpoint: `3.35037 @2325`, `3.34877 @2350`, `3.34715 @2375`, `3.34542 @2400`, checkpoint `/home/ubuntu/.cache/track3_checkpoints/track3_locom_2000_control_seed3710_seed3710_step2400.pt`. This did not create a breakout; it mostly confirmed that simply stretching the no-LocoProp schedule is not the missing late-tail fix.
    - Stopped the real 3300-schedule no-LocoProp run after `3.33472 @2600`; required straight-line from the `3.37335 @2000` state was about `3.31734 @2600`, so the suffix was slope-starved. Final local logs pulled to `.opencode/current_track3_ledger_20260607_logs/prime_2000gate_9b33955/`.
    - Reused the warm H100 for the aligned mechanism probe: `/home/ubuntu/run_prefix_scale_1800.sh`, PID `12791`, log root `/home/ubuntu/prime_track3_prefix_scale_1800_logs`. This tests K5 true-post c_fc normalized to `2%` and `5%` of base step against alpha-zero/natural/random controls through step `1800`.
    - First prefix-scale launch failed immediately because it did not activate `/home/ubuntu/venv`, so `torchrun` was unavailable. Relaunched as `/home/ubuntu/run_prefix_scale_1800_v2.sh`, PID `13009`; alpha-zero/noloco lane completed and matched the known curve: `3.45136 @1625`, `3.43562 @1650`, `3.42614 @1675`, `3.41884 @1700`, `3.41288 @1725`, `3.40795 @1750`, `3.40361 @1775`, `3.39874 @1800`.
    - Pruned the broad six-lane prefix-scale sequence after alpha-zero and killed the redundant natural-K5 lane. Launched focused decisive pair `/home/ubuntu/run_prefix_scale_pair1800.sh`, PID `14400`, log root `/home/ubuntu/prime_track3_prefix_scale_pair1800_logs`: `norm002_k5` vs same-scale `random_norm002`, both K5 true-post through step `1800`.
    - 2026-06-07T07:08:04Z: user requested stopping 1600-2000 probes and focusing on a schedule that carries the existing `3.36/3.32` region to `3.28`. Killed the prefix pair and launched schedule-only no-LocoProp suffix screen from `/home/ubuntu/.cache/track3_checkpoints/track3_locom_2000_control_seed3710_seed3710_step2125.pt` to step `2400` in `/home/ubuntu/prime_track3_suffix_schedule_probe_2125_logs/`: lanes `floor004,floor006,floor008,h3200p2`. Straight-line gate from `3.36216 @2125` is `3.33634 @2400`; terminate/redirect if lanes remain near the known `~3.345` cold-control band.
    - 2026-06-07T07:26:18Z: stopped the 2125 floor-family probe before `h3200p2` because `floor004` matched cold (`3.34512 @2400`), `floor006` worsened (`3.34630 @2400`), and `floor008` was already worse by `2225` (`3.35557`). Launched a later no-LocoProp terminal screen from `/home/ubuntu/.cache/track3_checkpoints/track3_locom_2000_control_seed3710_seed3710_step2600.pt` to `2800` in `/home/ubuntu/prime_track3_suffix_schedule_probe_2600_logs/`: lanes `h3300p2,pr287_h3075p110,pr287_h3105p120`. Straight-line gate from `3.33472 @2600` is `3.30736 @2800`.
    - 2026-06-07: stopped the 2600 terminal screen after `h3300p2` remained far too slow (`3.32745 @2800`) and direct `pr287_h3075p110` spiked (`3.33727 @2625`, `3.33722 @2650`). Did not run `pr287_h3105p120` because it is the stronger/hotter variant of the failed direct PR287 suffix. Pulled logs to `.opencode/current_track3_ledger_20260607_logs/prime_2000gate_9b33955/prime_track3_suffix_schedule_probe_{2125,2600}_logs/`. Terminated pod; Prime `pods list` returned zero active pods.

- pod_id: 29eb17f5760742a1a4bab682a23cb8ec
  name: oc-main-track3-suffixbridge-h100-20260607-0805
  owner: current-agent
  purpose: Track 3 suffix-only bridge screen from step2125 checkpoint; lanes=bump150_2250_2650,blend_p15_2250_2650
  gpu: H100 80GB (Spot) SXM5 datacrunch $1.14
  price_per_hour: selected by availability id 365368
  created_at: 2026-06-07T08:05:59Z
  expected_stop: after 2400 gate artifacts are pulled, setup failure, or spot interruption
  status: terminated_after_gate_failed_logs_pulled_prime_active_pods_0
  termination_policy: terminate after gated suffix screen unless a lane clears the gate and user approves continuation
  notes:
    - `bump150_2250_2650` reached `3.34638 @2400`; `blend_p15_2250_2650` reached `3.34595 @2400`; both failed gate `<=3.33650`.
    - Logs pulled to `.opencode/current_track3_ledger_20260607_logs/suffixbridge_29eb17/`.

- pod_id: 432c024310cb4fa79c1ea28036f50d1b
  name: oc-main-track3-late-linear-h100-20260607-0906
  owner: current-agent
  purpose: Track 3 late linear 3000-horizon suffix screen from step2400 checkpoint; lanes=linear3000_noloco
  gpu: H100 80GB (Spot) SXM5 datacrunch $1.14
  price_per_hour: selected by availability id 365368
  created_at: 2026-06-07T09:06:53Z
  expected_stop: after 2500/2600 gate artifacts are pulled, setup failure, or spot interruption
  status: terminated_after_linear3000_noloco_shocked_state_logs_pulled_prime_active_pods_0
  termination_policy: terminate after gated suffix screen unless the lane clears the gate and user approves continuation
  notes:
    - Resumed exact step2400 checkpoint at `3.34500`; no LocoProp active.
    - True 3000-horizon linear tail worsened immediately: `3.36474 @2425`, `3.36852 @2450`, `3.36917 @2475`, `3.36791 @2500`, missing gate `<=3.33450`.
    - Logs pulled to `.opencode/current_track3_ledger_20260607_logs/late_linear_432c02/`.
- pod_id: a7eb7c5aa9af4f01987d4fdde11bc226
  name: oc-main-track3-floor-20260607-1036
  owner: current-agent
  purpose: Track 3 suffix floor landing probe from 2400 checkpoint
  gpu: H100_80GB SXM5 spot/datacrunch availability 365368
  price_per_hour: 1.138 USD
  created_at: 2026-06-07T10:36:08Z
  expected_stop: after floor probe gates at 2600/2800/3000 or earlier failure
  status: terminated_transfer_too_slow
  termination_policy: terminate if setup fails or after queued suffix probes finish

- pod_id: pending
  name: oc-main-track3-floor-gh200-20260607-1050
  owner: current-agent
  purpose: Track 3 suffix floor landing probe from 2400 checkpoint after FI H100 transfer bottleneck
  gpu: GH200_96GB SXM5 vultr availability 5ba376
  price_per_hour: 1.99 USD
  created_at: 2026-06-07T10:50:11Z
  expected_stop: after floor probe gates at 2600/2800/3000 or earlier failure
  status: create_failed_provider_400
  termination_policy: none_created

- pod_id: d9f1d50e2cc844dd83c28ff92185c653
  name: oc-main-track3-floor-h100us-20260607-1050
  owner: current-agent
  purpose: Track 3 suffix floor landing probe from 2400 checkpoint after GH200 create failure
  gpu: H100_80GB PCIe US/massedcompute availability 6bd7c8
  price_per_hour: 2.35 USD
  created_at: 2026-06-07T10:50:53Z
  expected_stop: after floor probe gates at 2600/2800/3000 or earlier failure
  status: terminated_after_checkpoint_suffix_floor_failed_gate_prime_active_pods_0
  termination_policy: terminate if setup fails or after queued suffix probes finish
  notes:
    - Checkpoint upload to the earlier FI H100 SXM pod and this US pod was unusably slow, so this lane is replaying from step 0 despite the suffix-only intent.
    - Active command: `/home/ubuntu/prime_track3_floor_end2end_logs/run_floor_e2e.sh`; log `/home/ubuntu/prime_track3_floor_end2end_logs/floor006_r2600_e2e.log`.
    - Run is `floor006_r2600`: LocoProp active `0:1800`, power schedule horizon `3000`, `TRACK3_LR_MIN_ETA_WINDOWS=2400:2600:3000:3000:0.06`.
    - 2026-06-07T11:16Z: alive on `NVIDIA H100 PCIe`, `100%` utilization, `32923 MiB`; latest visible screen `4.49356 @150/3000`, active-prefix step time about `5.4s`.
    - 2026-06-07T11:30Z: stopped end-to-end replay after user correction. GPU was freed (`0 MiB`).
    - Copied local checkpoint `/Users/progyan/speedrun/tmp/prime_ckpt_transfer/track3_fast_noloco_from2125_seed3710_seed3710_step2400.pt` to remote `/home/ubuntu/.cache/track3_checkpoints/track3_locom_2000_control_seed3710_seed3710_step2400.pt`; SHA256 verified as `a02cacd423f809e89c90082343978fc7deae7a8dc5843a87d79e7f92049bb31b`.
    - Launched checkpoint-native suffix probe in `/home/ubuntu/prime_track3_suffix_landing_probe_logs/` with lanes `control_p2,floor004_r2500,floor006_r2500,floor006_r2600`.
    - First suffix log confirmed `track3_checkpoint_loaded ... step:2400 seed:3710`, `load_optimizers:True`, `track3_resume_advanced_data steps:2400`, and `3.34512 @2400`.
    - Stopped the sequential control lane after it missed the 2600 gate: control `3.33826 @2600` versus threshold `3.3260`; did not let it run to 3000.
    - Ran only `floor006_r2600` to the 2600 gate from the same checkpoint. It failed harder: `3.34042 @2600`; slope from 2500 to 2600 collapsed to `0.000007/step`, about `0.06x` required target slope.
    - Pulled logs to `.opencode/current_track3_ledger_20260607_logs/floor_h100us_d9f1d50/`.
    - Terminated pod successfully; follow-up `prime pods list` showed zero active pods.

- pod_id: 7a5c570e4582487a82b6a8c78fac26fb
  name: oc-main-track3-copyckpt-h100sxm-20260607-1215
  owner: current-agent
  purpose: Track 3 checkpoint-native suffix run; copy step2400 checkpoint before any training
  gpu: H100_80GB SXM5 spot/datacrunch availability ec854a
  price_per_hour: 1.138 USD
  created_at: 2026-06-07T12:15Z
  expected_stop: after checkpoint-native suffix gate or setup failure
  status: terminated_after_checkpoint_native_suffix_gates_logs_pulled_prime_active_pods_0
  termination_policy: terminate if checkpoint copy/setup fails or after queued suffix gate finishes
  notes:
    - Active pod `7a5c570e4582487a82b6a8c78fac26fb` is `H100 80GB HBM3` SXM5 at `root@86.38.238.33`.
    - Copied local `/Users/progyan/speedrun/tmp/prime_ckpt_transfer/track3_fast_noloco_from2125_seed3710_seed3710_step2400.pt` to remote `/home/ubuntu/.cache/track3_checkpoints/track3_locom_2000_control_seed3710_seed3710_step2400.pt`.
    - Remote SHA256 verified: `a02cacd423f809e89c90082343978fc7deae7a8dc5843a87d79e7f92049bb31b`.
    - Copied local `/Users/progyan/speedrun/tmp/prime_ckpt_transfer/track3_noloco_ckpt2125_seed3710_seed3710_step2125.pt` to remote `/home/ubuntu/.cache/track3_checkpoints/track3_locom_2000_control_seed3710_seed3710_step2125.pt`.
    - Remote SHA256 verified: `aa47660c30a596d64fa05dfbd3bc2b388008f43c5f64da5e26504b44b109cfb1`.
    - Immediate 2125->3300 power continuation loaded the checkpoint correctly (`3.36215 @2125`) but diverged to `val_loss:nan @2150`; stopped it.
    - Launched safer no-LocoProp suffix from the 2125 checkpoint: original power h3000 blended to power h3300 from 2125->2400, train/gate to 2600; remote log `/home/ubuntu/prime_track3_2125_blend3300_logs/run.nohup.log`.
    - The safer blend also hit `val_loss:nan @2150`; stopped it. Root cause looked like fresh pod package drift: `requirements.txt` installed `torch 2.10.0+cu128`, whereas prior successful Prime Track 3 scripts used `torch 2.7.1+cu126`.
    - Downgraded pod venv to `torch 2.7.1+cu126`, `triton 3.3.1`; GPU is `NVIDIA H100 80GB HBM3`.
    - Relaunched checkpoint-native no-LocoProp sanity lane from step2125, cold h3000/p2, to step2400. It loaded optimizer/RNG state and stayed finite: `3.36004 @2150`, `3.35627 @2200`, `3.35306 @2250`, `3.34996 @2300`, `3.34513 @2400`.
    - Saved branchable checkpoint `/home/ubuntu/.cache/track3_checkpoints/track3_suffix_cold3000_from2125_seed3710_to2400_seed3710_step2400.pt`.
    - Tested no-LocoProp h3300/p2 from the same step2125 checkpoint. It was stable but clearly worse by the early gate: `3.36292 @2150`, `3.36026 @2200`, versus cold sanity `3.35627 @2200`; killed it at 2200 to avoid wasting compute.
    - Tested no-LocoProp bridge bump `1.50x` from `2250:2400:2650:3000`; it failed the 2400 gate: `3.34638 @2400`, worse than cold sanity `3.34513 @2400`.
    - Pulled logs to `.opencode/current_track3_ledger_20260607_logs/copyckpt_h100sxm_7a5c57/`.
    - Terminated pod successfully; follow-up `prime pods list` showed zero active pods.

- pod_id: 45a63f7f45a5471fa42669792d146237
  name: oc-main-track3-copyckpt-h100sxm-20260607-1306
  owner: current-agent
  purpose: Copy local Track 3 seed3710 step1600 checkpoint first, then run only checkpoint-backed suffix probes
  gpu: 1x H100_80GB SXM5 datacrunch spot
  price_per_hour: 1.138 USD
  created_at: 2026-06-07T13:06Z
  expected_stop: after checkpoint-backed probe finishes/fails and artifacts are pulled
  status: terminated_after_c_proj_active_matched_alpha_zero_artifacts_pulled_prime_active_pods_0
  termination_policy: keep only while actively copying checkpoint/running queued probe; terminate on setup failure or after artifacts are pulled
  notes:
    - local checkpoint source: `/Users/progyan/speedrun/tmp/modal_ckpt_transfer/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt`
    - local sha256: `430dc1d871ad177e9675679174d5ee84d3f02e6ebdf8aba6bec72093210debf2`
    - prior copy lane showed checkpoint resumes require `torch 2.7.1+cu126`, `triton 3.3.1`; avoid default `torch 2.10.0+cu128`.
    - Active pod SSH: `root@86.38.238.33 -p 22`.
    - Copied checkpoint to `/root/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt`.
    - Remote SHA256 verified: `430dc1d871ad177e9675679174d5ee84d3f02e6ebdf8aba6bec72093210debf2`.
    - Remote GPU confirmed: `NVIDIA H100 80GB HBM3`, `81559 MiB`.
    - Synced tracked worktree files to `/root/wr-track3-locom-20260606`.
    - Installed pinned resume-safe stack: `torch 2.7.1+cu126`, `triton 3.3.1`.
    - Cached FineWeb10B with `python data/cached_fineweb10B.py 20`: 21 bin files, about 4.0 GB.
    - Initial run failed before data cache with `RuntimeError: generator raised StopIteration`; fixed by caching FineWeb.
    - Relaunched clean pair log dir `/root/prime_track3_locom_proj_specificity_logs_retry`, PID `5331`.
    - Confirmed checkpoint-native resume: `track3_checkpoint_loaded ... step:1600 seed:3710 load_optimizers:True`, `track3_resume_advanced_data steps:1600`.
    - First validation matches expected checkpoint trajectory: `3.48241 @1600`.
    - Alpha-zero control completed to `3.37336 @2000`.
    - Active c_proj K5 matched alpha-zero through the 1800 gate: active `3.39870`, alpha-zero `3.39872`, delta `0.00002`.
    - Stopped active lane at 1800 to avoid wasting compute; pulled artifact archive to `.opencode/current_track3_ledger_20260607_logs/proj_specificity_45a63/prime_track3_locom_proj_specificity_logs_retry.tgz`.
    - Local decision report: `.opencode/current_track3_ledger_20260607_logs/proj_specificity_45a63/proj_specificity_decision_1800.md`.
    - Terminated pod successfully; follow-up `prime pods list` showed zero active pods.

- pod_id: 43ad3702f6e843d397f1e5e2d1d6dbb1
  name: oc-main-track3-tailcopy-h100sxm-20260607-1515
  owner: current-agent
  purpose: Copy seed3710 step1600 checkpoint first, then run targeted Track 3 tail schedule probe
  gpu: 1x H100_80GB SXM5 datacrunch spot
  price_per_hour: 1.138 USD
  created_at: 2026-06-07T15:15Z
  expected_stop: after checkpoint-backed tail probe finishes/fails and artifacts are pulled
  status: active_idle_after_tail2500_locom_and_softpolar_tied_control
  termination_policy: keep only while actively copying checkpoint/running queued probe; terminate on setup failure or after artifacts are pulled
  notes:
    - local checkpoint source: `/Users/progyan/speedrun/tmp/modal_ckpt_transfer/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt`
    - local sha256: `430dc1d871ad177e9675679174d5ee84d3f02e6ebdf8aba6bec72093210debf2`
    - selected cheapest adequate H100 SXM/HBM-class offer: availability `ec854a`, datacrunch spot, `$1.138/hr`.
    - Active pod SSH: `root@86.38.238.33 -p 22`.
    - Remote GPU confirmed: `NVIDIA H100 80GB HBM3`, `81559 MiB`.
    - Copied checkpoint to `/root/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt`.
    - Remote SHA256 verified: `430dc1d871ad177e9675679174d5ee84d3f02e6ebdf8aba6bec72093210debf2`.
    - Synced worktree to `/root/wr-track3-locom-20260606`.
    - Installed resume-safe stack: `torch 2.7.1+cu126`, `triton 3.3.1`, `numpy 2.2.6`.
    - Cached FineWeb10B with `python data/cached_fineweb10B.py 20`: 21 bin files, about 4.0 GB.
    - Launched checkpoint-backed `MODE=save2000` via `/root/prime_track3_locom_2000_suffix_logs_43ad37/run_save2000.sh`, PID `4229`.
    - First launch loaded checkpoint correctly (`step:1600`, `3.48241`) but failed at first Triton compile because `/usr/include/python3.10/Python.h` was missing.
    - Installed `python3.10-dev` and `build-essential`; verified `Python.h` exists before relaunch.
    - Relaunched checkpoint-backed `MODE=save2000`, PID `4785`.
    - Save-2000 replay reached `3.37605 @1975` and wrote `/root/.cache/track3_checkpoints/track3_locom_good2000_tailcopy43ad37_seed3710_step2000.pt`.
    - Remote step-2000 SHA256: `53ee13b38d5b3f12279d02031fc1100c0c2467c2fc56daf34af642f750f4577b`.
    - Launched minimal step-2000 suffix probe to 2250 with lanes `control,natural`, PID `6016`.
    - Control suffix from step 2000 reached `3.35306 @2250` and saved `/root/.cache/track3_checkpoints/track3_locom_2000_control_seed3710_seed3710_step2250.pt`.
    - Natural K5 suffix was stopped after matching/worsening control: `3.37102 @2025` vs control `3.37099`, `3.36871 @2050` vs control `3.36869`.
    - User explicitly instructed not to terminate the pod; keep it warm for tail-end probes from the remote step-2000 checkpoint.
    - Launched no-LocoProp tail schedule probe from step 2000 to 2500, lanes `cold3000,floor006,floor010,pr287_h3105p120`, PID `8118`.
    - Cold3000 tail from step 2000 finished at `3.34114 @2500`.
    - `floor006` was worse after the floor became active: `3.34631 @2400` vs cold `3.34512`; stopped the floor sweep before `floor010`.
    - Launched single PR287 h3105,p1.20 tail lane from the same step-2000 checkpoint, PID `9362`.
    - PR287 h3105,p1.20 was catastrophically discontinuous from this checkpoint: `3.42081 @2025`, `3.40944 @2250`; stopped it.
    - Launched smooth horizon extension lanes `h3200p2,h3300p2` from the same step-2000 checkpoint, PID `9957`.
    - `h3200p2` was also worse early: `3.36497 @2125` vs cold `3.36215`; stopped before `h3300p2`.
    - Launched cold continuation from the saved cold `2500` checkpoint to `3000`, PID `10560`.
    - Cold continuation from `2500` to `3000` flatlined: `3.34114 @2500`, `3.33513 @2800`, `3.33472 @2875`, `3.33457 @3000`; checkpoints saved at `2750`, `2875`, `3000`.
    - Launched terminal SoftMuon suffix from the cold `2500` checkpoint with `TRACK3_SOFT_MUON=1`, `TRACK3_SOFT_MUON_BLEND=1.0`, `START_STEP=2500`, `END_STEP=3010`, `CEIL=0.80`, `NORM_RESTORE=1`.
    - Terminal SoftMuon finished and did not rescue the tail: `3.34114 @2500`, `3.33513 @2800`, `3.33472 @2875`, `3.33453 @3000`; essentially tied with cold control. Logs pulled to `.opencode/current_track3_ledger_20260607_logs/tailcopy_43ad37/soft2500_to3000/`.
    - User explicitly instructed not to terminate this pod after the tail run; pod is intentionally left up for immediate follow-up work.
    - Launched short LocoProp tick probe from cold `2500` checkpoint, lane `ungated_norm005`, active `2500:2600`, no loss/cos gate, norm target `0.05`, PID `12588`. Script: `.opencode/prime_scripts/run_prime_track3_locom_tail2500_tick.sh`.
    - `ungated_norm005` finished at `3.33829 @2600`, matching the cold tail and not improving slope. Apply diagnostics confirm nonzero correction with `eff_frac_med=0.05`; logs pulled to `.opencode/current_track3_ledger_20260607_logs/tailcopy_43ad37/tail2500_tick/`.
    - Launched `ungated_softpolar_norm005` from the same cold `2500` checkpoint, PID `13208`, to test spectral shaping of the LocoProp correction after normal correction tied control.
    - `ungated_softpolar_norm005` finished at `3.33830 @2600`, also matching/worsening cold and normal LocoProp. Apply diagnostics confirm nonzero correction with `eff_frac_med=0.05`; raw softpolar correction norm is huge (`raw_frac_med` hundreds of base-step norms) and is scaled down by the norm target. Logs pulled to `.opencode/current_track3_ledger_20260607_logs/tailcopy_43ad37/tail2500_tick/`.
    - 2026-06-07 18:25 UTC direct SSH status check: pod still running, `NVIDIA H100 80GB HBM3`, `0 %` GPU util, `0 MiB` GPU memory, no active `train_gpt`/`torchrun` process. User explicitly instructed not to terminate; pod remains intentionally warm for the next targeted suffix/mechanism probe.
    - Launched residual-after-Muon LocoProp-M probe from the cold step-2500 checkpoint, PID `14272`, script `.opencode/prime_scripts/run_prime_track3_locom_residual_tail2500.sh`.
    - First screen matched checkpoint provenance: `3.34115 @2500`; GPU active at `100 %`, about `37.5 GiB` memory.
