"""ヘッダー画像を作る。使い方: python3 tools/make_header.py kei-day1.html 1
記事のh1の行(<br>区切り)をそのまま画像に載せる。出力: assets/header-day1.jpg (1080x900)"""
import re, sys, html, pathlib, subprocess, tempfile, random

def lines_of(page):
    h = pathlib.Path(page).read_text()
    m = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
    return [re.sub(r'<[^>]+>', '', x) for x in m.group(1).split('<br>')]

def make(page, n, out):
    L = lines_of(page)
    mx = max(len(x) for x in L)
    size = int(min(96, 900 / mx, 740 / (len(L) * 1.42)))
    random.seed(n)
    petals = ''.join(
        f'<div class="p" style="left:{random.randint(2,92)}%;top:{random.choice([random.randint(2,18),random.randint(74,94)])}%;'
        f'transform:rotate({random.randint(0,180)}deg) scale({random.uniform(.6,1.3):.2f})"></div>' for _ in range(7))
    dust = ''.join(
        f'<i style="left:{random.randint(3,97)}%;top:{random.randint(3,97)}%;opacity:{random.uniform(.3,.9):.2f}"></i>' for _ in range(26))
    body = '<br>'.join(html.escape(x) for x in L)
    doc = f'''<!doctype html><meta charset="utf-8"><style>
html,body{{margin:0;width:1080px;height:900px;overflow:hidden;background:#000}}
.s{{position:relative;width:1080px;height:900px;overflow:hidden;
 background:radial-gradient(ellipse at 50% 108%,#7a0a1c 0%,#3a0610 38%,#0b0204 70%),#000}}
.s:before{{content:"";position:absolute;inset:0;background:
 radial-gradient(ellipse at 0 0,rgba(150,10,30,.55),transparent 38%),
 radial-gradient(ellipse at 100% 0,rgba(150,10,30,.5),transparent 34%),
 radial-gradient(ellipse at 100% 100%,rgba(140,8,28,.55),transparent 40%),
 radial-gradient(ellipse at 0 100%,rgba(140,8,28,.5),transparent 36%)}}
.p{{position:absolute;width:86px;height:56px;border-radius:70% 30% 70% 30%;
 background:linear-gradient(135deg,#d3283c,#6e0716);box-shadow:0 0 18px rgba(255,40,60,.35)}}
i{{position:absolute;width:5px;height:5px;border-radius:50%;background:#e8b45a;box-shadow:0 0 8px #e8b45a}}
.d{{position:absolute;top:70px;width:100%;text-align:center;font:600 34px "Hiragino Sans","Helvetica Neue",sans-serif;
 letter-spacing:.5em;color:#ff7480;text-shadow:0 0 14px #ff2a3a}}
.t{{position:absolute;left:0;right:0;top:160px;bottom:50px;display:flex;align-items:center;justify-content:center;text-align:center;
 font:700 {size}px/1.42 "Hiragino Mincho ProN","Yu Mincho",serif;color:#ff5a66;
 text-shadow:0 0 10px #ff2a3a,0 0 28px #d40f26,0 0 60px #9a0a1c}}
</style><div class="s">{petals}{dust}<div class="d">DAY {n}</div><div class="t"><div>{body}</div></div></div>'''
    tmp = pathlib.Path(tempfile.mkdtemp()) / 'h.html'
    tmp.write_text(doc)
    png = tmp.with_suffix('.png')
    subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--headless=new', '--hide-scrollbars',
                    '--window-size=1080,900', f'--screenshot={png}', f'file://{tmp}'], check=True, capture_output=True)
    subprocess.run(['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', '82', str(png), '--out', out], check=True, capture_output=True)

if __name__ == '__main__':
    make(sys.argv[1], sys.argv[2], f'assets/header-day{sys.argv[2]}.jpg')
