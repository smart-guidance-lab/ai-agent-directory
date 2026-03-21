import os
import requests
from openai import OpenAI
import json

# --- ユーザー設定エリア ---
STRIPE_LINK = "https://buy.stripe.com/aFafZgepV8NW7Cwc788so07" 
BASE_URL = "https://ai-agent-directory-woad.vercel.app" # 自分のVercelのURL（https://含む）
# ------------------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_ai_projects():
    url = "https://api.github.com/search/repositories?q=topic:ai-agent&sort=stars&order=desc"
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
    res = requests.get(url, headers=headers).json()
    return res.get('items', [])[:5]

def generate_ultimate_content(repo):
    prompt = f"""
    As a Senior Tech Analyst, write a deep-dive report on: {repo['name']}.
    Source: {repo['html_url']}
    Description: {repo['description']}

    Requirements:
    1. MARKET IMPACT: Industry disruption analysis.
    2. ARCHITECTURAL STRENGTHS: Why this is top-tier.
    3. POTENTIAL ROI: Business value estimation.
    4. CRITICAL RISKS: Main limitations.
    Style: Professional, sharp English. Use Markdown.
    Include a 'Verdict' score (x/10).
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content

# 1. 記事生成
projects = get_ai_projects()
post_list = []
os.makedirs("posts", exist_ok=True)

for p in projects:
    name = p['name']
    filename = f"posts/{name}.md"
    if not os.path.exists(filename):
        content = generate_ultimate_content(p)
        footer = f"\n\n---\n## 📢 Promotion\n- [Featured Listing on this page]({STRIPE_LINK})\n- [Source Code]({p['html_url']})"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content + footer)
    post_list.append(name)

# 2. JSONデータ更新
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(post_list, f, ensure_ascii=False, indent=4)

# 3. サイトマップ更新
sitemap = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
for name in post_list:
    sitemap += f"<url><loc>{BASE_URL}/posts/{name}.md</loc></url>"
sitemap += "</urlset>"
with open("sitemap.xml", "w") as f:
    f.write(sitemap)

# 4. 法的ページの生成（未存在時のみ）
if not os.path.exists("privacy.md"):
    with open("privacy.md", "w") as f:
        f.write("# Privacy Policy\nThis site uses AI to analyze public GitHub data. No personal data is collected unless provided via Stripe.")
if not os.path.exists("terms.md"):
    with open("terms.md", "w") as f:
        f.write("# Terms of Service\nAll reports are AI-generated. Use at your own risk. Promotion fees are non-refundable.")
