const $=id=>document.getElementById(id);
let resume,presentation,manifest,styles={},token,dirty=false,candidate=null,base='',comparing=false,history=[];
let inlineEditing=false;
let currentDoc=null,autosaveTimer=null,saveQueue=Promise.resolve(),persistedSnapshot='',archivePreview=null,agentRunning=false,libraryChanging=false,activeVersionId='';
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(path,data){const r=await fetch(path,{method:data===undefined?'GET':'POST',headers:{'Content-Type':'application/json','X-Studio-Token':token||''},body:data===undefined?undefined:JSON.stringify(data)});const b=await r.json();if(!r.ok)throw Error(b.error||r.statusText);return b;}
function status(s){$('status').textContent=s;}
function changed(){dirty=true;comparing=false;archivePreview=null;render();status('正在等待自动保存…');remember();}
function documentHTML(data){
 const profile=data.profile;
 const sections=data.sections.map((section,si)=>`<section class="section"><h2 data-path="sections.${si}.title">${esc(section.title)}</h2>${section.items.map((item,ii)=>item.hidden?'':`<div class="item"><div class="item-head"><h3 data-path="sections.${si}.items.${ii}.title">${esc(item.title)}</h3><span class="period" data-path="sections.${si}.items.${ii}.period">${esc(item.period)}</span></div><div class="subtitle" data-path="sections.${si}.items.${ii}.subtitle">${esc(item.subtitle)}</div>${item.bullets.length?`<ul>${item.bullets.map((bullet,bi)=>`<li data-path="sections.${si}.items.${ii}.bullets.${bi}">${esc(bullet)}</li>`).join('')}</ul>`:''}</div>`).join('')}</section>`).join('');
 return `<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>${esc(profile.name)} · 简历</title><style>${styles.base}\n${styles[presentation.template]}\n.inline-edit [contenteditable=\"true\"]{outline:1px dashed #4d89ad;outline-offset:2px;cursor:text}.inline-edit [contenteditable=\"true\"]:focus{outline:2px solid #2879a7;background:#f1f8fc}</style><body class="${presentation.density}"><article class="resume"><header class="profile"><h1 data-path="profile.name">${esc(profile.name)}</h1><div class="headline" data-path="profile.headline">${esc(profile.headline)}</div><div class="contact" data-path="profile.contact">${esc(profile.contact)}</div></header>${profile.summary?`<p class="summary" data-path="profile.summary">${esc(profile.summary)}</p>`:''}${sections}</article></body></html>`;
}
function applyInlineEditing(){
 const frame=$('preview'),enabled=inlineEditing&&!comparing&&!archivePreview&&$('comparison').hidden;
 $('inline-edit').disabled=comparing||!!archivePreview||!$('comparison').hidden;
 $('inline-edit').setAttribute('aria-pressed',String(enabled));
 $('inline-edit').textContent=enabled?'完成直接编辑':'直接编辑简历';
 try{
  const doc=frame.contentDocument;if(!doc)return;
  doc.body.classList.toggle('inline-edit',enabled);
  for(const el of doc.querySelectorAll('[data-path]')){
   el.contentEditable=String(enabled);el.spellcheck=enabled;
   if(!enabled)continue;
   el.onblur=()=>{
    const keys=el.dataset.path.split('.');let target=resume;
    for(const key of keys.slice(0,-1))target=target[(/^\d+$/.test(key)?Number(key):key)];
    const last=keys.at(-1);target[/^\d+$/.test(last)?Number(last):last]=el.innerText.replace(/\n+$/,'');
    changed();
   };
  }
 }catch{}
}

