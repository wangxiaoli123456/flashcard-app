const { createClient } = require('@supabase/supabase-js');
const SB_URL='https://bununhxkphvlvgvhanpk.supabase.co';
const KEY='sb_publishable_l2HHWkiboFYihQ_taLY9ZA_O3Xxh0aH';
const UID='cacd1a4b-ed34-4b60-b57e-7cf82f596aea';
const EMAIL='315276700@qq.com',PW='Wxl577520';
(async()=>{
  const sb=createClient(SB_URL,KEY,{auth:{persistSession:false}});
  await sb.auth.signInWithPassword({email:EMAIL,password:PW});
  // 取最早一批历史老词
  const {data,error}=await sb.from('flash_cards').select('id,data').eq('user_id',UID).order('data->>created',{ascending:true}).limit(6);
  if(error){console.error(error);process.exit(1);}
  console.log('=== 历史老词瘦身后再验证（设备端 cardImgUrl 将走 imgUrl 分支）===');
  for(const r of data){
    const d=r.data;
    const hasImgData = !!(d.imgData && String(d.imgData).length>50);
    const isPublic = typeof d.imgUrl==='string' && d.imgUrl.indexOf('/public/')>=0;
    let httpOk=false, ct='';
    if(isPublic){
      try{ const res=await fetch(d.imgUrl); httpOk=res.ok; ct=res.headers.get('content-type')||''; }catch(e){}
    }
    console.log('en='+((d.en||d.word)||'')+' | created='+(d.created||'?')+' | imgData='+(hasImgData?'有(异常!)':'无✓')+' | imgUrl='+(isPublic?'public✓':'非public✗')+' | 该URL='+(httpOk?('HTTP200 '+ct):'不可加载') );
  }
})().catch(e=>{console.error(e);process.exit(2);});
