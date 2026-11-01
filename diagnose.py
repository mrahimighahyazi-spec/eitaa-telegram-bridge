import re
import requests
from bs4 import BeautifulSoup

URL = "https://eitaa.com/basij_iasbs/435"

print("=== DIAGNOSTIC START ===")
print(f"Fetching: {URL}")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

try:
    r = requests.get(URL, headers=headers, timeout=30)
    print(f"HTTP status: {r.status_code}")
    print(f"Content length: {len(r.text)} chars")
except Exception as e:
    print(f"ERROR fetching page: {e}")
    raise SystemExit(1)

html = r.text
soup = BeautifulSoup(html, "html.parser")

# 1) Any direct file links?
file_pattern = re.compile(r'https?://[^\s"\'<>]+\.(pdf|mp4|mp3|ogg|zip|docx?|xlsx?|pptx?|rar|7z)', re.IGNORECASE)
matches = file_pattern.findall(html)
full_links = file_pattern.finditer(html)
print("\n--- Direct file links found in raw HTML ---")
found = False
for m in full_links:
    print(m.group(0))
    found = True
if not found:
    print("(none)")

# 2) Any <a href> pointing to files?
print("\n--- <a href> tags containing file extensions ---")
found2 = False
for a in soup.find_all("a", href=True):
    href = a["href"]
    if re.search(r'\.(pdf|mp4|mp3|ogg|zip|docx?|xlsx?|pptx?|rar|7z)(\?|$)', href, re.IGNORECASE):
        print(f"href: {href} | text: {a.get_text(strip=True)[:80]}")
        found2 = True
if not found2:
    print("(none)")

# 3) Look for the specific filename Owj_02.pdf
print("\n--- Search for 'Owj_02' in HTML ---")
if "Owj_02" in html:
    idx = html.find("Owj_02")
    print("Found 'Owj_02' in HTML. Context (300 chars):")
    print(html[max(0, idx-150):idx+150])
else:
    print("'Owj_02' NOT found in HTML.")

# 4) Any data-* attributes or download links?
print("\n--- Elements with 'download' attribute or data-file ---")
found3 = False
for tag in soup.find_all(attrs={"download": True}):
    print(f"<{tag.name}> download attr | text: {tag.get_text(strip=True)[:80]}")
    found3 = True
for tag in soup.find_all(attrs={"data-file": True}):
    print(f"<{tag.name}> data-file={tag.get('data-file')}")
    found3 = True
if not found3:
    print("(none)")

print("\n=== DIAGNOSTIC END ===")
