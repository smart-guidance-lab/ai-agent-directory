import os
import requests
from openai import OpenAI
from datetime import datetime
import re
import random

# --- Config ---
BASE_URL = "https://ai-agent-directory-woad.vercel.app"
STRIPE_LINK = "https://buy.stripe.com/aFafZgepV8NW7Cwc788so07"
# --------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
current_date = datetime.now().strftime('%Y-%m-%d')

def get_ai_projects():
    url = "https://api.github.com/search/repositories?q=topic:ai-agent+stars:>500&sort=stars&order=desc"
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
    res = requests.get(url, headers=headers).json()
    return res.get('items', [])[:8]

def markdown_to_html(text):
    # 余分な#を取り除きつつ、段落を整える
    text = re.sub(r'^#+ (.*)', r'<h2 class="text-2xl font-bold mt-8 mb-4">\1</h2>', text, flags=re.M)
    text = text.replace('\n', '<br>')
    return text

# 1. テンプレート読み込み
with open("template.html", "r", encoding="utf-8") as f:
    index_temp = f.read()
with open("post_template.html", "r", encoding="utf-8") as f:
    post_temp = f.read()

projects = get_ai_projects()
os.makedirs("agent", exist_ok=True)

# 2. 全記事の基本データを先に作成
all_posts = []
for p in projects:
    name = p['name']
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Analyze {name} ROI for business. 3 key impact points. No Markdown headers."}]
    )
    content = res.choices[0].message.content
    all_posts.append({
        "name": name,
        "content": content,
        "desc": content[:140].replace('"', '').replace('\n', ' ')
    })

# 3. 個別HTML生成（構造化データと相互リンク付き）
html_cards = ""
for current in all_posts:
    name = current['name']
    others = [p for p in all_posts if p['name'] != name]
    related_items = random.sample(others, min(len(others), 2))
    
    related_html = ""
    for r in related_items:
        related_html += f'''
        <a href="./{r['name']}.html" class="block p-6 bg-white rounded-2xl border border-slate-100 hover:border-indigo-300 transition-colors shadow-sm">
            <div class="font-bold text-slate-800">{r['name']}</div>
            <div class="text-xs text-slate-500 mt-2">View Fresh Analysis →</div>
        </a>
        '''

    # メタデータ置換
    post_html = post_temp.replace("{{TITLE}}", name)
    post_html = post_html.replace("{{DESCRIPTION}}", current['desc'])
    post_html = post_html.replace("{{CONTENT}}", markdown_to_html(current['content']))
    post_html = post_html.replace("{{RELATED_POSTS}}", related_html)
    post_html = post_html.replace("{{DATE}}", current_date)
    post_html = post_html.replace("{{URL}}", f"{BASE_URL}/agent/{name}.html")
    
    with open(f"agent/{name}.html", "w", encoding="utf-8") as f:
        f.write(post_html)

    # トップページ用カード
    html_cards += f'''
    <div class="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm hover:shadow-md transition-all">
        <div class="text-[10px] font-bold text-indigo-500 mb-2 uppercase tracking-tighter">Updated {current_date}</div>
        <h3 class="text-xl font-bold mb-2">{name}</h3>
        <p class="text-slate-500 text-sm mb-6">{current['desc']}...</p>
        <a href="./agent/{name}.html" class="text-indigo-600 font-bold text-sm inline-flex items-center gap-1">Expert Report →</a>
    </div>
    '''

# 4. トップページ出力
with open("index.html", "w", encoding="utf-8") as f:
    f.write(index_temp.replace("", html_cards))

# 5. サイトマップ出力
s = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
s += f'<url><loc>{BASE_URL}/</loc><lastmod>{current_date}</lastmod></url>'
for p in all_posts:
    s += f'<url><loc>{BASE_URL}/agent/{p["name"]}.html</loc><lastmod>{current_date}</lastmod></url>'
s += '</urlset>'
with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(s)
