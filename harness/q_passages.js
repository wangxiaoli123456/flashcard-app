const { createClient } = require('@supabase/supabase-js');
const sb = createClient('https://bununhxkphvlvgvhanpk.supabase.co','sb_publishable_l2HHWkiboFYihQ_taLY9ZA_O3Xxh0aH');
(async()=>{
  await sb.auth.signInWithPassword({email:'315276700@qq.com',password:'Wxl577520'});
  const { data, error } = await sb.from('flash_cards').select('id,data,updated_at').eq('user_id','cacd1a4b-ed34-4b60-b57e-7cf82f596aea');
  if(error){ console.log('ERR', error.message); return; }
  const ps = (data||[]).filter(r=>r.data&&r.data.kind==='passage');
  console.log('云端总行数:', (data||[]).length, '| 其中短文:', ps.length);
  ps.sort((a,b)=>String(a.updated_at).localeCompare(String(b.updated_at)));
  ps.forEach(r=>{
    const d=r.data;
    console.log('---');
    console.log(' id:', r.id, '| updated:', r.updated_at);
    console.log(' created:', d.created, 'state:', d.state, 'streak:', d.streak, 'next:', d.next);
    console.log(' text:', JSON.stringify(String(d.text||'').slice(0,90)));
  });
  // 墓碑
  const { data: m } = await sb.from('flash_meta').select('key,data').eq('user_id','cacd1a4b-ed34-4b60-b57e-7cf82f596aea').eq('key','deleted');
  const del = (m&&m[0]&&Array.isArray(m[0].data))?m[0].data:[];
  console.log('\n云端墓碑数:', del.length, '| 其中短文墓碑:', del.filter(x=>String(x).startsWith('p_')).length, del.filter(x=>String(x).startsWith('p_')).slice(0,10));
})();
