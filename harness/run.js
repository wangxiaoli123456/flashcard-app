// 双向同步验证：从 index.html 抽出真实 doPush/syncPull，连真实 Supabase，模拟 iPad/手机两台设备
const fs = require('fs');
const path = require('path');
const { createClient } = require('@supabase/supabase-js');

const SB_URL = 'https://bununhxkphvlvgvhanpk.supabase.co';
const KEY = 'sb_publishable_l2HHWkiboFYihQ_taLY9ZA_O3Xxh0aH';
const UID = 'cacd1a4b-ed34-4b60-b57e-7cf82f596aea';
const EMAIL = '315276700@qq.com', PW = 'Wxl577520';
const SRC = '/tmp/fc/index.html';

// ---- 从 index.html 主脚本中按函数名做花括号匹配抽取源码 ----
function extract(html, names) {
  // 取所有无 src 的 <script>，选最长者（主程序）
  const all = [...html.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)];
  let js = '';
  for (const m of all) if (m[1].length > js.length) js = m[1];
  if (!js) throw new Error('未找到主脚本');
  const out = {};
  for (const name of names) {
    // 支持带/不带 async 前缀；匹配 "function NAME("，并对带 label 参数的特例精确匹配
    const sigs = [
      new RegExp('(?:async\\s+)?function\\s+' + name + '\\s*\\(\\s*[\\w,]*\\s*[\\w]*\\s*,\\s*\\w+\\s*,\\s*\\w+\\s*\\)\\s*{'),
      new RegExp('(?:async\\s+)?function\\s+' + name + '\\s*\\([^)]*\\)\\s*{')
    ];
    let idx = -1, used = null;
    for (const re of sigs) { const mm = js.match(re); if (mm) { idx = mm.index; used = mm[0]; break; } }
    if (idx < 0) throw new Error('找不到函数 ' + name);
    const braceStart = js.indexOf('{', idx);
    let depth = 0, i = braceStart;
    for (; i < js.length; i++) {
      const ch = js[i];
      if (ch === '{') depth++;
      else if (ch === '}') { depth--; if (depth === 0) break; }
    }
    out[name] = js.slice(idx, i + 1);
  }
  return out;
}

const html = fs.readFileSync(SRC, 'utf8');
const fns = extract(html, ['_isEffective', 'withTimeout', 'mergeCloud', 'mergeLog', 'doPush', 'syncPull']);
// 注入调试：打印 doPush 是否真的把卡放进 rows
fns.doPush = fns.doPush.replace(
  'if(rows.length){\n      const BATCH_BYTES',
  "console.error('[DBG doPush] snapOk=',snapOk,'rows=',rows.length, JSON.stringify(rows.map(r=>({id:r.id,state:r.data&&r.data.state}))));\n    if(rows.length){\n      const BATCH_BYTES"
);
// 注入调试：打印 syncPull 的增量分支与待拉清单
fns.syncPull = fns.syncPull.replace(
  'if(!ex || rt>(ex._syncAt||0)) need.push(r.id);',
  "if(!ex || rt>(ex._syncAt||0)) need.push(r.id); console.error('[DBG pull] fullIdx=',fullIdx,'wet=',typeof _wf!=='undefined'?_wf:'(n/a)','idxN=',(idx||[]).length,'needN=',need.length,'need=',JSON.stringify(need.slice(0,8)));"
);

