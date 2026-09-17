const { createClient } = require('@supabase/supabase-js');
const SB_URL='https://bununhxkphvlvgvhanpk.supabase.co';
const KEY='sb_publishable_l2HHWkiboFYihQ_taLY9ZA_O3Xxh0aH';
const UID='cacd1a4b-ed34-4b60-b57e-7cf82f596aea';
const EMAIL='315276700@qq.com',PW='Wxl577520';
(async()=>{
  const sb=createClient(SB_URL,KEY,{auth:{persistSession:false}});
  await sb.auth.signInWithPassword({email:EMAIL,password:PW});
  let idx=[],from=0;
  while(true){const{data,e}=await sb.from('flash_cards').select('id,updated_at').eq('user_id',UID).range(from,from+999);if(e){console.error(e);process.exit(1);}idx=idx.concat(data);if(data.length<1000)break;from+=1000;}
  const t0=Date.now(); let bytes=0,n=0;
  for(let i=0;i<idx.length;i+=25){
    const chunk=idx.slice(i,i+25).map(r=>r.id);
    const{data:cd,error:cde}=await sb.from('flash_cards').select('id,data,updated_at').eq('user_id',UID).in('id',chunk);
    if(cde){console.warn('fail',cde.message);continue;}
    (cd||[]).forEach(x=>{ bytes+=JSON.stringify(x).length; if(x.data&&x.data.imgData)n++; });
  }
  console.log('瘦身验证：全量拉 '+idx.length+' 张 | 总data字节 '+(bytes/1024).toFixed(0)+' KB ('+(bytes/1024/1024).toFixed(2)+' MB) | 耗时 '+((Date.now()-t0)/1000).toFixed(1)+'s | 仍含imgData的 '+n+' 张');
})().catch(e=>{console.error(e);process.exit(2);});
