const fs = require('fs');
const html = fs.readFileSync('/tmp/fc/index.html', 'utf8');
const re = /<script\b[^>]*>([\s\S]*?)<\/script>/gi;
let m, n = 0, errs = 0;
const blocks = [];
while ((m = re.exec(html))) { const code = m[1]; if (!code.trim()) continue; blocks.push(code); }
console.log('内联 script 块数:', blocks.length);
blocks.forEach((code, i) => {
  n++;
  try { new Function(code); }
  catch (e) { errs++; console.error('  script#' + (i + 1) + ' 语法错误: ' + e.message); }
});
console.log('语法检查完成: 块 ' + n + ' | 错误 ' + errs);
const joined = blocks.join('\n');
['forceFullSync', 'function syncPull', 'const APP_VER=', 'idxFullCounter', 'lastPullIso'].forEach(k => {
  const esc = k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const c = (joined.match(new RegExp(esc, 'g')) || []).length;
  console.log('  引用/定义「' + k + '」出现 ' + c + ' 次');
});
