"""Transactional private resume library, separate from reusable skill assets."""
import json
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

class Conflict(ValueError):
    pass

def now():
    return datetime.now(timezone.utc).isoformat()

class Library:
    def __init__(self, workspace, validate, presentation_valid):
        self.workspace=Path(workspace)
        self.validate=validate
        self.presentation_valid=presentation_valid
        self.path=self.workspace/'studio.sqlite3'
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS documents (
              id TEXT PRIMARY KEY, name TEXT NOT NULL, state TEXT NOT NULL,
              revision INTEGER NOT NULL, updated TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS versions (
              id TEXT PRIMARY KEY, document_id TEXT NOT NULL, label TEXT NOT NULL,
              state TEXT NOT NULL, created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            ''')
        self.path.chmod(0o600)
    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path, timeout=10)
        db.row_factory=sqlite3.Row
        try:
            with db:yield db
        finally:db.close()
    def check(self, state):
        if not isinstance(state,dict) or set(state)!={'resume','presentation','memory'}:
            raise ValueError('草稿需包含内容、模板与会话记忆')
        self.validate(state['resume']);self.presentation_valid(state['presentation'])
        memory=state['memory']
        if not isinstance(memory,dict):raise ValueError('会话记忆无效')
        allowed={'history','source_text','paste_goal','paste_mode','prompt','model','candidate','base','active_version_id'}
        if set(memory)-allowed:raise ValueError('未知的会话记忆字段')
        for key in ('source_text','paste_goal','prompt','model','base'):
            if not isinstance(memory.get(key,''),str):raise ValueError('会话文字字段无效')
        if memory.get('paste_mode','replace') not in ('replace','merge'):raise ValueError('整理模式无效')
        history=memory.get('history',[])
        if not isinstance(history,list) or len(history)>100:raise ValueError('最多保留最近 100 条会话')
        for message in history:
            if not isinstance(message,dict) or message.get('role') not in ('user','assistant') or not isinstance(message.get('content'),str):raise ValueError('会话消息无效')
        if memory.get('candidate') is not None:self.validate(memory['candidate'])
        return json.dumps(state,ensure_ascii=False)
    def name(self, value):
        if not isinstance(value,str) or not value.strip() or len(value)>120:raise ValueError('名称需为 1–120 个字符')
        return value.strip()
    def row(self, db, doc_id):
        row=db.execute('SELECT * FROM documents WHERE id=?',(doc_id,)).fetchone()
        if row is None:raise ValueError('简历不存在')
        return row
    def document(self,row):
        return {'id':row['id'],'name':row['name'],'state':json.loads(row['state']),'revision':row['revision'],'updated':row['updated']}
    def list(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT id,name,revision,updated FROM documents ORDER BY updated DESC')]
    def active(self):
        with self.connect() as db:
            row=db.execute("SELECT value FROM settings WHERE key='active'").fetchone()
            return self.document(self.row(db,row['value'])) if row else None
    def create(self,name,state):
        payload=self.check(state); name=self.name(name);doc_id=secrets.token_hex(12)
        with self.connect() as db:
            db.execute('INSERT INTO documents VALUES (?,?,?,?,?)',(doc_id,name,payload,1,now()))
            db.execute("INSERT OR REPLACE INTO settings VALUES ('active',?)",(doc_id,))
            return self.document(self.row(db,doc_id))
    def open(self,doc_id):
        with self.connect() as db:
            result=self.document(self.row(db,doc_id))
            db.execute("INSERT OR REPLACE INTO settings VALUES ('active',?)",(doc_id,))
            return result
    def expected(self,row,revision):
        if type(revision) is not int or row['revision']!=revision:raise Conflict('此简历已被另一页面修改；请先导出当前内容，再刷新读取最新草稿。')
    def save(self,doc_id,state,revision,name=None):
        payload=self.check(state)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=self.row(db,doc_id);self.expected(row,revision)
            name=self.name(name) if name is not None else row['name']
            db.execute('UPDATE documents SET state=?,name=?,revision=revision+1,updated=? WHERE id=?',(payload,name,now(),doc_id))
            return self.document(self.row(db,doc_id))
    def versions(self,doc_id):
        with self.connect() as db:
            self.row(db,doc_id)
            return [dict(r) for r in db.execute('SELECT id,label,created FROM versions WHERE document_id=? ORDER BY rowid DESC',(doc_id,))]
    def snapshot(self,db,doc_id,label,payload):
        version_id=secrets.token_hex(12)
        db.execute('INSERT INTO versions VALUES (?,?,?,?,?)',(version_id,doc_id,self.name(label),payload,now()))
        return version_id
    def archive(self,doc_id,label,revision):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=self.row(db,doc_id);self.expected(row,revision)
            return self.snapshot(db,doc_id,label,row['state'])
    def version(self,doc_id,version_id):
        with self.connect() as db:
            row=db.execute('SELECT * FROM versions WHERE id=? AND document_id=?',(version_id,doc_id)).fetchone()
            if row is None:raise ValueError('存档不存在')
            return {'id':row['id'],'label':row['label'],'state':json.loads(row['state']),'created':row['created']}
    def restore(self,doc_id,version_id,revision):
        version=self.version(doc_id,version_id)
        payload=self.check(version['state'])
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=self.row(db,doc_id);self.expected(row,revision)
            self.snapshot(db,doc_id,'恢复前的草稿',row['state'])
            db.execute('UPDATE documents SET state=?,revision=revision+1,updated=? WHERE id=?',(payload,now(),doc_id))
            return self.document(self.row(db,doc_id))

    def activate_version(self,doc_id,version_id,revision,label):
        label=self.name(label)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            current=self.row(db,doc_id);self.expected(current,revision)
            selected=db.execute('SELECT state FROM versions WHERE id=? AND document_id=?',(version_id,doc_id)).fetchone()
            if selected is None:raise ValueError('存档不存在')
            # Preserve the state being left as an ordinary timestamped archive.
            self.snapshot(db,doc_id,label,current['state'])
            restored=json.loads(selected['state'])
            restored.setdefault('memory',{})['active_version_id']=version_id
            payload=self.check(restored)
            db.execute('UPDATE documents SET state=?,revision=revision+1,updated=? WHERE id=?',(payload,now(),doc_id))
            db.execute("INSERT OR REPLACE INTO settings VALUES ('active',?)",(doc_id,))
            return self.document(self.row(db,doc_id))
