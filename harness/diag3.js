const { createClient } = require('@supabase/supabase-js');
const SB_URL='https://bununhxkphvlvgvhanpk.supabase.co';
const KEY='sb_publishable_l2HHWkiboFYihQ_taLY9ZA_O3Xxh0aH';
const UID='cacd1a4b-ed34-4b60-b57e-7cf82f596aea';
const EMAIL='315276700@qq.com',PW='Wxl577520';
(async()=>{
  const sb=createClient(SB_URL,KEY,{auth:{persistSession:false}});
  await sb.auth.signInWithPassword({email:EMAIL,password:PW});
  // 全量索引
  let idx=[],from=0;
  while(true){const{data,e}=await sb.from('flash_cards').select('id,updated_at').eq('user_id',UID).range(from,from+999);if(e){console.error(e);process.exit(1);}idx=idx.concat(data);if(data.length<1000)break;from+=1000;}
  console.log('索引卡数',idx.length,'计时拉取全部 data（每批25）...');
  const t0=Date.now(); let ok=0,fail=0,bytes=0;
  for(let i=0;i<idx.length;i+=25){
    const chunk=idx.slice(i,i+25).map(r=>r.id);
    const t1=Date.now();
    try{
      const{data:cd,error:cde}=await sb.from('flash_cards').select('id,data,updated_at').eq('user_id',UID).in('id',chunk);
      const dt=Date.now()-t1;
      if(cde){console.warn('  批次',i,'失败',dt+'ms',cde.message);fail+=chunk.length;continue;}
      (cd||[]).forEach(x=>{ if(x.data&&x.data.imgData) bytes+=x.data.imgData.length; });
      ok+=chunk.length;
      if((i/25)%4===0) console.log('  已拉',ok,'张, 本批',dt+'ms, 累计',((Date.now()-t0)/1000).toFixed(1)+'s');
    }catch(e){console.warn('  批次',i,'异常',e.message);fail+=chunk.length;}
  }
  console.log('\n全量data拉取完成: 成功',ok,'失败',fail,'| 总imgData体积',(bytes/1024/1024).toFixed(1)+'MB | 总耗时',((Date.now()-t0)/1000).toFixed(1)+'s');
})().catch(e=>{console.error(e);process.exit(2);});
