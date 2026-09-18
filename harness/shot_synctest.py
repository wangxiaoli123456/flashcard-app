"""短文误删回归测试：同一份本地状态，跑同步拉取，看短文是否被误删。
对 old391.html(旧版) 与 index.html(新版) 各跑一遍，做对照。"""
import json, sys
from playwright.sync_api import sync_playwright
CHROME='/root/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome'

# 模拟 supabase：flash_cards 索引(增量轮=空) + 短文数据行 + meta
MOCK = """
() => {
  const UID = 'cacd1a4b-ed34-4b60-b57e-7cf82f596aea';
  window.__net = 0;
  function chain(res){
    const c = {
      select:()=>c, eq:()=>c, gt:()=>c, in:()=>c, order:()=>c, limit:()=>c,
      upsert:()=>Promise.resolve({error:null}), insert:()=>Promise.resolve({error:null}),
      update:()=>Promise.resolve({error:null}), delete:()=>c,
      then:(ok,bad)=>Promise.resolve(res).then(ok,bad)
    };
    return c;
  }
  const passageRow = { id:'p_today_local', data:{ kind:'passage', id:'p_today_local',
      text:'Five little ducks went out one day.', cn:'五只小鸭子出门了。',
      state:'new', nights:0, streak:1, next:'2026-09-19', confirm:false, created:'2026-09-18' },
    updated_at:'2026-09-18T14:53:24.634+00:00' };
  window.__mode = { deleted:[] };   // 测试用可调
  const fake = {
    from:(t)=>{
      if(t==='flash_meta') return { select:()=>chain({data:[{key:'deleted',data:window.__mode.deleted,updated_at:'2026-09-18T00:00:00Z'}],error:null}) };
      if(t==='flash_cards') return { select:(cols)=>{
          if(cols && cols.indexOf('data')>=0) return chain({data:window.__mode.deleted.length?[]:[passageRow], error:null});
          return chain({data:[], error:null});   // 增量轮：索引为空(这就是触发条件)
        }, upsert:()=>Promise.resolve({error:null}), delete:()=>chain({error:null}) };
      return { select:()=>chain({data:[],error:null}), upsert:()=>Promise.resolve({error:null}) };
    },
    storage:{ from:()=>({ list:()=>Promise.resolve({data:[],error:null}), upload:()=>Promise.resolve({error:null}), getPublicUrl:()=>({data:{publicUrl:''}}) }) },
    auth:{ signInWithPassword:()=>Promise.resolve({data:{user:{id:UID}},error:null}), getSession:()=>Promise.resolve({data:{session:null}}) }
  };
  // 同一个页面内跑两轮：round1 增量(索引空) / round2 带云端删除墓碑
  window.__run = async (mode) => {
    window.__mode.deleted = mode.deleted||[];
    sb = fake; sbUser = { id: UID };
    const t = todayKey();
    store.cards = { c1:{ id:'c1', en:'duck', cn:'鸭子', state:'new', _syncAt: Date.now() } };
    store.passages = { p_today_local:{ id:'p_today_local', text:'Five little ducks went out one day.',
        cn:'五只小鸭子出门了。', state:'new', nights:0, streak:1, next:t, confirm:false,
        created:t, _syncAt: Date.now() } };
    store.deletedIds = [];
    lastPullIso = '2026-09-17T00:00:00.000Z';
    idxFullCounter = 0;
    pulling = false;
    await syncPull(true);
    return { passages:Object.keys(store.passages), count:Object.keys(store.passages).length,
             cards:Object.keys(store.cards).length };
  };
  return true;
}
"""

with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    out={}
    for tag,f in [('旧版v391','old391.html'),('新版v392','index.html')]:
        ctx=b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True)
        ctx.route('**supabase.co/**', lambda r: r.abort())   # 断网，绝不动真数据
        pg=ctx.new_page()
        pg.goto(f'http://127.0.0.1:8899/{f}',wait_until='domcontentloaded'); pg.wait_for_timeout(2000)
        pg.evaluate(MOCK)
        r1=pg.evaluate("() => window.__run({deleted:[]})")            # ① 增量轮(云端索引为空)
        r2=pg.evaluate("() => window.__run({deleted:['p_today_local']})")  # ② 对端删除→墓碑
        out[tag]={'①增量轮后短文数':r1['count'],'①短文列表':r1['passages'],
                  '②墓碑删除后短文数':r2['count']}
        # ③ 短文页是否还有紫色「复习短文」按钮
        out[tag]['③短文页仍有紫按钮']=pg.evaluate("() => !!document.querySelector('#libPassageWrap .btn-purple')")
        ctx.close()
    print(json.dumps(out,ensure_ascii=False,indent=1))
    b.close()
