import os
import requests
from openai import OpenAI
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
    return res.get('items', [])[:6] # 6件取得

# 記事生成とHTMLパーツの作成
projects = get_ai_projects()
os.makedirs("posts", exist_ok=True)
html_cards = ""

for p in projects:
    name = p['name']
    filename = f"posts/{name}.md"
    
    # 記事がなければ生成
    if not os.path.exists(filename):
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Analyze {name} ROI. English."}]
        )
        content = res.choices[0].message.content
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {name}\n\n{content}\n\n---\n[🚀 Sponsor]({STRIPE_LINK})")

    # 静的HTML用のカードパーツを作成
    card = f'''
    <div class="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm hover:shadow-md transition-all">
        <h3 class="text-xl font-bold mb-2">{name}</h3>
        <p class="text-slate-500 text-sm mb-6">Autonomous AI analysis and business impact report.</p>
        <a href="./agent/{name}" class="text-indigo-600 font-bold text-sm inline-flex items-center gap-1">
            View Analysis →
        </a>
    </div>
    '''
    html_cards += card

# template.htmlを読み込んで index.html を出力
with open("template.html", "r", encoding="utf-8") as f:
    template = f.read()

final_html = template.replace("", html_cards)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(final_html)

# 究極にシンプルなサイトマップ
current_date = datetime.now().strftime('%Y-%m-%d')
s = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
s += f'<url><loc>{BASE_URL}/</loc><lastmod>{current_date}</lastmod></url>'
for p in projects:
    s += f'<url><loc>{BASE_URL}/agent/{p["name"]}</loc><lastmod>{current_date}</lastmod></url>'
s += '</urlset>'
with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(s)
