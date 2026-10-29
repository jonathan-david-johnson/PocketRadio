import json, collections as C, sys
R=[json.loads(l) for l in open('e3_raw.jsonl')]
def tab(name,rows,f,top=14):
    c=C.Counter(f(r) for r in rows); n=len(rows)
    print(f"\n{name} (n={n})")
    for k,v in c.most_common(top): print(f"  {str(k):34}{v:5} {100*v/n:5.1f}%")
def S(r): return r['meta']['stratum']
for lbl,rows in (("uniform_ok",[r for r in R if S(r)=='uniform_ok']),("uniform_broken",[r for r in R if S(r)=='uniform_broken'])):
    print("\n=========",lbl)
    tab("ok",rows,lambda r:r['ok'])
    tab("fail",[r for r in rows if not r['ok']],lambda r:r.get('fail'))
okr=[r for r in R if S(r)=='uniform_ok' and r['ok']]
print("\n========= uniform_ok, successful only")
tab("transport",okr,lambda r:r.get('transport'))
tab("container/codec",okr,lambda r:(r.get('container'),r.get('codec')))
tab("final scheme",okr,lambda r:r['final_scheme'])
tab("status kind",okr,lambda r:r['status_kind'])
tab("has playlist hop",okr,lambda r:r.get('playlist_kind'))
tab("tls verify failed",okr,lambda r:bool(r.get('tls_verify_failed')))
prog=[r for r in okr if r.get('transport')=='progressive']
tab("progressive: icy-metaint present",prog,lambda r:'icy-metaint' in r['icy'])
withicy=[r for r in prog if 'icy-metaint' in r['icy']]
tab("  of those: first title",withicy,lambda r:('empty' if not (r['icy_titles'] and r['icy_titles'][0]) else 'has title'))
tab("progressive: ACAO",prog,lambda r:('*' if r['cors'].get('access-control-allow-origin')=='*' else 'reflect' if r['cors'].get('access-control-allow-origin','').startswith('https://app.pocket') else 'none' if not r['cors'].get('access-control-allow-origin') else 'other'))
tab("progressive: preflight allows icy-metadata",prog,lambda r:('*' if (r.get('preflight_allow_headers') or '')=='*' else 'listed' if 'icy-metadata' in (r.get('preflight_allow_headers') or '').lower() else 'no' if r.get('preflight_allow_headers') is not None else 'no ACAH' ))
tab("ttfb bucket (s)",okr,lambda r:('<0.5' if r['ttfb_s']<.5 else '<1' if r['ttfb_s']<1 else '<2' if r['ttfb_s']<2 else '>=2'))
tab("server header",okr,lambda r:(r.get('server') or '-').split('/')[0][:28],16)
tab("icy-name present",prog,lambda r:'icy-name' in r['icy'])
tab("mp3 bitrate",[r for r in prog if r.get('codec')=='mp3'],lambda r:r.get('bitrate_kbps'))
tab("content-type",okr,lambda r:(r.get('content_type') or '-').split(';')[0].lower())
# hls stratum
H=[r for r in R if S(r)=='hls_ok']
print("\n========= hls_ok stratum")
tab("ok",H,lambda r:r['ok'])
tab("fail",[r for r in H if not r['ok']],lambda r:r.get('fail'))
Hk=[r for r in H if r['ok'] and r.get('transport')=='hls']
tab("ts/m4s/aac",Hk,lambda r:r['hls'].get('segment_ext'))
tab("segment codec",Hk,lambda r:(r['hls'].get('segment_container'),r['hls'].get('segment_codec')))
tab("master",Hk,lambda r:r['hls'].get('master'))
tab("variant codecs",[r for r in Hk if r['hls'].get('variants')],lambda r:tuple(sorted({v.get('codecs') for v in r['hls']['variants']})) ,10)
tab("target duration",Hk,lambda r:r['hls'].get('target_duration'))
tab("PROGRAM-DATE-TIME",Hk,lambda r:r['hls'].get('program_date_time'))
tab("DATERANGE",Hk,lambda r:r['hls'].get('daterange'))
tab("ID3 in last segment",Hk,lambda r:r['hls'].get('id3_tags_in_segment',0)>0)
tab("encryption",Hk,lambda r:r['hls'].get('encryption'))
tab("fMP4 map",Hk,lambda r:r['hls'].get('map_fmp4'))
tab("endlist(VOD)",Hk,lambda r:r['hls'].get('endlist'))
tab("low-latency",Hk,lambda r:r['hls'].get('low_latency'))
tab("hls acao",Hk,lambda r:r['cors'].get('access-control-allow-origin'))
tab("hls id3 frames",[r for r in Hk if r['hls'].get('id3_frames')],lambda r:tuple(r['hls']['id3_frames']))
# playlist_orig stratum
P=[r for r in R if S(r)=='playlist_orig']
print("\n========= playlist_orig")
tab("ok",P,lambda r:r['ok'])
tab("kind",P,lambda r:r.get('playlist_kind'))
tab("fail",[r for r in P if not r['ok']],lambda r:r.get('fail'))
# platform strata
print("\n========= per platform (n=12 each)")
plat=C.defaultdict(list)
for r in R:
    if S(r).startswith('platform:'): plat[S(r)[9:]].append(r)
print(f"{'platform':20}{'n':>3}{'ok':>4}{'icy':>4}{'title':>6}{'http':>5}{'acao*':>6}{'hls':>4}  codecs / servers / fails")
for p,rows in sorted(plat.items()):
    ok=[r for r in rows if r['ok']]
    icy=[r for r in ok if 'icy-metaint' in r.get('icy',{})]
    title=[r for r in icy if r['icy_titles'] and r['icy_titles'][0]]
    http=[r for r in ok if r['final_scheme']=='http']
    ac=[r for r in ok if r['cors'].get('access-control-allow-origin') in ('*',) or str(r['cors'].get('access-control-allow-origin','')).startswith('https://app.pocket')]
    hls=[r for r in ok if r.get('transport')=='hls']
    cod=C.Counter(str(r.get('codec')) for r in ok)
    srv=C.Counter((r.get('server') or '-').split('/')[0][:14] for r in ok)
    fl=C.Counter(r.get('fail') for r in rows if not r['ok'])
    print(f"{p:20}{len(rows):3}{len(ok):4}{len(icy):4}{len(title):6}{len(http):5}{len(ac):6}{len(hls):4}  {dict(cod)} {dict(srv.most_common(2))} {dict(fl)}")
