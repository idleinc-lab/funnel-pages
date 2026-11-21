#!/usr/bin/env python3
"""スマホ専用の記事HTMLを一発生成する。

使い方:  python3 tools/build_article.py 原稿.txt 出力名.html [--brand ケイ]

原稿の書き方（1行=1フレーズ。ここで区切った位置がそのまま改行になる）
  # タイトル             h1（「/」で意味のまとまりごとに改行。見出し・!key・!noteも同様）
  ## 見出し              h2
  ### 小見出し           h3
  !lead 小さなキャッチ    h1の上の薄字
  !rule 太字のルール見出し
  ---                    区切り線
  ::: box ... :::        ピンクの枠（話の転換・補足）
  ::: box key ... :::    太字ワインレッドの強調枠（一番言いたい転換の一文）
  ::: voice ... :::      ふきだし風の枠（周囲の声・本音・読者の心の声）
  !key 一文              太字ワインレッドの強調行（ケイの一言・問いかけ）
  !note 一文             ボタン直前の小さな注記（「任意です」など）
  ::: tpl LINE用|場面 ... :::   テンプレカード（会話用なら「会話用|場面」）
  [ボタン文言](URL)       ボタン（URLを @day1 のように書くと src/forms.txt の day1=URL に置き換わる）
  !sign ケイ             右寄せ署名
  空行                   段落の区切り

自動で行うこと
  ・1ブロック最大4行。超えたら均等に分けて空行1行を挿入（。」！？…で終わる行を優先）
  ・1行の最大字数を超えた行を警告（本文17字／枠・カード15字）。手で区切り直すこと
  ・全体の見た目は assets/style.css（ゴシック・ワインレッド）を共通利用
"""
import re, sys, html, pathlib

MAIN_CAP, BOX_CAP, MAX_LINES = 17, 15, 4


TERM = ("。", "」", "！", "？", "…")


def split_groups(lines):
    """最大4行ごとに分割。文の終わり(。」！？…)で切れる案を最優先、無ければ読点、最後に文中。"""
    n = len(lines)
    if n <= MAX_LINES:
        return [lines]

    def bcost(i):  # i行目の後ろで切るコスト
        t = lines[i - 1].rstrip()
        return 0 if t.endswith(TERM) else 4 if t.endswith("、") else 9

    def gcost(sz):
        return 1 + {1: 3, 2: 0.5, 3: 0, 4: 0.3}[sz]

    INF = float("inf")
    best = [(INF, 0)] * (n + 1)
    best[0] = (0, 0)
    for j in range(1, n + 1):
        for sz in range(1, MAX_LINES + 1):
            i = j - sz
            if i < 0 or best[i][0] == INF:
                continue
            c = best[i][0] + gcost(sz) + (bcost(j) if j < n else 0)
            if c < best[j][0]:
                best[j] = (c, i)
    groups, j = [], n
    while j > 0:
        i = best[j][1]
        groups.append(lines[i:j])
        j = i
    return groups[::-1]


KINSOKU = set("、。」』）)…！？ー々ぁぃぅぇぉゃゅょっ")
PARTICLES = set("はがをにでとものへ")


def _bcost(line, i):
    """line を i 文字目で切るときの不自然さ（小さいほど良い）"""
    prev, nxt = line[i - 1], line[i]
    if nxt in KINSOKU or prev in "「『（(":
        return 100
    # 括弧の内側で切る場合は少し不利
    depth = line[:i].count("「") - line[:i].count("」") + line[:i].count("（") - line[:i].count("）")
    pen = 2 if depth > 0 else 0
    if prev in "、。":
        return pen
    if prev in "」』）)" or nxt in "「『（(":
        return pen + 1
    if prev + nxt in ("もう", "とい", "でき", "にも", "では", "には", "とは", "まで", "ので", "のに", "ない", "なら", "こと", "もの", "ため", "から", "より", "ほど"):
        return pen + 30 if prev + nxt not in ("では", "には", "とは") else pen + 4
    if prev in PARTICLES and nxt not in PARTICLES:
        return pen + 3
    if prev in "てしたり":
        return pen + 6
    return pen + 30


