# 把云端词库里缺发音的词全部抓下来，补进同源库 audio/
# 每个词只存一个最可用的源：优先有道（音质最好），长句/失败时用百度整句真人音
import json, os, base64, urllib.request, urllib.parse, concurrent.futures as cf, sys, time
os.chdir('/tmp/fc')
UA={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'}
def b64en(w): return base64.b64encode(w.encode()).decode().replace('+','-').replace('/','_').replace('=','')
def youdao(w): return 'https://dict.youdao.com/dictvoice?audio='+urllib.parse.quote(w)+'&type=2'
def baidu(w):  return 'https://fanyi.baidu.com/gettts?lan=en&text='+urllib.parse.quote(w)+'&spd=3&source=web'
def get(url,timeout=25):
    req=urllib.request.Request(url,headers=UA)
    return urllib.request.urlopen(req,timeout=timeout).read()
def fetch_one(w):
    if not w: return (w,'skip','空')
    wc=len(w.split())
    order=['baidu','youdao'] if wc>=5 else ['youdao','baidu']   # 多词句子有道常返500，直接先用百度
    for src in order:
        f='audio/%s_%s.mp3'%(b64en(w),src)
        if os.path.exists(f) and os.path.getsize(f)>400: return (w,src,'已存在')
        try:
            d=get(youdao(w) if src=='youdao' else baidu(w))
            if len(d)>400:
                open(f,'wb').write(d); return (w,src,'%d'%len(d))
        except Exception as e:
            pass
    return (w,None,'失败')
if __name__=='__main__':
    words=json.load(open(sys.argv[1] if len(sys.argv)>1 else '/tmp/miss.json'))
    print('待补词数:',len(words))
    ok={}; fail=[]
    with cf.ThreadPoolExecutor(max_workers=10) as ex:
        for i,(w,src,info) in enumerate(ex.map(fetch_one,words),1):
            if src and src!='skip': ok[w]=src
            else: fail.append(w)
            if i%100==0: print('  进度 %d/%d'%(i,len(words)),flush=True)
    print('成功 %d，失败 %d'%(len(ok),len(fail)))
    if fail: print('失败词:', '、'.join(fail[:40]))
    json.dump(fail,open('/tmp/fail.json','w'),ensure_ascii=False)
