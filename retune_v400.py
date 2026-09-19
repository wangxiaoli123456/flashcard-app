#!/usr/bin/env python3
# v400：重调答对/答错 wav 音色，还原 v394「清脆明亮高频叮叮叮」听感；
# 并去掉加练开始时的 sfx('start') 两声短滴音（满足「除加练答题外不要滴声」）。
import wave, struct, math, base64, io, re

SR = 22050  # 更高采样率 → 更接近原 WebAudio 44.1k 的清脆明亮

def tone(freq, dur, sr=SR, peak=0.40, decay=22.0):
    n = int(sr * dur)
    fa = int(sr * 0.004)  # 4ms 快起音
    out = []
    for i in range(n):
        t = i / sr
        if i < fa:
            env = i / fa
        else:
            env = math.exp(-(t - fa / sr) * decay)  # 指数衰减（清脆尾音）
        s = peak * env * math.sin(2 * math.pi * freq * t)
        out.append(int(max(-1.0, min(1.0, s)) * 32767))
    return out

def seq(freqs, gap, sr=SR):
    frames = []
    for f in freqs:
        frames += tone(f, gap + 0.02)  # 每音时长随间隔给一点尾部
    return frames

def b64(frames):
    buf = io.BytesIO()
    w = wave.open(buf, 'wb')
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(b''.join(struct.pack('<h', v) for v in frames))
    w.close()
    return base64.b64encode(buf.getvalue()).decode()

# 上行叮叮叮：频率与原 v394 完全一致（523/659/784/1046），间隔 0.11s
OK_B64  = b64(seq([523.25, 659.25, 783.99, 1046.5], 0.11))
# 下行答错：220/174.61/146.83，间隔 0.22s
BAD_B64 = b64(seq([220.0, 174.61, 146.83], 0.22))

print("OK_WAV b64 len =", len(OK_B64))
print("BAD_WAV b64 len =", len(BAD_B64))

path = '/tmp/fc/index.html'
html = open(path, encoding='utf-8').read()

# 1) 仅替换 wav 数据（不动已插入的工厂/逻辑）
assert html.count('const OK_WAV="') == 1 and html.count('const BAD_WAV="') == 1
html = re.sub(r'const OK_WAV="[^"]*";', 'const OK_WAV="%s";' % OK_B64, html, count=1)
html = re.sub(r'const BAD_WAV="[^"]*";', 'const BAD_WAV="%s";' % BAD_B64, html, count=1)

# 2) 去掉加练开始那两声短滴音 sfx('start')
OLD_START = "  sfx('start');\n"
assert html.count(OLD_START) == 1, "sfx('start') 出现次数=%d" % html.count(OLD_START)
html = html.replace(OLD_START,
    "  /* v400：去掉加练开始的两声短滴音 sfx('start')，符合\"除加练答题外不要滴声\"；保留下方 TTS\"开始抢答\"语音提示 */\n", 1)

open(path, 'w', encoding='utf-8').write(html)
print("retune + 去开始音 OK. new size =", len(html))
