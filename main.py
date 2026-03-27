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
current_date = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000') # RSS用フォーマット
display_date = datetime.now().strftime('%Y-%m-%d')

def get_ai_projects():
    url = "https://api.github.com/search/repositories?q=topic:ai-agent+stars:>500&sort=stars&order=desc"
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
    res = requests.get(url, headers=headers).json()
    return res.get('items', [])[:12]

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

total_stars = sum([p['stargazers_count'] for p in projects])
total_count = len(projects)

all_posts = []
rss_items = ""

for p in projects:
    name = p['name']
    stars = p['stargazers_count']
    
    prompt = f"Critically evaluate {name}. Stars: {stars}. Score 0-100. Write 3-point business ROI impact. English."
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    raw_response = res.choices[0].message.content
    
    score_match = re.search(r'Score:\s*(\d+)', raw_response)
    score = score_match.group(1) if score_match else "85"
    clean_content = re.sub(r'Score:\s*\d+', '', raw_response).strip()
    summary = clean_content[:150].replace('<br>', ' ')

    all_posts.append({
        "name": name,
        "content": clean_content,
        "score": score,
        "stars": f"{stars:,}",
        "url": f"{BASE_URL}/agent/{name}.html"
    })

    # RSS Item生成
    rss_items += f"""
    <item>
        <title>[ROI {score}] {name}</title>
        <link>{BASE_URL}/agent/{name}.html</link>
        <description>{summary}...</description>
        <pubDate>{current_date}</pubDate>
        <guid>{BASE_URL}/agent/{name}.html</guid>
    </item>"""

    # 個別ページ生成 (post_templateを使用)
    post_html = post_temp.replace("{{TITLE}}", name).replace("{{DESCRIPTION}}", summary)
    post_html = post_html.replace("{{CONTENT}}", markdown_to_html(clean_content))
    post_html = post_html.replace("{{SCORE}}", score).replace("{{DATE}}", display_date)
    # 関連記事等は前回のロジックを継承（ここでは簡略化）
    with open(f"agent/{name}.html", "w", encoding="utf-8") as f:
        f.write(post_html)

# RSSフィード書き出し
rss_full = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>AI Agent Index - Market ROI Intelligence</title>
  <link>{BASE_URL}</link>
  <description>Daily updated AI agent ROI analysis and market heat tracking.</description>
  <lastBuildDate>{current_date}</lastBuildDate>
  {rss_items}
</channel>
</rss>"""

with open("feed.xml", "w", encoding="utf-8") as f:
    f.write(rss_full.strip())

# インデックス生成
html_cards = ""
for current in all_posts:
    html_cards += f'''
    <div class="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm hover:shadow-xl transition-all flex flex-col justify-between group">
        <div>
            <div class="flex justify-between items-start mb-4">
                <div class="bg-indigo-50 text-indigo-600 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-tighter">★ {current['stars']}</div>
                <div class="text-2xl font-black text-indigo-600">{current['score']}</div>
            </div>
            <h3 class="text-xl font-bold mb-2">{current['name']}</h3>
        </div>
        <a href="./agent/{current['name']}.html" class="bg-slate-900 text-white text-center py-3 rounded-2xl text-xs font-bold hover:bg-indigo-600 transition-colors">Analyze ROI</a>
    </div>'''

final_index = index_temp.replace("", html_cards)
final_index = final_index.replace("{{TOTAL_COUNT}}", str(total_count))
final_index = final_index.replace("{{TOTAL_STARS}}", f"{total_stars // 1000}")
final_index = final_index.replace("{{DATE}}", display_date)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(final_index)
