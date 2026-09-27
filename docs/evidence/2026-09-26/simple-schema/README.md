# Approved temperature/schema experiment

User requested lower temperature and simpler schema instead of EXAONE.
Keep patched Ollama and Qwen3-4B-Instruct-2507, system prompt and tool name.
Use saved wire requests; change temperature to0 and remove department.anyOf.
Department remains a required string enum with additionalProperties=false.
Descriptions remain in the unchanged system prompt. First case394 at temperature0
with original schema, then same input with simplified schema to separate effects.
Inspect each response before continuing. Then case235 and successful control393
with simplified schema. Each is one OpenAI-compatible POST, no retries and no
execution of returned tools. No bulk benchmark or production schema change;
Laya's described-choice contract remains intact while testing this hypothesis.
Save request/status/raw output per attempt. Prerequisites: running patched Ollama,
API container with httpx; run probe.py by passing each request on stdin through
`docker compose exec -T api python -c` with the script content. Never replay or
overwrite completed artifacts without separately naming a deliberate attempt.

## Results

Case394 temperature0 alone still emits send_department_it as text. Removing
anyOf at temperature0 produces send_department_email(department=it).
Case235 simplified produces a valid call but chooses it instead of help_desk.
Control393 simplified produces a valid call with correct it. Thus3/3 simplified
requests have valid calls,2/3 correct departments. Small diagnostic sample only,
not reliability proof. No tools executed, no emails. Production schema and API
settings remain unchanged pending adoption; Laya still needs described choices.
EXAONE experiment was superseded; no EXAONE inference was performed.
