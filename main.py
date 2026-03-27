import os
import requests
from openai import OpenAI
from datetime import datetime
import re
import random

# --- Config ---
BASE_URL = "https://ai-agent-directory-woad.vercel.app"
# --------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
current_date = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
display_date = datetime.now().strftime('%Y-%m-%d')

def get_ai_projects():
    url = "https://api.github.com/search/repositories?q=topic:ai-agent+stars:>500&sort=stars&order=desc"
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
    res = requests.get(url, headers=headers).json()
    return res.get('items', [])[:12]

# テンプレート読み込み
with open("template.html", "r", encoding="utf-8") as f:
    index_temp = f.read()
with open("post_template.html", "r", encoding="utf-8") as f:
    post_temp = f.read()

projects = get_ai_projects()
os.makedirs("agent", exist_ok=True)

total_stars = sum([p['stargazers_count'] for p in projects])
total_count = len(projects)

all_posts = []

for p in projects:
    name, stars = p['name'], p['stargazers_count']
    # プロンプトを「対話のコンテキスト」を意識した構成に変更
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Analyze {name} (Stars: {stars}). 1. ROI Score. 2. Business Impact. 3. Why this matters now. English."}]
    )
    raw = res.choices[0].message.content
    score = re.search(r'\d+', raw).group(0) if re.search(r'\d+', raw) else "88"
    summary = f"Professional assessment of {name} focusing on immediate business utility."

    all_posts.append({"name": name, "score": score, "stars": f"{stars:,}", "desc": summary})
    
    # 記事HTML生成（新しいチャットUI付きテンプレートを使用）
    content_html = raw.replace('\n', '<br>')
    post_html = post_temp.replace("{{TITLE}}", name).replace("{{DESCRIPTION}}", summary).replace("{{SCORE}}", score).replace("{{DATE}}", display_date).replace("{{CONTENT}}", content_html)
    
    with open(f"agent/{name}.html", "w", encoding="utf-8") as f:
        f.write(post_html)

# PWA & RSS 構成ファイルの生成（前回のロジックを継承）
with open("manifest.json", "w", encoding="utf-8") as f:
    f.write(f'{{"name":"AI Agent Index","short_name":"AgentIndex","start_url":"/","display":"standalone","background_color":"#ffffff","theme_color":"#4f46e5","icons":[{{"src":"https://cdn-icons-png.flaticon.com/512/2593/2593635.png","sizes":"512x512","type":"image/png"}}]}}')

with open("sw.js", "w", encoding="utf-8") as f:
    f.write("self.addEventListener('install',e=>e.waitUntil(caches.open('v2').then(c=>c.addAll(['/','/index.html']))));self.addEventListener('fetch',e=>e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request))));")

# インデックス生成
html_cards = ""
for c in all_posts:
    html_cards += f'''<div class="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm flex flex-col justify-between hover:shadow-lg transition-all">
        <div class="flex justify-between mb-4"><span class="bg-indigo-50 text-indigo-600 px-2 py-1 rounded-lg text-[10px] font-black">★ {c['stars']}</span><span class="font-black text-slate-300">Score {c['score']}</span></div>
        <h3 class="font-bold text-lg mb-2">{c['name']}</h3>
        <p class="text-xs text-slate-400 mb-6">{c['desc']}</p>
        <a href="./agent/{c['name']}.html" class="bg-slate-900 text-white text-center py-3 rounded-2xl text-xs font-bold hover:bg-indigo-600 transition-all">Open Report & Ask AI</a>
    </div>'''

index_html = index_temp.replace("", html_cards).replace("{{TOTAL_COUNT}}", str(total_count)).replace("{{TOTAL_STARS}}", f"{total_stars // 1000}").replace("{{DATE}}", display_date)
with open("index.html", "w", encoding="utf-8") as f:
    f.write(index_html)
