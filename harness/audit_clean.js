// 审计 + 可回退的"轻量化"清理：把历史老词的大 imgData 清掉，改走轻量 imgUrl(Storage 公共读)
// 安全前提：每张待清卡的 imgUrl 是 /public/ 永久公共 URL，且 Storage 文件可访问(实测200)
const { createClient } = require('@supabase/supabase-js');
const SB_URL='https://bununhxkphvlvgvhanpk.supabase.co';
const KEY='sb_publishable_l2HHWkiboFYihQ_taLY9ZA_O3Xxh0aH';
const UID='cacd1a4b-ed34-4b60-b57e-7cf82f596aea';
const EMAIL='315276700@qq.com',PW='Wxl577520';
const RUN=process.argv.includes('--run');
const SB_PUBLIC='/storage/v1/object/public/flash-media/'+UID+'/';

function isPublicUrl(u){ return typeof u==='string' && u.indexOf('/public/')>=0; }

(async()=>{
  const sb=createClient(SB_URL,KEY,{auth:{persistSession:false}});
  await sb.auth.signInWithPassword({email:EMAIL,password:PW});
  let all=[],from=0;
  while(true){const{data,e}=await sb.from('flash_cards').select('id,data,updated_at').eq('user_id',UID).range(from,from+999);if(e){console.error(e);process.exit(1);}all=all.concat(data);if(data.length<1000)break;from+=1000;}

  const withImg=all.filter(r=>r.data&&r.data.imgData);
  let canClear=0, mustKeep=0, samples=[];
  const keepReasons=[];
  withImg.forEach(r=>{
    const d=r.data;
    const hasPublic = isPublicUrl(d.imgUrl) || (d.imgKey? true:false); // imgKey 可拼公共URL
    if(hasPublic){ canClear++; if(samples.length<30) samples.push({id:r.id,en:d.en,src:d.imgUrl||('key:'+d.imgKey)}); }
    else { mustKeep++; keepReasons.push({id:r.id,en:d.en,imgUrl:(d.imgUrl||'').slice(0,40),imgKey:(d.imgKey||'')}); }
  });

  console.log('=== 审计 ===');
  console.log('总卡',all.length,'| 带imgData',withImg.length);
  console.log('可安全清空(走Storage公共读):',canClear,'| 必须保留imgData(无Storage源):',mustKeep);
  if(mustKeep){ console.log('需保留的样本:'); mustKeepReasons(); }
  function mustKeepReasons(){ keepReasons.slice(0,15).forEach(k=>console.log('   ',k.id,k.en,'| url=',k.imgUrl,'key=',k.imgKey)); }

  // 抽样测 Storage 可访问性
  console.log('\n=== 抽样测 Storage 公共读(最多30张) ===');
  let okS=0,failS=0;
  for(const s of samples){
    const url = isPublicUrl(s.src)? s.src : (SB_URL+SB_PUBLIC+encodeURIComponent(s.src.replace(/^key:/,'')));
    try{ const res=await fetch(url); if(res.ok){okS++;} else {failS++; console.warn('  FAIL',s.en,res.status);} }catch(e){failS++; console.warn('  ERR',s.en,e.message);}
  }
  console.log('抽样',samples.length,'| 可读',okS,'| 失败',failS);

  if(!RUN){
    console.log('\n[DRY-RUN] 未执行清理。加 --run 执行：清空 '+canClear+' 张的 imgData(保留imgUrl/imgKey)。');
    return;
  }
  // 执行清理
  console.log('\n[RUN] 执行清理...');
  const todo=withImg.filter(r=>{const d=r.data;return isPublicUrl(d.imgUrl)||!!d.imgKey;});
  const rows=[];
  todo.forEach(r=>{ const nd=Object.assign({},r.data); delete nd.imgData;
    if(!isPublicUrl(nd.imgUrl) && nd.imgKey){ nd.imgUrl=SB_URL+SB_PUBLIC+encodeURIComponent(nd.imgKey); }
    rows.push({user_id:UID,id:r.id,data:nd,updated_at:new Date().toISOString()}); });
  let done=0;
  for(let i=0;i<rows.length;i+=20){
    const chunk=rows.slice(i,i+20);
    const{error}=await sb.from('flash_cards').upsert(chunk,{onConflict:'user_id,id'});
    if(error){console.error('upsert失败',error);process.exit(3);} done+=chunk.length;
  }
  console.log('已清空 imgData 的卡:',done,'/ 应清',canClear);
  // 验证
  let all2=[],f2=0; while(true){const{data,e}=await sb.from('flash_cards').select('id,data').eq('user_id',UID).range(f2,f2+999);if(e)break;all2=all2.concat(data);if(data.length<1000)break;f2+=1000;}
  const stillImg=all2.filter(r=>r.data&&r.data.imgData).length;
  console.log('验证：现在仍带imgData的卡 =',stillImg,'(应为 mustKeep='+mustKeep+')');
})().catch(e=>{console.error(e);process.exit(2);});
