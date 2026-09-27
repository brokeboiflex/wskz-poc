"""Observed full corpus; persist failure details only, no tools executed."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CORPUS = ROOT / 'verification/benchmark/cases-500.json'
SHA = 'bd3cf10bc628dc0c27349201b443ef95a9b11112b272573766d323c547f5cd0e'
assert hashlib.sha256(CORPUS.read_bytes()).hexdigest() == SHA
cases = json.loads(CORPUS.read_text())
assert len(cases) == 500
with (HERE / 'started.json').open('x') as f:
    json.dump({'started': time.time(), 'corpus_sha256': SHA}, f)
request = json.loads((HERE.parent / 'simple-schema/394-simple-request.json').read_text())
request['messages'][0]['content'] = (HERE / 'prompt.txt').read_text().rstrip('\n')
request['tools'] = [json.loads((HERE / 'tool.json').read_text())]
probe = (HERE.parent / 'simple-schema/probe.py').read_text()
summary = {'planned':500, 'completed':0, 'correct':0, 'wrong_route':0, 'protocol_error':0, 'per_department':{}, 'status':'running'}
(HERE / 'failures.jsonl').touch()
for index, case in enumerate(cases, 1):
    request['messages'][-1] = {'role':'user','content':case['message']}
    (HERE / 'checkpoint.json').write_text(json.dumps({'attempting':index,'completed':index-1}))
    start = time.monotonic()
    result = subprocess.run(['docker','compose','exec','-T','api','python','-c',probe], input=json.dumps(request), capture_output=True, text=True, cwd=ROOT)
    actual, reason, category = None, None, 'protocol_error'
    try:
        assert result.returncode == 0, 'transport process failed'
        response = json.loads(result.stdout)
        assert response['status'] == 200, f"HTTP {response['status']}"
        body = json.loads(response['body'])
        assert len(body['choices']) == 1, 'unexpected choices'
        choice = body['choices'][0]
        assert choice['finish_reason'] == 'tool_calls', 'missing or incomplete native call'
        calls = choice['message'].get('tool_calls', [])
        assert len(calls) == 1 and calls[0]['function']['name'] == 'send_department_email', 'invalid function call'
        args = json.loads(calls[0]['function']['arguments'])
        assert set(args) == {'department'} and args['department'] in request['tools'][0]['function']['parameters']['properties']['department']['enum'], 'invalid arguments'
        actual = args['department']
        category = 'correct' if actual == case['department'] else 'wrong_route'
        if category == 'wrong_route':
            reason = f"expected {case['department']}, received {actual}"
    except Exception as exc:
        reason = str(exc)
    summary['completed'] = index
    summary[category] += 1
    counts = summary['per_department'].setdefault(case['department'], {'correct':0,'wrong_route':0,'protocol_error':0})
    counts[category] += 1
    if category != 'correct':
        failure = {'case':index,'case_id':case['id'],'expected':case['department'],'actual':actual,'category':category,'reason':reason,'seconds':round(time.monotonic()-start,3),'request':request,'raw_response':result.stdout,'stderr':result.stderr}
        with (HERE / 'failures.jsonl').open('a') as f:
            f.write(json.dumps(failure,ensure_ascii=False)+'\n')
        print('FAILURE '+json.dumps(failure,ensure_ascii=False),flush=True)
    (HERE / 'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (HERE / 'checkpoint.json').write_text(json.dumps({'completed':index,'in_flight':False}))
    if category != 'correct' or index % 10 == 0:
        print('PROGRESS '+json.dumps(summary),flush=True)
        if index < 500:
            action = input('REVIEW continue/stop: ').strip()
            with (HERE / 'reviews.jsonl').open('a') as f:
                f.write(json.dumps({'after_case':index,'action':action,'time':time.time()})+'\n')
            if action != 'continue':
                summary['status']='stopped'
                break
else:
    summary['status']='complete'
(HERE / 'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary),flush=True)
