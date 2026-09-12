#!/usr/bin/env bash
# 分批提交并推送 audio/ 下的新音频，避免一次性推 22MB 被 TLS 掐断
cd /tmp/fc
BATCH=80
PUSH_OPTS="-c http.sslVersion=tlsv1.2 -c http.lowSpeedLimit=0 -c http.lowSpeedTime=999999 -c http.postBuffer=524288000"

# 先确保工作区干净地按批提交
mapfile -t FILES < <(git status --porcelain -- audio/ | awk '{print $2}')
TOTAL=${#FILES[@]}
echo "待提交音频文件: $TOTAL"

i=0
while [ $i -lt $TOTAL ]; do
  chunk=("${FILES[@]:$i:$BATCH}")
  git add "${chunk[@]}"
  git commit -q -m "v335 补充儿童英语真人发音（第 $((i/BATCH+1)) 批，${#chunk[@]} 个）"
  echo "已提交第 $((i/BATCH+1)) 批（${#chunk[@]} 个）"

  # 推送，失败重试最多 6 次
  ok=0
  for t in 1 2 3 4 5 6; do
    OUT=$(timeout 240 git $PUSH_OPTS push origin main 2>&1)
    if echo "$OUT" | grep -q "main -> main\|up-to-date"; then
      echo "  ✅ 推送成功（第 $t 次尝试）"
      ok=1
      break
    else
      echo "  ⚠️ 第 $t 次失败，等待重试…"
      sleep 20
    fi
  done
  if [ $ok -eq 0 ]; then echo "  ❌ 本批推送失败，中止"; exit 1; fi

  i=$((i + BATCH))
done
echo "🎉 全部音频推送完成"
