import feedparser, requests, os
from datetime import datetime, timezone, timedelta

token = os.environ['GITHUB_TOKEN']
repo  = os.environ['REPO']
headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github.v3+json'
}

res = requests.get(
    f'https://api.github.com/repos/{repo}/issues?state=open&per_page=100',
    headers=headers
).json()
existing = {i['title'] for i in res} if isinstance(res, list) else set()

feeds = [
    ('경제', 'https://news.google.com/rss/search?q=세계+경제&hl=ko&gl=KR&ceid=KR:ko'),
    ('세계', 'https://news.google.com/rss/search?q=세계+뉴스&hl=ko&gl=KR&ceid=KR:ko'),
    ('정치', 'https://news.google.com/rss/search?q=국제+정치&hl=ko&gl=KR&ceid=KR:ko'),
]

since = datetime.now(timezone.utc) - timedelta(hours=24)
created = 0

for category, url in feeds:
    feed = feedparser.parse(url)
    for entry in feed.entries[:5]:
        title = f'[{category}] {entry.title}'
        if title in existing:
            print(f'중복 스킵: {title}')
            continue
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            pub = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        else:
            pub = datetime.now(timezone.utc)
        if pub < since:
            continue
        body = f"""## {entry.title}

**카테고리:** {category}
**출처:** {entry.get('source', {}).get('title', '알 수 없음')}
**발행일:** {pub.strftime('%Y-%m-%d %H:%M UTC')}
**원문:** {entry.link}

---
*GitHub Actions 자동 생성*"""

        r = requests.post(
            f'https://api.github.com/repos/{repo}/issues',
            headers=headers,
            json={'title': title, 'body': body}
        )
        if r.status_code == 201:
            print(f'생성: #{r.json()["number"]} {title}')
            created += 1
        else:
            print(f'오류: {r.status_code} {r.text[:100]}')

print(f'\n총 {created}개 이슈 생성')
