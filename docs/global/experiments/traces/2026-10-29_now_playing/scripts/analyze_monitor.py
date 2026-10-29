import json,re,sys,statistics as S,collections as C,unicodedata
E=[json.loads(l) for l in open(sys.argv[1])]
start=next(e for e in E if e.get('ev')=='start')['t']
def norm(s): 
    s=unicodedata.normalize('NFKD',s or '').encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+',' ',s).strip()
by=C.defaultdict(lambda:{'api':[],'icy':[],'err':C.Counter()})
for e in E:
    if 'id' not in e: continue
    if e['ev']=='change': by[e['id']][e['src']].append(e)
    elif e['ev'] in('error','noicy'): by[e['id']]['err'][(e['src'],e['ev'])]+=1
rows=[]; allpub=[]; alllag=[]
print(f"{'target':32}{'apiΔ':>5}{'icyΔ':>5} {'pub lag s (API first-seen − stamp)':>36} {'ICY − API s (matched)':>24}  notes")
for id_,d in sorted(by.items()):
    api=d['api'][1:] if d['api'] else []   # skip initial state
    icy=d['icy']; icy_after=[x for x in icy if not x.get('first')]
    pub=[e['t']-e['started_at'] for e in api if e.get('started_at') and e.get('kind')=='song' and 0<=e['t']-e['started_at']<900]
    lag=[]
    for a in api:
        if a.get('kind') not in ('song',): continue
        na=norm(a.get('title')); nar=norm(a.get('artist'))
        if len(na)<3: continue
        for i in icy_after:
            ni=norm(i.get('title'))
            if na and na in ni and (not nar or nar.split(' ')[0] in ni or True):
                dt=i['t']-a['t']
                if abs(dt)<400: lag.append(dt); break
    allpub+=pub; alllag+=lag
    f=lambda L:(f"n={len(L)} med={S.median(L):6.0f} min={min(L):5.0f} max={max(L):5.0f}" if L else "-")
    notes=[]
    if d['err']: notes.append(str(dict((f"{k[0]}:{k[1]}",v) for k,v in d['err'].items())))
    if not icy: notes.append("no ICY events")
    elif all(not (x.get('title')) for x in icy): notes.append("ICY title always empty")
    rows.append((id_,len(api),len(icy_after),pub,lag))
    print(f"{id_[:31]:32}{len(api):5}{len(icy_after):5} {f(pub):>36} {f(lag):>24}  {' '.join(notes)}")
print("\nOVERALL publication lag (stamped start -> API shows it):",f"n={len(allpub)} median={S.median(allpub):.0f}s p90={sorted(allpub)[int(.9*len(allpub))]:.0f}s" if allpub else "none")
print("OVERALL ICY-minus-API:",f"n={len(alllag)} median={S.median(alllag):.0f}s  ICY later in {sum(1 for x in alllag if x>0)}/{len(alllag)}" if alllag else "none")
