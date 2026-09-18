import json
from playwright.sync_api import sync_playwright
CHROME='/root/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome'
MOCK = """
() => {
  const UID='cacd1a4b-ed34-4b60-b57e-7cf82f596aea';
  const row = { id:'p_mu6kipgtdijc', data:{ kind:'passage', id:'p_mu6kipgtdijc',
      text:'Five little ducks went out one day.\\nOver the hill and far away.', cn:'五只小鸭子出门了。',
      state:'new', nights:0, streak:1, next:'2026-09-19', confirm:false, created:'2026-09-18' },
    updated_at:'2026-09-18T14:53:24.634+00:00' };
  function chain(res){ const c={select:()=>c,eq:()=>c,gt:()=>c,in:()=>c,order:()=>c,limit:()=>c,
      upsert:()=>Promise.resolve({error:null}),insert:()=>Promise.resolve({error:null}),
      update:()=>Promise.resolve({error:null}),delete:()=>c, then:(a,b)=>Promise.resolve(res).then(a,b)}; return c; }
  const fake={ from:(t)=>{
      if(t==='flash_meta') return {select:()=>chain({data:[{key:'deleted',data:[],updated_at:'2026-09-18T00:00:00Z'}],error:null})};
      if(t==='flash_cards') return {select:(cols)=> chain({data:(cols&&cols.indexOf('data')>=0)?[row]:[{id:row.id,updated_at:row.updated_at}],error:null}),
          upsert:()=>Promise.resolve({error:null}), delete:()=>chain({error:null})};
      return {select:()=>chain({data:[],error:null})}; },
    storage:{from:()=>({list:()=>Promise.resolve({data:[],error:null})})} };
  window.__go = async () => {
    sb=fake; sbUser={id:UID};
    store.cards={c1:{id:'c1',en:'duck',cn:'鸭子',state:'new',_syncAt:Date.now()}};
    store.passages={};                 // 手机本地：短文已被误删，为空
    store.deletedIds=[];
    lastPullIso='2026-09-18T00:00:00.000Z'; idxFullCounter=10; pulling=false;  // 强制全量轮
    await syncPull(true);
    const list=passageList();
    return { count:list.length, ids:Object.keys(store.passages),
             text:list[0]?list[0].text.split('\\n')[0]:null, state:list[0]?list[0].state:null,
             shownInList: document.querySelectorAll('#pgList .pg-item').length };
  };
  return true;
}"""
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True)
    ctx.route('**supabase.co/**', lambda r: r.abort())
    pg=ctx.new_page(); pg.goto('http://127.0.0.1:8899/index.html',wait_until='domcontentloaded'); pg.wait_for_timeout(2000)
    pg.evaluate(MOCK)
    print(json.dumps(pg.evaluate("() => window.__go()"),ensure_ascii=False))
    pg.evaluate("() => { setLibTab('passage'); }"); pg.wait_for_timeout(300)
    pg.screenshot(path='/tmp/fc/restore1.png')
    b.close()
