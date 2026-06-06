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
  status: launched_by_launch_prime_track3_kdiag.sh_head_b3e1d3f
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
