import json, random, urllib.parse as U
random.seed(20261029)
d=json.load(open('rb_all.json'))
def host(s): return U.urlparse(s['url_resolved']).hostname or ''
ok=[s for s in d if s['lastcheckok']==1 and s['url_resolved']]
bad=[s for s in d if s['lastcheckok']==0 and s['url_resolved']]
seen=set(); out=[]
def add(rows,stratum,n):
    pool=[s for s in rows if s['url_resolved'] not in seen]
    random.shuffle(pool)
    c=0
    for s in pool:
        if c>=n: break
        seen.add(s['url_resolved']); c+=1
        out.append({"url":s['url_resolved'],"stratum":stratum,"rb_name":s['name'].strip(),"rb_uuid":s['stationuuid'],"rb_codec":s['codec'],"rb_bitrate":s['bitrate'],"rb_hls":s['hls'],"rb_cc":s['countrycode'],"rb_ok":s['lastcheckok'],"rb_orig_url":s['url']})
add(ok,"uniform_ok",600)
add(bad,"uniform_broken",100)
add([s for s in ok if s['hls']==1],"hls_ok",150)
plats={"zeno":"zeno.fm","streamtheworld":"streamtheworld.com","laut.fm":"laut.fm","iheart":"ihrhls.com","radio.co":"radio.co","live365":"live365.com","streamguys":"streamguys1.com","radioking":"radioking.com","radiojar":"radiojar.com","securenet":"securenetsystems.net","azuracast_hosting":"asurahosting.com","revma":"revma.com","infomaniak":"infomaniak.ch","radioca.st":"radioca.st","fastcast4u":"fastcast4u.com","leanstream":"leanstream.co","cdnstream1":"cdnstream1.com","streamabc":"streamabc.net","myradiostream":"myradiostream.com","akamaized":"akamaized.net","surfernetwork":"surfernetwork.com","mdstrm":"mdstrm.com"}
for name,dom in plats.items():
    add([s for s in ok if host(s).endswith(dom)],"platform:"+name,12)
# playlist-type original urls
pl=[s for s in ok if any(x in s['url'].lower() for x in ('.pls','.m3u','.asx')) and not s['url'].lower().endswith('.m3u8') and '.m3u8' not in s['url'].lower()]
pool=pl[:]; random.shuffle(pool)
c=0
for s in pool[:80]:
    out.append({"url":s['url'],"stratum":"playlist_orig","rb_name":s['name'].strip(),"rb_uuid":s['stationuuid'],"rb_codec":s['codec'],"rb_bitrate":s['bitrate'],"rb_hls":s['hls'],"rb_cc":s['countrycode'],"rb_ok":1,"rb_orig_url":s['url']})
with open('sample.jsonl','w') as f:
    for o in out: f.write(json.dumps(o)+"\n")
import collections
print(len(out), collections.Counter(o['stratum'] for o in out))
