import asyncio,json,time,sys
from langchain_openai import ChatOpenAI
from langchain_core.tools import StructuredTool
from langchain_core.messages import SystemMessage, HumanMessage
from router_app.adapters.agent import SYSTEM_PROMPT,SendArguments,DEPARTMENT_CRITERIA
async def main():
 mode=sys.argv[1]
 cases=json.load(open('/cases.json'))
 async def send(department: str):
  """Schema only: diagnostics never executes this tool."""
  raise RuntimeError('diagnostics cannot send mail')
 tool=StructuredTool.from_function(coroutine=send,name='send_department_email',description='Send the original message to exactly one department. '+' '.join(f'{key}: {value}' for key,value in DEPARTMENT_CRITERIA.items()),args_schema=SendArguments.model_json_schema())
 options={'max_tokens':1024} if mode=='baseline' else {'extra_body':{'max_tokens':1024},'reasoning_effort':'none','temperature':.7,'top_p':.8}
 model=ChatOpenAI(model='qwen3:1.7b',base_url='http://ollama:11434/v1',api_key='ollama',max_retries=0,timeout=180,use_responses_api=False,**options).bind_tools([tool])
 prompt=SYSTEM_PROMPT if mode=='baseline' else SYSTEM_PROMPT.replace(' /no_think','')
 for idx in [n*100+i for n in range(5) for i in range(6)]:
  case=cases[idx]; start=time.monotonic()
  row={'mode':mode,'case_id':case['id']}
  try:
   result=await model.ainvoke([SystemMessage(prompt),HumanMessage(case['message'])])
   row.update(result.model_dump(mode='json'))
  except Exception as exc:
   row['error']=str(exc)
  row['seconds']=round(time.monotonic()-start,3)
  print(json.dumps(row,ensure_ascii=False),flush=True)
asyncio.run(main())
