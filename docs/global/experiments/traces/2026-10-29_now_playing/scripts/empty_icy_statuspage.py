import json,re,urllib.parse as U,concurrent.futures as cf,sys,socket
socket.setdefaulttimeout(6)
sys.path.insert(0,'np'); import np_adapters as A
R=[json.loads(l) for l in open('e3_raw.jsonl')]
def t(r): return (r['icy_titles'] or [None])[0]
emp=[r for r in R if r['meta']['stratum']=='uniform_ok' and r['ok'] and r.get('transport')=='progressive' and 'icy-metaint' in r['icy'] and not t(r)]
def probe(r):
    p=U.urlparse(r['final_url']); o=f"{p.scheme}://{p.netloc}"; out={}
    for nm,fn,cfg in (("icecast",A.icecast,{"origin":o,"path":p.path}),("shoutcast",A.shoutcast,{"origin":o})):
        try:
            x=fn(cfg); out[nm]=(x or {}).get('title') and A.split_combined(x)['title']
        except Exception as e: out[nm]=None
    return r['meta']['rb_name'][:25],out
with cf.ThreadPoolExecutor(32) as ex: res=list(ex.map(probe,emp))
got=[r for r in res if r[1]['icecast'] or r[1]['shoutcast']]
json.dump({"n":len(emp),"got":len(got),"examples":got[:15]},open('np/empty_icy_statuspage.json','w'),ensure_ascii=False,indent=1)