// ---- 组装可执行脚本：stub 掉 DOM/IndexedDB，注入真实 supabase 客户端 ----
const header = `
const { createClient } = require(${JSON.stringify(path.join(__dirname, 'node_modules', '@supabase', 'supabase-js'))});
const __SB_URL=${JSON.stringify(SB_URL)}, __KEY=${JSON.stringify(KEY)};
const UID=${JSON.stringify(UID)};
let sb = createClient(__SB_URL, __KEY, { auth:{ persistSession:false, autoRefreshToken:true } });
let sbUser=null, pulling=false, store=null;
let idxFullCounter=0, lastPullIso='';
let sbStatus='';
const SYNC_TIMEOUT=25000;
// stubs
const __mem={};
function dbGet(k){ return Promise.resolve(__mem[k]||null); }
function dbPut(k,v){ __mem[k]=v; return Promise.resolve(true); }
function idbPutCards(){}
function saveNow(){}
function schedulePush(){}
function save(){}
function renderAll(){}
function updateCloudUI(){}
function showToast(){}
function cloudReadOnly(){ return false; }
function cloudSig(){ return ''; }
`;
const footer = `
module.exports = { get sb(){return sb;}, set sbUser(v){sbUser=v;}, set store(v){store=v;}, get store(){return store;},
  set idxFullCounter(v){idxFullCounter=v;}, get idxFullCounter(){return idxFullCounter;},
  set lastPullIso(v){lastPullIso=v;}, get lastPullIso(){return lastPullIso;},
  set pulling(v){pulling=v;}, doPush, syncPull, get sbStatus(){return sbStatus;} };
`;
let gen = header + '\n' + Object.values(fns).join('\n') + '\n' + footer;
// 在写盘前替换：让 flush 的 catch 暴露真实错误
gen = gen.replace(
  "        }catch(e){\n          cardFail+=ids.length; firstErr=firstErr||e;\n          console.warn('[推卡分批失败] '+ids.length+' 张将在下一轮重试', e&&e.message||e);",
  "        }catch(e){\n          cardFail+=ids.length; firstErr=firstErr||e;\n          console.error('[推卡分批失败-真实]', JSON.stringify(ids), '| msg=', e&&e.message, '| code=', e&&e.code, '| details=', e&&e.details);"
);
const genPath = path.join(__dirname, 'gen.js');
fs.writeFileSync(genPath, gen);
const mod = require(genPath);

// ---- 设备模拟 ----
function makeDev() {
  return { cards: { __dummy: { _syncAt: Date.now() } }, today: { date: '', ids: [] }, log: {}, batch: '', deletedIds: [] };
}
async function devPush(dev) { mod.store = dev; mod.idxFullCounter = dev._ifc || 0; mod.lastPullIso = dev._lpi || ''; mod.pulling = false; await mod.doPush(); dev._ifc = mod.idxFullCounter; dev._lpi = mod.lastPullIso; }
async function devPull(dev) { mod.store = dev; mod.idxFullCounter = dev._ifc || 0; mod.lastPullIso = dev._lpi || ''; mod.pulling = false; await mod.syncPull(true); dev._ifc = mod.idxFullCounter; dev._lpi = mod.lastPullIso; }

const results = [];
function check(name, cond, extra) { results.push({ name, ok: !!cond, extra: extra || '' }); console.log((cond ? '✅' : '❌') + ' ' + name + (extra ? '  ' + extra : '')); }

