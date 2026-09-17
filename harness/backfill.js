// 一次性补齐：把"有 imgKey/imgUrl 但无 imgData"的卡，从 Storage 公共 URL 抓图内嵌进 DB
// 这样所有设备以后自带图，彻底不依赖 Storage 读图（根治"归档不出图/时有时无"）
const { createClient } = require('@supabase/supabase-js');
const SB_URL = 'https://bununhxkphvlvgvhanpk.supabase.co';
const KEY = 'sb_publishable_l2HHWkiboFYihQ_taLY9ZA_O3Xxh0aH';
const UID = 'cacd1a4b-ed34-4b60-b57e-7cf82f596aea';
const EMAIL = '315276700@qq.com', PW = 'Wxl577520';
const RUN = process.argv.includes('--run');
const LIMIT = process.argv.includes('--limit') ? parseInt(process.argv[process.argv.indexOf('--limit') + 1]) : 0;

function mimeFromBytes(buf) {
  if (buf[0] === 0xff && buf[1] === 0xd8) return 'image/jpeg';
  if (buf[0] === 0x89 && buf[1] === 0x50) return 'image/png';
  if (buf[0] === 0x52 && buf[1] === 0x49 && buf[2] === 0x46) return 'image/webp';
  return 'image/jpeg';
}
function toDataURL(buf) {
  const b64 = buf.toString('base64');
  return 'data:' + mimeFromBytes(buf) + ';base64,' + b64;
}

(async () => {
  const sb = createClient(SB_URL, KEY, { auth: { persistSession: false } });
  await sb.auth.signInWithPassword({ email: EMAIL, password: PW });

  // 取全部卡(id, data, updated_at)
  let all = [], from = 0;
  while (true) {
    const { data, error } = await sb.from('flash_cards').select('id,data,updated_at').eq('user_id', UID).range(from, from + 999);
    if (error) { console.error('拉卡失败', error); process.exit(1); }
    all = all.concat(data);
    if (data.length < 1000) break;
    from += 1000;
  }
  const cands = all.filter(r => (r.data && (r.data.imgKey || r.data.imgUrl)) && !r.data.imgData);
  console.log('卡片总数', all.length, '| 待补图候选', cands.length, RUN ? '(执行模式)' : '(dry-run，加 --run 执行)');
  if (!RUN) { console.log('候选取样:', cands.slice(0, 5).map(c => ({ id: c.id, en: c.data.en, imgKey: c.data.imgKey, imgUrl: (c.data.imgUrl || '').slice(0, 40) }))); return; }

  const todo = LIMIT ? cands.slice(0, LIMIT) : cands;
  let ok = 0, skip = 0, fail = 0, totalBytes = 0;
  const rows = [];
  for (const c of todo) {
    const url = c.data.imgUrl || (c.data.imgKey ? `${SB_URL}/storage/v1/object/public/flash-media/${UID}/${c.data.imgKey}` : null);
    if (!url) { skip++; continue; }
    try {
      const res = await fetch(url);
      if (!res.ok) { console.warn('  跳过(HTTP ' + res.status + '):', c.id, c.data.en); skip++; continue; }
      const buf = Buffer.from(await res.arrayBuffer());
      if (buf.length < 200) { skip++; continue; }
      const du = toDataURL(buf);
      totalBytes += du.length;
      const nd = Object.assign({}, c.data); nd.imgData = du;
      rows.push({ user_id: UID, id: c.id, data: nd, updated_at: new Date().toISOString() });
      ok++;
    } catch (e) { console.warn('  失败:', c.id, e.message); fail++; }
  }
  // 分批 upsert
  for (let i = 0; i < rows.length; i += 20) {
    const chunk = rows.slice(i, i + 20);
    const { error } = await sb.from('flash_cards').upsert(chunk, { onConflict: 'user_id,id' });
    if (error) { console.error('  upsert 失败:', error); fail += chunk.length; ok -= chunk.length; }
  }
  console.log(`\n补齐完成：成功 ${ok} 张，跳过 ${skip}，失败 ${fail}；新增 imgData 体积约 ${(totalBytes / 1024 / 1024).toFixed(1)} MB`);
  // 验证
  const { count } = await sb.from('flash_cards').select('*', { count: 'exact', head: true }).eq('user_id', UID).not('data->>imgData', 'is', null);
  console.log('验证：现在带 imgData 的卡 =', count, '/', all.length);
})().catch(e => { console.error('异常', e); process.exit(2); });
