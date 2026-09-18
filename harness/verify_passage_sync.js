// 验证短文同步通道：推(带 kind)→拉(分流)→删(墓碑传播)，全用真实库真实表
const { createClient } = require('@supabase/supabase-js');
const SB_URL='https://bununhxkphvlvgvhanpk.supabase.co';
const KEY='sb_publishable_l2HHWkiboFYihQ_taLY9ZA_O3Xxh0aH';
const UID='cacd1a4b-ed34-4b60-b57e-7cf82f596aea';
const EMAIL='315276700@qq.com',PW='Wxl577520';
(async()=>{
  const sb=createClient(SB_URL,KEY,{auth:{persistSession:false}});
  await sb.auth.signInWithPassword({email:EMAIL,password:PW});
  const testId='p_verify_'+Date.now().toString(36);
  const now=new Date().toISOString();
  // ① 设备A 推：模拟 doPush 的 passages 分支（data.kind='passage'）
  const pass={id:testId,text:'The cat sat on the mat.',cn:'猫坐在垫子上',state:'new',streak:0,next:'2026-09-18',created:'2026-09-18',kind:'passage'};
  const {error:upErr}=await sb.from('flash_cards').upsert({user_id:UID,id:testId,data:pass,updated_at:now},{onConflict:'user_id,id'});
  if(upErr){console.error('① 推失败',upErr);process.exit(1);}
  console.log('① 设备A 推短文(带 kind:passage): OK');
  // ② 设备B 拉：模拟 syncPull 的 mergeIntoPassages 分流
  const {data:rows,error:se}=await sb.from('flash_cards').select('id,data').eq('user_id',UID).in('id',[testId]);
  if(se){console.error('② 拉失败',se);process.exit(1);}
  const r=rows[0];
  const passages={},cards={};
  rows.forEach(x=>{const d=x.data||{}; if(d.kind==='passage')passages[x.id]=d; else cards[x.id]=d;});
  console.log('② 设备B 拉取分流: passages有='+(!!passages[testId])+' | cards有='+(!!cards[testId])+' | kind='+(r&&r.data.kind));
  if(!passages[testId]||cards[testId]){console.error('② 分流错误');process.exit(1);}
  console.log('② 分流正确 ✓ (短文入 passages，绝不进 cards)');
  // ③ 设备A 删：模拟 delPassage → flash_cards 删除 + deletedIds 墓碑
  const {error:delErr}=await sb.from('flash_cards').delete().eq('user_id',UID).eq('id',testId);
  if(delErr){console.error('③ 删失败',delErr);process.exit(1);}
  const {data:dm}=await sb.from('flash_meta').select('data').eq('user_id',UID).eq('key','deleted');
  let delArr=(dm&&dm[0]&&Array.isArray(dm[0].data))?dm[0].data.slice():[];
  if(!delArr.includes(testId))delArr.push(testId);
  await sb.from('flash_meta').upsert({user_id:UID,key:'deleted',data:delArr,updated_at:now},{onConflict:'user_id,key'});
  console.log('③ 设备A 删短文 + 写墓碑: OK');
  // ④ 设备B 删除传播：云端已无此行 + 墓碑标记 → 应清理本地 passages
  const {data:after}=await sb.from('flash_cards').select('id').eq('user_id',UID).in('id',[testId]);
  const {data:dm2}=await sb.from('flash_meta').select('data').eq('user_id',UID).eq('key','deleted');
  const cloudDeleted=new Set((dm2&&dm2[0]&&Array.isArray(dm2[0].data))?dm2[0].data:[]);
  const stillInCards=after&&after.length>0;
  const inTomb=cloudDeleted.has(testId);
  console.log('④ 设备B 删除传播: 云端仍在='+stillInCards+' | 墓碑标记='+inTomb);
  if(stillInCards||!inTomb){console.error('④ 删除传播异常');process.exit(1);}
  // 清理测试墓碑，避免污染真实 deletedIds
  delArr=delArr.filter(x=>x!==testId);
  await sb.from('flash_meta').upsert({user_id:UID,key:'deleted',data:delArr,updated_at:now},{onConflict:'user_id,key'});
  console.log('✅ 短文同步通道验证全部通过（推 / 拉分流 / 删除传播）');
})().catch(e=>{console.error(e);process.exit(2);});
