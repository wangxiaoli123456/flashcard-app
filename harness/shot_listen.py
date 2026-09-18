import json
from playwright.sync_api import sync_playwright
CHROME='/root/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome'
INIT="""() => {
  window.__speak=0;
  try{ Object.defineProperty(window,'speechSynthesis',{value:{cancel(){},speak(){window.__speak++;}}}); }catch(e){}
  const t=todayKey();
  store.passages={p1:{id:'p1',text:'Five little ducks went out one day.\\nOver the hill and far away.\\nMother duck said, "Quack, quack, quack, quack."\\nBut only four little ducks came back.\\nOne, two, three, four.',cn:'五只小鸭子出门了。',state:'new',nights:0,streak:0,confirm:false,next:t,created:t}};
  save&&save();
  pfQueue=['p1']; pfIdx=0; currentPfId=null; startPassageReview();
  const b=document.querySelector('#pfMask .fs-bottom > .btn');
  return { hasBigBtn: !!b, text: b?b.textContent.trim():null, cls: b?b.className:null,
           topSpeak: !!document.querySelector('#pfMask .fs-top button[onclick="pfSpeak()"]'),
           autoSpeak: window.__speak };
}"""
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    pg=b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True).new_page()
    pg.goto('http://127.0.0.1:8899/index.html',wait_until='domcontentloaded'); pg.wait_for_timeout(2200)
    print('① 按钮结构:', json.dumps(pg.evaluate(INIT),ensure_ascii=False))
    pg.wait_for_timeout(300); pg.screenshot(path='/tmp/fc/listen1.png')
    pg.evaluate("""() => { const b=document.querySelector('#pfMask .fs-bottom > .btn'); b.click(); b.click(); b.click(); }""")
    pg.wait_for_timeout(150)
    print('② 连点3次后的朗读计数:', pg.evaluate("window.__speak"))
    # 点「会」按钮仍工作（不误触大按钮）
    ok = pg.evaluate("""() => { document.querySelector('#pfMask .pf-bot .btn-green').click(); return { state: store.passages.p1.state, streak: store.passages.p1.streak, pfShown: document.getElementById('pfMask').classList.contains('show') }; }""")
    print('③ 点「会」:', json.dumps(ok,ensure_ascii=False))
    b.close()
print('OK')
