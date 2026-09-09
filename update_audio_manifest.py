import re, base64, glob, os
os.chdir('/tmp/fc')
words=set()
for f in glob.glob('audio/*.mp3'):
    b=os.path.basename(f).rsplit('_',1)[0].replace('-','+').replace('_','/')
    b+='='*(-len(b)%4)
    try: words.add(base64.b64decode(b).decode('utf-8'))
    except Exception as e: print('跳过',f,e)
words=sorted(words)
arr='const GH_AUDIO_WORDS=['+','.join("'"+w.replace('\\','\\\\').replace("'","\\'")+"'" for w in words)+'];'
s=open('index.html',encoding='utf-8').read()
s2,n=re.subn(r"const GH_AUDIO_WORDS=\[[^\]]*\];", arr, s, count=1)
open('index.html','w',encoding='utf-8').write(s2)
print('同源库词数:',len(words),'| 替换处数:',n)
print(words)
