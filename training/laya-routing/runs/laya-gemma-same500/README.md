# Laya vs Gemma: same500

User authorized one old500 regression run. Epoch1 selected solely by complete validation macro-F1; training stopped by user after epoch2, not by patience. No further training, retries, mail, critics or new held-out test. Existing Gemma493/500 evidence retained. Exact case content equality verified before inference. Different model-specific prompts/adapters and separate run times remain comparison limitations.

Prerequisites: existing epoch1 runtime and adapter, frozen weights/policy, local Docker. Start `docker start wskz-laya-eval-epoch1-runtime wskz-laya-eval-epoch1-adapter`. From PoC run `.venv/bin/python training/laya-routing/observed_eval.py --session training/laya-routing/runs/laya-gemma-same500/session.json`; inspect each error/every10 then resume with explicit `--note`. No automatic reviews. Finish with `--report` after final review. Runner validates hashes, preserves raw requests/responses, skips completed cases and refuses uncertain attempts. Stop both containers after saving logs. Session and freeze JSON pin paths and hashes.

## Results

All500 first attempts and review gates audited. Laya432/500 (86.4%), Gemma493/500 (98.6%). Laya median 0.230646s, Gemma 1.800000s; 7.80x median speedup. Summed request durations 119.981s vs 909.394s, excluding operator pauses. Both zero protocol errors.

| Department      | Laya /100 | Gemma /100 |
| --------------- | --------: | ---------: |
| help_desk       |       100 |         99 |
| human_resources |        87 |         99 |
| it              |        86 |        100 |
| other           |        60 |         99 |
| payroll         |        99 |         96 |

Timing includes HTTP; different model-specific prompts/adapters and separate runs. Gemma was previously adjusted using this regression corpus; this is not an independent generalization comparison. No Gemma rerun. Both Laya containers stopped. Full raw traces in results/, errors in failures.json, comparison in comparison.json. New held-out test remains unopened for inference. No further tuning authorized.

Hardware accounting and limitations are documented in the [main README](../../../../README.md). No matched RSS/cgroup RAM or CPU-seconds were collected for this500 comparison. Raw Gemma buffer logs are not resident-memory measurements.
