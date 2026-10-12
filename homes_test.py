from playwright.sync_api import sync_playwright
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1140,'height':720})
    pg.on('console',lambda m: errs.append(m.text) if m.type=='error' else None); pg.on('pageerror',lambda e: errs.append(str(e)))
    pg.goto('http://localhost:8765/iframe_test_page.html'); fr=pg.frame_locator('#f')
    pg.frames[1].wait_for_function('window.mapReady===true&&window.homesReady===true',timeout=20000); pg.wait_for_timeout(2500)
    pg.screenshot(path='homes_iframe_test.png')
    f=pg.frames[1]; f.select_option('#county','ny-putnam'); pg.wait_for_timeout(2000)
    f.evaluate("""()=>{for(const l of Object.values(map._layers)){if(l.feature&&l.feature.properties.address==='19 Twin Bridges Road'){l.openPopup();return}}}""")
    pg.wait_for_timeout(1200); pg.screenshot(path='homes_test.png')
    print('popup:',f.inner_text('.leaflet-popup-content')); b.close()
print('ERRORS:',errs)
