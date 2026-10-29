import json,time,traceback,concurrent.futures as cf
import np_adapters as A
T=json.load(open('targets.json'))
def run(t):
    cfg=dict(t['cfg']); name=cfg.pop('adapter')
    t0=time.time()
    try:
        r=A.split_combined(A.ADAPTERS[name](cfg)); err=None
    except Exception as e: r=None; err=f"{type(e).__name__}: {e}"[:90]
    return t['id'],name,r,err,round(time.time()-t0,2)
with cf.ThreadPoolExecutor(8) as ex: R=list(ex.map(run,T))
now=time.time()
print(f"{'target':32}{'adapter':14}{'kind':12}{'age_s':>7}{'dur':>6}  artist | title | art?")
out=[]
for id_,name,r,err,dt in R:
    if r is None: print(f"{id_[:31]:32}{name:14}{'NONE' if not err else 'ERR':12} {err or ''}"); out.append({"id":id_,"adapter":name,"error":err}); continue
    age=round(now-r['started_at']) if r['started_at'] else None
    print(f"{id_[:31]:32}{name:14}{r['kind']:12}{str(age):>7}{str(round(r['duration']) if r['duration'] else None):>6}  {str(r['artist'])[:22]} | {str(r['title'])[:34]} | {'Y' if r['artwork'] else '-'}")
    out.append({"id":id_,**r,"latency_s":dt})
json.dump(out,open('conformance.json','w'),indent=1,default=str)
