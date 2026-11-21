#!/usr/bin/env python3
"""スマホ専用の記事HTMLを一発生成する。

使い方:  python3 tools/build_article.py 原稿.txt 出力名.html [--brand ケイ]

原稿の書き方（1行=1フレーズ。ここで区切った位置がそのまま改行になる）
  # タイトル             h1
  ## 見出し              h2
  ### 小見出し           h3
  !lead 小さなキャッチ    h1の上の薄字
  !rule 太字のルール見出し
  ---                    区切り線
  ::: box ... :::        ピンクの枠
  ::: tpl LINE用|場面 ... :::   テンプレカード（会話用なら「会話用|場面」）
  [ボタン文言](URL)       ボタン
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


def para(lines, cap, warns, cls=""):
    for l in lines:
        if len(l) > cap:
            warns.append(f"{len(l)}字 > {cap}: {l}")
    out = []
    for g in split_groups(lines):
        c = f' class="{cls}"' if cls else ""
        out.append(f"<p{c}>" + "<br>\n".join(html.escape(x, quote=False) for x in g) + "</p>")
    return "\n\n".join(out)


def build(src, brand):
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
        if line.startswith("::: box"):
            flush(cap); mode = "box"; out.append('<div class="box">'); continue
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
                title = m.group(2)
            out.append(f"<h{lv}>{html.escape(m.group(2))}</h{lv}>")
            continue
        if line.startswith("!lead "):
            flush(cap); out.append(f'<p class="lead">{html.escape(line[6:])}</p>'); continue
        if line.startswith("!rule "):
            flush(cap); out.append(f'<p class="rule">{html.escape(line[6:])}</p>'); continue
        if line.startswith("!sign "):
            flush(cap); out.append(f'<p class="sign">{html.escape(line[6:])}</p>'); continue
        if line == "---":
            flush(cap); out.append("<hr>"); continue
        m = re.match(r"^\[(.+)\]\((.+)\)$", line)
        if m:
            flush(cap)
            out.append(f'<a class="btn" href="{html.escape(m.group(2))}">{html.escape(m.group(1))}</a>')
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
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<div class="wrap">

{body}

<div class="foot">© {html.escape(brand)}</div>
</div>
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
    text, warns = build(pathlib.Path(a[0]).read_text(), brand)
    pathlib.Path(a[1]).write_text(text)
    print(f"生成: {a[1]}")
    for w in warns:
        print("警告:", w)
