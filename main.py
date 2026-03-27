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
    return res.get('items', [])[:9]

def markdown_to_html(text):
    # 見出しを構造化
    text = re.sub(r'^### (.*)', r'<h3 class="text-xl font-bold mt-6 mb-3 text-slate-800">\1</h3>', text, flags=re.M)
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
    # 高度な分析プロンプト：スコアと各項目を要求
    prompt = f"""Analyze the AI agent '{name}'. 
    1. Assign a Total ROI Score (0-100).
    2. Write 3 brief sections: ### Business Impact, ### Technical Scalability, ### Implementation Ease.
    3. Format: Score: [number]. Content follows."""
    
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    raw_response = res.choices[0].message.content
    
    # スコアの抽出
    score_match = re.search(r'Score:\s*(\d+)', raw_response)
    score = score_match.group(1) if score_match else "85"
    clean_content = re.sub(r'Score:\s*\d+', '', raw_response).strip()

    all_posts.append({
        "name": name,
        "content": clean_content,
        "score": score,
        "desc": f"Expert analysis of {name} with a focus on business ROI and scalability."
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
            <div class="flex justify-between items-center mb-2">
                <span class="font-bold text-slate-800 text-sm">{r['name']}</span>
                <span class="text-[10px] font-black text-indigo-600">{r['score']}/100</span>
            </div>
            <div class="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Compare Report →</div>
        </a>'''

    # メタデータ置換
    post_html = post_temp.replace("{{TITLE}}", name)
    post_html = post_html.replace("{{DESCRIPTION}}", current['desc'])
    post_html = post_html.replace("{{CONTENT}}", markdown_to_html(current['content']))
    post_html = post_html.replace("{{RELATED_POSTS}}", related_html)
    post_html = post_html.replace("{{DATE}}", current_date)
    post_html = post_html.replace("{{SCORE}}", current['score'])
    post_html = post_html.replace("{{URL}}", f"{BASE_URL}/agent/{name}.html")
    
    with open(f"agent/{name}.html", "w", encoding="utf-8") as f:
        f.write(post_html)

    # トップページ用カード（スコア表示付き）
    html_cards += f'''
    <div class="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm hover:shadow-md transition-all flex flex-col justify-between relative overflow-hidden">
        <div class="absolute top-0 right-0 bg-indigo-50 text-indigo-600 px-4 py-1 text-xs font-black rounded-bl-xl">
            {current['score']}
        </div>
        <div>
            <div class="text-[10px] font-bold text-slate-400 mb-2 uppercase tracking-widest">Global Rank: #00{all_posts.index(current)+1}</div>
            <h3 class="text-xl font-bold mb-3">{name}</h3>
            <p class="text-slate-500 text-sm leading-relaxed mb-6">{current['desc']}</p>
        </div>
        <a href="./agent/{name}.html" class="text-indigo-600 font-black text-xs uppercase tracking-widest border-b-2 border-indigo-50 hover:border-indigo-600 transition-all inline-block w-fit">Deep Analysis & ROI</a>
    </div>'''

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
