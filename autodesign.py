"""Local, explicit and reversible asset workflow."""
import argparse, hashlib, io, json, os, shutil, subprocess, uuid, webbrowser
from pathlib import Path
import requests
from PIL import Image

class Workflow:
    def __init__(self, root):
        self.root=Path(root).resolve(); self.store=self.root/'.autodesign'
        self.store.mkdir(exist_ok=True)
        self.manifest=self.store/'manifest.json'
        self.data=json.loads(self.manifest.read_text()) if self.manifest.exists() else {'assets':[], 'history':[]}
    def save(self):
        tmp=self.manifest.with_suffix('.tmp'); tmp.write_text(json.dumps(self.data,ensure_ascii=False,indent=2),encoding='utf-8'); tmp.replace(self.manifest)
    def safe(self, name):
        p=(self.root/name).resolve()
        if not p.is_relative_to(self.root): raise ValueError('Path outside project')
        return p
    def search(self, query, provider='pexels', count=6, mode='review', role='hero'):
        count=max(1,min(count,20))
        if provider=='pexels':
            key=os.environ.get('PEXELS_API_KEY')
            if not key: raise ValueError('Set PEXELS_API_KEY')
            r=requests.get('https://api.pexels.com/v1/search',params={'query':query,'per_page':count},headers={'Authorization':key},timeout=30);r.raise_for_status()
            rows=[(x['src']['large'],x['url'],x['photographer'],'https://www.pexels.com/license/') for x in r.json()['photos']]
        else:
            key=os.environ.get('PIXABAY_API_KEY')
            if not key: raise ValueError('Set PIXABAY_API_KEY')
            r=requests.get('https://pixabay.com/api/',params={'key':key,'q':query,'per_page':max(3,count),'safesearch':'true'},timeout=30);r.raise_for_status()
            rows=[(x['largeImageURL'],x['pageURL'],x['user'],'https://pixabay.com/service/license-summary/') for x in r.json()['hits'][:count]]
        for url,source,author,license_url in rows:
            r=requests.get(url,timeout=30,stream=True);r.raise_for_status(); raw=bytearray()
            for chunk in r.iter_content(65536):
                raw.extend(chunk)
                if len(raw)>20_000_000: raise ValueError('Image exceeds 20 MB')
            with Image.open(io.BytesIO(raw)) as im:
                im.thumbnail((1920,1920)); im=im.convert('RGB')
                ident=hashlib.sha256(raw).hexdigest()[:20]
                if any(a['id']==ident for a in self.data['assets']): continue
                status='approved' if mode=='auto' or (mode=='hybrid' and role in ['decoration','texture','background']) else 'pending'
                dest=self.safe(f'assets/{status}/{ident}.jpg');dest.parent.mkdir(parents=True,exist_ok=True);im.save(dest,quality=88)
            self.data['assets'].append(dict(id=ident,path=str(dest.relative_to(self.root)),status=status,query=query,role=role,provider=provider,source=source,author=author,license=license_url,favorite=False))
            self.save()
    def decide(self, ident, status):
        if status not in ['approved','rejected','pending']: raise ValueError('Invalid status')
        a=next(a for a in self.data['assets'] if a['id']==ident)
        old=self.safe(a['path']); new=self.safe(f'assets/{status}/{old.name}');new.parent.mkdir(parents=True,exist_ok=True)
        if old!=new: shutil.copy2(old,new)
        a.update(path=str(new.relative_to(self.root)),status=status);self.save()
    def integrate(self, bindings):
        changes={}
        for b in bindings:
            a=next(a for a in self.data['assets'] if a['id']==b['asset'])
            if a['status']!='approved': raise ValueError('Only approved assets may be integrated')
            p=self.safe(b['file'])
            if p.suffix not in ['.html','.css','.js','.jsx','.ts','.tsx','.wxml','.wxss','.json','.dart']: raise ValueError('Unsupported code file')
            old=changes.get(b['file'],p.read_text(encoding='utf-8'))
            if not b['old'] or b['old'] not in old: raise ValueError('Reference not found')
            ref=os.path.relpath(self.safe(a['path']),p.parent).replace('\\','/')
            changes[b['file']]=old.replace(b['old'],ref)
        ident=uuid.uuid4().hex; checkpoint=self.store/'checkpoints'/ident;checkpoint.mkdir(parents=True)
        history={'id':ident,'files':{}}
        for name,new in changes.items():
            old=self.safe(name).read_text(encoding='utf-8');backup=checkpoint/name;backup.parent.mkdir(parents=True,exist_ok=True);backup.write_text(old,encoding='utf-8')
            history['files'][name]=hashlib.sha256(new.encode()).hexdigest()
        self.data['history'].append(history);self.save()
        for name,new in changes.items(): self.safe(name).write_text(new,encoding='utf-8')
        return ident
    def rollback(self):
        h=self.data['history'][-1]
        for name,digest in h['files'].items():
            if hashlib.sha256(self.safe(name).read_text(encoding='utf-8').encode()).hexdigest()!=digest: raise ValueError('File changed after integration; restore manually from checkpoint')
        for name in h['files']: shutil.copy2(self.store/'checkpoints'/h['id']/name,self.safe(name))
        self.data['history'].pop();self.save()
    def analyze(self):
        extensions={'.html','.wxml','.dart','.tsx','.jsx'}
        pages=[str(p.relative_to(self.root)) for p in self.root.rglob('*') if p.suffix in extensions and not any(x in p.parts for x in ['node_modules','.git','.venv'])][:500]
        report={'pages':pages,'asset_count':len(self.data['assets']),'needs_visual_planning':True,'suggested_roles':['hero','background','illustration','icon']}
        (self.store/'analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');return report

