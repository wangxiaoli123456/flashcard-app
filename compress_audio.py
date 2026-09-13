#!/usr/bin/env python3
# 音频瘦身：有道/百度返回的 mp3 多为 768kbps 高码率（1.4秒的词要 132KB），
# 加载慢是「长句读不出来」的直接原因。统一转 单声道 22050Hz 48kbps，并裁掉首尾静音。
import os,subprocess,sys,shutil
from concurrent.futures import ThreadPoolExecutor
SRC='audio'; TMP='audio_tmp'
os.makedirs(TMP,exist_ok=True)
files=[f for f in os.listdir(SRC) if f.endswith('.mp3')]
print('待处理:',len(files))

def dur(p):
    try:
        o=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',p],
                         capture_output=True,text=True,timeout=20).stdout.strip()
        return float(o)
    except Exception: return 0.0

def one(f):
    src=os.path.join(SRC,f); tmp=os.path.join(TMP,f)
    d0=dur(src)
    # 裁首尾静音(-45dB) + 转单声道 22050Hz 48kbps
    af=("silenceremove=start_periods=1:start_duration=0.03:start_threshold=-45dB:detection=peak,"
        "areverse,"
        "silenceremove=start_periods=1:start_duration=0.03:start_threshold=-45dB:detection=peak,"
        "areverse")
    try:
        subprocess.run(['ffmpeg','-y','-v','error','-i',src,'-af',af,'-ac','1','-ar','22050',
                        '-b:a','48k',tmp],capture_output=True,timeout=60)
    except Exception:
        return (f,'ERR',0,0)
    d1=dur(tmp); s1=os.path.getsize(tmp) if os.path.exists(tmp) else 0
    # 校验：裁坏了（时长不足原长 40% 或短于 0.2s）→ 退回「只转码不裁静音」
    if s1==0 or d1<0.2 or (d0>0 and d1<d0*0.4):
        try:
            subprocess.run(['ffmpeg','-y','-v','error','-i',src,'-ac','1','-ar','22050','-b:a','48k',tmp],
                           capture_output=True,timeout=60)
        except Exception: return (f,'ERR2',0,0)
        d1=dur(tmp); s1=os.path.getsize(tmp) if os.path.exists(tmp) else 0
        if s1==0: return (f,'FAIL',0,0)
        shutil.move(tmp,src); return (f,'转码',os.path.getsize(src) if False else s1,d1)
    shutil.move(tmp,src)
    return (f,'裁+转',s1,d1)

ok=err=0; tot_before=sum(os.path.getsize(os.path.join(SRC,f)) for f in files)
with ThreadPoolExecutor(max_workers=8) as ex:
    for i,r in enumerate(ex.map(one,files),1):
        if r[1] in ('ERR','ERR2','FAIL'): err+=1; print('  失败:',r)
        else: ok+=1
        if i%200==0: print('  已处理 %d/%d'%(i,len(files)))
tot_after=sum(os.path.getsize(os.path.join(SRC,f)) for f in files)
print('完成: 成功%d 失败%d'%(ok,err))
print('体积: %.1fMB -> %.1fMB (省 %.0f%%)'%(tot_before/1048576,tot_after/1048576,100*(1-tot_after/tot_before)))
shutil.rmtree(TMP,ignore_errors=True)
