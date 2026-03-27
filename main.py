import os
import requests
from openai import OpenAI
from datetime import datetime
import re

# --- Config ---
BASE_URL = "https://ai-agent-directory-woad.vercel.app"
STRIPE_LINK = "https://buy.stripe.com/aFafZgepV8NW7Cwc788so07"
# --------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_ai_projects():
    url = "https://api.github.com/search/repositories?q=topic:ai-agent+stars:>500&sort=stars&order=desc"
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
    res = requests.get(url, headers=headers).json()
    return res.get('items', [])[:6]

def markdown_to_html(text):
    # 簡易的なマークダウン変換（#と改行のみ対応）
    text = re.sub(r'^# (.*)', r'<h1 class="text-4xl font-black mb-6">\1</h1>', text, flags=re.M)
    text = text.replace('\n', '<br>')
    return text

# 1. テンプレートの読み込み
with open("template.html", "r", encoding="utf-8") as f:
    index_temp = f.read()
with open("post_template.html", "r", encoding="utf-8") as f:
    post_temp = f.read()

projects = get_ai_projects()
os.makedirs("agent", exist_ok=True) # postsではなくagentディレクトリにHTMLを生成
html_cards = ""

for p in projects:
    name = p['name']
    
    # 記事内容の生成
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Analyze AI agent {name} for business ROI. 3 points."}]
    )
    raw_content = res.choices[0].message.content
    description = raw_content[:150].replace('"', '')

    # 個別HTMLの生成
    post_html = post_temp.replace("{{TITLE}}", name)
    post_html = post_html.replace("{{DESCRIPTION}}", description)
    post_html = post_html.replace("{{CONTENT}}", markdown_to_html(raw_content))
    
    with open(f"agent/{name}.html", "w", encoding="utf-8") as f:
        f.write(post_html)

    # トップページ用カードの生成
    card = f'''
    <div class="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm hover:shadow-md transition-all">
        <h3 class="text-xl font-bold mb-2">{name}</h3>
        <p class="text-slate-500 text-sm mb-6">{description}...</p>
        <a href="./agent/{name}.html" class="text-indigo-600 font-bold text-sm inline-flex items-center gap-1">
            Read Full Analysis →
        </a>
    </div>
    '''
    html_cards += card

# 2. トップページ(index.html)の出力
final_index = index_temp.replace("", html_cards)
with open("index.html", "w", encoding="utf-8") as f:
    f.write(final_index)

# 3. サイトマップの出力
current_date = datetime.now().strftime('%Y-%m-%d')
s = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
s += f'<url><loc>{BASE_URL}/</loc><lastmod>{current_date}</lastmod></url>'
for p in projects:
    s += f'<url><loc>{BASE_URL}/agent/{p["name"]}.html</loc><lastmod>{current_date}</lastmod></url>'
s += '</urlset>'
with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(s)