def serve(w,port):
    from flask import Flask, request, jsonify, send_file
    app=Flask(__name__);token=uuid.uuid4().hex
    @app.get('/')
    def index():
        return """<!doctype html><meta charset=utf-8><title>AutoDesign · 素材审核中心</title><style>body{font:16px system-ui;background:#f5f3ed;color:#263c35;padding:40px}button{padding:10px;margin:4px;border:0;border-radius:8px;background:#d7e8dc}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:24px}article{background:white;padding:16px;border-radius:18px}img{width:100%;height:200px;object-fit:cover}</style><h1>AutoDesign / 素材审核中心</h1><p>候选 → 审核 → 正式接入 · 代码替换使用 CLI bindings，支持批量与回滚</p><main></main><script>const token='"""+token+"""';async function load(){let a=await(await fetch('/api/assets')).json();document.querySelector('main').replaceChildren();for(let x of a){let c=document.createElement('article'),im=document.createElement('img');im.src='/image/'+x.id;c.append(im);let p=document.createElement('p');p.textContent=x.query+' · '+x.status;c.append(p);let link=document.createElement('a');link.href=x.source;link.textContent=x.provider+' / '+x.author;link.target='_blank';link.rel='noopener';c.append(link);for(let [s,t] of [['approved','采用'],['rejected','拒绝'],['pending','保留']]){let b=document.createElement('button');b.textContent=t;b.onclick=async()=>{await fetch('/api/decide',{method:'POST',headers:{'Content-Type':'application/json','X-Token':token},body:JSON.stringify({id:x.id,status:s})});load()};c.append(b)}document.querySelector('main').append(c)}}load()</script>"""
    @app.get('/api/assets')
    def assets(): return jsonify(w.data['assets'])
    @app.get('/image/<ident>')
    def image(ident): return send_file(w.safe(next(a['path'] for a in w.data['assets'] if a['id']==ident)))
    @app.post('/api/decide')
    def decide():
        if request.headers.get('X-Token')!=token: return 'Forbidden',403
        try: w.decide(request.json['id'],request.json['status']);return jsonify(ok=True)
        except (ValueError,StopIteration,KeyError): return 'Invalid request',400
    webbrowser.open(f'http://127.0.0.1:{port}');app.run(host='127.0.0.1',port=port,threaded=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--project',default='.');s=p.add_subparsers(dest='command',required=True)
    s.add_parser('analyze');q=s.add_parser('search');q.add_argument('query');q.add_argument('--provider',choices=['pexels','pixabay'],default='pexels');q.add_argument('--count',type=int,default=6);q.add_argument('--mode',choices=['auto','review','hybrid'],default='hybrid');q.add_argument('--role',default='hero')
    q=s.add_parser('serve');q.add_argument('--port',type=int,default=8765)
    q=s.add_parser('integrate');q.add_argument('bindings');s.add_parser('rollback')
    a=p.parse_args();w=Workflow(a.project)
    try:
        if a.command=='analyze': print(json.dumps(w.analyze(),ensure_ascii=False,indent=2))
        elif a.command=='search': w.search(a.query,a.provider,a.count,a.mode,a.role)
        elif a.command=='serve': serve(w,a.port)
        elif a.command=='integrate': print(w.integrate(json.loads(Path(a.bindings).read_text(encoding='utf-8'))))
        elif a.command=='rollback': w.rollback()
    except Exception as e: p.exit(1,f'{type(e).__name__}: operation failed; check configuration and project state.\n')
if __name__=='__main__': main()
