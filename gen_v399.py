#!/usr/bin/env python3
# 生成"叮叮叮"答对/答错音 wav(data URI)，并替换 index.html 的 sfx 实现为 <audio>+wav，
# 播放前 speechSynthesis.cancel() 清场，彻底规避 iOS TTS/WebAudio 争用导致的间歇性无声。
import wave, struct, math, base64, io, re

SR = 11025
AMP = 0.55

def tone(freq, dur):
    n = int(SR * dur)
    fa = int(SR * 0.006)
    out = []
    for i in range(n):
        s = math.sin(2 * math.pi * freq * (i / SR))
        if i < fa:
            env = i / fa
        elif i > n - fa:
            env = (n - i) / fa
        else:
            env = 1.0
        out.append(int(max(-1.0, min(1.0, AMP * env * s)) * 32767))
    return out

def seq_wav(freqs, dur_each):
    frames = []
    for f in freqs:
        frames += tone(f, dur_each)
    return frames

def to_b64(frames):
    buf = io.BytesIO()
    w = wave.open(buf, 'wb')
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(b''.join(struct.pack('<h', v) for v in frames))
    w.close()
    return base64.b64encode(buf.getvalue()).decode()

OK_B64  = to_b64(seq_wav([523.25, 659.25, 783.99, 1046.5], 0.13))   # 上行叮叮叮(原始频率)
BAD_B64 = to_b64(seq_wav([220.0, 174.61, 146.83], 0.20))            # 下行(答错)

print("OK_WAV b64 len =", len(OK_B64))
print("BAD_WAV b64 len =", len(BAD_B64))

# ---- 读取 index.html ----
path = '/tmp/fc/index.html'
html = open(path, encoding='utf-8').read()

# 1) 在 `let _actx=null;` 之前插入 wav 常量 + Audio 全局变量 + _aud 工厂
INSERT = (
    "/* v399：答对/答错提示音改用预生成 wav + 标准 HTMLAudio 播放，\n"
    "   彻底规避 iOS 上 speechSynthesis(TTS) 与 WebAudio 振荡器争用同一音频会话、\n"
    "   导致\"叮叮叮\"被静音/间歇没声的问题；同时恢复用户原本熟悉的原始高频上行叮叮叮(523/659/784/1046Hz)。 */\n"
    f"const OK_WAV=\"{OK_B64}\";\n"
    f"const BAD_WAV=\"{BAD_B64}\";\n"
    "let _okAud=null,_badAud=null;\n"
    "function _aud(kind){\n"
    "  try{\n"
    "    if(kind==='ok'){ if(!_okAud){_okAud=new Audio('data:audio/wav;base64,'+OK_WAV);_okAud.preload='auto';} return _okAud; }\n"
    "    if(kind==='bad'){ if(!_badAud){_badAud=new Audio('data:audio/wav;base64,'+BAD_WAV);_badAud.preload='auto';} return _badAud; }\n"
    "  }catch(e){}\n"
    "  return null;\n"
    "}\n"
)
assert html.count('let _actx=null;') == 1
html = html.replace('let _actx=null;', INSERT + 'let _actx=null;', 1)

# 2) 替换 sfx 整个函数块（到 /* v397： 注释之前）
start = html.index('function sfx(kind){')
end = html.index('/* v397：iOS 必须')
NEW_SFX = (
    "function sfx(kind){\n"
    "  try{\n"
    "    if(kind==='ok'||kind==='bad'){\n"
    "      // v399：播放前强制取消任何进行中的 TTS，释放 iOS 音频会话，避免被 TTS 压掉\n"
    "      if(window.speechSynthesis){ try{speechSynthesis.cancel();}catch(e){} }\n"
    "      const a=_aud(kind);\n"
    "      if(a){\n"
    "        setTimeout(function(){ try{ a.pause();a.currentTime=0;var p=a.play();if(p&&p.catch)p.catch(function(){}); }catch(e){} },60);\n"
    "      }\n"
    "      return;\n"
    "    }\n"
    "    // 其他非关键音(start/pop)仍走 WebAudio 振荡器\n"
    "    const ctx=ac();if(!ctx)return;\n"
    "    const seq={start:[659.25,880],pop:[987.77,1318.5]};\n"
    "    const freqs=seq[kind];if(!freqs)return;\n"
    "    const play=function(){\n"
    "      const now=ctx.currentTime;\n"
    "      freqs.forEach(function(f,i){\n"
    "        const o=ctx.createOscillator(),g=ctx.createGain();\n"
    "        o.type='sine';o.frequency.value=f;\n"
    "        const t=now+i*0.1;\n"
    "        g.gain.setValueAtTime(0.0001,t);\n"
    "        g.gain.exponentialRampToValueAtTime(0.3,t+0.02);\n"
    "        g.gain.exponentialRampToValueAtTime(0.0001,t+0.45);\n"
    "        o.connect(g);g.connect(ctx.destination);\n"
    "        o.start(t);o.stop(t+0.5);\n"
    "      });\n"
    "    };\n"
    "    if(ctx.state==='suspended'){ctx.resume().then(play).catch(play);}else play();\n"
    "  }catch(e){}\n"
    "}\n"
    "/* v399：答对/答错音已改用预生成 wav + HTMLAudio（见上方 OK_WAV/BAD_WAV 常量），\n"
    "   播放前 speechSynthesis.cancel() 清场，从根消除 iOS 上 TTS 与 WebAudio 争用导致的间歇无声。 */\n"
)
html = html[:start] + NEW_SFX + html[end:]

# 3) 早解锁监听：首次手势内顺便解锁并预载 Audio 实例（iOS 要求手势内首次 play 才解锁）
OLD_UNLOCK = (
    "['pointerdown','touchstart','click'].forEach(function(ev){\n"
    "  document.addEventListener(ev,function(){try{ac();}catch(e){}},true);\n"
    "});"
)
NEW_UNLOCK = (
    "['pointerdown','touchstart','click'].forEach(function(ev){\n"
    "  document.addEventListener(ev,function(){\n"
    "    try{ac();}catch(e){}\n"
    "    try{ if(window.speechSynthesis) speechSynthesis.cancel(); }catch(e){}\n"
    "    try{ _aud('ok');_aud('bad'); [_okAud,_badAud].forEach(function(a){ if(a){ var p=a.play(); if(p&&p.catch)p.catch(function(){}); setTimeout(function(){try{a.pause();a.currentTime=0;}catch(e){}},20); } }); }catch(e){}\n"
    "  },true);\n"
    "});"
)
assert html.count(OLD_UNLOCK) == 1
html = html.replace(OLD_UNLOCK, NEW_UNLOCK, 1)

open(path, 'w', encoding='utf-8').write(html)
print("replaced OK. new file size =", len(html))