def auto_split(line, cap):
    """cap を超える行を、文節の切れ目（読点・助詞・括弧の前後）でできるだけ均等に分割する。"""
    n = len(line)
    if n <= cap:
        return [line]
    k = -(-n // cap)
    ideal = n / k
    best, bc = None, 1e9
    for i in range(max(1, n - cap * (k - 1) if k > 1 else 1), min(cap, n - 1) + 1):
        left = line[:i]
        if len(left) > cap:
            continue
        c = _bcost(line, i) + 0.6 * abs(i - ideal)
        if i < 3 or n - i < 3:
            c += 20
        if c < bc:
            best, bc = i, c
    if best is None:
        best = cap
    return [line[:best]] + auto_split(line[best:], cap)


def brs(t):
    """見出し・強調行の「/」を改行(<br>)にする"""
    return html.escape(t, quote=False).replace("/", "<br>")


def para(lines, cap, warns, cls=""):
    lines = [x for l in lines for x in auto_split(l, cap)]
    for l in lines:
        if len(l) > cap:
            warns.append(f"{len(l)}字 > {cap}: {l}")
    out = []
    for g in split_groups(lines):
        c = f' class="{cls}"' if cls else ""
        out.append(f"<p{c}>" + "<br>\n".join(html.escape(x, quote=False) for x in g) + "</p>")
    return "\n\n".join(out)


def load_forms(path):
    """原稿と同じフォルダの forms.txt（名前=URL を1行ずつ）を読む。ボタンのURLに @名前 と書くと置き換わる。"""
    forms = {}
    f = pathlib.Path(path).parent / "forms.txt"
    if f.exists():
        for ln in f.read_text().splitlines():
            if "=" in ln and not ln.lstrip().startswith("#"):
                k, _, v = ln.partition("=")
                forms[k.strip()] = v.strip()
    return forms


def build(src, brand, forms=None):
    forms = forms or {}
    warns, out, buf = [], [], []
    title = "無題"
    mode = None  # None | box | tpl
    tpl_head = None

    def flush(cap):
        nonlocal buf
        if buf:
            out.append(para(buf, cap, warns))
            buf = []

    for raw in src.splitlines():
        line = raw.rstrip()
        cap = BOX_CAP if mode else MAIN_CAP
        if line.startswith("::: voice"):
            flush(cap); mode = "box"; out.append('<div class="voice">'); continue
        if line.startswith("::: box"):
            flush(cap); mode = "box"
            out.append('<div class="box key">' if line.strip().endswith("key") else '<div class="box">'); continue
        if line.startswith("::: tpl"):
            flush(cap); mode = "tpl"
            head = line[7:].strip()
            tag, _, when = head.partition("|")
            talk = " talk" if "会話" in tag else ""
            out.append(f'<div class="tpl">\n<span class="tag{talk}">{html.escape(tag.strip())}</span>\n<p class="when">{html.escape(when.strip())}</p>')
            continue
        if line == ":::":
            flush(BOX_CAP); out.append("</div>"); mode = None; continue
        if not line.strip():
            flush(cap); continue
        m = re.match(r"^(#{1,3}) (.+)", line)
        if m:
            flush(cap)
            lv = len(m.group(1))
            if lv == 1:
                title = m.group(2).replace("/", "")
            out.append(f"<h{lv}>{brs(m.group(2))}</h{lv}>")
            continue
        if line.startswith("!lead "):
            flush(cap); out.append(f'<p class="lead">{html.escape(line[6:])}</p>'); continue
        if line.startswith("!key "):
            flush(cap); out.append(f'<p class="key">{brs(line[5:])}</p>'); continue
        if line.startswith("!note "):
            flush(cap); out.append(f'<p class="note">{brs(line[6:])}</p>'); continue
        if line.startswith("!rule "):
            flush(cap); out.append(f'<p class="rule">{brs(line[6:])}</p>'); continue
        if line.startswith("!sign "):
            flush(cap); out.append(f'<p class="sign">{html.escape(line[6:])}</p>'); continue
        if line == "---":
            flush(cap); out.append("<hr>"); continue
        m = re.match(r"^\[(.+)\]\((.+)\)$", line)
        if m:
            flush(cap)
            url = m.group(2)
            if url.startswith("@"):
                if url[1:] not in forms:
                    warns.append(f"forms.txt に {url[1:]} がありません")
                url = forms.get(url[1:], "#")
            out.append(f'<a class="btn" href="{html.escape(url)}">{html.escape(m.group(1))}</a>')
            if len(m.group(1)) > 14:
                warns.append(f"ボタン文言が長い（折り返しの恐れ）: {m.group(1)}")
            continue
        buf.append(line)
    flush(MAIN_CAP)
    body = "\n\n".join(out)
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="assets/style.css?v=3">
</head>
<body>
<div class="wrap">

{body}

<div class="foot">© {html.escape(brand)}</div>
</div>
<script src="assets/fit.js"></script>
</body>
</html>
""", warns


if __name__ == "__main__":
    a = sys.argv[1:]
    brand = "ケイ"
    if "--brand" in a:
        i = a.index("--brand"); brand = a[i + 1]; del a[i:i + 2]
    if len(a) != 2:
        sys.exit(__doc__)
    text, warns = build(pathlib.Path(a[0]).read_text(), brand, load_forms(a[0]))
    pathlib.Path(a[1]).write_text(text)
    print(f"生成: {a[1]}")
    for w in warns:
        print("警告:", w)
