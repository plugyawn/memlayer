- pod_id: 93b003de7290466abe00948cb9aa0330
  name: oc-codex-fgdiag-h100-20260526
  owner: current-agent
  purpose: Feature-Gram diagonal NanoGPT H100 compile/smoke validation
  gpu: 1x H100 80GB PCIe
  price_per_hour: $2.35
  created_at: 2026-05-26T11:23:57Z
  expected_stop: after feature-diag compile/smoke validation or earlier unrecoverable setup failure
  status: terminated-after-feature-gram-control
  termination_policy: keep only while actively setting up or running this validation block
- pod_id: 8249f5e6edc947139c108f5da9c7b480
  name: oc-codex-locodiag-h100-20260526-2059
  owner: current-agent
  purpose: MLP-only true diagonal LocoProp-S NanoGPT compile/backward smoke and first timing screen
  gpu: 1x H100 80GB PCIe
  price_per_hour: $2.35
  created_at: 2026-05-26T15:30:39Z
  expected_stop: after LocoProp-S compile/backward smoke and any immediately justified short screen
  status: terminated-after-negative-60step-screen
  termination_policy: keep only while actively setting up or running this validation block
- pod_id: 33d31eff010347a5b8066ec3d22837c9
  name: oc-codex-locodiag-normuon-h100-20260526-2233
  owner: current-agent
  purpose: MLP diagonal feature-Gram preconditioning on top of NorMuon compile/smoke and short H100 screen
  gpu: 1x H100 80GB PCIe
  price_per_hour: $2.35
  created_at: 2026-05-26T16:34:00Z
  expected_stop: after corrected NorMuon-composed diagonal feature-Gram validation or earlier unrecoverable setup failure
  status: terminated-after-negative-postfix-ablation-suite
  termination_policy: keep only while actively setting up or running this validation block
- pod_id: 437d65f60bb14daaa946235638bcdd02
  name: oc-codex-newtonv-20260527-0147
  owner: current-agent
  purpose: V-only full feature Gram Newton-Muon no-op and short H100 screens
  gpu: 1x H100 80GB PCIe
  price_per_hour: $3.29
  created_at: 2026-05-27T01:47:00+05:30
  expected_stop: after full-V no-op and first real Newton-Muon screen unless loss-positive enough to continue
  status: terminated-after-qk-o-topshrink-screens
  termination_policy: keep only while actively setting up or running Newton-Muon validation; do not touch other active pods
- pod_id: da5dfb0923c24d049348b1d6615fd167
  name: oc-codex-norminverse-v01-20260527-1107
  owner: current-agent
  purpose: 60-step V layers 0-1 normalized-inverse no-norm Newton-Muon gate
  gpu: 1x H100 80GB PCIe
  price_per_hour: $2.35
  created_at: 2026-05-27T11:07:00+05:30
  expected_stop: immediately after the 60-step gate or earlier unrecoverable setup failure
  status: terminated-after-norminverse-blend05-reject
  termination_policy: keep only while actively setting up or running this single gate
- pod_id: b45df3092c7640cf9f7b112cb54534f0
  name: track3-locom-nm-1xh100-20260531
  owner: current-agent
  purpose: Track 3 official Newton-Muon source with LocoProp-M correction, 1x H100, two trials to target loss 3.28
  gpu: 1x H100 80GB PCIe
  price_per_hour: $2.35
  created_at: 2026-05-31T11:46:00Z
  expected_stop: after the two-trial 1x target-loss run completes, fails, or user redirects
  status: terminated-after-provenance-mismatch-audit
  termination_policy: keep while actively training or gathering requested benchmark evidence; do not touch unrelated pods
- pod_id: d60c61dbd5284331b6467023e35acf9c
  name: track3-locom-nm-4xh100-20260531
  owner: current-agent
  purpose: Track 3 official Newton-Muon source with LocoProp-M correction, 4x H100 distributed two-seed target-loss test
  gpu: 4x H100 80GB PCIe
  price_per_hour: $9.40
  created_at: 2026-05-31T11:46:00Z
  expected_stop: after the two-seed 4x target-loss run completes, fails, or user redirects
  status: terminated-after-step375-distributed-mismatch
  termination_policy: keep while actively training or gathering requested benchmark evidence; do not touch unrelated pods
- pod_id: 8312077bfda9403fb5377b81c1e802e0
  name: track3-simple-locom-prime-a-1xh100-20260531
  owner: current-agent
  purpose: Simple Track 3 base with LocoProp-M correction, 1x H100, one run to target loss 3.28
  gpu: 1x H100 80GB PCIe
  price_per_hour: $2.35
  created_at: 2026-05-31T22:31:00+05:30
  expected_stop: after the one-run 1x target-loss run completes, fails, or user redirects
  status: active-training-running-step125-val-4.65727-6922ms
  termination_policy: keep while actively training or gathering requested benchmark evidence; terminate after completion/failure
- pod_id: b3ebfcf259094999b5a363fcd749e07d
  name: track3-simple-locom-prime-b-1xh100-20260531
  owner: current-agent
  purpose: Simple Track 3 base with LocoProp-M correction, 1x H100, one run to target loss 3.28
  gpu: 1x H100 80GB PCIe
  price_per_hour: $2.35
  created_at: 2026-05-31T22:31:00+05:30
  expected_stop: after the one-run 1x target-loss run completes, fails, or user redirects
  status: active-training-running-step125-val-4.63836-6928ms
  termination_policy: keep while actively training or gathering requested benchmark evidence; terminate after completion/failure
