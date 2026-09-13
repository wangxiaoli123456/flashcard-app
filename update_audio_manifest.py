import re, base64, glob, os
os.chdir('/tmp/fc')
# v343：清单顺带记录「该词在同源库里存的是哪个源」。
# 旧版只存词表，播放时靠「>=5词猜百度、短词猜有道」来选源，猜错就白等一次 404 往返 ——
# 实测 3 词里有 21 个只有百度版、4 词里 7 个只有百度版，按词长猜必然踩空，这正是长句「读得慢」的次因。
def dec(stem):
    b = stem.replace('-', '+').replace('_', '/')
    b += '=' * (-len(b) % 4)
    return base64.b64decode(b).decode('utf-8')

srcs = {}
for f in glob.glob('audio/*.mp3'):
    stem, src = os.path.basename(f)[:-4].rsplit('_', 1)
    try:
        w = dec(stem)
    except Exception as e:
        print('跳过', f, e); continue
    srcs.setdefault(w, set()).add(src)

words = sorted(srcs)
def arr(name, ws):
    return 'const %s=[' % name + ','.join("'" + w.replace('\\', '\\\\').replace("'", "\\'") + "'" for w in ws) + '];'

arr_all = arr('GH_AUDIO_WORDS', words)
# 只记录「没有 youdao 版、只有 baidu 版」的词 —— 其余默认走 youdao，清单因此很短
b_only = sorted(w for w, s in srcs.items() if 'baidu' in s and 'youdao' not in s)
b64 = lambda w: base64.b64encode(w.encode()).decode().replace('+', '-').replace('/', '_').replace('=', '')
arr_b = "const GH_AUDIO_BAIDU_KEYS=['" + "','".join(b64(w) for w in b_only) + "'];"

s = open('index.html', encoding='utf-8').read()
s, n1 = re.subn(r"const GH_AUDIO_WORDS=\[[^\]]*\];", arr_all, s, count=1)
s, n2 = re.subn(r"const GH_AUDIO_BAIDU_KEYS=\[[^\]]*\];", arr_b, s, count=1)
open('index.html', 'w', encoding='utf-8').write(s)
print('同源库词数: %d | 纯百度版: %d | 替换 GH_AUDIO_WORDS %d 处, BAIDU_KEYS %d 处' % (len(words), len(b_only), n1, n2))
