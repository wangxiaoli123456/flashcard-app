
const { createClient } = require("/tmp/fc/harness/node_modules/@supabase/supabase-js");
const __SB_URL="https://bununhxkphvlvgvhanpk.supabase.co", __KEY="sb_publishable_l2HHWkiboFYihQ_taLY9ZA_O3Xxh0aH";
const UID="cacd1a4b-ed34-4b60-b57e-7cf82f596aea";
let sb = createClient(__SB_URL, __KEY, { auth:{ persistSession:false, autoRefreshToken:true } });
let sbUser=null, pulling=false;
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

function _isEffective(v){ return v!==null && v!==undefined && !(typeof v==='string' && v.trim()===''); }
function withTimeout(p, ms, label){
  return Promise.race([
    p,
    new Promise((_,rej)=>setTimeout(()=>rej(new Error('同步超时('+(label||'')+')')), ms))
  ]);
}
function mergeCloud(local,remote,remoteTime){
  if(!remote)return local;
  if(!local)return remote;
  // today 是「已挑卡 ID 集合」：取并集，绝不因「数量多」而覆盖丢弃任意一端挑的卡，
  // 保证「你和我(agent)的改动都能更新且互不丢失」
  const a=(local.ids||[]), b=(remote.ids||[]);
  const union=[...new Set([...a,...b])];
  const date=(b.length>=a.length)?(remote.date||local.date):(local.date||remote.date);
  return {date,ids:union};
}
function mergeLog(local,remote){
  local=local||{}; remote=remote||{};
  const out=Object.assign({},local);
  Object.keys(remote).forEach(d=>{
    const rl=remote[d], ll=local[d];
    const rn=(rl&&rl.items)?rl.items.length:0;
    const ln=(ll&&ll.items)?ll.items.length:0;
    if(!ll || rn>ln) out[d]=rl; // 远端某天记录更完整则采用远端，避免空记录覆盖本地进度
  });
  return out;
}
async function doPush(){
  if(cloudReadOnly()){ sbStatus='只读模式（未上传）'; try{updateCloudUI();}catch(e){} return; }
  if(!sb||!sbUser)return;
  try{
    const uid=sbUser.id; const now=Date.now(); const iso=new Date(now).toISOString();
    // v382【省流量】推前只拉"轻量索引"(id,updated_at)判断该不该推；仅对"本地有改动/新建"的卡
    // 才补拉云端 data 做字段级合并。不再全量拉 data（原来每轮约 20MB，是流量爆表的主因）。
    let cwMap={}, snapOk=false, cloudIdx={};
    try{
      const {data:ci,error:cie}=await withTimeout(sb.from('flash_cards').select('id,updated_at').eq('user_id',uid), SYNC_TIMEOUT, '推前拉索引');
      if(!cie){
        snapOk=true;
        (ci||[]).forEach(r=>{ cloudIdx[r.id]=r.updated_at?new Date(r.updated_at).getTime():0; });
        const needData=[];
        Object.keys(store.cards).forEach(id=>{
          const c=store.cards[id]; if(!c)return;
          const dirty=(c._dirty&&Object.keys(c._dirty).length)>0;
          if(!c._syncAt || dirty) needData.push(id);
        });
        for(let i=0;i<needData.length;i+=25){
          const chunk=needData.slice(i,i+25);
          const {data:cd,error:cde}=await withTimeout(sb.from('flash_cards').select('id,data').eq('user_id',uid).in('id',chunk), SYNC_TIMEOUT, '推前拉变更卡');
          if(cde) throw cde;
          (cd||[]).forEach(r=>{ cwMap[r.id]=(r.data&&typeof r.data==='object')?r.data:{}; });
        }
      }
    }catch(e){ /* 读取失败不阻断；snapOk=false 时下面只推"本地新建/有脏标记"的卡，绝不按全量重推 */ }
    // v367：读取云端 deleted 墓碑，合并进本地删除集合，保证删除跨端传播
    let cloudDelMeta=[];
    try{
      const {data:dm,error:dme}=await withTimeout(sb.from('flash_meta').select('data').eq('user_id',uid).eq('key','deleted'), SYNC_TIMEOUT, '推前拉墓碑');
      if(!dme && dm && dm.length && Array.isArray(dm[0].data)) cloudDelMeta=dm[0].data;
    }catch(e){}
    // 计算需要推送的卡：与云端任一有效字段不同，或云端没有这张
    const rows=[];
    Object.keys(store.cards).forEach(id=>{
      const local=store.cards[id];
      if(!local)return;
      const cc=Object.assign({},local); delete cc._syncAt; delete cc._dirty;
      const cloud=cwMap[id];
      const dirty=local._dirty&&typeof local._dirty==='object'?local._dirty:{};
      const hasDirty=Object.keys(dirty).length>0;
      const inCloud=cloudIdx[id]!==undefined;   // v382：云端索引里是否有这张卡
      const neverSynced=!local._syncAt;         // v382：本地新建、从未同步过
      // v382：只有"有本地改动 / 本地新建 / 云端没有这张"才需要推；其余(无改动且云端已有)直接跳过。
      // 索引不可信(snapOk=false)时更保守：只推"有脏标记/新建"的卡，绝不按全量重推。
      if(!snapOk){ if(!hasDirty && !neverSynced) return; }
      else if(!hasDirty && !neverSynced && inCloud) return;
      const cloudData=cloud||{};
      // 字段级合并：本地有效且(云端无效 或 本地该字段刚脏)才用本地；否则沿用云端
      Object.keys(cc).forEach(k=>{
        if(k==='_syncAt'||k==='_dirty'||k==='_fieldAt')return;
        const lv=cc[k], cv=cloudData[k];
        const localDirty=dirty[k]===true;
        if(_isEffective(lv) && (!_isEffective(cv) || localDirty)){ /* 用本地 lv（已是 cc[k]） */ }
        else if(_isEffective(cv)){ cc[k]=cv; } // 本地无效/未改 → 继承云端，防止空值冲掉正确值
      });
      // 是否真有差异需要推（拿到云端 data 就精确比对，拿不到就用"脏标记/新建/云端无"判定）
      const changed = (cloud!==undefined)
        ? Object.keys(cc).some(k=>JSON.stringify(cc[k])!==JSON.stringify(cloudData[k]))
        : (hasDirty || neverSynced || !inCloud);
      if(changed) rows.push({user_id:uid,id,data:cc,updated_at:iso});
    });
    // v381：分批推送。单卡 data 含 imgData(内嵌图) 时可能有几十~上百 KB，
    // 一次 upsert 全部卡片会生成数 MB 请求体，在后端降级/弱网下必然撞 25s 超时。
    // 改成按"累计字节 ≤900KB 且 ≤12 张"分批，逐批带超时；某批失败只影响该批，
    // 成功的批立即标记已同步，失败的批保留脏标记由下次心跳重试，不会整轮白跑。
    let cardFail=0;
    console.error('[DBG doPush] snapOk=',snapOk,'rows=',rows.length, JSON.stringify(rows.map(r=>({id:r.id,state:r.data&&r.data.state}))));
    if(rows.length){
      const BATCH_BYTES=900*1024, BATCH_MAX=12;
      let buf=[], bufBytes=0, firstErr=null;
      const flush=async()=>{
        if(!buf.length)return;
        const ids=buf.map(r=>r.id);
        try{
          const {error}=await withTimeout(sb.from('flash_cards').upsert(buf,{onConflict:'user_id,id'}), SYNC_TIMEOUT, '推卡片');
          if(error) throw error;
          ids.forEach(id=>{ const c=store.cards[id]; if(c){ c._syncAt=now; if(c._dirty)c._dirty={}; } });
        }catch(e){
          cardFail+=ids.length; firstErr=firstErr||e;
          console.warn('[推卡分批失败] '+ids.length+' 张将在下一轮重试', e&&e.message||e);
        }
        buf=[]; bufBytes=0;
      };
      for(const r of rows){
        let sz=0; try{ sz=JSON.stringify(r.data).length; }catch(e){ sz=1024; }
        if(buf.length && (bufBytes+sz>BATCH_BYTES || buf.length>=BATCH_MAX)) await flush();
        buf.push(r); bufBytes+=sz;
      }
      await flush();
      if(cardFail && cardFail===rows.length){ if(firstErr) throw firstErr; else throw new Error('推卡片失败'); }
    }
    // 删除云端中本地已不存在的卡：删除操作必须同步到云端，否则下次 syncPull 又把已删卡拉回本地（删了又复活）
    try{
      // 删除同步以"墓碑"为准：只删 deletedIds 中云端确实存在的卡。
      // 绝不用"云端有、本地没有"的差集——否则本地索引未完全加载时会把真实卡当冗余误删。
      const del=store.deletedIds||[];
      if(del.length){
        const {data:cloudIds,error:ide}=await withTimeout(sb.from('flash_cards').select('id').eq('user_id',uid), SYNC_TIMEOUT, '删前拉ID');
        if(!ide){
          const cloudSet=new Set((cloudIds||[]).map(r=>r.id));
          const toDel=del.filter(id=>cloudSet.has(id));
          // 删除哨兵：单次删除量超过本地 20%（且>3张）即视为异常（如旧版差集逻辑/同步竞态），
          // 拒绝执行删除、保留墓碑，避免任何"批量误删"把真实卡清空。下次推送重试时若恢复则正常删。
          const localN=rows.length;
          const SENTINEL=Math.max(3, Math.floor(localN*0.2));
          if(toDel.length>SENTINEL){
            console.warn('[删除哨兵] 拟删 '+toDel.length+' 张 > 阈值 '+SENTINEL+'，疑似异常，已跳过删除以保护数据');
          } else if(toDel.length){ const {error:de}=await sb.from('flash_cards').delete().in('id',toDel).eq('user_id',uid); if(de)throw de;
            // v382：删除后【保留】墓碑，不再清空——增量同步下墓碑是唯一的跨端删除信号，清掉对端就永远删不掉。
            // 复活(重加同 id)由"创建处清墓碑 + syncPull 发现云端已有该卡即移除墓碑"保证。
            if(store.deletedIds.length>3000) store.deletedIds=store.deletedIds.slice(-3000);
          }
        }
      }
    }catch(e){ /* 删除同步失败不阻断主流程，下次推送重试 */ }
    store.today._syncAt=now;
    // 推送 today/log/batch 到云端。关键保护：本地 today.ids 为空时【不推送 today】，
    // 避免新设备/清缓存首启本地为空时用空列表覆盖云端已挑好的今日队列（之前因此被清空过）。
    const metaRows=[];
    if(store.today && (store.today.ids||[]).length){ metaRows.push({user_id:uid,key:'today',data:store.today,updated_at:iso}); }
    metaRows.push({user_id:uid,key:'log',data:store.log,updated_at:iso});
    metaRows.push({user_id:uid,key:'batch',data:store.batch,updated_at:iso});
    // v367：云端墓碑权威删除——把本地与云端 deleted 取并集推回云端，各端同步时依此清理，避免误删独有卡
    const delUnion=[...new Set([...(store.deletedIds||[]),...cloudDelMeta])];
    metaRows.push({user_id:uid,key:'deleted',data:delUnion,updated_at:iso});
    const {error:me}=await withTimeout(sb.from('flash_meta').upsert(metaRows,{onConflict:'user_id,key'}), SYNC_TIMEOUT, '推元数据'); if(me)throw me;
    // v381：媒体上传(Storage)失败不应拖垮整轮同步——图片主通道已改走卡片内嵌 imgData(DB 同步)，
    // Storage 桶当前不可用是常态，故此处只告警不抛错，避免"卡和元数据都推成功了却被判定同步失败"。
    try{ await withTimeout(syncPushMedia(uid), SYNC_TIMEOUT, '推媒体'); }catch(e){ console.warn('[推媒体失败,不影响数据同步]', e&&e.message||e); }
    saveNow();
    if(cardFail){ sbStatus='部分同步：'+cardFail+' 张卡待重试'; }
    else { lastSyncOkAt=Date.now(); sbStatus='已同步 ✓'; }
    updateCloudUI();
  }catch(e){ sbStatus='同步失败：'+(e.message||e); updateCloudUI(); }
}
async function syncPull(silent){
  if(cloudReadOnly())return;   // v345：只读模式下不拉取，测试卡不被真实数据覆盖
  if(!sb||!sbUser||pulling)return;
  pulling=true;
  try{
    if(!silent){ sbStatus='同步中…'; updateCloudUI(); }
    const uid=sbUser.id;
    const sig0=cloudSig(); // 同步前快照
    // v382【省流量·根治】先只拉"轻量索引"(id,updated_at)，再按需拉取"有变化"的卡 data。
    // 真因：卡片内嵌 imgData(约 88KB/张 × 246 张) → 原「全量拉 data」每轮约 20MB；
    // 30s 心跳一天就是几十 GB，直接打爆 Supabase 免费版 5GB/月 出网额度 → 后端限流 →
    // 表现为"同步时好时坏/超时/图时有时无"。改增量后每轮仅传几十 KB(降约 200 倍)。
    const {data:meta,error:me}=await withTimeout(
      sb.from('flash_meta').select('key,data,updated_at').eq('user_id',uid), SYNC_TIMEOUT, '拉元数据');
    if(me)throw me;
    // v382【省流量·根治】卡片索引走"增量拉取"：默认只拉上次水位之后变化的行（通常为空→几乎零流量），
    // 每 10 轮 / 本地为空时做一次全量校准。原来每轮全量拉 data(约 20MB) 是打爆免费流量的主因。
    idxFullCounter++;
    const fullIdx = idxFullCounter>=10 || !Object.keys(store.cards).length || !lastPullIso;
    let idx=[];
    if(fullIdx){
      const {data:ci,error:e1}=await withTimeout(sb.from('flash_cards').select('id,updated_at').eq('user_id',uid), SYNC_TIMEOUT, '拉卡片索引(全量)');
      if(e1)throw e1; idx=ci||[]; idxFullCounter=0;
    }else{
      const {data:ci,error:e1}=await withTimeout(sb.from('flash_cards').select('id,updated_at').eq('user_id',uid).gt('updated_at',lastPullIso), SYNC_TIMEOUT, '拉卡片索引(增量)');
      if(e1)throw e1; idx=ci||[];
    }
    // 仅拉"本地没有 / 云端更新时间比本地记录(_syncAt=上次云端时间戳)新"的卡，分批 25 张
    const cards=[];
    let allFetched=true;
    try{
      const need=[];
      (idx||[]).forEach(r=>{
        const ex=store.cards[r.id];
        const rt=r.updated_at?new Date(r.updated_at).getTime():0;
        if(!ex || rt>(ex._syncAt||0)) need.push(r.id);
      });
      for(let i=0;i<need.length;i+=25){
        const chunk=need.slice(i,i+25);
        const {data:cd,error:cde}=await withTimeout(
          sb.from('flash_cards').select('id,data,updated_at').eq('user_id',uid).in('id',chunk),
          SYNC_TIMEOUT, '拉卡片数据');
        if(cde) throw cde;
        (cd||[]).forEach(x=>cards.push(x));
      }
    }catch(e){ allFetched=false; console.warn('[增量拉卡] 本轮部分未取到，下次心跳补', e&&e.message||e); }
    // v382：只有本批"全部取回"才推进水位；否则不推进，下轮增量仍会把漏掉的卡带回来重试（避免永久漏卡）
    if(allFetched){
      try{
        let maxTs=lastPullIso||'';
        (idx||[]).forEach(r=>{ if(r.updated_at&&(!maxTs||r.updated_at>maxTs)) maxTs=r.updated_at; });
        if(maxTs){ lastPullIso=maxTs; try{ localStorage.setItem('fc_lastPull',maxTs); }catch(e){} }
      }catch(e){}
    }
    const cloudDeleted=new Set();
    (meta||[]).forEach(r=>{ if(r.key==='today')store.today=mergeCloud(store.today,r.data,r.updated_at); else if(r.key==='log')store.log=mergeLog(store.log,r.data); else if(r.key==='batch')store.batch=(r.data&&r.data!=='')?r.data:store.batch; else if(r.key==='deleted'){ (Array.isArray(r.data)?r.data:[]).forEach(id=>{ if(id)cloudDeleted.add(id); }); } });
    // v367：云端墓碑权威合并——把云端已删 id 并入本地墓碑，保证各端删除最终一致（替换原“孤儿清理”）
    cloudDeleted.forEach(id=>{ if(!store.deletedIds.includes(id))store.deletedIds.push(id); });
    (cards||[]).forEach(r=>{
      // v368b：移除「墓碑拦截卡片合并」。删除靠「云端 flash_cards 真正无此卡」传播（syncPullMedia/doPush 删云端 → 各端 cards 遍历不到 → 不再拉回），
      // 而非靠 deleted 墓碑拦截 cards 合并——否则旧版孤儿清理残留的 deleted 墓碑会永久阻止复活卡拉回，双设备长期差固定张数（如本例差 7 张）。
      // 此处仅当云端确实返回该卡时才合并；墓碑的剩余作用只剩「清理本地残留的已删卡」（见下方 cloudDeleted.forEach）。
      const ex=store.cards[r.id]; const rt=r.updated_at?new Date(r.updated_at).getTime():0;
      // v251 修复：云端有主题元数据(theme)而本地缺失时，强制采用云端，避免仅比 updated_at 导致主题字段进不来
      const cloudHasTheme=r.data&&r.data.theme; const localHasTheme=ex&&ex.theme;
      // v366：回退到整卡合并（撤销 v365 字段级 LWW 回归）。
      // 回归根因：v365 字段级 LWW 在「云端有某字段、但两端都无该字段时间戳」时把该字段整条丢弃(clT=-1)，
      // 导致同步后 imgKey/imgUrl/state/confirm 等字段丢失 → ①跨设备图片无法恢复(ensureAllImgUrls/syncPullMedia 匹配不到 imgKey) ②新词池被污染丢词。
      // 整卡合并完整保留云端卡全部字段，跨设备图片与词数一致性恢复。
      // 两设备"修改不同步"的时序问题已由 syncNow(先推后拉)+pagehide flush(离台强制推送)解决，无需再做字段级手术。
      if(!ex||rt>(ex._syncAt||0)||(cloudHasTheme&&!localHasTheme)){
        const c=Object.assign({},r.data); c._syncAt=rt;
        // v370：图片字段保护——云端无图/无URL但本地有，则保留本地图（imgKey/imgUrl），
        // 避免「无图版本覆盖有图版本」导致双设备图片互吃（iPad 上传图后被无图版覆盖→自己看不到、手机却能看到）。
        if(ex && ex.imgKey && !c.imgKey) c.imgKey=ex.imgKey;
        if(ex && ex.imgUrl && !c.imgUrl) c.imgUrl=ex.imgUrl;
        if(ex && ex.imgData && !c.imgData) c.imgData=ex.imgData; // v372：保护本地内嵌图，不被云端空值覆盖（旧 migrateV7 曾清空）
        store.cards[r.id]=c;
        // v372：把云端内嵌图(imgData)写入本机IndexedDB，并经DB同步通道跨设备显示；
        // 不再依赖失效的 Storage 桶（RLS 拦截写入→桶空→另一台永不可见）。imgData 保留在卡上随同步传播。
        if(c.imgKey && c.imgData){ try{ dbPut(c.imgKey,c.imgData); }catch(e){} }
      } // 严格大于才覆盖：相等(=本地未推送改动，如刚确认)时保留本地，避免"确认后被云端旧值覆盖回重新确认"
    });
    // v367：删除"孤儿清理"（原逻辑：云端没有就删本地 _syncAt 卡）。该逻辑会把「另一台设备独有、
    // 尚未推到云端」的卡当成冗余误删，导致双设备卡片数长期对不上（如本例差 7 张）。
    // 改为「云端墓碑权威」：仅当云端 deleted 列表标记删除时才本地移除；其余一律保留，
    // 交由 doPush 把本地独有卡推上云端后自愈，绝不再因云端暂时缺卡而丢失数据。
    // v368b：清理本地残留的已删卡。关键：仅删「云端 cards 里确实不存在」的本地卡，
    // 跳过云端 cards 已恢复（复活）的 id——否则会把刚从云端拉回的复活卡又删掉，永远补不齐。
    const cloudCardIds=new Set((idx||[]).map(r=>r.id)); // v382：云端全集改用轻量索引（cards 现在只含"有变化的卡"，不再是全集）
    // v373b：云端 flash_cards 为权威全集，删除传播 = 云端无此卡则各端清理。
    // 三重保护避免重蹈 v368「孤儿清理误删独有卡」：①仅删本地 _syncAt 存在（曾同步过）的卡，本地新建未推(_syncAt缺失)绝不删；
    // ②今日队列(today.ids)里的卡绝不删（用户主动挑的词）；③极端哨兵：云端卡片数骤降超 50%（疑似同步/网络异常）本批不删。
    // 该方案天然支持「删了又加」的复活：重加后 doPush 把卡推回云端 cards，云端有此卡即保留，不依赖易碎的墓碑传播。
    // v382：全集清理只在"全量校准轮"执行——增量轮拿不到云端全集，不能据此判定"云端没有此卡"
    if(fullIdx && idx && Array.isArray(idx)){
      const localN=Object.keys(store.cards).length;
      const missing=Object.keys(store.cards).filter(id=>!cloudCardIds.has(id)).length;
      if(localN===0 || missing<=Math.max(3,Math.floor(localN*0.5))){
        Object.keys(store.cards).forEach(id=>{
          const c=store.cards[id];
          if(!c || cloudCardIds.has(id) || !c._syncAt) return;
          if(store.today && store.today.ids && store.today.ids.includes(id)) return;
          delete store.cards[id];
        });
      } else { console.warn('[syncPull清理哨兵] 云端缺失 '+missing+'/本地 '+localN+'，疑似异常，跳过删除清理'); }
    }
    // v382：删除传播改「墓碑驱动」——云端 deleted 列表标了删除的 id，本地若有(且曾同步过)就删。
    // 原因：增量同步拿不到云端全集，"云端无此卡则清"不再可靠；墓碑是可靠的跨端删除信号。
    if(cloudDeleted.size){
      let dn=0;
      cloudDeleted.forEach(id=>{ const c=store.cards[id]; if(c && c._syncAt){ delete store.cards[id]; dn++; } });
      if(dn) console.log('[墓碑删除] 本地清理 '+dn+' 张已删卡');
    }
    // v382：若某 id 已存在于云端卡片索引，说明它被"删了又加"复活 → 从本地墓碑移除，避免把复活卡再删掉
    if(idx && idx.length && store.deletedIds && store.deletedIds.length){
      const liveIds=new Set(idx.map(r=>r.id));
      store.deletedIds=store.deletedIds.filter(id=>!liveIds.has(id));
    }
    // 清理今日队列里指向已删/不存在卡(id 不在本地 cards)的孤立 id：删除卡后今日队列可能残留
    // 其引用（旧版删除未同步清理过），不处理会在首页显示空白卡，且 doPush 会把带孤立的队列
    // 推回云端造成反弹。统一在此过滤，保证 today 只含真实存在的卡。
    if(store.today && store.today.ids){ store.today.ids=store.today.ids.filter(id=>!!store.cards[id]); }
    const sig1=cloudSig(); // 同步后快照
    if(sig0!==sig1){
      // 仅在数据真正变化时才落盘+重绘，避免 30s 轮询/实时事件无谓重建素材库网格导致闪屏
      saveNow();
      await withTimeout(syncPullMedia(uid), SYNC_TIMEOUT, '拉媒体');
      lastSyncOkAt=Date.now(); sbStatus='已同步 ✓'; if(!silent) updateCloudUI(); renderAll();
    } else {
      lastSyncOkAt=Date.now(); sbStatus='已同步 ✓'; if(!silent) updateCloudUI();
    }
  }catch(e){ sbStatus='同步失败：'+(e.message||e); if(!silent) updateCloudUI(); }
  finally{ pulling=false; }
}

module.exports = { get sb(){return sb;}, set sbUser(v){sbUser=v;}, set store(v){store=v;}, get store(){return store;},
  set idxFullCounter(v){idxFullCounter=v;}, get idxFullCounter(){return idxFullCounter;},
  set lastPullIso(v){lastPullIso=v;}, get lastPullIso(){return lastPullIso;},
  set pulling(v){pulling=v;}, doPush, syncPull, get sbStatus(){return sbStatus;} };
