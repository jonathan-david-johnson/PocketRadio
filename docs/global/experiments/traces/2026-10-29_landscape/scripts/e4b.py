import json, re, random, urllib.parse as U, concurrent.futures as cf, collections as C
from api_probe import probe
random.seed(7)
R=[json.loads(l) for l in open('e3_raw.jsonl')]
P=[r for r in R if r['ok'] and r.get('transport')=='progressive']
def origin(r):
    p=U.urlparse(r['final_url']); return f"{p.scheme}://{p.netloc}"
def fam(r):
    s=(r.get('server') or '').lower(); n=' '.join(r['icy'].values()).lower()
    return 'icecast' if 'icecast' in s else 'shoutcast' if ('shoutcast' in n or 'shoutcast' in s) else 'other'
jobs=[]
ice=[r for r in P if fam(r)=='icecast']; random.shuffle(ice)
for r in ice[:70]: jobs.append(("icecast:status-json",origin(r)+"/status-json.xsl",r))
sc=[r for r in P if fam(r)=='shoutcast']; random.shuffle(sc)
for r in sc[:60]:
    jobs.append(("shoutcast:7.html",origin(r)+"/7.html",r)); jobs.append(("shoutcast:stats-json",origin(r)+"/stats?sid=1&json=1",r))
for r in R:
    if not r['ok']: continue
    u=r['final_url']; h=r['final_host'] or ''
    if 'asurahosting' in h or '/radio.mp3' in u or '/listen/' in u:
        p=U.urlparse(u); jobs.append(("azuracast:api/nowplaying",f"{p.scheme}://{p.hostname}/api/nowplaying",r))
    m=re.search(r'radio\.co/(s[0-9a-f]{9})',u)
    if m: jobs.append(("radio.co:status",f"https://public.radio.co/stations/{m.group(1)}/status",r))
    m=re.search(r'radioking\.com/radio/(\d+)',u)
    if m: jobs.append(("radioking:widget",f"https://api.radioking.io/widget/radio/{m.group(1)}/track/current",r))
    m=re.search(r'(\w+)\.stream\.laut\.fm/(\w[\w-]*)',u)
    if m: jobs.append(("laut.fm:current_song",f"https://api.laut.fm/station/{m.group(2)}/current_song",r))
    m=re.search(r'radiojar\.com/(\w+)',u)
    if m: jobs.append(("radiojar:now_playing",f"https://www.radiojar.com/api/stations/{m.group(1)}/now_playing/",r))
    m=re.search(r'live365.*/(a\d+)',u)
    if m: jobs.append(("live365:station",f"https://api.live365.com/station/{m.group(1)}",r))
    m=re.search(r'live\.streamtheworld\.com(?::\d+)?/([A-Z0-9_]+?)(?:_SC)?(?:\.aac|\.mp3)?$',u)
    if m: jobs.append(("triton:nowplaying",f"https://np.tritondigital.com/public/nowplaying?mountName={re.sub(r'(AAC|_SC)$','',m.group(1))}&numberToFetch=1&eventType=track",r))
    m=re.search(r'ihrhls\.com/(zc\d+)',u)
    if m: jobs.append(("iheart:live-meta",f"https://us.api.iheart.com/api/v3/live-meta/stream/{m.group(1)[2:]}/currentTrackMeta",r))
print(len(jobs),"jobs")
def run(j):
    k,url,r=j; rec=probe((k,url)); rec["stratum"]=r['meta']['stratum']; rec["station"]=r['meta']['rb_name'][:40]
    b=rec.get("body") or ""
    rec["hit"]=bool(rec.get("status")==200 and len(b)>20 and re.search(r'title|song|artist|current|track|nowplaying|now_playing|"streams?"|icestats|<HTML|\d+,\d+,\d+',b,re.I) and not b.lstrip().lower().startswith('<!doctype'))
    return rec
with cf.ThreadPoolExecutor(24) as ex: out=list(ex.map(run,jobs))
with open('e4b_raw.jsonl','w') as f:
    for o in out: f.write(json.dumps(o,ensure_ascii=False)+"\n")
t=C.defaultdict(lambda:[0,0,0,0,0])
for o in out:
    x=t[o['name']]; x[0]+=1; x[1]+=o['hit']; x[2]+= (o.get('status')==200); x[3]+=(o.get('acao')=='*' or str(o.get('acao','')).startswith('https://app.pocket')); x[4]+=(o.get('status') is None)
print(f"{'endpoint':28}{'tried':>6}{'hit':>5}{'200':>5}{'cors':>6}{'neterr':>7}")
for k,v in sorted(t.items()): print(f"{k:28}{v[0]:6}{v[1]:5}{v[2]:5}{v[3]:6}{v[4]:7}")
for k in t:
    ex_=[o for o in out if o['name']==k and o['hit']][:1]
    for o in ex_: print("\n",k,o['url'],"\n   ",(o['body'] or '').replace('\n',' ')[:330])
