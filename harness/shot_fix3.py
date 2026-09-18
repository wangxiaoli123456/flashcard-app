import json
from playwright.sync_api import sync_playwright
CHROME='/root/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome'
INIT = """() => {
  // mock 语音，统计自动朗读调用
  window.__speak = 0;
  try { Object.defineProperty(window,'speechSynthesis',{value:{cancel(){},speak(){window.__speak++;}}}); } catch(e){}
  const t = todayKey();
  const y = (()=>{ const d=new Date(); d.setDate(d.getDate()-3); return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'); })();
  store.passages = {
    p1:{id:'p1',text:'Five little ducks went out one day.',cn:'五只小鸭子出门了。',state:'new',nights:0,streak:0,confirm:false,next:t,created:t},
    p2:{id:'p2',text:'A red bus is on the road.',cn:'一辆红色公交车在路上。',state:'wrong',nights:0,streak:0,confirm:false,next:t,created:t},
    p3:{id:'p3',text:'The big brown bear sleeps.',cn:'棕色大熊在睡觉。',state:'hist',nights:1,streak:0,confirm:false,next:t,created:y}
  };
  save && save();
  // 直接进复习
  pfQueue=['p1','p2','p3']; pfIdx=0; currentPfId=null; startPassageReview();
  return { autoSpeakAtEnter: window.__speak };
}"""
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    pg=b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True).new_page()
    pg.goto('http://127.0.0.1:8899/index.html',wait_until='domcontentloaded'); pg.wait_for_timeout(2200)
    print('① 进入复习是否自动读:', json.dumps(pg.evaluate(INIT),ensure_ascii=False))
    pg.wait_for_timeout(300); pg.screenshot(path='/tmp/fc/fix_review.png')
    # 点顶部🔊 手动读，应 +1
    pg.evaluate("pfSpeak()"); pg.wait_for_timeout(100)
    print('   点🔊后 speak 计数:', pg.evaluate("window.__speak"))

    # 切到素材库短文页
    pg.evaluate("""() => {
      document.getElementById('page-lib') && (document.getElementById('page-lib').style.display='block');
      setLibTab('passage');
    }""")
    pg.wait_for_timeout(300)
    info = pg.evaluate("""() => {
      const foldMonths=[...document.querySelectorAll('#pgList .card.fold')].length;
      const foldDays=[...document.querySelectorAll('#pgList .fold')].length;
      const items=document.querySelectorAll('#pgList .pg-item').length;
      return { monthFolders:foldMonths, allFolds:foldDays, items };
    }""")
    print('② 按日期分组:', json.dumps(info,ensure_ascii=False))
    pg.screenshot(path='/tmp/fc/fix_group.png')

    # ③ 删除 p1：点第一个删除按钮，检查该项消失 + 列表刷新
    before = pg.evaluate("Object.keys(store.passages).length")
    pg.evaluate("""() => {
      const btn=[...document.querySelectorAll('#pgList .pg-del')].find(b=>b.getAttribute('onclick').includes(\"p1'\"));
      btn.click();
    }""")
    pg.wait_for_timeout(200)
    after = pg.evaluate("""() => ({ storeCount: Object.keys(store.passages).length, domItems: document.querySelectorAll('#pgList .pg-item').length, p1gone: !document.querySelector('#pgList .pg-item[onclick*=\"p1\"]') })""")
    print('③ 删除p1:', json.dumps({'before':before,**after},ensure_ascii=False))
    pg.screenshot(path='/tmp/fc/fix_afterdel.png')
    b.close()
print('OK')
