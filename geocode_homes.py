import csv,io,json,time,requests
rows=list(csv.DictReader(open('/workspace/house-hunting/zillow_for_sale.csv')))
buf=io.StringIO();w=csv.writer(buf)
for i,r in enumerate(rows): w.writerow([i,r['address'],r['city'],r['state'],r['zip']])
res=requests.post('https://geocoding.geo.census.gov/geocoder/locations/addressbatch',
  files={'addressFile':('a.csv',buf.getvalue(),'text/csv')},data={'benchmark':'Public_AR_Current'},timeout=300).text
got={}
for l in csv.reader(io.StringIO(res)):
    if len(l)>5 and l[2]=='Match': x,y=map(float,l[5].split(',')); got[int(l[0])]=(x,y,'census')
UA={'User-Agent':'house-hunting-map/1.0 (personal project; SilkyMS@users.noreply.github.com)'}
fail=[]
for i,r in enumerate(rows):
    if i in got: continue
    for q in (f"{r['address']}, {r['city']}, {r['state']} {r['zip']}", f"{r['address']}, {r['zip']}, USA"):
        time.sleep(1.1); j=requests.get('https://nominatim.openstreetmap.org/search',params={'q':q,'format':'json','limit':1,'countrycodes':'us'},headers=UA,timeout=30).json()
        if j: got[i]=(float(j[0]['lon']),float(j[0]['lat']),'nominatim'); break
    else: fail.append(f"{r['list']}: {r['address']}, {r['city']}, {r['state']} {r['zip']}")
na=lambda v:'not available' if v.strip() in ('--','') else v.strip()
feats=[{'type':'Feature','geometry':{'type':'Point','coordinates':[round(got[i][0],6),round(got[i][1],6)]},
 'properties':{**{k:na(r[k]) for k in r},'geocoder':got[i][2]}} for i,r in enumerate(rows) if i in got]
json.dump({'type':'FeatureCollection','features':feats},open('assets/homes.geojson','w'))
open('geocode_failures.txt','w').write('\n'.join(fail)+'\n')
print(len(feats),'ok;',sum(v[2]=='census' for v in got.values()),'census; failures:',fail)
