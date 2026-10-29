import json,re,urllib.parse as U,random
random.seed(3)
E3=[json.loads(l) for l in open('../e3_raw.jsonl')]
E4=[json.loads(l) for l in open('../e4b_raw.jsonl')]
def useful(o):
    b=o.get('body') or ''; n=o['name']
    if o.get('status')!=200: return False
    if n=='triton:nowplaying': return '<nowplaying-info ' in b
    if n=='radiojar:now_playing': return bool(re.search(r'"title": "(?!-?")[^"]+"',b))
    if n=='laut.fm:current_song': return '"title"' in b
    if n=='radio.co:status': return '"current_track"' in b
    if n=='icecast:status-json': return '"icestats"' in b
    if n.startswith('shoutcast:7'): return bool(re.search(r'<body>\d+,\d+,\d+,\d+,\d+,\d+,',b))
    if n.startswith('azuracast'): return b.startswith('[{"station"')
    return False
by={}
for r in E3:
    if r['ok']: by.setdefault((r['meta']['stratum'],r['meta']['rb_name'][:40]),r)
T=[]
def stream_of(o):
    r=by.get((o['stratum'],o['station']))
    return r['final_url'] if r else None
cnt={}
for o in E4:
    if not useful(o): continue
    n=o['name']; s=stream_of(o)
    if not s: continue
    k=n.split(':')[0]
    if cnt.get(k,0)>=3: continue
    p=U.urlparse(o['url']); cfg=None
    if n.startswith('azuracast'):
        m=re.search(r'/listen/([^/]+)/',s)
        cfg={"adapter":"azuracast","api":o['url'],"shortcode":m.group(1) if m else None}
        if not m: continue
    elif n.startswith('laut'):
        cfg={"adapter":"laut","name":o['url'].split('/station/')[1].split('/')[0]}
    elif n.startswith('radio.co'):
        cfg={"adapter":"radioco","sid":o['url'].split('/stations/')[1].split('/')[0]}
    elif n.startswith('triton'):
        cfg={"adapter":"triton","mount":U.parse_qs(p.query)['mountName'][0]}
    elif n.startswith('radiojar'):
        cfg={"adapter":"radiojar","id":o['url'].split('/stations/')[1].split('/')[0]}
    elif n.startswith('icecast'):
        cfg={"adapter":"icecast","origin":f"{p.scheme}://{p.netloc}","path":U.urlparse(s).path}
    elif n.startswith('shoutcast:7'):
        cfg={"adapter":"shoutcast","origin":f"{p.scheme}://{p.netloc}"}
    if cfg:
        cnt[k]=cnt.get(k,0)+1
        T.append({"id":f"{k}:{o['station'][:22]}","stream":s,"cfg":cfg})
named=[
 {"id":"somafm:groovesalad","stream":"https://ice1.somafm.com/groovesalad-128-mp3","cfg":{"adapter":"somafm","channel":"groovesalad"}},
 {"id":"radioparadise:main","stream":"https://stream.radioparadise.com/mp3-128","cfg":{"adapter":"radioparadise"}},
 {"id":"kexp","stream":"https://kexp.streamguys1.com/kexp160.aac","cfg":{"adapter":"kexp"}},
 {"id":"kcrw:e24","stream":"https://streams.kcrw.com/e24_mp3","cfg":{"adapter":"kcrw"}},
 {"id":"nts:1","stream":"https://stream-relay-geo.ntslive.net/stream","cfg":{"adapter":"nts","ch":0}},
 {"id":"azuracast:demo","stream":"https://demo.azuracast.com/listen/azuratest_radio/radio.mp3","cfg":{"adapter":"azuracast","api":"https://demo.azuracast.com/api/nowplaying","shortcode":"azuratest_radio"}},
 {"id":"live365:a75642","stream":"https://das-edge11-live365-dal03.cdnstream.com/a75642","cfg":{"adapter":"live365","mount":"a75642"}},
 {"id":"iheart:5162 K-LOVE","stream":"https://stream.revma.ihrhls.com/zc5162","cfg":{"adapter":"iheart","id":5162}},
 {"id":"iheart:6045 Power106","stream":"https://stream.revma.ihrhls.com/zc6045","cfg":{"adapter":"iheart","id":6045}},
 {"id":"radioking:416299","stream":"https://listen.radioking.com/radio/416299/stream/469240","cfg":{"adapter":"radioking","id":416299}},
 {"id":"airtime:dublab","stream":"https://dublab.out.airtime.pro/dublab_a","cfg":{"adapter":"airtime","host":"dublab.airtime.pro"}},
 {"id":"npr_composer:KUTX","stream":"https://streams.kut.org/4428_192.mp3","cfg":{"adapter":"npr_composer","ucs":"50ef24ebe1c8a1369593d032","tz":"America/Chicago"}},
 {"id":"sr:P3","stream":"https://http-live.sr.se/p3-mp3-192","cfg":{"adapter":"sr","channel":164}},
 {"id":"abc:triplej","stream":"https://abc.streamguys1.com/live/triplej/icecast.audio","cfg":{"adapter":"abc","station":"triplej"}},
 {"id":"radiofrance:FIP","stream":"https://icecast.radiofrance.fr/fip-midfi.mp3","cfg":{"adapter":"radiofrance","id":7}},
 {"id":"npo:radio2","stream":"https://icecast.omroep.nl/radio2-bb-mp3","cfg":{"adapter":"npo"}},
 {"id":"tunein:KCSB","stream":"https://kcsb.streamguys1.com/live","cfg":{"adapter":"tunein","id":"s32156"}},
]
T=named+T
json.dump(T,open('targets.json','w'),indent=1); print(len(T))
for t in T: print(t['id'],t['stream'][:70])
