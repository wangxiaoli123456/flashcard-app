import json
from playwright.sync_api import sync_playwright
CHROME='/root/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome'

JS = r"""
() => {
  const t = todayKey();
  const mk = (id, createdOffset) => ({id, text:'Five little ducks', cn:'', title:'',
    state:'new', nights:0, streak:0, next:t, confirm:false, created: addDays(t, createdOffset)});
  const mark = (id, good) => { currentPfId=id; pfQueue=[id]; pfIdx=0; markPassage(good); };
  const out = {};

  // A: 今天上传(前7天)，连点「会」3次 → 不应毕业（streak累加但不掌握）
  store.passages = { a: mk('a', 0) };
  mark('a',true); mark('a',true); mark('a',true);
  out.A_within7 = { state: store.passages.a.state, streak: store.passages.a.streak,
                    next: store.passages.a.next, mastered: store.passages.a.state==='hist' };

  // B: 上传已8天(过7天窗口)，连点「会」2次 → 应毕业
  store.passages = { b: mk('b', -8) };
  mark('b',true); mark('b',true);
  out.B_after7 = { state: store.passages.b.state, streak: store.passages.b.streak,
                   mastered: store.passages.b.state==='hist' };

  // C: 过窗口且前7天累积了streak(模拟孩子前7天每天会)，跨窗口后第1次会应清零重新数
  store.passages = { c: Object.assign(mk('c', -9), {streak:5, window7done:false}) };
  mark('c',true); // 跨窗口，应重置streak=0再+1=1，不毕业
  out.C_boundary1 = { state: store.passages.c.state, streak: store.passages.c.streak,
                      window7done: store.passages.c.window7done, mastered: store.passages.c.state==='hist' };
  mark('c',true); // 第2次会 → 2 → 毕业
  out.C_boundary2 = { state: store.passages.c.state, streak: store.passages.c.streak,
                      mastered: store.passages.c.state==='hist' };

  // D: 前7天每天都出现（含 wrong 状态）
  store.passages = { d1: mk('d1', 0), d2: Object.assign(mk('d2', -5),{state:'wrong'}), d3: mk('d3', -3) };
  store.stats = store.stats||{}; store.stats.passage={date:t,count:0};
  out.D_within7_due = passageDueIds().sort();

  // E: 过7天但 next 在未来 → 不应出现
  store.passages = { e: Object.assign(mk('e', -10), {next: addDays(t,2)}) };
  out.E_after7_future_next = passageDueIds();

  // F: 前7天即使 next 在未来也出现
  store.passages = { f: Object.assign(mk('f', -1), {next: addDays(t,2)}) };
  out.F_within7_force_future = passageDueIds();

  return out;
}
"""

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
    pg = b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2, is_mobile=True, has_touch=True).new_page()
    pg.goto('http://127.0.0.1:8899/index.html', wait_until='domcontentloaded'); pg.wait_for_timeout(2200)
    res = pg.evaluate(JS)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    b.close()
