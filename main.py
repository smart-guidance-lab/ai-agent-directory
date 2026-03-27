import os
import requests
from openai import OpenAI
import json
from datetime import datetime
import email.utils

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
    prompt = f"Summarize {repo['name']} ROI. Source: {repo['html_url']}. English."
    response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
    return response.choices[0].message.content

# 1. コンテンツ生成
projects = get_ai_projects()
post_data = []
os.makedirs("posts", exist_ok=True)
current_date = datetime.now().strftime('%Y-%m-%d')
pub_date = email.utils.formatdate(datetime.now().timestamp())

for p in projects:
    name = p['name']
    filename = f"posts/{name}.md"
    content = generate_content(p)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {name}\n\n{content}\n\n---\n[🚀 Feature]({STRIPE_LINK})")
    post_data.append({"name": name, "url": f"{BASE_URL}/agent/{name}", "desc": content[:100]})

# 2. XML / RSS 同時出力（極限までシンプルに）
def save_file(name, content):
    with open(name, "w", encoding="utf-8") as f:
        f.write(content.strip())

# Sitemap
s = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
s += f'<url><loc>{BASE_URL}/</loc><lastmod>{current_date}</lastmod></url>'
for p in post_data:
    s += f'<url><loc>{p["url"]}</loc><lastmod>{current_date}</lastmod></url>'
s += '</urlset>'
save_file("sitemap.xml", s)

# Feed
r = f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>AI Index</title><link>{BASE_URL}</link>'
for p in post_data:
    r += f'<item><title>{p["name"]}</title><link>{p["url"]}</link><pubDate>{pub_date}</pubDate></item>'
r += '</channel></rss>'
save_file("feed.xml", r)

# 3. JSON
with open("data.json", "w", encoding="utf-8") as f:
    json.dump([p["name"] for p in post_data], f, ensure_ascii=False, indent=4)
