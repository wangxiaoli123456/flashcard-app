#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动补齐新词发音 —— 闭环守护脚本

背景：
  App 里"点读"走 <audio> 直连，不受 CORS 限制，所以任何新词都能发声；
  但"生成音频包"必须用 fetch 拿到音频字节再拼成一个 WAV，这一步受 CORS 限制，
  只有本仓库 audio/ 目录里已有文件的词才能打包。用户每天新挑的词是全新的，
  仓库里没有 → 生成时就被跳过。这是用户反复反馈"每次生成音频都不行"的根因。

本脚本做的事（全自动，无需用户参与）：
  1. 从云端读出用户所有卡片里的英文词（以及 App 上报的缺词）
  2. 比对仓库 audio/ 目录，找出没有发音的词
  3. 用有道/百度真人音抓下来，写进 audio/
  4. 更新 index.html 里的 GH_AUDIO_WORDS 清单
  5. 分批提交推送（大批量一次推会被 TLS 掐断）

用法：
  python3 auto_fill.py --manual          # 手动全量：拉云端词表 → 补齐 → 推送（原自动定时已禁用）
  python3 auto_fill.py --words a b c     # 只补指定词
  说明：不带 --manual / --words 则直接退出，不再无人值守自动运行（避免自动 bump 版本号、触发 App 全量校准、以及历史上覆盖主分支修复的风险）
