// 用 run.js 完全相同的环境跑场景3，并在 flush 前后查云端
const fs=require('fs');
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
const SB='https://bununhxkphvlvgvhanpk.supabase.co',K='sb_publishable_l2HHWkiboFYihQ_taLY9ZA_O3Xxh0aH',UID='cacd1a4b-ed34-4b60-b57e-7cf82f596aea';
const sb=createClient(SB,K,{auth:{persistSession:false}});
let sbUser=null,pulling=false,idxFullCounter=0,lastPullIso='',sbStatus='';
const SYNC_TIMEOUT=25000;
const __mem={}; function dbGet(k){return Promise.resolve(__mem[k]||null);} function dbPut(k,v){__mem[k]=v;return Promise.resolve(true);}
function idbPutCards(){} function saveNow(){} function schedulePush(){} function save(){}
function renderAll(){} function updateCloudUI(){} function showToast(){} function cloudReadOnly(){return false;} function cloudSig(){return '';}
const _isEffective=(v)=>v!==null&&v!==undefined&&!(typeof v==='string'&&v.trim()==='');
function withTimeout(p,ms,label){return Promise.race([p,new Promise((_,rej)=>setTimeout(()=>rej(new Error('timeout('+(label||'')+')')),ms))]);}
let store=null;
const doPush=eval('('+extract('doPush')+')');
(async()=>{
  await sb.auth.signInWithPassword({email:'315276700@qq.com',password:'Wxl577520'});
  sbUser={id:UID};
  const NEWID='harness_mininow';
  await sb.from('flash_cards').delete().eq('user_id',UID).eq('id',NEWID);
  store={cards:{},today:{date:'',ids:[]},log:{},batch:'',deletedIds:[]};
  store.cards[NEWID]={en:'MN',cn:'迷',state:'new'};
  const before=await sb.from('flash_cards').select('id').eq('user_id',UID).eq('id',NEWID);
  console.log('推前云端有=',(before.data||[]).length);
  await doPush();
  const after=await sb.from('flash_cards').select('id,data').eq('user_id',UID).eq('id',NEWID);
  console.log('推后云端有=',(after.data||[]).length, after.data&&after.data[0]&&after.data[0].data);
  console.log('sbStatus=',sbStatus);
  await sb.from('flash_cards').delete().eq('user_id',UID).eq('id',NEWID);
})();
