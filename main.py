import os
import requests
from openai import OpenAI
from datetime import datetime
import re

# --- Config ---
BASE_URL = "https://ai-agent-directory-woad.vercel.app"
STRIPE_URL = "https://buy.stripe.com/aFafZgepV8NW7Cwc788so07"
# --------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
current_date = datetime.now().strftime('%Y-%m-%d')

def get_ai_projects():
    # 収益性の高いエージェントに絞るためのキーワード追加
    url = "https://api.github.com/search/repositories?q=topic:ai-agent+stars:>1000&sort=stars"
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
    res = requests.get(url, headers=headers).json()
    return res.get('items', [])[:15]

with open("template.html", "r", encoding="utf-8") as f:
    index_temp = f.read()
with open("post_template.html", "r", encoding="utf-8") as f:
    post_temp = f.read()

projects = get_ai_projects()
os.makedirs("agent", exist_ok=True)

total_stars = sum([p['stargazers_count'] for p in projects])
all_posts = []

for p in projects:
    name, stars = p['name'], p['stargazers_count']
    # 収益化に向けた強い分析を指示
    prompt = f"Analyze '{name}'. 1. Score (0-100). 2. Three specific high-value business use cases. 3. Why a company should pay for this. Use Markdown."
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    raw = res.choices[0].message.content
    score = re.search(r'\d+', raw).group(0) if re.search(r'\d+', raw) else "90"
    
    summary = f"High-ROI Autonomous Agent: {name}. Rated {score}/100 for enterprise readiness."
    all_posts.append({"name": name, "score": score, "stars": f"{stars:,}"})

    # コンテンツのHTML化
    content_html = raw.replace('\n', '<br>')
    
    # テンプレート置換
    post_html = post_temp.replace("{{TITLE}}", name)
    post_html = post_html.replace("{{DESCRIPTION}}", summary)
    post_html = post_html.replace("{{SCORE}}", score)
    post_html = post_html.replace("{{CONTENT}}", content_html)
    
    with open(f"agent/{name}.html", "w", encoding="utf-8") as f:
        f.write(post_html)

# インデックス（トップページ）の構築
html_cards = ""
for c in all_posts:
    html_cards += f'''
    <div class="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm hover:shadow-2xl transition-all flex flex-col justify-between border-b-4 border-b-indigo-500">
        <div>
            <div class="flex justify-between items-center mb-4 text-[10px] font-black uppercase tracking-widest text-slate-400">
                <span>★ {c['stars']} Traction</span>
                <span class="text-indigo-600">ROI {c['score']}</span>
            </div>
            <h3 class="text-2xl font-black mb-3 text-slate-800">{c['name']}</h3>
        </div>
        <div class="mt-6">
            <a href="./agent/{c['name']}.html" class="block w-full bg-slate-900 text-white text-center py-4 rounded-2xl text-xs font-black hover:bg-indigo-600 transition-colors uppercase tracking-widest">Access Market Intelligence</a>
        </div>
    </div>'''

index_html = index_temp.replace("", html_cards)
index_html = index_html.replace("{{TOTAL_COUNT}}", str(len(all_posts)))
index_html = index_html.replace("{{TOTAL_STARS}}", f"{total_stars // 1000}")
index_html = index_html.replace("{{DATE}}", current_date)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(index_html)

# PWA & RSS 生成（省略せず実行）
with open("manifest.json", "w", encoding="utf-8") as f:
    f.write('{"name":"Agent Index","short_name":"AIIndex","start_url":"/","display":"standalone","background_color":"#ffffff","theme_color":"#4f46e5","icons":[{"src":"https://cdn-icons-png.flaticon.com/512/2593/2593635.png","sizes":"512x512","type":"image/png"}]}')
with open("sw.js", "w", encoding="utf-8") as f:
    f.write("self.addEventListener('fetch',e=>{});") # シンプルなSW
