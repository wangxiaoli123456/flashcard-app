const path=require('path');
const fs=require('fs');
// 复用 run.js 的抽取逻辑，但只取 doPush 相关，最小化依赖
const {execSync}=require('child_process');
// 直接 require run.js 生成的模块？改用独立方式：
const src=fs.readFileSync('/tmp/fc/index.html','utf8');
const all=[...src.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)];
let js=''; for(const m of all) if(m[1].length>js.length) js=m[1];
function extract(name){
  const re=new RegExp('(?:async\\s+)?function\\s+'+name+'\\s*\\([^)]*\\)\\s*{');
  const m=js.match(re); if(!m) throw new Error('no '+name);
  let i=js.indexOf('{',m.index),d=0;
  for(;i<js.length;i++){ if(js[i]==='{')d++; else if(js[i]==='}'){d--; if(!d)break;} }
  return js.slice(m.index,i+1);
}
const {createClient}=require('@supabase/supabase-js');
const sb=createClient('https://bununhxkphvlvgvhanpk.supabase.co','sb_publishable_l2HHWkiboFYihQ_taLY9ZA_O3Xxh0aH',{auth:{persistSession:false}});
const UID='cacd1a4b-ed34-4b60-b57e-7cf82f596aea';
let sbUser=null,pulling=false,idxFullCounter=0,lastPullIso='',sbStatus='';
const SYNC_TIMEOUT=25000;
function dbGet(){return Promise.resolve(null);} function dbPut(){return Promise.resolve(true);}
function idbPutCards(){} function saveNow(){} function schedulePush(){} function save(){}
function renderAll(){} function updateCloudUI(){} function showToast(){} function cloudReadOnly(){return false;}
function cloudSig(){return '';}
const _isEffective=(v)=>v!==null&&v!==undefined&&!(typeof v==='string'&&v.trim()==='');
function withTimeout(p,ms,label){return Promise.race([p,new Promise((_,rej)=>setTimeout(()=>rej(new Error('同步超时('+(label||'')+')')),ms))]);}
const doPush=eval('('+extract('doPush')+')');
(async()=>{
  await sb.auth.signInWithPassword({email:'315276700@qq.com',password:'Wxl577520'});
  sbUser={id:UID};
  const NEWID='harness_mini_new';
  await sb.from('flash_cards').delete().eq('user_id',UID).eq('id',NEWID);
  const store={cards:{},today:{date:'',ids:[]},log:{},batch:'',deletedIds:[]};
  store.cards[NEWID]={en:'MINI',cn:'迷你',state:'new'}; // 新建，无_syncAt
  // 注入全局
  global.store=store;
  const fn=new Function('sb','sbUser','store','pulling','idxFullCounter','lastPullIso','sbStatus','SYNC_TIMEOUT',
    'dbGet','dbPut','idbPutCards','saveNow','schedulePush','save','renderAll','updateCloudUI','showToast','cloudReadOnly','cloudSig','_isEffective','withTimeout','doPush',
    'return doPush();');
  try{
    await fn(sb,sbUser,store,pulling,idxFullCounter,lastPullIso,sbStatus,SYNC_TIMEOUT,dbGet,dbPut,idbPutCards,saveNow,schedulePush,save,renderAll,updateCloudUI,showToast,cloudReadOnly,cloudSig,_isEffective,withTimeout,doPush);
    console.log('doPush 完成, sbStatus=',sbStatus);
  }catch(e){ console.log('doPush 异常:',e.message); }
  const {data:d}=await sb.from('flash_cards').select('id,data').eq('user_id',UID).eq('id',NEWID);
  console.log('云端有 MINI 卡=', d&&d.length, d&&d[0]&&d[0].data);
  await sb.from('flash_cards').delete().eq('user_id',UID).eq('id',NEWID);
})();
