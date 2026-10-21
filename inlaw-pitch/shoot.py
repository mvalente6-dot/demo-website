"""Screenshot every scene beat and slide at TV (1920x1080) and laptop (1440x900) sizes; print self-test results."""
import sys, os, asyncio
from playwright.async_api import async_playwright
OUT = sys.argv[1] if len(sys.argv) > 1 else 'shots'
os.makedirs(OUT, exist_ok=True)
URL = 'file://' + os.path.abspath('pitch.html')
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium', args=['--autoplay-policy=no-user-gesture-required'])
        for name, (w, h) in {'tv': (1920, 1080), 'laptop': (1440, 900)}.items():
            pg = await b.new_page(viewport={'width': w, 'height': h})
            errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
            await pg.goto(URL); await pg.wait_for_timeout(800)
            res = await pg.evaluate('window.__selftest && window.__selftest.summary')
            print(f'== {name} {w}x{h}\n{res}\nerrors: {errs}')
            await pg.screenshot(path=f'{OUT}/{name}-start.png')
            n = await pg.evaluate('DATA.scenes.length')
            for i in range(n):
                nb = await pg.evaluate(f'DATA.scenes[{i}].beats.length')
                beats = range(nb) if name == 'tv' else [nb - 1]
                for bt in beats:
                    await pg.evaluate(f'window.__show({i},{bt})'); await pg.wait_for_timeout(1500 if name == 'tv' else 900)
                    await pg.screenshot(path=f'{OUT}/{name}-scene{i+1}-b{bt+1}.png')
            ns = await pg.evaluate('document.querySelectorAll(".slide").length')
            for i in range(ns):
                await pg.evaluate(f'window.__slide({i})'); await pg.wait_for_timeout(1000)
                await pg.screenshot(path=f'{OUT}/{name}-slide{i+1}.png')
            await pg.close()
        await b.close()
asyncio.run(main())
