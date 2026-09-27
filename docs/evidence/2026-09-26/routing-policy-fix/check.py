"""One observed transport case, using existing probe; no tools executed."""
import json
import subprocess
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parents[3]
i = int(sys.argv[1])
case = json.loads((root/'verification/benchmark/cases-500.json').read_text())[i-1]
request = json.loads((here.parent/'simple-schema/394-simple-request.json').read_text())
request['messages'] = [{'role':'system','content':(here/'prompt.txt').read_text().rstrip('\n')},{'role':'user','content':case['message']}]
request['tools'] = [json.loads((here.parent/'english-minimal-500/tool.json').read_text())]
with (here/f'{i:03d}-started.json').open('x') as f:
    json.dump({'case':i,'request':request},f,ensure_ascii=False)
r = subprocess.run(['docker','compose','exec','-T','api','python','-c',(here.parent/'simple-schema/probe.py').read_text()],input=json.dumps(request),text=True,capture_output=True,cwd=root)
category,actual = 'protocol_error',None
try:
    raw=json.loads(r.stdout)
    assert r.returncode==0 and raw['status']==200
    choice=json.loads(raw['body'])['choices'][0]
    calls=choice['message'].get('tool_calls',[])
    assert choice['finish_reason']=='tool_calls' and len(calls)==1
    assert calls[0]['function']['name']=='send_department_email'
    args=json.loads(calls[0]['function']['arguments'])
    assert set(args)=={'department'} and args['department'] in ['human_resources','payroll','help_desk','it','other']
    actual=args['department']
    category='correct' if actual==case['department'] else 'wrong_route'
except Exception:
    pass
out={'case':i,'expected':case['department'],'actual':actual,'category':category}
(here/f'{i:03d}-result.json').write_text(json.dumps(out,indent=2)+'\n')
if category!='correct':
    with (here/'failures.jsonl').open('a') as f:
        f.write(json.dumps({**out,'request':request,'raw_response':r.stdout,'stderr':r.stderr},ensure_ascii=False)+'\n')
print(json.dumps(out))
print(r.stdout)
print(r.stderr)
