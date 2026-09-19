import json
from playwright.sync_api import sync_playwright
CHROME='/root/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome'

# 模拟：昨天答对一次（streak=1, next=今天），今天该不该出现
JS = """
() => {
  const t = todayKey();
  const y = addDays(t,-1);
  const created = addDays(t,-3);
  // 情况A：已答对一次，next=今天，streak=1，state=new
  store.passages = {
    pA:{id:'pA',text:'Five little ducks.',cn:'小鸭子',state:'new',nights:0,streak:1,confirm:false,next:t,created:created},
    pB:{id:'pB',text:'A red bus.',cn:'红公交',state:'new',nights:0,streak:0,confirm:false,next:t,created:created}
  };
  const dueA = passageDueIds();
  // 情况B：完整走两天——昨天next=y(到期)，markPassage(true)一次 → 应 next=today, streak=1
  store.passages.pC={id:'pC',text:'The bear sleeps.',cn:'熊睡觉',state:'new',nights:0,streak:0,confirm:false,next:y,created:created};
  currentPfId='pC'; pfQueue=['pC']; pfIdx=0;
  markPassage(true); // 模拟昨天答对
  const c=store.passages.pC;
  const dueB = passageDueIds();
  return {
    t, y,
    情况A_dueIds: dueA,
    情况B_afterMark: {next:c.next, streak:c.streak, state:c.state},
    情况B_dueIncludeC: dueB.includes('pC')
  };
}
"""

with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    pg=b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True).new_page()
    pg.goto('http://127.0.0.1:8899/index.html',wait_until='domcontentloaded'); pg.wait_for_timeout(2200)
    res = pg.evaluate(JS)
    print('PASSAGE TEST:', json.dumps(res, ensure_ascii=False, indent=1))
    b.close()
print('done')
