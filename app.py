import re
import xml.etree.ElementTree as ET
import cloudscraper
import requests
import itertools
import os
from urllib.parse import quote_plus, urljoin

HEADERS = {"User-Agent": "flibusta-client/1.0",
           "Accept": "application/atom+xml"}

MIRRORS = [
    "https://flibusta.monster",          # рабочий TLS, без CF
    "https://flibusta.site",             # CF => cloudscraper
    "https://flibusta.is",               # self‑signed TLS
    "https://flibusta.su",               # OPDS выкл.
]


def get_session(url):
    if ".site" in url:
        return cloudscraper.create_scraper()
    s = requests.Session()
    if ".is" in url:                     # игнорируем кривой cert
        s.verify = False
    return s


def pick_mirror():
    for base in MIRRORS:
        s = get_session(base)
        try:
            r = s.get(f"{base}/opds", timeout=10)
            if r.status_code == 200 and r.headers["content-type"].startswith("application/atom+xml"):
                print(" ✓", base)
                return base, s
        except requests.RequestException:
            print(" ✗", base)
    raise RuntimeError("Нет доступных зеркал с OPDS")


BASE, SESSION = pick_mirror()


def _search_template():
    # 1. корневой /opds
    root = ET.fromstring(SESSION.get(f"{BASE}/opds", headers=HEADERS).content)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    # 2. берём ссылку rel="search" (любую), а не ковыряем contains()
    for ln in root.findall(".//a:link[@rel='search']", ns):
        href = ln.attrib["href"]
        if href.endswith("xml"):              # opensearch
            tmpl = ET.fromstring(
                SESSION.get(urljoin(BASE, href), headers=HEADERS).content
            ).find(".//{http://a9.com/-/spec/opensearch/1.1/}Url"
                   "[@type='application/atom+xml']").attrib["template"]
            return tmpl
        if "search?" in href:                 # прямой шаблон
            return urljoin(BASE, href)
    raise RuntimeError("OPDS‑поиск не объявлен")


SEARCH_TMPL = _search_template()


def opds_search(term, limit=15):
    url = (SEARCH_TMPL.replace("{searchTerms}", quote_plus(term))
           .replace("{startPage?}", "0"))
    feed = SESSION.get(url, headers=HEADERS, timeout=15).content
    root = ET.fromstring(feed)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    books = {}
    for entry in root.findall("a:entry", ns)[:limit]:
        # ---------- ID и форматы ----------
        links = entry.findall("a:link", ns)
        fmt_map, bid = {}, None
        for ln in links:
            rel = ln.attrib.get("rel", "")
            href = ln.attrib.get("href", "")
            if "acquisition" in rel and "/b/" in href:
                m = re.search(r"/b/(\d+)/", href)
                if m:
                    bid = m.group(1)
                # определяем формат по MIME‑type
                mime = ln.attrib.get("type", "")
                fmt = (
                    "fb2" if "fb2" in mime else
                    "epub" if "epub" in mime else
                    "mobi" if "mobipocket" in mime else
                    "txt" if "text/plain" in mime else "bin"
                )
                fmt_map[fmt] = {
                    "url":   urljoin(BASE, href),
                    "size":  int(ln.attrib.get("length", 0)),
                    "title": ln.attrib.get("title", fmt.upper())
                }
            elif rel == "alternate":
                alt_url = urljoin(BASE, href)
            elif "image/thumbnail" in rel:
                thumb = urljoin(BASE, href)
            elif "image" == rel.split("/")[-1]:
                cover = urljoin(BASE, href)

        if not bid:            # без ID смысла нет
            continue

        # ---------- прочие поля ----------
        title = entry.findtext("a:title", "", ns).strip()
        content = entry.findtext("a:content", "", ns).strip()
        authors = ", ".join(
            a.text for a in entry.findall("a:author/a:name", ns))

        # TODO: проблема с ns
        # published = entry.findtext("a:published", "", ns)[:4]  # год
        # language = entry.findtext("dc:language", "", ns)
        # publisher = entry.findtext("dc:publisher", "", ns)

        genres = [cat.attrib.get("label", cat.attrib.get("term", ""))
                  for cat in entry.findall("a:category", ns)]

        books[bid] = {
            "id":        bid,
            "title":     title,
            "authors":   authors,
            "content":   content,
            # "year":      published,
            # "language":  language,
            # "publisher": publisher,
            "genres":    genres,
            "cover":     cover if 'cover' in locals() else None,
            "thumb":     thumb if 'thumb' in locals() else None,
            "html":      alt_url if 'alt_url' in locals() else None,
            "formats":   fmt_map
        }
    return books


FMT_DEFAULT = "fb2"


def _safe_filename(name: str) -> str:
    """Очищает имя файла от запрещённых символов Windows/macOS/Linux."""
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()


def download_book(book_id: str,
                  fmt: str = FMT_DEFAULT,
                  dest_dir: str = "downloads") -> str:
    """
    Скачивает файл `/b/<id>/<fmt>` с текущего зеркала и возвращает путь.

    :param book_id: строковый ID книги, например "16631"
    :param fmt:     "fb2", "epub", "mobi", "txt" …
    :param dest_dir: каталог для сохранения (создаётся при отсутствии)
    """
    url = f"{BASE}/b/{book_id}/{fmt}"
    r = SESSION.get(url, stream=True, timeout=60)
    r.raise_for_status()

    # пытаемся извлечь имя из Content‑Disposition; иначе делаем своё
    filename = f"{book_id}.{fmt}"
    cd = r.headers.get("Content-Disposition", "")
    m = re.search(r'filename="?(?P<name>[^"]+)"?', cd)
    if m:
        filename = _safe_filename(m.group("name").encode("latin1")
                                  .decode("utf‑8", "ignore"))

    os.makedirs(dest_dir, exist_ok=True)
    path = os.path.join(dest_dir, filename)

    with open(path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1 << 15):
            f.write(chunk)

    return path
