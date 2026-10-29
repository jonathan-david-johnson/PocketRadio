import json,sys,os,re,time,types,copy,urllib.request
sys.path.insert(0,'/tmp/lab/np')
import np_adapters as A
OUT='/Users/jdj/code/PocketRadio/contracts/now_playing_feed'; os.makedirs(OUT+'/cases',exist_ok=True)
NOW=int(time.time())
def fetch(u,n=3_000_000):
    return urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":A.UA}),timeout=15).read(n).decode('utf-8','replace')
class Fake:
    def __init__(s,now,raws): s.now=now; s.raws=raws
    def time(s): return s.now
def zeno(cfg):
    m=re.search(r'^data:(.*)$',cfg['block'],re.M); d=json.loads(m.group(1)); st=d.get('streamTitle','')
    return A.mk('zeno',st,extra={'combined':True}) if st.strip(' -') else None
A.ADAPTERS['zeno']=zeno
cases=[]
def case(id_,adapter,cfg,raws,desc,now=NOW,content_type='application/json',station='fixture-station'):
    # raws: {url_substring: body}
    def serve(url,**kw):
        for k,v in raws.items():
            if k in url: return v if isinstance(v,str) else json.dumps(v)
        raise RuntimeError('no raw for '+url)
    A.http=lambda url,**kw: serve(url); A.jget=lambda url,**kw: json.loads(serve(url))
    A.time=Fake(now,raws)
    c=dict(cfg); name=c.pop('adapter',adapter)
    try: out=A.ADAPTERS[name](c)
    except Exception as e: print("FAIL",id_,type(e).__name__,e); return
    rec=A.to_record(out,now,station,channel='icy' if name=='icy' else 'api',adapter=name)
    cases.append({"id":id_,"description":desc,"adapter":name,"params":{k:v for k,v in cfg.items() if k!='adapter'},
                  "now":now,"raw":{k:(v if isinstance(v,str) else json.dumps(v,ensure_ascii=False)) for k,v in raws.items()},"expected":rec})
real=lambda u:fetch(u)
# ---------- fetch live bodies (once) ----------
kexp=json.loads(real("https://api.kexp.org/v2/plays/?limit=2")); kexp['results']=kexp['results'][:2]
for r in kexp['results']: r.pop('comment',None)
kcrw=json.loads(real("https://tracklist-api.kcrw.com/Music/all/1?page_size=2"))[:2]
def azt(sc):
    a=json.loads(real(f"https://stream.radios.bzh/api/nowplaying/{sc}")); a={k:a[k] for k in ('station','listeners','live','now_playing')}; a['station']={k:a['station'][k] for k in ('id','name','shortcode','listen_url')}; return a
az=azt('rkb'); azrcf=azt('rcf')
laut=real("https://api.laut.fm/station/odessa/current_song")
rco=json.loads(real("https://public.radio.co/stations/s78f983952/status")); rco['history']=rco['history'][:3]; rco['collaborators']=[]
tri=real("https://np.tritondigital.com/public/nowplaying?mountName=SRGSTR07AAC&numberToFetch=1&eventType=track")
l365=json.loads(real("https://api.live365.com/station/a75642")); l365={k:l365[k] for k in ('mount-id','name','current-track') if k in l365}
rj=real("https://www.radiojar.com/api/stations/5tyqrwpgpfeuv/now_playing/")
ih=real("https://us.api.iheart.com/api/v3/live-meta/stream/6045/currentTrackMeta")
rk=real("https://api.radioking.io/widgets/api/v1/radio/416299/track/current")
at=json.loads(real("https://dublab.airtime.pro/api/live-info-v2")); at['tracks']={k:at['tracks'][k] for k in ('previous','current','next')}
for k in ('previous','current','next'):
    t=at['tracks'][k]
    if t: t['metadata']={x:t['metadata'][x] for x in t.get('metadata',{}) if x in ('track_title','artist_name','album_title','genre')}
