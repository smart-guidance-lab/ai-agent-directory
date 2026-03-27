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
    return res.get('items', [])[:12] # 12件に拡大

def markdown_to_html(text):
    text = re.sub(r'^### (.*)', r'<h3 class="text-xl font-bold mt-6 mb-3 text-slate-800">\1</h3>', text, flags=re.M)
    text = text.replace('\n', '<br>')
    return text

with open("template.html", "r", encoding="utf-8") as f:
    index_temp = f.read()
with open("post_template.html", "r", encoding="utf-8") as f:
    post_temp = f.read()

projects = get_ai_projects()
os.makedirs("agent", exist_ok=True)

# 統計データの算出
total_stars = sum([p['stargazers_count'] for p in projects])
total_count = len(projects)

all_posts = []
for p in projects:
    name = p['name']
    stars = p['stargazers_count']
    
    prompt = f"Critically evaluate AI agent '{name}'. Stars: {stars}. 1. Score 0-100. 2. 3-point ROI analysis. English."
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    raw_response = res.choices[0].message.content
    
    score_match = re.search(r'Score:\s*(\d+)', raw_response)
    score = score_match.group(1) if score_match else "88"
    clean_content = re.sub(r'Score:\s*\d+', '', raw_response).strip()

    all_posts.append({
        "name": name,
        "content": clean_content,
        "score": score,
        "stars": f"{stars:,}",
        "desc": f"Technical analysis of {name}. Current market traction: {stars:,} stars."
    })

html_cards = ""
for current in all_posts:
    name = current['name']
    others = [p for p in all_posts if p['name'] != name]
    related_items = random.sample(others, min(len(others), 2))
    
    related_html = ""
    for r in related_items:
        related_html += f'''
        <a href="./{r['name']}.html" class="block p-4 bg-slate-50 rounded-2xl border border-slate-100 hover:border-indigo-200 transition-all">
            <div class="flex justify-between items-center">
                <span class="font-bold text-slate-700 text-xs">{r['name']}</span>
                <span class="text-[9px] font-black text-indigo-500">ROI {r['score']}</span>
            </div>
        </a>'''

    post_html = post_temp.replace("{{TITLE}}", name)
    post_html = post_html.replace("{{DESCRIPTION}}", current['desc'])
    post_html = post_html.replace("{{CONTENT}}", markdown_to_html(current['content']))
    post_html = post_html.replace("{{RELATED_POSTS}}", related_html)
    post_html = post_html.replace("{{DATE}}", current_date)
    post_html = post_html.replace("{{SCORE}}", current['score'])
    post_html = post_html.replace("{{URL}}", f"{BASE_URL}/agent/{name}.html")
    
    with open(f"agent/{name}.html", "w", encoding="utf-8") as f:
        f.write(post_html)

    # トップページ用カード（スター数とスコアを同時表示）
    html_cards += f'''
    <div class="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm hover:shadow-xl transition-all flex flex-col justify-between group">
        <div>
            <div class="flex justify-between items-start mb-4">
                <div class="bg-indigo-50 text-indigo-600 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-tighter">
                    ★ {current['stars']}
                </div>
                <div class="text-2xl font-black text-slate-200 group-hover:text-indigo-600 transition-colors">
                    {current['score']}
                </div>
            </div>
            <h3 class="text-xl font-bold mb-2">{name}</h3>
            <p class="text-slate-400 text-xs leading-relaxed mb-6">{current['desc']}</p>
        </div>
        <a href="./agent/{name}.html" class="bg-slate-900 text-white text-center py-3 rounded-2xl text-xs font-bold hover:bg-indigo-600 transition-colors">
            Analyze Market ROI
        </a>
    </div>'''

# インデックスの最終置換
final_index = index_temp.replace("", html_cards)
final_index = final_index.replace("{{TOTAL_COUNT}}", str(total_count))
final_index = final_index.replace("{{TOTAL_STARS}}", f"{total_stars // 1000}")
final_index = final_index.replace("{{DATE}}", current_date)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(final_index)

# サイトマップ出力
s = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
s += f'<url><loc>{BASE_URL}/</loc><lastmod>{current_date}</lastmod></url>'
for p in all_posts:
    s += f'<url><loc>{BASE_URL}/agent/{p["name"]}.html</loc><lastmod>{current_date}</lastmod></url>'
s += '</urlset>'
with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(s)
