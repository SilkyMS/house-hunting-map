import json,sys
sys.path.insert(0,'/workspace/house-hunting'); sys.path.insert(0,'.')
import make_maps_v2 as M, geopandas as gpd
from districts import D,NA,COUNTY_MEDIAN
from shapely.geometry import box
c,s,cs,pl,w=M.load()
T=json.load(open('/workspace/house-hunting/towns.json'))
towns,pts,cos=[],[],[]
for key,items in T.items():
    ab,cn=key.split('-',1); fp,stn=M.ST[ab]
    co=c[(c.STATEFP==fp)&(c.NAME.str.lower()==cn)]; assert len(co)==1,key
    cname=f"{co.NAME.iloc[0]} County, {stn}"
    cos.append(gpd.GeoDataFrame({'key':[key],'name':[cname]},geometry=co.geometry.values,crs=M.CRS))
    sub=cs[(cs.STATEFP==fp)&(cs.COUNTYFP==co.COUNTYFP.iloc[0])]
    for it in items:
        if isinstance(it,dict) and 'point' in it:
            n=it['point']; lab=it.get('label',n)
            hit,miss,_=M.match(pl,[n]); assert hit,n
            g=pl.loc[[hit[0]]].geometry.representative_point()
            tgt=pts
        else:
            n=it if isinstance(it,str) else it['name']; lab=n if isinstance(it,str) else it.get('label',n)
            hit,miss,notes=M.match(sub,[n]); assert hit and not miss,(key,n,miss); print(notes) if notes else None
            g=sub.loc[hit].geometry.union_all(); g=gpd.GeoSeries([g],crs=M.CRS); tgt=towns
        d=D[lab]
        tgt.append(gpd.GeoDataFrame({'label':[lab],'county':[key],'cname':[cname],'district':[d[0]],'niche':[d[1]],'commute':[d[2]],'price':[d[3]],'cmed':[COUNTY_MEDIAN.get(key,NA)]},geometry=list(g.values),crs=M.CRS))
def out(gs,f,tol=60):
    g=gpd.pd.concat(gs); g['geometry']=g.geometry.simplify(tol); g.to_crs(4326).to_file(f'assets/{f}.geojson',driver='GeoJSON',COORDINATE_PRECISION=5); print(f,len(g))
out(cos,'counties'); out(towns,'towns'); out(pts,'points',0)
x0,y0,x1,y1=gpd.pd.concat(cos).total_bounds; bb=box(x0-30000,y0-30000,x1+30000,y1+30000)
reg=s[s.STATEFP.isin(list(M.STATE_FILL))].clip(bb); reg['fill']=reg.STATEFP.map(M.STATE_FILL); out([reg[['NAME','fill','geometry']]],'states',150)
ww=w.clip(bb); ww=ww[ww.FULLNAME.fillna('').str.contains('Hudson Riv|Long Island Sound|Atlantic Ocean|Bay|Riv')|(ww.area>3e6)]
ww=ww.dissolve('FULLNAME',dropna=False).reset_index(); out([ww],'water',40)
man=c[(c.STATEFP=='36')&(c.NAME=='New York')]; out([gpd.GeoDataFrame({'name':['Manhattan']},geometry=man.geometry.values,crs=M.CRS)],'manhattan',30)