function render(){
 if(!resume)return;
 const split=$('comparison').hidden===false;
 if(split){$('current-preview').srcdoc=documentHTML(resume);$('candidate-preview').srcdoc=documentHTML(candidate||resume);}
 else{
  const frame=$('preview');frame.onload=()=>applyInlineEditing();
  frame.srcdoc=documentHTML(archivePreview||(comparing&&candidate?candidate:resume));
  applyInlineEditing();
 }
 applyInlineEditing();
}
$('inline-edit').onclick=()=>{if(comparing||archivePreview||!$('comparison').hidden)return;inlineEditing=!inlineEditing;applyInlineEditing();status(inlineEditing?'直接编辑已开启：点击文字进行修改':'直接编辑已完成');};

function button(parent,text,fn){const el=document.createElement('button');el.textContent=text;el.onclick=fn;parent.append(el);return el;}
function field(parent,label,value,set,multi=false){const l=document.createElement('label');l.textContent=label;const el=document.createElement(multi?'textarea':'input');el.value=value;if(multi)el.rows=3;el.oninput=()=>{set(el.value);changed();};l.append(el);parent.append(l);}
function fields(){const p=$('fields');p.replaceChildren();for(const [k,l]of Object.entries({name:'姓名',headline:'求职方向',contact:'联系方式',summary:'个人简介'}))field(p,l,resume.profile[k],v=>resume.profile[k]=v,k==='summary');resume.sections.forEach((s,si)=>{const box=document.createElement('div');box.className='edit-section';p.append(box);field(box,'章节标题',s.title,v=>s.title=v);button(box,'上移',()=>{if(si){[resume.sections[si-1],resume.sections[si]]=[s,resume.sections[si-1]];fields();changed();}});button(box,'删除章节',()=>{if(confirm('删除这个章节？')){resume.sections.splice(si,1);fields();changed();}});s.items.forEach((i,ii)=>{const row=document.createElement('div');row.className='edit-item';box.append(row);for(const[k,l]of Object.entries({title:'名称',subtitle:'职位 / 技术栈',period:'时间'}))field(row,l,i[k],v=>i[k]=v);field(row,'要点（每行一条）',i.bullets.join('\n'),v=>i.bullets=v.split('\n').filter(Boolean),true);const hide=button(row,i.hidden?'恢复显示':'在简历中隐藏',()=>{i.hidden=!i.hidden;fields();changed();});hide.setAttribute('aria-pressed',String(!!i.hidden));if(i.hidden){const note=document.createElement('span');note.className='hidden-note';note.textContent='隐藏 · 不显示在预览，也不会发给 Codex';row.append(note);}button(row,'删除条目',()=>{s.items.splice(ii,1);fields();changed();});});button(box,'添加条目',()=>{s.items.push({title:'',subtitle:'',period:'',bullets:[],hidden:false});fields();changed();});});}
function download(name,text,type){const u=URL.createObjectURL(new Blob([text],{type}));const a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}
function message(who,text){const div=document.createElement('div');div.className='bubble';const label=document.createElement('strong');label.textContent=who;div.append(label,document.createTextNode(text));$('messages').append(div);div.scrollIntoView({block:'nearest'});}
function draftState(){return {resume,presentation,memory:{history:history.slice(-100),source_text:$('source-text').value,paste_goal:$('paste-goal').value,paste_mode:$('paste-mode').value,prompt:$('prompt').value,model:$('model').value,candidate,base,active_version_id:activeVersionId}};}
function remember(){if(!currentDoc)return;dirty=true;clearTimeout(autosaveTimer);autosaveTimer=setTimeout(()=>persist().catch(e=>status('保存失败：'+e.message)),700);}
function persist(){
 clearTimeout(autosaveTimer);if(!currentDoc)return Promise.resolve();
 const snapshot=JSON.stringify(draftState()),id=currentDoc.id;
 const task=saveQueue.catch(()=>{}).then(async()=>{
  if(!currentDoc||currentDoc.id!==id)throw Error('简历已切换，请重试保存');
  if(snapshot!==persistedSnapshot){const result=await api('/api/draft',{id,revision:currentDoc.revision,state:JSON.parse(snapshot)});currentDoc=result.document;persistedSnapshot=snapshot;}
  if(JSON.stringify(draftState())===snapshot){dirty=false;status('草稿已自动保存 · '+new Date().toLocaleTimeString());}
 });saveQueue=task;return task;
}
function libraryBusy(value){libraryChanging=value;for(const id of ['document-list','new-document','copy-document','rename-document','archive','export-draft','version-list'])$(id).disabled=value||agentRunning;}
async function refreshLibrary(){
 const b=await api('/api/library/list',{});$('document-list').replaceChildren();
 for(const d of b.documents){const o=document.createElement('option');o.value=d.id;o.textContent=d.name;$('document-list').append(o);}$('document-list').value=currentDoc.id;
 const versions=await api('/api/versions',{id:currentDoc.id});$('version-list').replaceChildren();
 const currentOption=document.createElement('option');currentOption.value='';currentOption.textContent='当前工作版本 · '+currentDoc.name;$('version-list').append(currentOption);
 for(const v of versions.versions){const o=document.createElement('option');o.value=v.id;o.textContent=v.label+' · '+new Date(v.created).toLocaleString();$('version-list').append(o);}
 $('version-list').value=activeVersionId;
}
function loadDocument(doc,versionId=''){
 currentDoc=doc;activeVersionId=versionId||doc.state.memory?.active_version_id||'';({resume,presentation}=doc.state);const m=doc.state.memory||{};
 history=m.history||[];candidate=m.candidate||null;base=m.base||'';comparing=!!candidate;archivePreview=null;
 for(const[id,key]of [['source-text','source_text'],['paste-goal','paste_goal'],['prompt','prompt']])$(id).value=m[key]||'';
 $('paste-mode').value=m.paste_mode||'replace';if(m.model&&[...$('model').options].some(o=>o.value===m.model))$('model').value=m.model;else{$('model').value=$('model').dataset.default||'';if(m.model)$('model-note').textContent='已忽略草稿中 CLI 不支持的模型 '+m.model+'，改用 '+$('model').value+'。当前 ChatGPT 对话和本机 CLI 的模型列表分别配置。';}
 $('template').value=presentation.template;$('density').value=presentation.density;
 $('messages').replaceChildren();for(const h of history)message(h.role==='user'?'你':'Codex',h.content);
 $('candidate').hidden=!candidate;$('compare').textContent='返回当前稿';$('side-by-side').hidden=!candidate;$('comparison').hidden=true;comparing=!!candidate;
 fields();render();persistedSnapshot=JSON.stringify(draftState());dirty=false;document.title=doc.name+' · Resume Studio';status('已恢复草稿与会话');
}
async function libraryAction(fn){if(libraryChanging||agentRunning)return;libraryBusy(true);try{await persist();await fn();await refreshLibrary();}catch(e){status(e.message);$('document-list').value=currentDoc.id;}finally{libraryBusy(false);}}
$('save').onclick=()=>persist().catch(e=>status('保存失败：'+e.message));
function timeLabel(){return new Intl.DateTimeFormat('sv-SE',{timeZone:Intl.DateTimeFormat().resolvedOptions().timeZone,dateStyle:'short',timeStyle:'short'}).format(new Date());}
function archiveLabel(){return currentDoc.name+' · '+timeLabel();}
$('archive').onclick=()=>libraryAction(async()=>{const label=archiveLabel();await api('/api/archive',{id:currentDoc.id,revision:currentDoc.revision,label});activeVersionId='';await refreshLibrary();status('已存档：'+label);});
$('export-draft').onclick=async()=>{try{await persist();const stamp=new Date().toISOString().replace(/[:.]/g,'-');const payload={format:'resume-studio-draft-v1',exportedAt:new Date().toISOString(),name:currentDoc.name,state:draftState()};download(currentDoc.name+'-draft-'+stamp+'.json',JSON.stringify(payload,null,2),'application/json');status('完整草稿已导出');}catch(e){status('导出失败：'+e.message);}};
$('document-list').onchange=()=>{const id=$('document-list').value;libraryAction(async()=>loadDocument((await api('/api/library/open',{id})).document));};
function createDocument(copy){const name=prompt(copy?'复制后的简历名称':'新简历名称');if(!name)return;libraryAction(async()=>{
 const state=copy?draftState():{resume:{version:1,profile:{name:'',headline:'',contact:'',summary:''},sections:[]},presentation:{template:'classic',density:'comfortable'},memory:{}};
 loadDocument((await api('/api/library/create',{name,state})).document);
});}
$('new-document').onclick=()=>createDocument(false);$('copy-document').onclick=()=>createDocument(true);
$('rename-document').onclick=()=>{const name=prompt('简历名称',currentDoc.name);if(name)libraryAction(async()=>loadDocument((await api('/api/draft',{id:currentDoc.id,revision:currentDoc.revision,state:draftState(),name})).document));};
$('version-list').onchange=()=>{const versionId=$('version-list').value;if(!versionId){activeVersionId='';status('当前工作版本');return;}libraryAction(async()=>{const result=await api('/api/activate-version',{id:currentDoc.id,version_id:versionId,revision:currentDoc.revision,label:archiveLabel()});loadDocument(result.document,versionId);status('已切换到存档：'+$('version-list').selectedOptions[0].textContent);});};
for(const id of ['source-text','paste-goal','paste-mode','prompt','model'])$(id).addEventListener('input',remember);
$('template').onchange=()=>{presentation.template=$('template').value;changed();};$('density').onchange=()=>{presentation.density=$('density').value;changed();};
$('add-section').onclick=()=>{resume.sections.push({title:'新章节',items:[]});fields();changed();};
$('json').onclick=()=>download('resume.json',JSON.stringify(resume,null,2),'application/json');$('html').onclick=()=>download('resume.html',documentHTML(resume),'text/html');
$('print').onclick=()=>{comparing=false;render();$('preview').onload=()=>{$('preview').onload=null;$('preview').contentWindow.print();};};
$('import').onclick=()=>$('file').click();$('file').onchange=async e=>{try{const f=e.target.files[0];if(!f)return;const data=JSON.parse(await f.text());await api('/api/validate',{resume:data});if(dirty&&!confirm('导入将替换尚未保存的内容，继续？'))return;resume=data;fields();changed();}catch(err){alert('导入失败：'+err.message);}finally{e.target.value='';}};
function restoreHidden(proposed,original){for(let si=0;si<original.sections.length;si++){const hidden=original.sections[si].items.filter(i=>i.hidden);if(!hidden.length)continue;const target=proposed.sections[si];if(target)target.items.push(...hidden);else proposed.sections.push({title:original.sections[si].title,items:hidden});}return proposed;}
function busy(value){agentRunning=value;for(const id of ['send','organize','check-connection'])$(id).disabled=value;document.body.classList.toggle('agent-busy',value);$('send').setAttribute('aria-busy',String(value));$('send').querySelector('.button-label').textContent=value?'Codex 正在处理':'发送给 Codex';libraryBusy(libraryChanging);}
function connection(text){$('connection').textContent=text;}
async function submitAgent(prompt, extra={}, check=false){
 if(!resume){status('请等待内容载入');return;}
 if(!check&&candidate&&!confirm('本次请求会替换尚未应用的候选稿，继续？'))return;
 if(!check){candidate=null;$('candidate').hidden=true;comparing=false;render();}
 const snapshot=JSON.stringify(resume);archivePreview=null;busy(true);message('你',check?'检查 Codex 连接':prompt);connection('Codex 正在处理…');if(!check){history.push({role:'user',content:prompt});remember();}
 try{
  status('Codex 正在处理…');
  const result=await api('/api/agent',{resume:JSON.parse(snapshot),prompt,model:$('model').value.trim(),history:check?[]:history.slice(-6),...extra});
  connection('已连接 · '+$('model').value);message('Codex',result.message);
  if(!check){history.push({role:'assistant',content:result.message});candidate=result.resume?restoreHidden(result.resume,JSON.parse(snapshot)):null;base=snapshot;$('candidate').hidden=!candidate;$('compare').textContent='返回当前稿';$('side-by-side').hidden=!candidate;comparing=!!candidate;$('comparison').hidden=true;render();}
  if(!check)remember();
  status(check?'Codex 连接正常':candidate?'候选稿已显示，可返回当前稿或并排对比':'Codex 已回复');
 }catch(e){message('请求失败',e.message);connection('连接失败 · '+e.message);status('请求失败，原始内容已保留');}
 finally{busy(false);}
}
$('send').onclick=()=>{const prompt=$('prompt').value.trim();if(prompt)submitAgent(prompt);};
$('organize').onclick=()=>{
 const source=$('source-text').value.trim();if(!source){$('source-text').focus();status('请先粘贴内容');return;}
 const mode=$('paste-mode').value;
 const prompt=(mode==='replace'?'根据粘贴材料生成新简历。':'将粘贴材料合并到当前简历。')+($('paste-goal').value.trim()||'提取事实、梳理结构并润色，缺失信息留空。');
 submitAgent(prompt,{source_text:source,mode});
};
$('check-connection').onclick=()=>submitAgent('连接检查：仅回复“连接正常”，不要修改简历。',{},true);
$('compare').onclick=()=>{archivePreview=null;$('comparison').hidden=true;comparing=false;render();status('当前稿');};
$('side-by-side').onclick=()=>{archivePreview=null;$('comparison').hidden=false;render();status('并排对比：当前稿与候选稿');};
$('apply').onclick=()=>{if(JSON.stringify(resume)!==base){alert('请求后内容已改变，请重新提交，避免覆盖新编辑。');return;}resume=candidate;candidate=null;comparing=false;$('comparison').hidden=true;$('candidate').hidden=true;$('compare').textContent='返回当前稿';$('side-by-side').hidden=true;fields();changed();};
$('discard').onclick=()=>{candidate=null;comparing=false;$('comparison').hidden=true;$('candidate').hidden=true;$('side-by-side').hidden=true;$('compare').textContent='返回当前稿';render();remember();};
window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue='';}});
(async()=>{try{
 const b=await api('/api/state');({resume,presentation,token,manifest}=b);
 const select=$('model');select.replaceChildren();
 for(const m of b.agent.models){const o=document.createElement('option');o.value=m.id;o.textContent=m.name;select.append(o);}
 select.dataset.default=b.agent.default||b.agent.selected||'';
 const savedModel=b.document.state.memory?.model;
 select.value=b.agent.models.some(m=>m.id===savedModel)?savedModel:select.dataset.default;
 $('model-note').textContent='运行环境：'+(b.agent.runtime||'本机')+'。列表来自该环境的 Codex CLI；当前选择可从此简历恢复，和 ChatGPT 对话模型分开。';if(savedModel&&!b.agent.models.some(m=>m.id===savedModel))$('model-note').textContent='草稿保存的模型 '+savedModel+' 不在 '+(b.agent.runtime||'本机')+' CLI 列表中，已切换到 '+(b.agent.models.find(m=>m.id===select.value)?.name||'CLI 推荐模型')+'。当前对话模型与 CLI 模型分别配置。';
 connection(b.agent.status+' · '+(select.value||'无可用模型')+(b.agent.error?' · '+b.agent.error:''));
 for(const t of manifest){const o=document.createElement('option');o.value=t.id;o.textContent=t.name;$('template').append(o);styles[t.id]=await(await fetch('/templates/'+t.file)).text();}
 styles.base=await(await fetch('/templates/base.css')).text();$('storage-location').textContent='本地私有目录：'+b.workspace;
 loadDocument(b.document);await refreshLibrary();
 }catch(e){status('载入失败：'+e.message);}})();
