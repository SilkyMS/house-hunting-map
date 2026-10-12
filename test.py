from playwright.sync_api import sync_playwright
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1140,'height':720})
    pg.on('console',lambda m: errs.append(m.text) if m.type=='error' else None); pg.on('pageerror',lambda e: errs.append(str(e)))
    pg.goto('http://localhost:8765/iframe_test_page.html'); fr=pg.frame_locator('#f')
    pg.frames[1].wait_for_function('window.mapReady===true',timeout=20000); pg.wait_for_timeout(2500)
    pg.screenshot(path='iframe_test.png')
    f=pg.frames[1]; f.select_option('#county','ct-fairfield'); pg.wait_for_timeout(2000)
    f.evaluate("""()=>{for(const l of Object.values(map._layers)){if(l.feature&&l.feature.properties.label==='Darien'){l.openPopup();return}}}""")
    pg.wait_for_timeout(1200); pg.screenshot(path='popup_test.png')
    print('popup:',f.inner_text('.leaflet-popup-content')); b.close()
print('ERRORS:',errs)
