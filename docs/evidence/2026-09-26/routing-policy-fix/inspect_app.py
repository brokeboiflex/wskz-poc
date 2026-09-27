"""Read existing correlated app traces; save full details only on failure."""
import json
import subprocess
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parents[3]
i = int(sys.argv[1])
row = json.loads((here/f'app-{i}-result.jsonl').read_text().splitlines()[0])
logs = subprocess.check_output(['docker','compose','logs','--no-color','api'],text=True,cwd=root)
events = [json.loads(l.split('model_trace ',1)[1]) for l in logs.splitlines() if 'model_trace ' in l]
events = [e for e in events if e['request_id']==row['request_id']]
requests = [e for e in events if e['event']=='request']
responses = [e for e in events if e['event']=='response']
try:
 assert row['passed'] and len(requests)==len(responses)==1
 request = json.loads(requests[0]['body'])
 assert request['messages'][0]['content'] == (here/'prompt.txt').read_text().rstrip('\n')
 assert request['temperature']==0 and request['model']=='qwen3:4b-instruct-2507-q4_K_M'
 choice = json.loads(responses[0]['body'])['choices'][0]
 assert choice['finish_reason']=='tool_calls'
 assert len(choice['message']['tool_calls'])==1
 assert choice['message']['tool_calls'][0]['function']['name']=='send_department_email'
 assert len([e for e in events if e['event']=='delivery_completed'])==1
 assert len([e for e in events if e['event']=='parsed' and e['rejection_reason'] is None])==1
 print(json.dumps({'case':i,'wire':choice,'passed':True,'mime_checked_by':'verification/e2e.py'}))
except Exception:
 (here/f'app-{i}-failure-trace.json').write_text(json.dumps(events,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(events,ensure_ascii=False))
 raise
