from playwright.sync_api import sync_playwright
CHROME='/root/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome'
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    pg=b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True).new_page()
    pg.goto('http://127.0.0.1:8899/index.html',wait_until='domcontentloaded'); pg.wait_for_timeout(2200)
    # 跳到一键复习页（page-review），截图短文规则块
    pg.evaluate("()=>{ switchTab('review'); document.querySelectorAll('.rulebox').forEach(r=>r.classList.add('open')); }")
    pg.wait_for_timeout(500)
    el = pg.locator('.rb-sec').nth(3)
    if el.count():
        el.screenshot(path='/tmp/fc/rule_passage.png')
        print('shot ok')
    else:
        pg.screenshot(path='/tmp/fc/rule_passage.png'); print('fallback shot')
    b.close()
