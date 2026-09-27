"""One OpenAI-compatible request; never executes returned tools."""
import json
import sys
import httpx
request = json.load(sys.stdin)
response = httpx.post('http://ollama:11434/v1/chat/completions', json=request, timeout=180)
print(json.dumps({'status': response.status_code, 'body': response.text}, ensure_ascii=False, indent=2))
