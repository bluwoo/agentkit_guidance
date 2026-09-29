#!/tmp/agentkit_verify_venv/bin/python
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'deploy'))
import cloud_deploy as cd

STATE=ROOT/'deployment-state'
E2E=STATE/'e2e-secrets.env'

def envfile(path):
    out={}
    for line in path.read_text().splitlines():
        if '=' in line:
            k,v=line.split('=',1); out[k]=v
    return out

def atomic_json(path,data):
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(data,indent=2)); os.chmod(tmp,0o600); os.replace(tmp,path)

def result(call):
    r=call.get('Result',{})
    return r

def create(kind,image,name,state_file,extra_envs):
    old=cd._call('GetRuntime',{'RuntimeId':os.environ['SAMPLE_RUNTIME_ID']}).get('Result',{})
    state={}
    if state_file.exists():
        try: state=json.loads(state_file.read_text())
        except Exception: state={}
    runtime_id=state.get('runtime_id')
    if not runtime_id:
        envs=[{'Key':k,'Value':v} for k,v in extra_envs.items()]
        body={
          'ProjectName':'default','Name':name,'Description':name+' managed deployment',
          'ArtifactType':'image','ArtifactUrl':image,'RoleName':old['RoleName'],
          'Command': old.get('Command') if kind=='wizard' else 'uvicorn app:app --host 0.0.0.0 --port 8000',
          'AuthorizerConfiguration':{'KeyAuth':{'ApiKeyLocation':'Header','ApiKeyName':'Authorization'}},
          'Envs':envs,'NetworkConfiguration':{'EnablePublicNetwork':True},
          'ClientToken':state.get('client_token') or uuid.uuid4().hex,
          'CpuMilli':2000,'MemoryMb':4096,'MinInstance':1,'MaxInstance':2,'MaxConcurrency':100,
          'ApmplusEnable':True,'Tags':[{'Key':'managed_by','Value':'agentkit-wizard-e2e','Type':'custom'}]
        }
        if kind=='wizard': body['ModelAgentName']='doubao-1-5-pro-32k-250115'
        out=cd._call('CreateRuntime',body); err=(out.get('ResponseMetadata') or {}).get('Error')
        if err: raise RuntimeError('CreateRuntime '+str(err.get('Code'))+' '+str(err.get('Message')))
        r=out.get('Result',{})
        runtime_id=r.get('RuntimeId') or r.get('Id')
        if not runtime_id: raise RuntimeError('CreateRuntime missing id')
        state={'runtime_id':runtime_id,'client_token':body['ClientToken'],'image':image,'kind':kind}
        atomic_json(state_file,state)
    endpoint=''; status=''
    for i in range(120):
        out=cd._call('GetRuntime',{'RuntimeId':runtime_id}); r=out.get('Result',{}); status=r.get('Status',''); endpoint=r.get('Endpoint','') or endpoint
        if status=='Ready': break
        if status=='UnReleased':
            rel=cd._call('ReleaseRuntime',{'RuntimeId':runtime_id,'VersionNumber':0}); err=(rel.get('ResponseMetadata') or {}).get('Error')
            if err and err.get('Code') not in ('InvalidResourceStatus',): raise RuntimeError('ReleaseRuntime '+str(err.get('Code')))
        if status in ('Error','Deleted','Deleting'): raise RuntimeError('Runtime '+status+': '+str(r.get('StatusMessage','')))
        time.sleep(5)
    if status!='Ready': raise RuntimeError('Runtime did not become Ready: '+status)
    state.update({'endpoint':endpoint,'status':status}); atomic_json(state_file,state)
    return {'runtime_id':runtime_id,'endpoint':endpoint,'status':status}

def main():
    e=envfile(E2E)
    model_key=os.environ.get('MODEL_AGENT_API_KEY') or os.environ.get('ARK_API_KEY')
    if not model_key: raise SystemExit('model key unavailable')
    wizard_env={
      'WIZARD_MODE':'production','SERVE_FRONTEND_DIST':'/app/web/dist','WIZARD_DATA_DIR':'/app/wizard_data',
      'WIZARD_LLM_BASE_URL':'https://ark.cn-beijing.volces.com/api/v3/','WIZARD_LLM_API_KEY':model_key,
      'WIZARD_LLM_MODEL':'doubao-1-5-pro-32k-250115','WIZARD_ALLOWED_ORIGINS':'',
      'WIZARD_PUBLIC_ORIGIN':'','WIZARD_OWNER_SETUP_TOKEN':e['WIZARD_OWNER_SETUP_TOKEN']
    }
    target_env={'MODEL_NAME':'doubao-1-5-pro-32k-250115','MODEL_API_KEY':model_key,'MODEL_BASE_URL':'https://ark.cn-beijing.volces.com/api/v3/'}
    w=create('wizard',os.environ['WIZARD_IMAGE'],'agentkit-wizard-human-v2',STATE/'runtime-v2.json',wizard_env)
    t=create('target',os.environ['TARGET_IMAGE'],'support-triage-agent',STATE/'target-runtime.json',target_env)
    print(json.dumps({'wizard':w,'target':t}))
if __name__=='__main__': main()
