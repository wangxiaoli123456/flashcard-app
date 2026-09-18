import json
from playwright.sync_api import sync_playwright
CHROME='/root/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome'
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    pg=b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True).new_page()
    pg.goto('http://127.0.0.1:8899/index.html',wait_until='domcontentloaded'); pg.wait_for_timeout(2500)
    # 默认不可见
    idle = pg.evaluate("() => getComputedStyle(document.getElementById('pfMask')).display")
    # 模拟一键复习走到第④项：闪卡层打开 + 队列里是 passage 占位
    flow = pg.evaluate("""() => {
      const t=todayKey();
      store.passages={p1:{id:'p1',text:'Five little ducks went out one day.',cn:'五只小鸭子出门了。',state:'new',nights:0,streak:0,confirm:false,next:t,created:t}};
      document.getElementById('fs').classList.add('show');
      fsQueue=[{id:null,pool:'passage'}]; fsIdx=0; fsPool='all';
      renderFs();
      return { fsShown: document.getElementById('fs').classList.contains('show'),
               pfShown: document.getElementById('pfMask').classList.contains('show'),
               pfDisplay: getComputedStyle(document.getElementById('pfMask')).display,
               text: document.getElementById('pfText').textContent };
    }""")
    pg.wait_for_timeout(400); pg.screenshot(path='/tmp/fc/shot_flow_from_all.png')
    # 点「会」→ 队列走完应自动关闭并回原页
    after = pg.evaluate("""() => { markPassage(true); return { pfShown: document.getElementById('pfMask').classList.contains('show'), state: store.passages.p1.state, streak: store.passages.p1.streak, next: store.passages.p1.next }; }""")
    print(json.dumps({'idleDisplay':idle,'flow':flow,'after':after},ensure_ascii=False,indent=1))
    b.close()