(async () => {
  // 登录（与 app 一致：从 getSession().session.user 取 sbUser）
  const { data, error } = await mod.sb.auth.signInWithPassword({ email: EMAIL, password: PW });
  if (error) { console.error('登录失败', error); process.exit(1); }
  const { data: sess } = await mod.sb.auth.getSession();
  const u = (data && data.user) || (sess && sess.session && sess.session.user) || null;
  mod.sbUser = u;
  if (!u) { console.error('sbUser 为空'); process.exit(1); }
  console.log('已登录 sbUser.id=', u.id);

  const TEST = 'harness_sync_test';
  // 在云端建一张测试卡（先清掉可能存在的同名）
  await mod.sb.from('flash_cards').delete().eq('user_id', UID).eq('id', TEST);
  const base = { en: 'AAA', cn: '测试', state: 'new', nights: 0, streak: 0, next: '', created: '2026-01-01' };
  await mod.sb.from('flash_cards').upsert({ user_id: UID, id: TEST, data: base, updated_at: new Date().toISOString() });

  // 设备A(手机) 与 设备B(iPad)
  const A = makeDev(), B = makeDev();
  A._lpi = new Date(Date.now() - 60000).toISOString(); // 设为1分钟前，使增量只拉到我们改的卡
  B._lpi = A._lpi;
  // 预置测试卡到两台设备（带旧 _syncAt），模拟"都已同步过"
  A.cards[TEST] = Object.assign({}, base, { _syncAt: 1 });
  B.cards[TEST] = Object.assign({}, base, { _syncAt: 1 });

  // —— 场景1：A 改(复习：state=learned) → 推 → B 拉 → B 应收到 ——
  A.cards[TEST].state = 'learned';
  A.cards[TEST]._dirty = { state: true };
  await devPush(A);
  console.log('  [调试] devPush(A) 后 sbStatus=', mod.sbStatus);
  const cs1 = await mod.sb.from('flash_cards').select('data,updated_at').eq('user_id', UID).eq('id', TEST).single();
  console.log('  [调试] A推后云端TEST.state=', cs1.data && cs1.data.data && cs1.data.data.state, '| updated_at=', cs1.data && cs1.data.updated_at);
  await devPull(B);
  console.log('  [调试] B拉后本地TEST.state=', B.cards[TEST] && B.cards[TEST].state, '| B._lpi=', B._lpi);
  check('场景1 iPad(本例B)收到 手机(A)的复习更新', B.cards[TEST] && B.cards[TEST].state === 'learned', 'B.state=' + (B.cards[TEST] && B.cards[TEST].state));

  // —— 场景2：B 改(state=master) → 推 → A 拉 → A 应收到且保留A的字段(LWW) ——
  B.cards[TEST].state = 'master';
  B.cards[TEST]._dirty = { state: true };
  await devPush(B);
  await devPull(A);
  check('场景2 手机(A)收到 iPad(B)的更新', A.cards[TEST] && A.cards[TEST].state === 'master', 'A.state=' + (A.cards[TEST] && A.cards[TEST].state));
  check('场景2 字段级未丢字段(en保留)', A.cards[TEST] && A.cards[TEST].en === 'AAA', 'A.en=' + (A.cards[TEST] && A.cards[TEST].en));

  // —— 场景3：A 新增一张卡 → 推 → B 拉 → B 应出现 ——
  const NEWID = 'harness_sync_new';
  A.cards[NEWID] = { en: 'NEW', cn: '新', state: 'new' }; // 无 _syncAt → 新建
  console.log('  [调试] A推前 cards键=', JSON.stringify(Object.keys(A.cards)), '| NEW有无_syncAt=', A.cards[NEWID]._syncAt);
  await devPush(A);
  const cn1 = await mod.sb.from('flash_cards').select('id,updated_at').eq('user_id', UID).eq('id', NEWID);
  console.log('  [调试] A推后云端NEW存在=', cn1.data && cn1.data.length, '| NEW.updated_at=', cn1.data && cn1.data[0] && cn1.data[0].updated_at);
  console.log('  [调试] B拉前 _lpi=', B._lpi, '| NEW>_lpi?', cn1.data && cn1.data[0] && (cn1.data[0].updated_at > B._lpi));
  await devPull(B);
  console.log('  [调试] B拉后 _lpi=', B._lpi, '| B有NEW=', !!B.cards[NEWID], '| B卡数=', Object.keys(B.cards).length);
  check('场景3 iPad(B)收到 手机(A)新增的卡', !!B.cards[NEWID], 'B有NEW=' + !!B.cards[NEWID]);

  // —— 场景4：B 删除该卡 → 推 → A 拉 → A 应删除 ——
  B.deletedIds = B.deletedIds || [];
  B.deletedIds.push(NEWID);
  delete B.cards[NEWID];
  await devPush(B);
  await devPull(A);
  check('场景4 手机(A)删除传播（iPad删除后A也删）', !A.cards[NEWID], 'A无NEW=' + !A.cards[NEWID]);

  // 清理云端测试卡
  await mod.sb.from('flash_cards').delete().eq('user_id', UID).eq('id', TEST);
  await mod.sb.from('flash_cards').delete().eq('user_id', UID).eq('id', NEWID);

  const pass = results.filter(r => r.ok).length;
  console.log('\\n=== 同步验证结果：' + pass + '/' + results.length + ' 通过 ===');
  process.exit(pass === results.length ? 0 : 2);
})().catch(e => { console.error('运行异常', e); process.exit(3); });
