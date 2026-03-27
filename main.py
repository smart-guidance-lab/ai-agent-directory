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

# 1. 各種テンプレート読み込み
with open("template.html", "r", encoding="utf-8") as f:
    index_temp = f.read()
with open("post_template.html", "r", encoding="utf-8") as f:
    post_temp = f.read()

projects = get_ai_projects()
os.makedirs("agent", exist_ok=True)

# 統計
total_stars = sum([p['stargazers_count'] for p in projects])
total_count = len(projects)

all_posts = []
rss_items = ""

for p in projects:
    name, stars = p['name'], p['stargazers_count']
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Briefly score {name} ROI (0-100) and give 3 points analysis."}]
    )
    raw = res.choices[0].message.content
    score = re.search(r'\d+', raw).group(0) if re.search(r'\d+', raw) else "85"
    summary = raw[:140].replace('\n', ' ')

    all_posts.append({"name": name, "score": score, "stars": f"{stars:,}", "desc": summary})
    
    # RSS Item
    rss_items += f"<item><title>[{score}] {name}</title><link>{BASE_URL}/agent/{name}.html</link><description>{summary}</description><pubDate>{current_date}</pubDate></item>"

    # Post HTML
    post_html = post_temp.replace("{{TITLE}}", name).replace("{{DESCRIPTION}}", summary).replace("{{SCORE}}", score).replace("{{DATE}}", display_date).replace("{{CONTENT}}", raw.replace('\n', '<br>'))
    with open(f"agent/{name}.html", "w", encoding="utf-8") as f:
        f.write(post_html)

# 2. PWA: manifest.json
manifest = f'''{{
    "name": "AI Agent Index",
    "short_name": "AgentIndex",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#ffffff",
    "theme_color": "#4f46e5",
    "icons": [{{ "src": "https://cdn-icons-png.flaticon.com/512/2593/2593635.png", "sizes": "512x512", "type": "image/png" }}]
}}'''
with open("manifest.json", "w", encoding="utf-8") as f:
    f.write(manifest)

# 3. PWA: sw.js (Offline Cache)
sw = '''self.addEventListener('install', (e) => { e.waitUntil(caches.open('v1').then((cache) => cache.addAll(['/', '/index.html']))); });
self.addEventListener('fetch', (e) => { e.respondWith(caches.match(e.request).then((res) => res || fetch(e.request))); });'''
with open("sw.js", "w", encoding="utf-8") as f:
    f.write(sw)

# 4. RSS: feed.xml
with open("feed.xml", "w", encoding="utf-8") as f:
    f.write(f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>AI Agent Index</title><link>{BASE_URL}</link>{rss_items}</channel></rss>')

# 5. Index: index.html
html_cards = ""
for c in all_posts:
    html_cards += f'''<div class="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm flex flex-col justify-between">
        <div class="flex justify-between mb-4"><span class="text-[10px] font-black text-indigo-600">★ {c['stars']}</span><span class="font-black text-slate-300">{c['score']}</span></div>
        <h3 class="font-bold mb-2">{c['name']}</h3>
        <a href="./agent/{c['name']}.html" class="bg-slate-50 text-slate-900 text-center py-2 rounded-xl text-xs font-bold hover:bg-indigo-600 hover:text-white transition-all">View Report</a>
    </div>'''

index_html = index_temp.replace("", html_cards).replace("{{TOTAL_COUNT}}", str(total_count)).replace("{{TOTAL_STARS}}", f"{total_stars // 1000}").replace("{{DATE}}", display_date)
with open("index.html", "w", encoding="utf-8") as f:
    f.write(index_html)
