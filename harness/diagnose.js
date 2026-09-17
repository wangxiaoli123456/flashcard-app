// 诊断：真实库所有卡的图状态分布 + Storage 桶实际存量
const { createClient } = require('@supabase/supabase-js');
const SB_URL = 'https://bununhxkphvlvgvhanpk.supabase.co';
const KEY = 'sb_publishable_l2HHWkiboFYihQ_taLY9ZA_O3Xxh0aH';
const UID = 'cacd1a4b-ed34-4b60-b57e-7cf82f596aea';
const EMAIL = '315276700@qq.com', PW = 'Wxl577520';

function classify(d) {
  if (!d) return 'no-data';
  const hasImgData = !!(d.imgData && String(d.imgData).length > 50);
  const hasKeyOrUrl = !!(d.imgKey || d.imgUrl);
  if (hasImgData) return '有内嵌图';
  if (hasKeyOrUrl) return '无内嵌但有key/url';
  return '完全无图来源';
}

(async () => {
  const sb = createClient(SB_URL, KEY, { auth: { persistSession: false } });
  await sb.auth.signInWithPassword({ email: EMAIL, password: PW });

  // 全量卡
  let all = [], from = 0;
  while (true) {
    const { data, error } = await sb.from('flash_cards').select('id,data,updated_at').eq('user_id', UID).range(from, from + 999);
    if (error) { console.error('拉卡失败', error); process.exit(1); }
    all = all.concat(data);
    if (data.length < 1000) break;
    from += 1000;
  }

  const dist = {};
  const archDist = {};
  const noSource = [];
  for (const r of all) {
    const c = classify(r.data);
    dist[c] = (dist[c] || 0) + 1;
    const archived = r.data && r.data.archived ? '归档' : '未归档';
    archDist[archived + ' / ' + c] = (archDist[archived + ' / ' + c] || 0) + 1;
    if (c === '完全无图来源') noSource.push({ id: r.id, en: (r.data && (r.data.en || r.data.word)) || '', updated: r.updated_at, archived });
  }

  console.log('=== 卡片总数', all.length, '===');
  console.log('--- 按图状态 ---'); Object.entries(dist).forEach(([k, v]) => console.log('  ', k, v));
  console.log('--- 按 归档×图状态 ---'); Object.entries(archDist).forEach(([k, v]) => console.log('  ', k, v));
  console.log('--- 完全无图来源的老词(' + noSource.length + ') ---');
  noSource.slice(0, 30).forEach(c => console.log('  ', c.id, '|', c.en, '|', c.archived, '|', c.updated));
  if (noSource.length > 30) console.log('  ... 共', noSource.length, '条');

  // Storage 桶该用户目录
  try {
    const { data: files, error } = await sb.storage.from('flash-media').list(UID, { limit: 2000 });
    if (error) { console.error('列 Storage 失败', error); }
    else {
      console.log('--- Storage 桶 flash-media/' + UID + ' 文件数', files.length, '---');
      const names = files.map(f => f.name);
      // 看这些无源老词有没有对应图片文件名匹配
      const matched = noSource.filter(c => {
        // imgKey 可能就是文件名；老词若曾上传，可能以 id 或 en 命名
        return names.some(n => n === c.id + '.jpg' || n === c.id + '.png' || n.startsWith(c.id));
      });
      console.log('无图来源老词中，Storage 文件名疑似匹配 id 的:', matched.length);
      if (files.length) console.log('  前 10 个文件名:', names.slice(0, 10));
    }
  } catch (e) { console.error('Storage 异常', e.message); }
})().catch(e => { console.error('异常', e); process.exit(2); });
