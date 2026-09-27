"""One observed request; retain failure details only. No tool execution."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
number = int(sys.argv[1])
assert number in (394, 235, 393)
state_path = HERE / 'summary.json'
state = json.loads(state_path.read_text()) if state_path.exists() else {'completed': [], 'passed': 0, 'failed': 0}
assert number not in state['completed'], 'Never replay completed cases'
marker = HERE / f'attempt-{number}.lock'
with marker.open('x') as f:
    f.write('Request attempted. If interrupted inspect before resuming.\n')
request = json.loads((HERE.parent / 'simple-schema' / f'{number}-simple-request.json').read_text())
request['messages'][0]['content'] = (HERE / 'prompt.txt').read_text().rstrip('\n')
request['tools'] = [json.loads((HERE / 'tool.json').read_text())]
probe = (HERE.parent / 'simple-schema/probe.py').read_text()
result = subprocess.run(['docker', 'compose', 'exec', '-T', 'api', 'python', '-c', probe], input=json.dumps(request), capture_output=True, text=True, cwd=ROOT)
expected = 'help_desk' if number == 235 else 'it'
reason = None
try:
    response = json.loads(result.stdout)
    body = json.loads(response['body'])
    choice = body['choices'][0]
    calls = choice['message'].get('tool_calls', [])
    assert response['status'] == 200 and choice['finish_reason'] == 'tool_calls', 'missing or incomplete native call'
    assert len(calls) == 1 and calls[0]['function']['name'] == 'send_department_email', 'invalid function call'
    args = json.loads(calls[0]['function']['arguments'])
    assert set(args) == {'department'} and args['department'] in ['human_resources','payroll','help_desk','it','other'], 'invalid arguments'
    assert args['department'] == expected, f'wrong department: {args["department"]}, expected {expected}'
except Exception as exc:
    reason = str(exc)
    with (HERE / 'failures.jsonl').open('a') as f:
        f.write(json.dumps({'case': number, 'expected_department': expected, 'failure': reason, 'request': request, 'raw_response': result.stdout, 'stderr': result.stderr}, ensure_ascii=False)+'\n')
state['completed'].append(number)
state['failed' if reason else 'passed'] += 1
state_path.write_text(json.dumps(state, indent=2)+'\n')
# Inspect live output, but persist detailed records only for failures.
print(result.stdout)
print(json.dumps({'case': number, 'failure': reason, 'summary': state}))
