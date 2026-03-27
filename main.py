import os
import requests
from openai import OpenAI
import json
from datetime import datetime

# --- Config ---
BASE_URL = "https://ai-agent-directory-woad.vercel.app"
STRIPE_LINK = "https://buy.stripe.com/aFafZgepV8NW7Cwc788so07"
# --------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_ai_projects():
    url = "https://api.github.com/search/repositories?q=topic:ai-agent+stars:>500&sort=stars&order=desc"
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
    res = requests.get(url, headers=headers).json()
    return res.get('items', [])[:5]

# 記事生成と保存
projects = get_ai_projects()
post_names = []
os.makedirs("posts", exist_ok=True)

for p in projects:
    name = p['name']
    filename = f"posts/{name}.md"
    if not os.path.exists(filename):
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Analyze {name}. ROI focus."}]
        )
        content = res.choices[0].message.content
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {name}\n\n{content}\n\n---\n[🚀 Sponsor]({STRIPE_LINK})")
    post_names.append(name)

# data.jsonを更新（index.htmlがこれを読んでリンクを作る）
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(post_names, f, ensure_ascii=False, indent=4)

# 念のためsitemap.xmlも更新（1行にまとめてパースエラーを防止）
current_date = datetime.now().strftime('%Y-%m-%d')
s = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
s += f'<url><loc>{BASE_URL}/</loc><lastmod>{current_date}</lastmod></url>'
for n in post_names:
    s += f'<url><loc>{BASE_URL}/agent/{n}</loc><lastmod>{current_date}</lastmod></url>'
s += '</urlset>'
with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(s)
