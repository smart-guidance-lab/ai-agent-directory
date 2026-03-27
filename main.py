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
    # 常に旬なリポジトリを取得（品質担保）
    url = "https://api.github.com/search/repositories?q=topic:ai-agent+stars:>500&sort=stars&order=desc"
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
    res = requests.get(url, headers=headers).json()
    return res.get('items', [])[:9] # 9枚にしてグリッドを美しく埋める

def markdown_to_html(text):
    text = re.sub(r'^#+ (.*)', r'<h2 class="text-2xl font-bold mt-8 mb-4">\1</h2>', text, flags=re.M)
    text = text.replace('\n', '<br>')
    return text

with open("template.html", "r", encoding="utf-8") as f:
    index_temp = f.read()
with open("post_template.html", "r", encoding="utf-8") as f:
    post_temp = f.read()

projects = get_ai_projects()
os.makedirs("agent", exist_ok=True)

all_posts = []
for p in projects:
    name = p['name']
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Analyze {name} ROI. Focus on business value. English."}]
    )
    content = res.choices[0].message.content
    all_posts.append({
        "name": name,
        "content": content,
        "desc": content[:130].replace('"', '').replace('\n', ' ')
    })

html_cards = ""
for current in all_posts:
    name = current['name']
    others = [p for p in all_posts if p['name'] != name]
    related_items = random.sample(others, min(len(others), 2))
    
    related_html = ""
    for r in related_items:
        related_html += f'''
        <a href="./{r['name']}.html" class="block p-6 bg-white rounded-2xl border border-slate-100 hover:border-indigo-300 transition-all shadow-sm">
            <div class="font-bold text-slate-800 text-sm">{r['name']}</div>
            <div class="text-[10px] text-indigo-500 font-bold mt-2 tracking-widest">NEXT REPORT →</div>
        </a>'''

    post_html = post_temp.replace("{{TITLE}}", name)
    post_html = post_html.replace("{{DESCRIPTION}}", current['desc'])
    post_html = post_html.replace("{{CONTENT}}", markdown_to_html(current['content']))
    post_html = post_html.replace("{{RELATED_POSTS}}", related_html)
    post_html = post_html.replace("{{DATE}}", current_date)
    post_html = post_html.replace("{{URL}}", f"{BASE_URL}/agent/{name}.html")
    
    with open(f"agent/{name}.html", "w", encoding="utf-8") as f:
        f.write(post_html)

    # 一般カードの生成
    html_cards += f'''
    <div class="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
        <div>
            <div class="text-[10px] font-bold text-slate-400 mb-2 uppercase tracking-widest">Analysis: {current_date}</div>
            <h3 class="text-xl font-bold mb-3">{name}</h3>
            <p class="text-slate-500 text-sm leading-relaxed mb-6">{current['desc']}...</p>
        </div>
        <a href="./agent/{name}.html" class="text-indigo-600 font-black text-xs uppercase tracking-widest border-b-2 border-indigo-50 hover:border-indigo-600 transition-all inline-block w-fit">Full ROI Report</a>
    </div>'''

# インデックス出力
with open("index.html", "w", encoding="utf-8") as f:
    f.write(index_temp.replace("", html_cards))

# サイトマップ出力
s = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
s += f'<url><loc>{BASE_URL}/</loc><lastmod>{current_date}</lastmod></url>'
for p in all_posts:
    s += f'<url><loc>{BASE_URL}/agent/{p["name"]}.html</loc><lastmod>{current_date}</lastmod></url>'
s += '</urlset>'
with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(s)
