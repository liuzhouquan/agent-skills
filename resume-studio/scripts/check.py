#!/usr/bin/env python3
"""Offline behavioral checks; no model requests or personal data."""
import copy
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import serve
from storage import Library, Conflict

def main():
    demo=serve.read(serve.ASSETS/'demo.json'); serve.validate(demo)
    bad=copy.deepcopy(demo);bad['sections'][0]['items'][0]['bullets']='<script>'
    try:serve.validate(bad)
    except ValueError:pass
    else:raise AssertionError('Invalid bullets accepted')
    for template in serve.read(serve.ASSETS/'templates'/'manifest.json'):
        assert (serve.ASSETS/'templates'/template['file']).is_file()
    with tempfile.TemporaryDirectory() as d:
        workspace=Path(d);(workspace/'history').mkdir();path=workspace/'resume.json'
        serve.write(path,demo); assert serve.read(path)==demo
        expect_hidden_filtered=False
        def fake_run(args,**kwargs):
            assert args[args.index('--sandbox')+1]=='read-only'
            assert '--dangerously-bypass-approvals-and-sandbox' not in args
            payload=json.loads(kwargs['input'].split('以下 JSON 为用户请求及文档数据：\n',1)[1])
            if payload.get('mode')=='replace':
                assert payload['resume']['profile']['name']==''
                assert payload['resume']['sections']==[]
                assert payload['history']==[]
                assert payload['source_text']=='仅测试材料'
            else:
                assert payload['resume']==demo
                if expect_hidden_filtered:
                    assert '隐藏测试项' not in json.dumps(payload['resume'],ensure_ascii=False)
            output=Path(args[args.index('--output-last-message')+1])
            output.write_text(json.dumps({'message':'候选稿','resume_json':json.dumps(demo)}))
            class Result:returncode=0;stderr=''
            return Result()
        with patch('serve.shutil.which',return_value='/fake/codex'),patch('serve.subprocess.run',side_effect=fake_run):
            reply=serve.run_agent(workspace,{'resume':demo,'prompt':'精简','history':[]})
            assert reply['resume']==demo
            assert serve.read(path)==demo
            assert len(list((workspace/'history').iterdir()))==1
            hidden=copy.deepcopy(demo);hidden['sections'][0]['items'].append({'title':'隐藏测试项','subtitle':'私密草稿','period':'','bullets':[],'hidden':True})
            expect_hidden_filtered=True
            serve.run_agent(workspace,{'resume':hidden,'prompt':'润色','history':[]})
            serve.run_agent(workspace,{'resume':demo,'prompt':'整理','mode':'replace','source_text':'仅测试材料','history':[{'role':'user','content':'旧会话'}]})
            assert serve.read(path)==demo
            try:serve.run_agent(workspace,{'resume':demo,'prompt':'整理','mode':'merge','source_text':' '})
            except ValueError:pass
            else:raise AssertionError('Empty paste accepted')
    with tempfile.TemporaryDirectory() as d:
        state={'resume':copy.deepcopy(demo),'presentation':{'template':'classic','density':'comfortable'},'memory':{'source_text':'原始素材','history':[{'role':'user','content':'突出项目'}]}}
        library=Library(Path(d),serve.validate,lambda p:None)
        first=library.create('后端实习',state)
        version=library.archive(first['id'],'初稿',first['revision'])
        state['resume']['profile']['name']='修改后的姓名'
        saved=library.save(first['id'],state,first['revision'])
        try:library.save(first['id'],state,first['revision'])
        except Conflict:pass
        else:raise AssertionError('Stale tab overwrote draft')
        reopened=Library(Path(d),serve.validate,lambda p:None)
        assert reopened.active()['state']['memory']==state['memory']
        assert reopened.active()['state']['resume']['profile']['name']=='修改后的姓名'
        second=library.create('另一岗位',state)
        assert len(library.list())==2
        try:library.version(second['id'],version)
        except ValueError:pass
        else:raise AssertionError('Version leaked across documents')
        restored=library.restore(first['id'],version,saved['revision'])
        assert restored['state']['resume']==demo
        assert library.version(first['id'],library.versions(first['id'])[0]['id'])['state']['resume']['profile']['name']=='修改后的姓名'
        assert library.open(second['id'])['state']['resume']['profile']['name']=='修改后的姓名'
        assert library.open(first['id'])['revision']==restored['revision']
        switched=library.activate_version(first['id'],version,restored['revision'],'切换前自动存档')
        assert switched['state']['resume']==demo
        assert switched['state']['memory']['active_version_id']==version
        assert any(v['label']=='切换前自动存档' for v in library.versions(first['id']))
    print('PASS: validation, CLI adapter (mock), persistent draft/memory, independent documents, immutable versions, restore backup and stale-write conflict.')
if __name__=='__main__':main()
