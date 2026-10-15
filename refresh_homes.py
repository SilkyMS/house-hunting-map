import csv,io,json,re,time,requests
B='/workspace/house-hunting/'
old=json.load(open(B+'homes_old_backup.geojson'))['features']
new=list(csv.DictReader(open(B+'zillow_for_sale_new.csv')))
zp=lambda u:(re.search(r'(\d+)_zpid',u or '') or [None,None])[1]
na_=lambda a:re.sub(r'[^a-z0-9 ]','',a.lower().replace('-',' ')).split()
def nk(a,z):
    ab={'road':'rd','street':'st','avenue':'ave','lane':'ln','drive':'dr','court':'ct','place':'pl','boulevard':'blvd','north':'n','south':'s','east':'e','west':'w'}
    return ' '.join(ab.get(w,w) for w in na_(a))+'|'+z.strip()[:5]
oz={zp(f['properties']['url']):f for f in old}; oa={nk(f['properties']['address'],f['properties']['zip']):f for f in old}
fmt=lambda v,m:'not available' if v.strip() in ('--','') else (('$' if m else '')+f"{int(float(v.replace(',','').replace('$',''))):,}" if re.fullmatch(r'[\d,.$]+',v.strip()) else v.strip())
feats,added,changes,matched,todo=[],[],[],set(),[]
for r in new:
    o=oz.get(zp(r['url'])) or oa.get(nk(r['address'],r['zip']))
    p={'list':r['list'],'status':r['status'],'address':r['address'],'city':r['city'],'state':r['state'],'zip':r['zip'],
       'price':fmt(r['price'],1),'beds':fmt(r['beds'],0),'baths':fmt(r['baths'],0),'sqft':fmt(r['sqft'],0),'url':r['url'].strip() or 'not available'}
    if o:
        matched.add(id(o)); p['geocoder']=o['properties']['geocoder']
        if o['properties']['price']!=p['price']: p['prev_price']=o['properties']['price']; changes.append((r['address'],r['city'],o['properties']['price'],p['price']))
        if o['properties']['list']!=p['list']: changes.append((r['address'],r['city'],'list '+o['properties']['list'],'list '+p['list']))
        feats.append({'type':'Feature','geometry':o['geometry'],'properties':p})
    else: todo.append(p); added.append(p)
removed=[f['properties'] for f in old if id(f) not in matched]
fail=[]
if todo:
    buf=io.StringIO();w=csv.writer(buf)
    for i,p in enumerate(todo): w.writerow([i,p['address'],p['city'],p['state'],p['zip']])
    res=requests.post('https://geocoding.geo.census.gov/geocoder/locations/addressbatch',files={'addressFile':('a.csv',buf.getvalue(),'text/csv')},data={'benchmark':'Public_AR_Current'},timeout=300).text
    got={}
    for l in csv.reader(io.StringIO(res)):
        if len(l)>5 and l[2]=='Match': x,y=map(float,l[5].split(',')); got[int(l[0])]=([round(x,6),round(y,6)],'census')
    UA={'User-Agent':'house-hunting-map/1.0 (personal project; SilkyMS@users.noreply.github.com)'}
    for i,p in enumerate(todo):
        if i not in got:
            time.sleep(1.1); j=requests.get('https://nominatim.openstreetmap.org/search',params={'q':f"{p['address']}, {p['city']}, {p['state']} {p['zip']}",'format':'json','limit':1,'countrycodes':'us'},headers=UA,timeout=30).json()
            if j:
                time.sleep(1.1); rv=requests.get('https://nominatim.openstreetmap.org/reverse',params={'lat':j[0]['lat'],'lon':j[0]['lon'],'format':'json'},headers=UA).json()
                print('NOMINATIM VERIFY',p['address'],p['city'],p['zip'],'->',rv.get('display_name'))
                got[i]=([round(float(j[0]['lon']),6),round(float(j[0]['lat']),6)],'nominatim')
        if i in got: p['geocoder']=got[i][1]; feats.append({'type':'Feature','geometry':{'type':'Point','coordinates':got[i][0]},'properties':p})
        else: fail.append(f"{p['list']}: {p['address']}, {p['city']}, {p['state']} {p['zip']}")
json.dump({'type':'FeatureCollection','features':feats},open('assets/homes.geojson','w'))
open('geocode_failures_refresh.txt','w').write('\n'.join(fail)+'\n')
print('ADDED',[(p['address'],p['city'],p['price'],p['list'],p.get('geocoder')) for p in added])
print('REMOVED',[(p['address'],p['city'],p['price'],p['list']) for p in removed])
print('CHANGES',changes); import collections
print('PINS',len(feats),collections.Counter(f['properties']['list'] for f in feats),'FAIL',fail)