at['shows']={k:(at['shows'].get(k)) for k in ('previous','current','next')}
sr=None
for ch in (164,163,132,2576,224):
    x=json.loads(real(f"https://api.sr.se/api/v2/playlists/rightnow?channelid={ch}&format=json"))
    if x['playlist'].get('song'): sr=x; SRCH=ch; break
abc=json.loads(real("https://music.abcradio.net.au/api/v1/plays/search.json?station=triplej&limit=1")); it=abc['items'][0]
abc={"total":abc['total'],"offset":0,"limit":1,"items":[{"entity":"Play","played_time":it['played_time'],"service_id":it['service_id'],"recording":{"title":it['recording']['title'],"duration":it['recording']['duration'],"artists":[{"name":a['name']} for a in it['recording']['artists']],"releases":[{"title":(it['recording']['releases'] or [{}])[0].get('title'),"artwork":[{"url":x['url'],"type":x.get('type')} for x in ((it['recording']['releases'] or [{}])[0].get('artwork') or [])[:1]]}]}}]}
rf=json.loads(real("https://api.radiofrance.fr/livemeta/pull/7")); steps=rf['steps']
cur=[k for k,v in steps.items() if v['start']<=NOW<v['end'] and v.get('embedType')=='song']
keep=cur[-1:]+[k for k in steps if k not in cur][:2]
rf={"stationId":7,"steps":{k:{x:steps[k][x] for x in ('title','start','end','embedType','authors','titreAlbum','visual','stationId') if x in steps[k]} for k in keep}}
npo=json.loads(real("https://www.nporadio2.nl/api/tracks")); npo={"data":[{k:t[k] for k in ('artist','title','startdatetime','enddatetime','image_url_400x400')} for t in npo['data'][:3]]}
npr=json.loads(real("https://api.composer.nprstations.org/v1/widget/50ef24ebe1c8a1369593d032/now?format=json")); on=npr['onNow']
npr={"onNow":{"start_utc":on['start_utc'],"end_utc":on['end_utc'],"program":{"name":on['program']['name'],"ucs":on['program'].get('ucs')},"song":on.get('song')}}
ice=json.loads(real("http://icstream.rds.radio/status-json.xsl")); src=ice['icestats']['source']; src=src if isinstance(src,list) else [src]
ice={"icestats":{"host":"icstream.rds.radio","server_id":ice['icestats']['server_id'],"source":[{k:s[k] for k in ('listenurl','title','server_name','audio_info') if k in s} for s in src[:1]]}}
sc=real("http://usa10.fastcast4u.com:1680/7.html")
# ---------- cases ----------
K="https://api.kexp.org/v2/plays/"
case("kexp__song","kexp",{"adapter":"kexp"},{K:kexp},"KEXP: newest play is a trackplay. Start stamp has an offset.")
kb=copy.deepcopy(kexp); kb['results'][0].update(play_type='airbreak',song=None,artist=None,album=None)
case("kexp__airbreak","kexp",{"adapter":"kexp"},{K:kb},"KEXP: newest row is an airbreak (no song). Shown as 'between'.")
case("kcrw__song","kcrw",{"adapter":"kcrw"},{"tracklist-api.kcrw.com":kcrw},"KCRW: tracklist top entry with programme name.",now=NOW)
case("azuracast__song","azuracast",{"adapter":"azuracast","api":"https://stream.radios.bzh/api/nowplaying","shortcode":"rkb"},{"/api/nowplaying/rkb":az},"AzuraCast per-station endpoint: epoch stamps, duration, artwork.",now=az['now_playing']['played_at']+60)
case("azuracast__placeholder","azuracast",{"adapter":"azuracast","api":"https://stream.radios.bzh/api/nowplaying","shortcode":"rcf"},{"/api/nowplaying/rcf":azrcf},"AzuraCast: station slate ('technical problem') from a real station. Must not reach the UI as a song.",now=azrcf['now_playing']['played_at']+60)
e=az['now_playing']['played_at']+az['now_playing']['duration']
azd=copy.deepcopy(az); azd['now_playing']['duration']=214; azd['now_playing']['elapsed']=214; azd['now_playing']['remaining']=0
e2=azd['now_playing']['played_at']+214
case("azuracast__ended_recently","azuracast",{"adapter":"azuracast","api":"https://stream.radios.bzh/api/nowplaying","shortcode":"rkb"},{"/api/nowplaying/rkb":azd},"AzuraCast (duration set to 214 s by hand): the song ended 5 minutes ago and nothing newer is listed. 'between', not the old title.",now=e2+300)
case("azuracast__with_duration","azuracast",{"adapter":"azuracast","api":"https://stream.radios.bzh/api/nowplaying","shortcode":"rkb"},{"/api/nowplaying/rkb":azd},"AzuraCast (duration set to 214 s by hand): mid-song, so startedAt, durationSec and endsAt are all present.",now=e2-100)
case("azuracast__stale","azuracast",{"adapter":"azuracast","api":"https://stream.radios.bzh/api/nowplaying","shortcode":"rkb"},{"/api/nowplaying/rkb":azd},"AzuraCast (duration set by hand): newest item ended 3 hours ago. 'stale'.",now=e2+10800)
case("laut__song","laut",{"adapter":"laut","name":"odessa"},{"api.laut.fm":laut},"laut.fm: offset stamps without a colon (+0100), artist is an object.",now=NOW)
case("radioco__combined_string","radioco",{"adapter":"radioco","sid":"s78f983952"},{"public.radio.co":rco},"Radio.co: one 'Artist - Title' string, split at the first ' - '.",now=NOW)
rj2=copy.deepcopy(rco); rj2['current_track']['title']="Unknown Artist - XYZ_ID6"
case("radioco__slate","radioco",{"adapter":"radioco","sid":"s78f983952"},{"public.radio.co":rj2},"Radio.co: automation slate 'Unknown Artist - XYZ_ID6'. Suppressed.",now=NOW)
case("triton__song","triton",{"adapter":"triton","mount":"SRGSTR07AAC"},{"np.tritondigital.com":tri},"Triton: XML, epoch milliseconds for start and duration.",now=NOW)
case("triton__empty_list","triton",{"adapter":"triton","mount":"X"},{"np.tritondigital.com":'<?xml version="1.0" encoding="UTF-8"?><nowplaying-info-list></nowplaying-info-list>'},"Triton: 200 with an empty list. 'between'.",now=NOW)
tt=re.sub(r'(<property name="cue_title"><!\[CDATA\[).*?(\]\])',r'\1eng-bodhinatha-veylanswami-kauai-h.mp3\2',tri); 
case("triton__filename","triton",{"adapter":"triton","mount":"X"},{"np.tritondigital.com":tt},"Triton: a file name in place of a title. Suppressed.",now=NOW)
case("live365__song","live365",{"adapter":"live365","mount":"a75642"},{"api.live365.com":l365},"Live365: ISO with fractional seconds and +00:00.",now=NOW)
case("radiojar__song","radiojar",{"adapter":"radiojar","id":"5tyqrwpgpfeuv"},{"radiojar.com/api":rj},"RadioJar: title and artist present; no start stamp, so timing is 'observed'.",now=NOW)
case("radiojar__dash_title","radiojar",{"adapter":"radiojar","id":"x"},{"radiojar.com/api":'{"album": "", "sku": "", "thumb": "", "artist": "", "title": "-", "show": {}, "buy_urls": "", "info_urls": "", "duration": "0", "guid": null}'},"RadioJar: title is just '-'. 'between'.",now=NOW)
case("iheart__song","iheart",{"adapter":"iheart","id":6045},{"live-meta/stream/6045":ih},"iHeart: epoch ms start, duration in seconds, artwork.",now=NOW)
case("iheart__empty_body","iheart",{"adapter":"iheart","id":5162},{"live-meta/stream/5162":""},"iHeart: 200 with an empty body (no track). 'between'.",now=NOW)
case("radioking__song","radioking",{"adapter":"radioking","id":416299},{"widgets/api/v1/radio/416299":rk},"RadioKing: ISO with +0000, duration as a decimal.",now=NOW)
case("airtime__song","airtime",{"adapter":"airtime","host":"dublab.airtime.pro"},{"dublab.airtime.pro":at},"Airtime Pro: times are naive and in the station's zone (station.timezone).",now=NOW)
ab=copy.deepcopy(at); ab['tracks']['current'].update(name=" - 26_Q4_Good_English_Billboard_Style_Meloxicam.mp3",metadata={})
case("airtime__filename","airtime",{"adapter":"airtime","host":"dublab.airtime.pro"},{"dublab.airtime.pro":ab},"Airtime Pro: file name and no tag metadata. Suppressed.",now=NOW)
case("sr__song","sr",{"adapter":"sr","channel":SRCH},{"api.sr.se":sr},"Sveriges Radio: /Date(ms)/ stamps.",now=int(re.search(r"\d+",sr["playlist"]["song"]["starttimeutc"]).group())//1000+30)
sn=copy.deepcopy(sr); sn['playlist'].pop('song',None)
case("sr__no_song","sr",{"adapter":"sr","channel":SRCH},{"api.sr.se":sn},"Sveriges Radio: no current song (talk programme). 'between'.",now=NOW)
case("abc__song","abc",{"adapter":"abc","station":"triplej"},{"music.abcradio.net.au":abc},"ABC: newest play, multiple artists joined, release artwork.",now=int(__import__('datetime').datetime.fromisoformat(abc['items'][0]['played_time']).timestamp())+30)
case("radiofrance__song","radiofrance",{"adapter":"radiofrance","id":7},{"livemeta/pull/7":rf},"Radio France: a tree of steps; choose the song step that spans now.",now=NOW)
from zoneinfo import ZoneInfo
_t0=int(__import__('datetime').datetime.fromisoformat(npo['data'][0]['startdatetime']).replace(tzinfo=ZoneInfo('Europe/Amsterdam')).timestamp())
case("npo__song","npo",{"adapter":"npo"},{"nporadio2.nl/api/tracks":npo},"NPO Radio 2: naive local times (Europe/Amsterdam); leading '#256:' removed from the title.",now=_t0+60)
from datetime import datetime as _dt
from zoneinfo import ZoneInfo as _Z
_st=(_dt.fromtimestamp(NOW-60,_Z('America/Chicago'))).strftime('%m-%d-%Y %H:%M:%S')
nsong=copy.deepcopy(npr); nsong['onNow']['song']={"_start_time":_st,"artistName":"Justice","collectionName":"Hyperdrama","trackName":"Flower in a Hurricane","_duration":223000}
case("npr_composer__song","npr_composer",{"adapter":"npr_composer","ucs":"50ef24ebe1c8a1369593d032","tz":"America/Chicago"},{"composer.nprstations.org":nsong},"NPR Composer (song object added by hand from an earlier live response): start time as MM-DD-YYYY in the station's zone; duration in ms.",now=NOW)
nq=copy.deepcopy(npr); nq['onNow']['song']=None
case("npr_composer__show_only","npr_composer",{"adapter":"npr_composer","ucs":"x","tz":"America/Chicago"},{"composer.nprstations.org":nq},"NPR Composer: no song, only the live programme. Shown as a show with the programme's own start and end.",now=NOW)
case("icecast__song","icecast",{"adapter":"icecast","origin":"http://icstream.rds.radio","path":"/ENI_S1_64"},{"status-json.xsl":ice},"Icecast status page: plain 'Artist - Title' in one field.",now=NOW)
ice2=copy.deepcopy(ice); ice2['icestats']['source'][0]['title']="Song*I'M NOT IN LOVE*10 CC*1975*41"
case("icecast__star_format","icecast",{"adapter":"icecast","origin":"http://icstream.rds.radio","path":"/ENI_S1_64"},{"status-json.xsl":ice2},"Icecast status page: automation format 'Song*TITLE*ARTIST*YEAR*ID' split into fields.",now=NOW)
case("shoutcast__7html","shoutcast",{"adapter":"shoutcast","origin":"http://usa10.fastcast4u.com:1680"},{"7.html":sc},"SHOUTcast 7.html: a comma list; the last field is 'Artist - Title'.",now=NOW)
case("zeno__sse_event","zeno",{"adapter":"zeno","block":'id:1793269678157\nevent:message\ndata:{"mount":"47080zndvbruv","streamTitle":"Ivan Spell - Buddha Bar Sessions 7","streamUrl":"&artist=Ivan Spell&album=Bar Sessions"}\n'},{},"Zeno SSE: one event with a combined title.",now=NOW)
case("zeno__blank_title","zeno",{"adapter":"zeno","block":'event:message\ndata:{"mount":"ud2u96xst5quv","streamTitle":" - "}\n'},{},"Zeno SSE: title is ' - '. 'between'.",now=NOW)
for nm,blk,sn_ in (("artist_title","StreamTitle='Alex Cortiz - Diabla Caliente';",None),("empty","StreamTitle='';",None),("station_echo","StreamTitle='VRT Radio 1';","VRT Radio 1"),("ad_marker","StreamTitle=' - text=\"Spot Block End\" amgTrackId=\"9876543\" length=\"00:00:00\"';",None),("iheart_music","StreamTitle='Tame Impala / Jennie - text=\"Dracula\" song_spot=\"M\" MediaBaseId=\"3164232\" itunesTrackId=\"0\" amgTrackId=\"-1\" TAID=\"0\" amgArtworkURL=\"https://i.iheart.com/v3/catalog/track/377776484?ops=fit(200,200),format(%22jpeg%22)\" length=\"00:03:23\" unsID=\"-1\" spotInstanceId=\"-1\"';",None),("iheart_station_promo","StreamTitle='NY\'s #1 Hit Music Station - text=\"Z100\" song_spot=\"T\" MediaBaseId=\"0\" amgArtworkURL=\"\" length=\"00:00:00\" unsID=\"0\" spotInstanceId=\"-1\"';",None),("stream_url_ignored","StreamTitle='Whats going on';StreamUrl='<!DOCTYPE HTML PUBLIC';",None)):
    case(f"icy__{nm}","icy",{"adapter":"icy","block":blk,"station_name":sn_},{},{"artist_title":"ICY block: Artist - Title in one string.","empty":"ICY block: empty title. 'between'.","station_echo":"ICY block: the title is the station name (VRT Radio 1). Suppressed.","ad_marker":"ICY block: automation ad marker. Suppressed.","stream_url_ignored":"ICY block: StreamUrl holds junk (HTML); only StreamTitle is used.","iheart_music":"ICY block with automation attributes (iHeart): song_spot=M is a song; text is the title, the prefix is the artist, amgArtworkURL is the artwork, length is the duration.","iheart_station_promo":"ICY block with automation attributes: song_spot=T is a station promo, not a song. Suppressed as station_id."}[nm],now=NOW)
json.dump({"generated_at":NOW},open('/tmp/lab/np/fixture_gen.json','w'))
for c in cases:
    json.dump(c,open(f"{OUT}/cases/{c['id']}.json",'w'),indent=2,ensure_ascii=False); open(f"{OUT}/cases/{c['id']}.json",'a').write("\n")
print(len(cases),"cases")
for c in cases:
    e=c['expected']; i=e['item'] or {}
    print(f"{c['id']:28}{e['status']:9}{e['provenance'].get('suppressed',''):12}{e['provenance']['timing']:8} {str(i.get('artist'))[:20]:20}|{str(i.get('title'))[:32]:32}|{str(i.get('startedAt'))[11:19]}|{i.get('durationSec')}|{str(i.get('endsAt'))[11:19]}")
