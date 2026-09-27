"""Offline audit and failure-only Markdown report; performs no inference."""
import hashlib
import json
from collections import Counter
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parents[3]
corpus = root / 'verification/benchmark/cases-500.json'
assert hashlib.sha256(corpus.read_bytes()).hexdigest() == json.loads((here / 'started.json').read_text())['corpus_sha256']
cases = json.loads(corpus.read_text())
summary = json.loads((here / 'summary.json').read_text())
failures = [json.loads(line) for line in (here / 'failures.jsonl').read_text().splitlines()]
reviews = [json.loads(line) for line in (here / 'reviews.jsonl').read_text().splitlines()]
assert summary['status'] == 'complete' and summary['completed'] == len(cases) == 500
assert json.loads((here / 'checkpoint.json').read_text()) == {'completed':500, 'in_flight':False}
assert len({f['case'] for f in failures}) == len(failures) == summary['wrong_route'] + summary['protocol_error']
assert sum(summary[k] for k in ('correct','wrong_route','protocol_error')) == 500
reference = json.loads((here.parent / 'simple-schema/394-simple-request.json').read_text())
reference['messages'][0]['content'] = (here / 'prompt.txt').read_text().rstrip('\n')
reference['tools'] = [json.loads((here / 'tool.json').read_text())]
counts = Counter()
confusion = Counter()
lines = ['# Failure-only audit: English minimal schema', '', 'Completed 500 cases: 353 correct (70.6%), 109 wrong routes, 38 missing native tool calls. All 38 missing calls occurred in the other category. No HTTP failure or malformed native call was found in the saved failures.', '', 'Transport-only evaluation on patched Ollama/Qwen3 4B at temperature 0; no tools executed or emails sent. This experimental prompt/schema has not been promoted to the application. Successful raw responses were deliberately not retained, so their aggregate count cannot be independently reconstructed from saved responses. The corpus has prior diagnostic exposure and paired scenarios; this is not a clean held-out reliability estimate.', '', 'Every failure below includes the original input and returned assistant message. Full requests and HTTP responses: [failures.jsonl](failures.jsonl). Repeat approach and limits: [README.md](README.md).', '']
for f in failures:
    case = cases[f['case'] - 1]
    assert f['case_id'] == case['id'] and f['expected'] == case['department']
    reference['messages'][-1] = {'role':'user','content':case['message']}
    assert f['request'] == reference
    response = json.loads(f['raw_response'])
    assert response['status'] == 200 and not f['stderr']
    choices = json.loads(response['body'])['choices']
    assert len(choices) == 1
    choice = choices[0]
    calls = choice['message'].get('tool_calls', [])
    if choice['finish_reason'] == 'tool_calls':
        assert len(calls) == 1 and calls[0]['function']['name'] == 'send_department_email'
        args = json.loads(calls[0]['function']['arguments'])
        assert set(args) == {'department'} and args['department'] in reference['tools'][0]['function']['parameters']['properties']['department']['enum']
        assert args['department'] == f['actual'] != case['department']
        assert f['category'] == 'wrong_route'
    else:
        assert choice['finish_reason'] == 'stop' and not calls
        assert f['category'] == 'protocol_error' and f['actual'] is None
    counts[(case['department'],f['category'])] += 1
    confusion[(case['department'],f['actual'] or 'missing_call')] += 1
    lines += [f"## Case {f['case']:03d}: {f['reason']}", '', f"ID: `{f['case_id']}`", '', '```text', case['message'], '```', '', '```json', json.dumps(choice,ensure_ascii=False,indent=2), '```', '']
for department, totals in summary['per_department'].items():
    assert sum(totals.values()) == sum(c['department'] == department for c in cases) == 100
    for category in ('wrong_route','protocol_error'):
        assert counts[(department,category)] == totals[category]
expected_gates = sorted({f['case'] for f in failures} | set(range(10,500,10)))
assert [r['after_case'] for r in reviews] == expected_gates
assert all(r['action'] == 'continue' for r in reviews)
(here / 'FAILURES.md').write_text('\n'.join(lines))
(here / 'audit.json').write_text(json.dumps({'status':'passed','failed_cases_audited':len(failures),'review_gates':len(reviews),'confusion':[{'expected':a,'actual':b,'count':n} for (a,b),n in confusion.items()],'limits':'Success raw responses not retained; aggregate success counts checked for conservation only. No delivery verification.'},indent=2)+'\n')
print(json.dumps({'audited_failures':len(failures),'review_gates':len(reviews),'summary':summary}))
