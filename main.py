import os
import requests
from openai import OpenAI
import json

# --- Config ---
STRIPE_LINK = "https://buy.stripe.com/your_link_here" 
# --------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_ai_projects():
    url = "https://api.github.com/search/repositories?q=topic:ai-agent&sort=stars&order=desc"
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
    res = requests.get(url, headers=headers).json()
    return res.get('items', [])[:5]

def generate_ultimate_content(repo):
    # 独自の付加価値（推論）を強制するプロンプト
    prompt = f"""
    As a Senior Tech Analyst, write a deep-dive report on this AI project: {repo['name']}.
    Source URL: {repo['html_url']}
    Input Description: {repo['description']}

    Requirements for THE ULTIMATE REPORT:
    1. MARKET IMPACT: How does this disrupt current industries?
    2. ARCHITECTURAL STRENGTHS: Why is this better than others?
    3. POTENTIAL ROI: For a company, what is the estimated value?
    4. CRITICAL RISKS: What are the 2 main limitations?
    
    Style: Professional, sharp, and data-driven English. Use Markdown headers.
    Include a 'Verdict' section at the end with a score out of 10.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7 # 少しの創造性を許可
    )
    return response.choices[0].message.content

# 実行ロジック
projects = get_ai_projects()
post_list = []
os.makedirs("posts", exist_ok=True)

for p in projects:
    name = p['name']
    filename = f"posts/{name}.md"
    
    # 【コスト削減】既にファイルがあればスキップ
    if os.path.exists(filename):
        post_list.append(name)
        continue

    content = generate_ultimate_content(p)
    footer = f"\n\n---\n## 📢 Global Opportunity\n- **Featured Slot:** [Promote your tool to 50k+ readers]({STRIPE_LINK})\n- **Repository:** [View on GitHub]({p['html_url']})"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content + footer)
    post_list.append(name)

# JSON & Sitemap 更新
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(post_list, f, ensure_ascii=False, indent=4)

# 簡易サイトマップ
sitemap = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
for name in post_list:
    sitemap += f"<url><loc>https://your-vercel.app/posts/{name}.md</loc></url>"
sitemap += "</urlset>"
with open("sitemap.xml", "w") as f:
    f.write(sitemap)
