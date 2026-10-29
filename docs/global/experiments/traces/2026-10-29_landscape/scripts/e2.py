import json, collections as C, urllib.parse as U
d=json.load(open('rb_all.json'))
N=len(d); print("total",N)
ok=[s for s in d if s['lastcheckok']==1]; print("lastcheckok=1",len(ok),"=0",N-len(ok))
def tab(name,f,rows,top=15):
    c=C.Counter(f(s) for s in rows)
    print(f"\n{name} (n={len(rows)})")
    for k,v in c.most_common(top): print(f"  {str(k):28} {v:6} {100*v/len(rows):5.1f}%")
for lbl,rows in (("ALL",d),("OK",ok)):
    print("\n=====",lbl)
    tab("codec",lambda s:(s['codec'] or '?').upper(),rows,12)
    tab("hls",lambda s:s['hls'],rows)
    tab("scheme(url_resolved)",lambda s:U.urlparse(s['url_resolved'] or s['url']).scheme,rows)
    tab("ssl_error",lambda s:s['ssl_error'],rows)
    tab("bitrate bucket",lambda s:(0 if not s['bitrate'] else 32 if s['bitrate']<=32 else 64 if s['bitrate']<=64 else 96 if s['bitrate']<=96 else 128 if s['bitrate']<=128 else 192 if s['bitrate']<=192 else 320 if s['bitrate']<=320 else 999),rows)
    tab("has_extended_info",lambda s:s['has_extended_info'],rows)
    tab("url ext/path hint",lambda s:('m3u8' if '.m3u8' in s['url_resolved'].lower() else 'pls' if '.pls' in s['url'].lower() else 'm3u' if s['url'].lower().endswith('.m3u') else 'asx' if '.asx' in s['url'].lower() else 'port-in-url' if U.urlparse(s['url_resolved']).port else 'other'),rows)
tab("country (OK)",lambda s:s['countrycode'],ok,12)
tab("language (OK)",lambda s:s['language'].split(',')[0].lower(),ok,10)
host=lambda s:(U.urlparse(s['url_resolved'] or s['url']).hostname or '')
tab("host (OK)",host,ok,30)
# registrable-ish domain
def dom(s):
    h=host(s).split('.'); return '.'.join(h[-2:]) if len(h)>1 else h[0]
tab("domain (OK)",dom,ok,30)
print("\ndistinct hosts OK:",len({host(s) for s in ok}),"distinct domains:",len({dom(s) for s in ok}))
# ports
tab("port (OK)",lambda s:U.urlparse(s['url_resolved']).port,ok,15)
tab("tags(OK)",lambda s:'',ok,1)
tc=C.Counter(t.strip().lower() for s in ok for t in s['tags'].split(',') if t.strip()); print("\ntop tags",tc.most_common(25))
# age of last check
import datetime
print("\nlastchecktime year-month (all)",C.Counter(s['lastchecktime'][:7] for s in d).most_common(6))
# broken but recently ok
print("broken w/ lastcheckoktime in 2026:",sum(1 for s in d if s['lastcheckok']==0 and s['lastcheckoktime'] and s['lastcheckoktime'][:4]=='2026'))
print("dup url_resolved among OK:",len(ok)-len({s['url_resolved'] for s in ok}))
print("votes>0 OK:",sum(1 for s in ok if s['votes']>0),"clickcount>0:",sum(1 for s in ok if s['clickcount']>0))