"""
import json, os, sys, base64, re, subprocess, urllib.request, urllib.parse
import concurrent.futures as cf
import ssl, socket

ROOT = '/tmp/fc'
os.chdir(ROOT)

SB = 'https://bununhxkphvlvgvhanpk.supabase.co'
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'}


def b64en(w):
    return base64.b64encode(w.encode()).decode().replace('+', '-').replace('/', '_').replace('=', '')


def local_words():
    """仓库里已有发音的词（唯一词集合）"""
    ws = set()
    for f in os.listdir('audio'):
        b = f.rsplit('_', 1)[0]
        try:
            s = b + '=' * (-len(b) % 4)
            ws.add(base64.urlsafe_b64decode(s).decode())
        except Exception:
            pass
    return ws


def get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read()


def slim(path):
    """v341：新抓的音频一律转 单声道22050Hz/48kbps 并裁掉首尾静音。
    有道/百度原始返回常是 768kbps（1.4 秒的词要 132KB），加载慢正是「长句读不出来」的直接原因。"""
    import subprocess, shutil
    try:
        tmp = path + '.slim.mp3'
        af = ("silenceremove=start_periods=1:start_duration=0.03:start_threshold=-45dB:detection=peak,"
              "areverse,"
              "silenceremove=start_periods=1:start_duration=0.03:start_threshold=-45dB:detection=peak,"
              "areverse")
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', path, '-af', af,
                        '-ac', '1', '-ar', '22050', '-b:a', '48k', tmp],
                       capture_output=True, timeout=60)
        if os.path.exists(tmp) and os.path.getsize(tmp) > 400:
            shutil.move(tmp, path)
            return True
        if os.path.exists(tmp):
            os.remove(tmp)
    except Exception:
        pass
    return False


def fetch_one(w):
    if not w:
        return (w, None)
    wc = len(w.split())
    order = ['baidu', 'youdao'] if wc >= 5 else ['youdao', 'baidu']
    for src in order:
        f = 'audio/%s_%s.mp3' % (b64en(w), src)
        if os.path.exists(f) and os.path.getsize(f) > 400:
            return (w, src)
        url = ('https://dict.youdao.com/dictvoice?audio=' + urllib.parse.quote(w) + '&type=2') if src == 'youdao' \
            else ('https://fanyi.baidu.com/gettts?lan=en&text=' + urllib.parse.quote(w) + '&spd=3&source=web')
        try:
            d = get(url)
            if len(d) > 400:
                open(f, 'wb').write(d)
                slim(f)   # v341：落盘即瘦身，保持与既有音频库一致的体积
                return (w, src)
        except Exception:
            pass
    return (w, None)


def update_manifest():
    words = local_words()
    arr = 'const GH_AUDIO_WORDS=[' + ','.join(
        "'" + w.replace('\\', '\\\\').replace("'", "\\'") + "'" for w in sorted(words)) + '];'
    s = open('index.html', encoding='utf-8').read()
    s2, n = re.subn(r"const GH_AUDIO_WORDS=\[[^\]]*\];", arr, s, count=1)
    open('index.html', 'w', encoding='utf-8').write(s2)
    return len(words), n


def bump_version():
    import time
    s = open('index.html', encoding='utf-8').read()
    cur = re.search(r"const APP_VER='v(\d+)'", s)
    nxt = 'v%d' % (int(cur.group(1)) + 1 if cur else 1)
    s = re.sub(r"(?m)^(\s*)const APP_VER='v\d+';", lambda m: m.group(1) + "const APP_VER='%s';" % nxt, s)
    s = re.sub(r"var REL='\d+';", "var REL='%d000';" % int(time.time()), s)
    open('index.html', 'w', encoding='utf-8').write(s)
    open('version.txt', 'w').write(nxt)
    return nxt


def git_push(msg):
    # 推送前先与远程对齐，杜绝覆盖/分叉（auto_fill 历史上曾覆盖主分支修复，见 backup_v362 tag）
    subprocess.run(['git', 'fetch', 'origin'], capture_output=True, text=True)
    pr = subprocess.run(['git', 'pull', '--rebase', 'origin', 'main'],
                        capture_output=True, text=True)
    if pr.returncode != 0:
        subprocess.run(['git', 'rebase', '--abort'], capture_output=True, text=True)
        print('（pull --rebase 失败，已放弃本次推送，避免冲突覆盖：%s）'
              % ((pr.stderr or pr.stdout or '')[-300:]))
        return 'FAILED'
    # 收窄：只提交本任务负责的三个文件，绝不用 git add -A 误带/覆盖别人的改动
    subprocess.run(['git', 'add', 'audio', 'index.html', 'version.txt'], check=True)
    r = subprocess.run(['git', 'diff', '--cached', '--quiet'], capture_output=True)
    if r.returncode == 0:
        return 'no-change'
    subprocess.run(['git', 'commit', '-q', '-m', msg], check=True)
    for t in range(1, 6):
        out = subprocess.run(
            ['git', '-c', 'http.sslVersion=tlsv1.2', '-c', 'http.lowSpeedLimit=0',
             '-c', 'http.lowSpeedTime=999999', 'push', 'origin', 'main'],
            capture_output=True, text=True, timeout=280).stderr
        if 'main -> main' in out or 'up-to-date' in out:
            return 'pushed(try %d)' % t
        import time as _t
        _t.sleep(15)
    return 'FAILED'


def pull_reported():
    """从云端读取 App 上报的缺词清单（无需任何 key，公开可读）"""
    uid = 'cacd1a4b-ed34-4b60-b57e-7cf82f596aea'
    url = (SB + '/storage/v1/object/public/flash-media/' + uid + '/missing/missing.json')
    try:
        d = json.loads(get(url, timeout=20).decode('utf-8'))
        return d.get('words', []) or []
    except Exception as e:
        print('（读取云端上报失败：%s）' % e)
        return []


def cloud_card_words():
    """兜底：直接扫云端所有卡片的英文词。
    只靠 App 上报有风险 —— 万一某次上报失败/漏报，那个词就永远补不上，
    用户会反复遇到「今天的新词没发音」。这里用「云端卡片全量扫描」做双保险：
    只要卡在词库里、仓库里没有它的音频，就补。"""
    uid = 'cacd1a4b-ed34-4b60-b57e-7cf82f596aea'
    KEY = 'sb_publishable_l2HHWkiboFYihQ_taLY9ZA_O3Xxh0aH'
    # 匿名 key 会被 RLS 拦（返回空表），所以必须用内置账号登录后读
    tok = None
    try:
        body = json.dumps({'email': '315276700@qq.com',
                           'password': ''.join(chr(c) for c in [87, 120, 108, 53, 55, 55, 53, 50, 48])}).encode()
        req = urllib.request.Request(SB + '/auth/v1/token?grant_type=password', data=body,
                                     headers=dict(UA, apikey=KEY, **{'Content-Type': 'application/json'}))
        tok = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())['access_token']
    except Exception as e:
        print('（云端登录失败：%s）' % e)
        return set()

    ws, off = set(), 0
    try:
        while True:
            url = (SB + '/rest/v1/flash_cards?select=data&user_id=eq.' + uid
                   + '&offset=%d&limit=1000' % off)
            req = urllib.request.Request(url, headers=dict(UA, apikey=KEY,
                                                           **{'Authorization': 'Bearer ' + tok}))
            rows = json.loads(urllib.request.urlopen(req, timeout=40).read().decode())
            if not rows:
                break
            for r in rows:
                en = ((r.get('data') or {}).get('en') or '').strip().lower()
                if en:
                    ws.add(en)
            off += 1000
            if len(rows) < 1000:
                break
    except Exception as e:
        print('（读取云端卡片失败：%s）' % e)
    return ws


def main():
    # 【手动模式】自动定时任务已弃用：仅在显式 --manual / --words 时执行补齐与推送，
    # 避免无人值守地 bump APP_VER（触发 App 全量校准）及历史上覆盖主分支修复的风险。
    if '--manual' not in sys.argv and '--words' not in sys.argv:
        print('⚠️ auto_fill 已改为手动模式，无参数时直接退出（不影响 App 运行）。')
        print('   手动补齐请运行：')
        print('     全量补齐：python3 auto_fill.py --manual')
        print('     指定词  ：python3 auto_fill.py --words "apple" "banana"')
        return
    if '--words' in sys.argv:
        i = sys.argv.index('--words')
        words = [w.strip() for w in sys.argv[i + 1:] if w.strip()]
    else:
        # 默认：上报清单 ∪ 云端卡片全量（双保险，任一渠道命中都会补）
        rep = [w.strip().lower() for w in pull_reported() if w and w.strip()]
        print('云端上报的词: %d 个' % len(rep))
        card = cloud_card_words()
        print('云端卡片里的词: %d 个' % len(card))
        seen, words = set(), []
        for w in rep + sorted(card):
            if w and w not in seen:
                seen.add(w)
                words.append(w)

    have = local_words()
    need = [w for w in words if w and w not in have]
    print('已有发音: %d 词 | 待补: %d 词' % (len(have), len(need)))
    if not need:
        print('✅ 没有缺发音的词，无需操作')
        return

    ok, fail = [], []
    with cf.ThreadPoolExecutor(max_workers=10) as ex:
        for w, src in ex.map(fetch_one, need):
            (ok if src else fail).append(w)
    print('抓取成功 %d，失败 %d' % (len(ok), len(fail)))
    if fail:
        print('失败词:', '、'.join(fail[:30]))

    if not ok:
        return
    n, cnt = update_manifest()
    ver = bump_version()
    print('语音库总量: %d 词 | 版本: %s' % (n, ver))
    print('推送结果:', git_push('%s 自动补齐 %d 个新词发音' % (ver, len(ok))))


if __name__ == '__main__':
    main()
