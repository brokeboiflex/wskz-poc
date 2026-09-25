# Local CPU and RAM measurement

Requested 2026-09-25. Reuses the approved synthetic local test approach in
[APPROACH.md](APPROACH.md), unchanged models, services, and `verification/cases.json`.
Observe Docker counters around that same test; no weight training, paid compute,
external email, concurrency changes, or model tuning.

## Measured result

CPU-only Linux ARM64 Docker Desktop VM, 10 logical CPUs and 7.75 GiB available
RAM. Existing cached models; startup/model loading excluded from E2E timings.
One sequential 15-message run per provider, no concurrent inference workload.

| Observation                                  |  Laya multilingual | Qwen3 via Ollama (`qwen3:1.7b`) |
| -------------------------------------------- | -----------------: | ------------------------------: |
| Model runtime RAM before requests            |          1.883 GiB |                       1.861 GiB |
| Model runtime RAM after requests             |          1.925 GiB |                       1.942 GiB |
| Maximum sampled runtime RAM                  |          1.926 GiB |                       1.957 GiB |
| Selected app containers RAM after requests   |          2.127 GiB |                       2.103 GiB |
| Runtime CPU time during observation interval | 13.592 CPU-seconds |            1652.187 CPU-seconds |
| CPU time divided by 15 requests              |  0.906 CPU-seconds |             110.146 CPU-seconds |
| Median E2E request duration                  |      0.171 seconds |                  10.698 seconds |
| Correct routing in this run                  |              13/15 |                           13/15 |

RAM savings are **not material in this configuration**. Laya uses much less CPU
time for these short messages. CPU-seconds sum usage over all cores, so they
are not elapsed seconds. The counter intervals include health checks and
observation commands; they are approximate workload comparisons, not isolated
per-inference profiling. The sampled CPU maxima (517.52% and 1089.4%) are retained
in the summary; short sampling windows and VM accounting make them unsuitable
as hard core requirements. Laya is configured with four PyTorch threads; neither
provider required a GPU in this test.

Selected app containers mean runtime + API + mailer + Mailpit, plus Laya's
adapter for that variant. Docker VM/host overhead is excluded. The idle Ollama
server that Compose starts for the Laya variant is excluded from the selected
container sum; no Ollama model was loaded in that variant.
These short, sequential requests do not establish minimum RAM, long-input peaks,
concurrent capacity or server sizing. Leave headroom beyond the observed 2.1 GiB.

The local Ollama model reports Q4_K_M quantization. Laya's checkpoint stores
643,817,990 bytes of F16 tensors and 12 bytes of F32 tensors; file storage dtype
does not establish runtime allocation. Model weight size alone therefore cannot
be substituted for measured process/container memory.

Ollama's repeat made routing errors on cases 3 (employment certificate → HR)
and 6 (printer → IT), unlike the preceding 15/15 run. Laya repeated its known
errors on cases 4 and 15. Both E2E commands exited 1. This is retained evidence
of imperfect/variable routing, not an error in the resource collection.
Run IDs: Ollama `1010942b42fc`, Laya `56876801584a`.

Summary: [summary.json](evidence/2026-09-25/resources/summary.json).
Before/after snapshots, raw CPU counters, normalized sample JSONL and E2E
results are in the same directory. Containers were stopped after measurement;
all volumes and messages remain available. No application code or model weights
were changed for this measurement.

## Reproduce

Use the existing built images and cached volumes. Requirements: working Docker,
Compose, available ports 8000/8025, existing models, sufficient VM memory. On this
host use the temporary Docker client configuration documented in APPROACH if
its credentials helper hangs. Run one provider at a time, without other model
workloads. Start with the Ollama environment, then repeat with the Laya environment.

```sh
docker compose --env-file .env.ollama-example up -d --no-build
docker compose --env-file .env.ollama-example ps -a
# Record baseline and final counters around E2E. For Laya use laya-runtime.
docker exec message-router-ollama-1 cat /sys/fs/cgroup/cpu.stat
docker stats --no-stream --format '{{json .}}' message-router-ollama-1 message-router-api-1 message-router-mailer-1 message-router-mailpit-1
# In a separate terminal, collect samples until E2E finishes; stop with Ctrl-C.
docker stats --format '{{json .}}' message-router-ollama-1 message-router-api-1 message-router-mailer-1 message-router-mailpit-1
# Run in the main terminal; this creates 15 new synthetic messages in Mailpit.
docker compose --env-file .env.ollama-example --profile test run --no-deps --rm e2e
docker exec message-router-ollama-1 cat /sys/fs/cgroup/cpu.stat
docker stats --no-stream --format '{{json .}}' message-router-ollama-1 message-router-api-1 message-router-mailer-1 message-router-mailpit-1
docker compose --env-file .env.ollama-example stop
# Repeat for Laya; include both laya-runtime and laya-adapter in Docker stats.
docker compose --env-file .env.laya-example up -d --no-build
docker compose --env-file .env.laya-example --profile test run --no-deps --rm e2e
docker compose --env-file .env.laya-example stop
```

Do not bypass a failed model-init probe. Save failures as evidence. On interruption,
retain volumes and partial logs. Do not reuse partial logs as a completed benchmark.
Resume with a fresh log filename; startup can reuse cached weights.

## Metrics and limits

Raw observations and E2E outputs: `docs/evidence/2026-09-25/resources/`.
Docker memory is the Linux cgroup working-set estimate: usage minus inactive file
cache, as described in [Docker's documentation](https://docs.docker.com/reference/cli/docker/container/stats/).
It is neither model-file size nor whole-machine RAM use. Docker CPU 100% corresponds
to one CPU core; multiple cores can exceed 100%. Sampling can miss brief peaks.
`cpu.stat` cumulative `usage_usec` before/after includes health checks and observation
processes in that container, not only inference. The interval also includes any
measurement overhead around E2E. Use this as observed workload cost, not a minimum
hardware specification, load-test capacity, power measurement, or cloud bill.
