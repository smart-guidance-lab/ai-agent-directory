import os
import requests
from openai import OpenAI
import json
from datetime import datetime

# --- Config ---
STRIPE_LINK = "https://buy.stripe.com/aFafZgepV8NW7Cwc788so07" 
BASE_URL = "https://ai-agent-directory-woad.vercel.app" # 最新のURLに固定
# --------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_ai_projects():
    url = "https://api.github.com/search/repositories?q=topic:ai-agent&sort=stars&order=desc"
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
    res = requests.get(url, headers=headers).json()
    return res.get('items', [])[:5]

def generate_content(repo):
    prompt = f"Write a deep-dive analysis on: {repo['name']}. Source: {repo['html_url']}. English, Professional."
    response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
    return response.choices[0].message.content

# 1. 記事生成
projects = get_ai_projects()
post_list = []
os.makedirs("posts", exist_ok=True)
current_date = datetime.now().strftime('%Y-%m-%d') # 今日の日付

for p in projects:
    name = p['name']
    filename = f"posts/{name}.md"
    if not os.path.exists(filename):
        content = generate_content(p)
        footer = f"\n\n---\n[🚀 Feature your tool]({STRIPE_LINK}) | [Source]({p['html_url']})"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content + footer)
    post_list.append(name)

# 2. JSON更新
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(post_list, f, ensure_ascii=False, indent=4)

# 3. 究極のサイトマップ生成（lastmod追加版）
sitemap = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    '  <url>',
    f'    <loc>{BASE_URL}/</loc>',
    f'    <lastmod>{current_date}</lastmod>',
    '  </url>'
]

for name in post_list:
    sitemap.append('  <url>')
    sitemap.append(f'    <loc>{BASE_URL}/posts/{name}.md</loc>')
    sitemap.append(f'    <lastmod>{current_date}</lastmod>')
    sitemap.append('  </url>')

sitemap.append('</urlset>')

with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write("\n".join(sitemap))
