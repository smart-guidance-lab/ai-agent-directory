import os
import requests
from openai import OpenAI
import json
from datetime import datetime
import email.utils # RSSの日付形式用

# --- Config ---
STRIPE_LINK = "https://buy.stripe.com/aFafZgepV8NW7Cwc788so07" 
BASE_URL = "https://ai-agent-directory-woad.vercel.app" 
# --------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_ai_projects():
    url = "https://api.github.com/search/repositories?q=topic:ai-agent+stars:>500&sort=stars&order=desc"
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
    res = requests.get(url, headers=headers).json()
    return res.get('items', [])[:5]

def generate_content(repo):
    prompt = f"Summarize {repo['name']} for a business audience. Focus on efficiency and ROI. Source: {repo['html_url']}. English."
    response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
    return response.choices[0].message.content

# 1. 記事生成
projects = get_ai_projects()
post_data = []
os.makedirs("posts", exist_ok=True)
now = datetime.now()
pub_date = email.utils.formatdate(now.timestamp()) # RSS形式の日付

for p in projects:
    name = p['name']
    filename = f"posts/{name}.md"
    content = generate_content(p)
    footer = f"\n\n---\n[🚀 Feature your tool]({STRIPE_LINK}) | [Source]({p['html_url']})"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {name}\n\n" + content + footer)
    post_data.append({"name": name, "url": f"{BASE_URL}/agent/{name}", "desc": content[:150]})

# 2. RSSフィード生成（Googleへの「攻め」の通知）
rss = f'<?xml version="1.0" encoding="UTF-8" ?>\n<rss version="2.0">\n<channel>\n'
rss += f'<title>Global AI Agent Index</title>\n<link>{BASE_URL}</link>\n<description>Latest AI Agents Analysis</description>\n'
for post in post_data:
    rss += f'<item>\n<title>{post["name"]}</title>\n<link>{post["url"]}</link>\n<description>{post["desc"]}...</description>\n<pubDate>{pub_date}</pubDate>\n</item>\n'
rss += '</channel>\n</rss>'

with open("feed.xml", "w", encoding="utf-8") as f:
    f.write(rss)

# 3. サイトマップ（極限まで簡素化）
sitemap = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
sitemap += f'<url><loc>{BASE_URL}/</loc></url>'
for post in post_data:
    sitemap += f'<url><loc>{post["url"]}</loc></url>'
sitemap += '</urlset>'

with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(sitemap)

# 4. JSON更新
with open("data.json", "w", encoding="utf-8") as f:
    json.dump([p["name"] for p in post_data], f, ensure_ascii=False, indent=4)
