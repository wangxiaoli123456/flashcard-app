import json
from playwright.sync_api import sync_playwright

CHROME = '/root/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome'
TEXT = 'Five little ducks went out one day.\\nOver the hill and far away.\\nMother duck said, "Quack, quack, quack, quack."\\nBut only four little ducks came back.\\nOne, two, three, four'

INJECT = """() => {
  const t = todayKey();
  store.passages = { p1: { id:'p1', text:'%s', cn:'五只小鸭子出门了。翻过小山走远了。鸭妈妈说："嘎嘎嘎嘎。"可是只回来四只小鸭子。一、二、三、四。', title:'Five little ducks', state:'new', nights:0, streak:0, confirm:false, next:t, created:t } };
  save && save();
  pfQueue = ['p1']; pfIdx = 0; currentPfId = null;
  startPassageReview();
  const m = document.getElementById('pfMask');
  const cs = getComputedStyle(m);
  const r = m.getBoundingClientRect();
  const body = document.querySelector('#pfMask .pf-body');
  return {
    shown: m.classList.contains('show'),
    cls: m.className,
    display: cs.display,
    position: cs.position,
    zIndex: cs.zIndex,
    rect: [Math.round(r.width), Math.round(r.height)],
    viewport: [innerWidth, innerHeight],
    hasOldCard: !!document.querySelector('#pfMask .pf-card'),
    textLen: (document.getElementById('pfText').textContent || '').length,
    bodyScroll: body ? [body.scrollHeight, body.clientHeight] : null,
    count: document.getElementById('pfCount').textContent,
    btns: [...document.querySelectorAll('#pfMask .pf-bot .btn')].map(b => b.textContent.trim())
  };
}""" % TEXT

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox', '--disable-dev-shm-usage'])
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    pg = ctx.new_page()
    pg.goto('http://127.0.0.1:8899/index.html', wait_until='domcontentloaded')
    pg.wait_for_timeout(2500)
    info = pg.evaluate(INJECT)
    pg.wait_for_timeout(700)
    pg.screenshot(path='/tmp/fc/shot_passage_full.png')
    print('=== 直接进入短文复习 ===')
    print(json.dumps(info, ensure_ascii=False, indent=1))

    # 点「看中文」再截一张
    pg.evaluate("togglePfCn()")
    pg.wait_for_timeout(300)
    pg.screenshot(path='/tmp/fc/shot_passage_cn.png')

    # 一篇超长短文，验证可滚动不裁切
    LONG = " ".join(["This is a very long passage used to verify scrolling behaviour."] * 40)
    longinfo = pg.evaluate("""(long) => {
      store.passages.p2 = { id:'p2', text: long, cn:'', title:'L', state:'new', nights:0, streak:0, confirm:false, next: todayKey(), created: todayKey() };
      pfQueue=['p2']; pfIdx=0; renderPf();
      const b = document.querySelector('#pfMask .pf-body');
      const inner = document.querySelector('#pfMask .pf-inner');
      return { scrollH: b.scrollHeight, clientH: b.clientHeight, canScroll: b.scrollHeight > b.clientHeight, innerTop: Math.round(inner.getBoundingClientRect().top - b.getBoundingClientRect().top) };
    }""", LONG)
    print('=== 超长短文滚动 ===')
    print(json.dumps(longinfo, ensure_ascii=False))
    pg.evaluate("document.querySelector('#pfMask .pf-body').scrollTop = 99999")
    pg.wait_for_timeout(300)
    pg.screenshot(path='/tmp/fc/shot_passage_long_bottom.png')
    b.close()
print('OK')
