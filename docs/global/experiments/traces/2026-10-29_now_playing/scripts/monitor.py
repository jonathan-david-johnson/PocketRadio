import json,sys,time,threading,re,importlib.util,socket,urllib.request
sys.path.insert(0,'/tmp/lab/np')
import np_adapters as A
spec=importlib.util.spec_from_file_location("ss","/Users/jdj/code/PocketRadio/tools/source-survey.py"); ss=importlib.util.module_from_spec(spec); spec.loader.exec_module(ss)
T=json.load(open('targets.json'))
T=[t for t in T if '\n' not in t['id']]
zs=[json.loads(l) for l in open('../e3_raw.jsonl')]
for r in zs:
    if r['meta']['stratum']=='platform:zeno' and r['ok'] and 'icy-metaint' in r['icy'] and len([t for t in T if t['id'].startswith('zeno')])<3:
        m=re.search(r'/([a-z0-9]{10,16})(?:\?|$)',r['final_url'])
        if m: T.append({"id":"zeno:"+r['meta']['rb_name'][:18],"stream":r['final_url'],"cfg":{"adapter":"zeno_sse","mount":m.group(1)}})
DUR=float(sys.argv[1]); POLL=float(sys.argv[2]); OUT=open(sys.argv[3],'a'); lock=threading.Lock(); END=time.time()+DUR
def emit(**k):
    k['t']=time.time()
    with lock: OUT.write(json.dumps(k,ensure_ascii=False,default=str)+"\n"); OUT.flush()
def api_loop(t):
    cfg=dict(t['cfg']); name=cfg.pop('adapter'); last=None; errs=0
    if name=='zeno_sse':
        while time.time()<END:
            try:
                req=urllib.request.Request(f"https://api.zeno.fm/mounts/metadata/subscribe/{cfg['mount']}",headers={"User-Agent":A.UA})
                with urllib.request.urlopen(req,timeout=30) as r:
                    emit(id=t['id'],src='api',ev='open')
                    for line in r:
                        if time.time()>END: return
                        line=line.decode('utf-8','replace').strip()
                        if line.startswith('data:'):
                            try: d=json.loads(line[5:])
                            except Exception: continue
                            st=d.get('streamTitle','')
                            if st!=last: last=st; emit(id=t['id'],src='api',ev='change',title=st,artist=None,kind=A.classify(st,None),started_at=None)
            except Exception as e:
                emit(id=t['id'],src='api',ev='error',err=str(e)[:80]); time.sleep(10)
        return
    while time.time()<END:
        try:
            r=A.split_combined(A.ADAPTERS[name](cfg))
            key=(r['title'],r['artist']) if r else None
            if key!=last:
                last=key
                emit(id=t['id'],src='api',ev='change',title=r and r['title'],artist=r and r['artist'],kind=r and r['kind'],started_at=r and r['started_at'],duration=r and r['duration'],stale=A.stale(r))
        except Exception as e:
            errs+=1; emit(id=t['id'],src='api',ev='error',err=f"{type(e).__name__}: {e}"[:80])
        time.sleep(POLL)
def icy_loop(t):
    last=None
    while time.time()<END:
        try:
            url=t['stream']
            for _ in range(5):
                s,st,hd,rest,info=ss.open_conn(url,8)
                if ss.status_code(st) in (301,302,307,308) and 'location' in hd:
                    s.close(); import urllib.parse as U; url=U.urljoin(url,hd['location']); continue
                break
            if ss.status_code(st)!=200 or 'icy-metaint' not in hd: emit(id=t['id'],src='icy',ev='noicy',status=st[:30]); s.close(); return
            emit(id=t['id'],src='icy',ev='open',metaint=hd['icy-metaint'])
            mi=int(hd['icy-metaint']); buf=bytearray(rest); first=True
            s.settimeout(20)
            while time.time()<END:
                while len(buf)<mi+1:
                    c=s.recv(16384)
                    if not c: raise EOFError
                    buf+=c
                n=buf[mi]*16
                while len(buf)<mi+1+n:
                    c=s.recv(16384)
                    if not c: raise EOFError
                    buf+=c
                raw=bytes(buf[mi+1:mi+1+n]).rstrip(b'\0').decode('utf-8','replace'); del buf[:mi+1+n]
                if raw:
                    title=ss.stream_title(raw)
                    if title!=last:
                        last=title; emit(id=t['id'],src='icy',ev='change',title=title,first=first,kind=A.classify(title,None))
                first=False
            s.close(); return
        except Exception as e:
            emit(id=t['id'],src='icy',ev='error',err=f"{type(e).__name__}: {e}"[:80]); time.sleep(10)
th=[]
for t in T:
    th.append(threading.Thread(target=api_loop,args=(t,),daemon=True)); th[-1].start()
    if t['stream']: th.append(threading.Thread(target=icy_loop,args=(t,),daemon=True)); th[-1].start()
    time.sleep(0.15)
emit(ev='start',n=len(T),dur=DUR,poll=POLL)
while time.time()<END: time.sleep(5)
emit(ev='end')
