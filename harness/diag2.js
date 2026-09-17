const { createClient } = require('@supabase/supabase-js');
const SB_URL='https://bununhxkphvlvgvhanpk.supabase.co';
const KEY='sb_publishable_l2HHWkiboFYihQ_taLY9ZA_O3Xxh0aH';
const UID='cacd1a4b-ed34-4b60-b57e-7cf82f596aea';
const EMAIL='315276700@qq.com',PW='Wxl577520';
(async()=>{
  const sb=createClient(SB_URL,KEY,{auth:{persistSession:false}});
  await sb.auth.signInWithPassword({email:EMAIL,password:PW});
  let all=[],from=0;
  while(true){const{data,e}=await sb.from('flash_cards').select('id,data,updated_at').eq('user_id',UID).range(from,from+999);if(e){console.error(e);process.exit(1);}all=all.concat(data);if(data.length<1000)break;from+=1000;}
  const withData=all.filter(r=>r.data&&(r.data.en||r.data.word));
  withData.sort((a,b)=> (a.data.created||'').localeCompare(b.data.created||''));
  let valid=0,bad=0,total=0; const prefixCount={};
  withData.forEach(r=>{const d=r.data;if(d&&d.imgData){total++;const p=String(d.imgData).slice(0,22);prefixCount[p]=(prefixCount[p]||0)+1;if(String(d.imgData).startsWith('data:image/'))valid++;else bad++;}});
  console.log('有imgData总数',total,'| 有效data:image',valid,'| 非image前缀',bad);
  console.log('前缀分布(前10):');Object.entries(prefixCount).slice(0,10).forEach(([k,v])=>console.log('   ['+k+'...] x'+v));
  console.log('\n=== 最早的14张历史老词 ===');
  withData.slice(0,14).forEach(c=>{
    const d=c.data;
    console.log('en='+(d.en||d.word||'')+' | created='+(d.created||'?')+' | imgKey='+(d.imgKey||'')+' | imgUrl='+((d.imgUrl||'').slice(0,50))+' | imgData='+(d.imgData?('len='+d.imgData.length):'无'));
  });
  // 检查：有 imgKey 但无 imgData 的（若这类存在，说明 backfill 没覆盖到，且它们本可走 Storage URL）
  const keyNoData=withData.filter(r=>r.data&&r.data.imgKey&&!r.data.imgData);
  console.log('\n有imgKey但无imgData的卡数:',keyNoData.length);
})().catch(e=>{console.error(e);process.exit(2);});
