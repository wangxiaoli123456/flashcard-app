#!/usr/bin/env bash
# 闪卡 App 一键发布脚本
#
# 作用：保证 version.txt / index.html 里的 APP_VER / head 里的 REL 三件套永远同步。
# 背景：曾因只改了 version.txt、漏改 APP_VER，导致手机端「发现新版本」绿色横幅
#       无限弹出、点刷新也没用（检测逻辑是 nv===APP_VER，永远不等）。
#       本脚本把三件套同步自动化，从根本上杜绝该事故复发。
#
# 用法：bash deploy.sh "本次改动说明"
# 例：  bash deploy.sh "修复前后音重复"
set -e
cd "$(dirname "$0")"

MSG="${1:-update}"

# 1) 计算下一个版本号（v303 -> v304）
CUR=$(tr -d ' \r\n' < version.txt 2>/dev/null || echo "v0")
NUM=${CUR#v}
NEXT="v$((NUM + 1))"

# 2) 同步三件套（APP_VER + REL 写回 index.html，version.txt 单独写）
PYBIN=$(command -v python3 || command -v python3.11 || command -v python)
"$PYBIN" - "$NEXT" <<'PY'
import re, sys, time
nxt = sys.argv[1]
s = open('index.html', encoding='utf-8').read()
s, n1 = re.subn(r"const APP_VER='v\d+';", "const APP_VER='%s';" % nxt, s)
s, n2 = re.subn(r"var REL='\d+';", "var REL='%d000';" % int(time.time()), s)
open('index.html', 'w', encoding='utf-8').write(s)
print('  APP_VER 替换 %d 处，REL 替换 %d 处' % (n1, n2))
PY
echo "$NEXT" > version.txt

# 3) 发布前校验：三件套必须一致，否则拒绝提交
AV=$(grep -oE "const APP_VER='[^']+'" index.html | head -1 | grep -oE "v[0-9]+")
VT=$(tr -d ' \r\n' < version.txt)
if [ "$AV" != "$VT" ]; then
  echo "❌ 版本不一致，已中止：APP_VER=$AV  version.txt=$VT"
  exit 1
fi
if ! grep -qE "var REL='[0-9]+'" index.html; then
  echo "❌ 未找到 REL 缓存戳，已中止"
  exit 1
fi
echo "✅ 版本三件套已同步 -> $NEXT"

# 4) 提交并推送（tlsv1.2 是为兼容受限网络出口，正常环境无副作用）
git add -A
git commit -m "flashcard $NEXT: $MSG"
git -c http.sslVersion=tlsv1.2 push origin main
echo "✅ 已推送 $NEXT"
