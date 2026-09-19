import subprocess, sys, time, os
from playwright.sync_api import sync_playwright

try:
    subprocess.run(["pkill","-9","-f","chrome-linux64/chrome"], check=False)
except Exception:
    pass

URL = "http://127.0.0.1:8899/index.html"

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required",
                                    "--no-sandbox",
                                    "--use-fake-ui-for-media-stream"])
        pg = b.new_page(viewport={"width":390,"height":844}, is_mobile=True)
        msgs=[]
        pg.on("console", lambda m: msgs.append(m.text))
        pg.goto(URL, wait_until="load")
        time.sleep(1.0)

        # 注入：统计 HTMLMediaElement.play 调用次数（含 Audio 元素）
        pg.evaluate("""()=>{
          window.__playCount=0; window.__playKinds=[];
          const orig=HTMLMediaElement.prototype.play;
          HTMLMediaElement.prototype.play=function(){
            window.__playCount++;
            window.__playKinds.push(this.src ? this.src.slice(0,16) : 'unknown');
            try{return orig.apply(this,arguments);}catch(e){return Promise.reject(e);}
          };
        }""")

        # 模拟首次手势解锁
        pg.evaluate("()=>{ document.dispatchEvent(new Event('pointerdown')); }")
        pg.evaluate("()=>{ document.dispatchEvent(new Event('click')); }")
        time.sleep(0.3)

        # sfx 是否为全局函数
        is_global = pg.evaluate("()=> typeof window.sfx==='function'")
        has_ok = pg.evaluate("()=> typeof window.OK_WAV==='string' && window.OK_WAV.length>1000")
        has_bad = pg.evaluate("()=> typeof window.BAD_WAV==='string' && window.BAD_WAV.length>1000")

        # 触发答对/答错
        pg.evaluate("()=>{ try{window.sfx('ok');}catch(e){window.__err_ok=e.message;} }")
        pg.evaluate("()=>{ try{window.sfx('bad');}catch(e){window.__err_bad=e.message;} }")
        time.sleep(0.4)

        pc = pg.evaluate("()=>window.__playCount")
        kinds = pg.evaluate("()=>window.__playKinds")
        err_ok = pg.evaluate("()=>window.__err_ok||''")
        err_bad = pg.evaluate("()=>window.__err_bad||''")

        print("is_global_sfx =", is_global)
        print("has_OK_WAV    =", has_ok)
        print("has_BAD_WAV   =", has_bad)
        print("audio play() called count =", pc)
        print("play kinds (prefix)        =", kinds)
        print("err_ok =", err_ok, "| err_bad =", err_bad)
        print("RESULT:", "OK" if (is_global and has_ok and has_bad and pc>=2) else "FAIL")
        b.close()

if __name__=="__main__":
    main()
