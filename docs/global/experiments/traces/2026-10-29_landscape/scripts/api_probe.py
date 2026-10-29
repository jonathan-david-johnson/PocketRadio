import json, sys, urllib.request, urllib.error, ssl, time, concurrent.futures as cf
UA="PocketRadio-survey/0.1 (+research)"
def probe(item):
    name,url=item[0],item[1]; hdr=item[2] if len(item)>2 else {}
    h={"User-Agent":UA,"Origin":"https://app.pocketradio.example","Accept":"*/*"}; h.update(hdr)
    t=time.time()
    rec={"name":name,"url":url}
    try:
        req=urllib.request.Request(url,headers=h)
        with urllib.request.urlopen(req,timeout=10) as r:
            body=r.read1(6000)
            rec.update(status=r.status,final=r.geturl(),ct=r.headers.get("content-type"),acao=r.headers.get("access-control-allow-origin"),server=r.headers.get("server"),body=body.decode("utf-8","replace")[:700])
    except urllib.error.HTTPError as e:
        rec.update(status=e.code,ct=e.headers.get("content-type"),acao=e.headers.get("access-control-allow-origin"),body=e.read(400).decode("utf-8","replace")[:300])
    except Exception as e:
        rec.update(status=None,error=f"{type(e).__name__}: {e}"[:200])
    rec["s"]=round(time.time()-t,2)
    return rec
if __name__=="__main__":
    items=json.load(open(sys.argv[1]))
    with cf.ThreadPoolExecutor(16) as ex:
        res=list(ex.map(probe,items))
    with open(sys.argv[2],"w") as f:
        for r in res: f.write(json.dumps(r,ensure_ascii=False)+"\n")
    for r in res:
        b=(r.get("body") or "").replace("\n"," ")[:150]
        print(f"{r['name'][:26]:26} {str(r.get('status')):5} {str(r.get('ct'))[:28]:28} acao={str(r.get('acao'))[:20]:20} {r.get('error','')[:60]} | {b}")
