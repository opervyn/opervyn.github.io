#!/usr/bin/env python3
"""Build CMS-managed ABLEHARBOR pages without deleting unrelated site content."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CONTENT_FILE = ROOT / "content" / "pages.json"
SITE_FILE = ROOT / "content" / "site.json"
MANIFEST_FILE = ROOT / ".cms-generated-files.json"
SITE_URL = "https://ableharbor.github.io/"

CANONICAL_ROUTES = {
    "about": "about",
    "data-entry": "services/data-entry",
    "virtual-assistant": "services/virtual-assistant",
    "nda-confidentiality": "nda-confidentiality",
}
CANONICAL_FILES = {f"{route}/index.html" for route in CANONICAL_ROUTES.values()}
LEGACY_SECTION_IDS = {
    "home": {"home", "about", "services", "process", "seo-directory", "team", "founding-member", "faq", "contact"},
    "services": {"services-hero", "services-data-entry", "services-model", "services-faq", "services-team"},
}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def esc(value: object = "") -> str:
    return html.escape(str(value or ""), quote=True)


def load_pages() -> list[dict]:
    if not CONTENT_FILE.is_file():
        raise SystemExit("Missing content/pages.json")
    try:
        payload = json.loads(CONTENT_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"content/pages.json is invalid JSON: {exc}") from exc

    pages = payload.get("pages") if isinstance(payload, dict) else None
    if not isinstance(pages, list):
        raise SystemExit('content/pages.json must contain a "pages" array.')

    seen: set[str] = set()
    for page in pages:
        if not isinstance(page, dict):
            raise SystemExit("Every CMS page must be a JSON object.")
        slug = str(page.get("slug") or "")
        if not SLUG_RE.fullmatch(slug):
            raise SystemExit(f"Invalid page slug {slug!r}; use lowercase letters, numbers and hyphens.")
        if slug in seen:
            raise SystemExit(f"Duplicate CMS page slug: {slug}")
        seen.add(slug)
        if not str(page.get("title") or "").strip():
            raise SystemExit(f"Page {slug!r} has no title.")
        if page.get("status", "draft") not in {"draft", "published"}:
            raise SystemExit(f"Page {slug!r} has an invalid status.")
        sections = page.get("sections", [])
        if not isinstance(sections, list):
            raise SystemExit(f"Page {slug!r} sections must be an array.")
        section_ids: set[str] = set()
        for section in sections:
            if not isinstance(section, dict):
                raise SystemExit(f"Page {slug!r} contains a section that is not an object.")
            section_id = str(section.get("id") or "")
            if not section_id or section_id in section_ids:
                raise SystemExit(f"Page {slug!r} has a missing or duplicate section ID: {section_id!r}.")
            section_ids.add(section_id)
            if not isinstance(section.get("type", "text"), str):
                raise SystemExit(f"Section {section_id!r} has an invalid template type.")
            for collection in ("items", "members"):
                values = section.get(collection, [])
                if not isinstance(values, list) or any(not isinstance(item, dict) for item in values):
                    raise SystemExit(f"Section {section_id!r} {collection} must be an array of objects.")
    seo = page.get("seo", {})
    if seo is not None and not isinstance(seo, dict):
        raise SystemExit(f"Page {slug!r} SEO settings must be an object.")
    return pages


def route_for(slug: str) -> str:
    return CANONICAL_ROUTES.get(slug, f"pages/{slug}")


def base_for(route: str) -> str:
    return "../" * len(route.split("/"))


def asset_url(value: object, base: str) -> str:
    path = str(value or "").strip()
    if not path:
        return ""
    if path.startswith(("https://", "http://", "/", "data:")):
        return path
    return base + path.lstrip("./")


def safe_link(value: object) -> str:
    raw = str(value or "mailto:ABLEHARBOR.BUSINESS@GMAIL.COM").strip()
    parsed = urlsplit(raw)
    if parsed.scheme and parsed.scheme.lower() not in {"http", "https", "mailto", "tel"}:
        return "mailto:ABLEHARBOR.BUSINESS@GMAIL.COM"
    if raw.startswith("//"):
        return "mailto:ABLEHARBOR.BUSINESS@GMAIL.COM"
    return raw or "mailto:ABLEHARBOR.BUSINESS@GMAIL.COM"



def load_site() -> dict:
    try:
        data = json.loads(SITE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"content/site.json is unavailable or invalid: {exc}") from exc
    return data if isinstance(data, dict) else {}


def render_nav(items: list, base: str = "") -> str:
    rendered = []
    for item in items:
        if not isinstance(item, dict) or not item.get("label") or not item.get("url"):
            continue
        raw_url = str(item.get("url") or "")
        url = (base + raw_url) if base and raw_url.startswith("#") else safe_link(raw_url)
        target = ' target="_blank" rel="noopener noreferrer"' if item.get("newTab") else ""
        klass = ' class="nav-cta"' if item.get("cta") else ""
        label = esc(item.get("label")) + (" ↗" if item.get("cta") else "")
        children = item.get("children") if isinstance(item.get("children"), list) else []
        if children:
            submenu = "".join(
                f'<a href="{esc((base + str(child.get("url"))) if base and str(child.get("url") or "").startswith("#") else safe_link(child.get("url")))}"{' target="_blank" rel="noopener noreferrer"' if child.get("newTab") else ""}>{esc(child.get("label"))}</a>'
                for child in children if isinstance(child, dict) and child.get("label") and child.get("url")
            )
            rendered.append(f'<details class="cms-nav-dropdown"><summary><a href="{esc(url)}"{target}>{esc(item.get("label"))}</a></summary><div class="cms-nav-submenu">{submenu}</div></details>')
        else:
            rendered.append(f'<a{klass} href="{esc(url)}"{target}>{label}</a>')
    return "".join(rendered)

def render_section(section: dict, base: str) -> str:
    if section.get("visible") is False:
        return ""
    section_type = section.get("type", "text")
    eyebrow = f'<div class="section-kicker">{esc(section.get("eyebrow"))}</div>' if section.get("eyebrow") else ""
    heading = f'<h2>{esc(section.get("heading"))}</h2>' if section.get("heading") else ""
    body = f'<p>{esc(section.get("body"))}</p>' if section.get("body") else ""
    items = [item for item in section.get("items", []) if isinstance(item, dict)]
    def item_cards(cards, extra=""):
        rendered = []
        for item in cards:
            image = asset_url(item.get("image"), base)
            image_html = f'<img class="cms-item-image" src="{esc(image)}" alt="{esc(item.get("alt") or item.get("title") or item.get("name"))}" loading="lazy">' if image else ""
            icon_html = f'<div class="cms-item-icon">{esc(item.get("icon"))}</div>' if item.get("icon") else ""
            title_html = f'<h3>{esc(item.get("title") or item.get("name"))}</h3>' if item.get("title") or item.get("name") else ""
            description = item.get("body") or item.get("description") or item.get("quote") or ""
            body_html = f'<p>{esc(description)}</p>' if description else ""
            role_html = f'<small>{esc(item.get("role"))}</small>' if item.get("role") else ""
            features = item.get("features") if isinstance(item.get("features"), list) else []
            features_html = "<ul>" + "".join(f"<li>{esc(feature)}</li>" for feature in features) + "</ul>" if features else ""
            link = item.get("link") or item.get("url")
            link_html = f'<a class="text-link" href="{esc(safe_link(link))}">{esc(item.get("linkLabel") or "Learn more ↗")}</a>' if link else ""
            rendered.append(f'<article class="cms-item {extra}">{image_html}{icon_html}{title_html}{body_html}{features_html}{role_html}{link_html}</article>')
        return "".join(rendered)
    if section_type == "hero":
        image = asset_url(section.get("image"), base)
        hero_image = f'<img class="cms-hero-image" src="{esc(image)}" alt="{esc(section.get("alt"))}" loading="lazy">' if image else ""
        return f'<section class="seo-hero"><div class="eyebrow"><span class="eyebrow-line"></span>{esc(section.get("eyebrow") or "ABLEHARBOR")}</div><h1>{esc(section.get("heading"))}</h1>{body}{hero_image}</section>'
    if section_type in {"image", "text-image"}:
        image = asset_url(section.get("image"), base)
        img = f'<img src="{esc(image)}" alt="{esc(section.get("alt"))}" loading="lazy">' if image else ""
        return f'<section class="cms-image-section">{eyebrow}{heading}<div class="cms-split">{body}{img}</div><p>{esc(section.get("caption"))}</p></section>'
    if section_type in {"text", "about", "introduction", "custom"}:
        return f'<section class="seo-content-main">{eyebrow}{heading}{body}</section>'
    if section_type in {"list", "cards", "feature", "service-cards", "faq", "steps", "process", "testimonials", "stats", "gallery", "logos"}:
        if section_type == "gallery":
            cards = "".join(f'<figure class="cms-gallery-item">{f"<img src=\"{esc(asset_url(x.get('image') or x.get('url'), base))}\" alt=\"{esc(x.get('alt') or x.get('title'))}\" loading=\"lazy\">" if x.get("image") or x.get("url") else ""}<figcaption>{esc(x.get("caption") or x.get("title"))}</figcaption></figure>' for x in items)
        elif section_type == "stats":
            cards = "".join(f'<article class="cms-stat"><strong>{esc(x.get("value") or x.get("title"))}</strong><span>{esc(x.get("label") or x.get("body"))}</span></article>' for x in items)
        elif section_type == "logos":
            cards = "".join(f'<div class="cms-logo-item">{f"<img src=\"{esc(asset_url(x.get(chr(105)+chr(109)+chr(97)+chr(103)+chr(101)), base))}\" alt=\"{esc(x.get(chr(97)+chr(108)+chr(116)) or x.get(chr(110)+chr(97)+chr(109)+chr(101)))}\">" if x.get("image") else ""}<span>{esc(x.get("name") or x.get("title"))}</span></div>' for x in items)
        elif section_type == "faq":
            cards = "".join(f'<details class="cms-faq-item"><summary>{esc(x.get("title") or "Question")}</summary><p>{esc(x.get("body") or x.get("description"))}</p></details>' for x in items)
        else:
            cards = item_cards(items, "cms-quote" if section_type == "testimonials" else "")
        klass = "cms-gallery" if section_type == "gallery" else "cms-stats" if section_type == "stats" else "cms-logos" if section_type == "logos" else "cms-faq" if section_type == "faq" else "cms-items"
        return f'<section class="seo-content-main">{eyebrow}{heading}{body}<div class="{klass}">{cards}</div></section>'
    if section_type in {"founders", "team"}:
        members = section.get("members", items)
        cards = "".join(f'<article class="cms-founder">{f"<img src=\"{esc(asset_url(member.get('image'), base))}\" alt=\"{esc(member.get('alt') or member.get('name'))}\" loading=\"lazy\">" if member.get("image") else ""}<h3>{esc(member.get("name"))}</h3><p>{esc(member.get("role") or "Team member")}</p><p>{esc(member.get("bio"))}</p></article>' for member in members if isinstance(member, dict))
        return f'<section class="cms-founders">{eyebrow}{heading}{body}<div class="cms-founder-grid">{cards}</div></section>'
    if section_type == "cta":
        return f'<section class="onboarding-panel">{eyebrow}{heading}{body}<a class="btn btn-primary" href="{esc(safe_link(section.get("buttonUrl")))}">{esc(section.get("buttonText") or "Contact ABLEHARBOR")} ↗</a></section>'
    if section_type == "contact":
        return f'<section class="onboarding-panel">{eyebrow}{heading}{body}<a class="btn btn-primary" href="{esc(safe_link(section.get("buttonUrl") or "mailto:ableharbor.operation@gmail.com"))}">{esc(section.get("buttonText") or "Contact us")} ↗</a></section>'
    return f'<section class="seo-content-main">{eyebrow}{heading}{body}</section>'


PAGE_CSS = """\
.cms-page{max-width:1180px;margin:0 auto;padding:36px 28px 80px}
.cms-breadcrumb{font-size:12px;color:#718096;margin:0 0 28px}
.cms-breadcrumb a{color:inherit}
.cms-page .seo-hero{margin-bottom:26px}
.cms-page .seo-hero h1{max-width:900px}
.cms-page .seo-hero p{max-width:820px;line-height:1.8}
.cms-hero-image{display:block;max-width:min(100%,760px);height:auto;border-radius:14px;margin-top:22px}
.cms-page .seo-content-main,.cms-page .cms-image-section,.cms-page .cms-founders{margin:26px 0;padding:28px;background:#fff;border:1px solid #e6ebf2;border-radius:14px}
.cms-page .cms-items{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}
.cms-page .cms-item{padding:20px;border:1px solid #e2e8f0;border-radius:10px;background:#fbfcfe}
.cms-page .cms-item h3{margin:0 0 9px}
.cms-page .cms-item-image{display:block;width:100%;max-height:180px;object-fit:cover;border-radius:8px;margin-bottom:14px}
.cms-page .cms-item-icon{font-size:24px;color:#2879d0;margin-bottom:8px}
.cms-faq{border-top:1px solid #e2e8f0}.cms-faq-item{padding:16px 2px;border-bottom:1px solid #e2e8f0}.cms-faq-item summary{font:700 14px Manrope;color:#182a43}.cms-faq-item p{font-size:12px;line-height:1.8;color:#718098;margin:12px 0 0}
.cms-page .cms-item ul{padding-left:18px;line-height:1.8}
.cms-page .cms-item-image{display:block;width:100%;max-height:180px;object-fit:cover;border-radius:8px;margin-bottom:14px}
.cms-page .cms-item-icon{font-size:24px;color:#2879d0;margin-bottom:8px}
.cms-faq{border-top:1px solid #e2e8f0}.cms-faq-item{padding:16px 2px;border-bottom:1px solid #e2e8f0}.cms-faq-item summary{font:700 14px Manrope;color:#182a43}.cms-faq-item p{font-size:12px;line-height:1.8;color:#718098;margin:12px 0 0}
.cms-page .cms-item p{margin:0;line-height:1.7}
.cms-page .cms-image-section img{display:block;max-width:100%;height:auto;border-radius:12px;margin-top:18px}
.cms-founder-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:18px;margin-top:22px}
.cms-founder{overflow:hidden;border:1px solid #e1e8f0;border-radius:13px;background:#fff;text-align:center;padding-bottom:18px}
.cms-founder img{width:100%;height:280px;object-fit:cover;object-position:center 25%}
.cms-founder h3{margin:15px 8px 5px}
.cms-founder p{margin:0;color:#718096;font-size:13px}
.cms-page .onboarding-panel{margin:26px 0}\n.cms-split{display:grid;grid-template-columns:1fr 1fr;gap:24px;align-items:center}.cms-split img{width:100%;height:auto;border-radius:12px}.cms-gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px}.cms-gallery-item{margin:0}.cms-gallery-item img{width:100%;height:190px;object-fit:cover;border-radius:10px}.cms-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:14px}.cms-stat{padding:22px;border:1px solid #e2e8f0;border-radius:12px}.cms-stat strong{display:block;font-size:30px}.cms-logos{display:flex;flex-wrap:wrap;gap:24px;align-items:center}.cms-logo-item img{max-width:140px;max-height:70px;object-fit:contain}.cms-logo-item span{display:block}@media(max-width:650px){.cms-split{grid-template-columns:1fr}}
@media(max-width:600px){.cms-page{padding:24px 16px 55px}.cms-page .seo-content-main,.cms-page .cms-image-section,.cms-page .cms-founders{padding:19px}.cms-founder img{height:240px}}
"""


def render_page(page: dict, route: str, all_pages: list[dict], site: dict) -> str:
    base = base_for(route)
    nav_links = "".join(
        f'<a href="{base}{esc(route_for(item["slug"]))}/">'
        f'{esc(item.get("navLabel") or item["title"])}</a>'
        for item in all_pages
        if item.get("status") == "published"
    )
    body = "".join(
        render_section(section, base)
        for section in page.get("sections", [])
        if isinstance(section, dict)
    )
    navigation = site.get("navigation") if isinstance(site.get("navigation"), dict) else {}
    header_links = render_nav(navigation.get("header", []), base)
    footer_links = render_nav(navigation.get("footer", []), base)
    seo = page.get("seo") if isinstance(page.get("seo"), dict) else {}
    title = seo.get("title") or page["title"]
    description = seo.get("description") or ""
    canonical = f"{SITE_URL}{route}/"
    fonts = (
        "https://fonts.googleapis.com/css2?"
        "family=DM+Sans:wght@400;500;600;700;800&amp;"
        "family=Inter:wght@400;500;600;700;800&amp;"
        "family=Manrope:wght@400;500;600;700;800&amp;"
        "family=Montserrat:wght@500;600;700;800&amp;display=swap"
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <link rel="canonical" href="{esc(canonical)}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{esc(canonical)}">
  <meta property="og:type" content="website">
  <meta property="og:image" content="{esc(asset_url(seo.get("image") or "assets/ableharbor-logo.png", base))}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image" content="{esc(asset_url(seo.get("image") or "assets/ableharbor-logo.png", base))}">
  <link rel="icon" href="{base}assets/ableharbor-icon.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="{fonts}" rel="stylesheet">
  <link rel="stylesheet" href="{base}styles.css">
  <link rel="stylesheet" href="{base}theme-redesign.css">
  <style>{PAGE_CSS}</style>
</head>
<body>
  <header class="site-header">
    <a aria-label="ABLEHARBOR home" class="brand" href="{base}">
      <img alt="ABLEHARBOR — Your Offshore Operations Partner" src="{base}assets/ableharbor-logo.png">
    </a>
    <button aria-expanded="false" aria-label="Open navigation" class="menu-toggle">
      <span></span><span></span><span></span>
    </button>
    <nav class="nav">
      {header_links}
    </nav>
  </header>
  <main class="cms-page">
    <p class="cms-breadcrumb"><a href="{base}">Home</a> &nbsp;›&nbsp; {esc(page["title"])}</p>
    {body}
  </main>
  <footer class="footer">
    <div class="seo-footer-links">{footer_links}</div>
    <div class="footer-main">
      <a aria-label="ABLEHARBOR home" class="brand footer-brand" href="{base}">
        <img alt="ABLEHARBOR — Your Offshore Operations Partner" src="{esc(asset_url((site.get("footer") or {}).get("logo") or "assets/ableharbor-logo.png", base))}">
      </a>
      {f"<h3>{esc((site.get('footer') or {}).get('heading'))}</h3>" if (site.get("footer") or {}).get("heading") else ""}
      <p>{esc((site.get("footer") or {}).get("description") or "ABLEHARBOR — Your Offshore Operations Partner.")}</p>
    </div>
    <div class="footer-bottom">
      <span>{esc((site.get("footer") or {}).get("bottomNote") or "Remote-first operations support from Bangladesh")}</span>
      <span>{esc((site.get("footer") or {}).get("copyright") or "© ABLEHARBOR. All rights reserved.")}</span>
      <span>{esc((site.get("footer") or {}).get("serviceNote") or "Data Entry · Virtual Assistant")}</span>
    </div>
  </footer>
  <script src="{base}script.js"></script>
  <script defer src="{base}site.js"></script>
</body>
</html>
"""


def read_manifest() -> set[str]:
    if not MANIFEST_FILE.is_file():
        return set()
    try:
        payload = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
        items = payload.get("generated_files", [])
        return {str(item) for item in items if isinstance(item, str)}
    except (json.JSONDecodeError, AttributeError):
        raise SystemExit(".cms-generated-files.json is invalid; refusing to delete generated files.")


def safe_output_path(relative: str) -> Path:
    target = (ROOT / relative).resolve()
    try:
        target.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise SystemExit(f"Refusing to write outside the repository: {relative}") from exc
    return target


def replace_marker_block(source: str, start: str, end: str, content: str) -> str:
    start_at = source.find(start)
    end_at = source.find(end)
    if start_at < 0 or end_at < 0 or end_at < start_at:
        raise SystemExit(f"Homepage is missing valid markers: {start} / {end}")
    content_at = start_at + len(start)
    return source[:content_at] + content + source[end_at:]


def update_legacy_page(path: Path, page: dict, route: str) -> None:
    """Keep the bespoke homepage/services markup while publishing CMS SEO and visibility."""
    if not path.is_file():
        return
    document = path.read_text(encoding="utf-8")
    seo = page.get("seo") if isinstance(page.get("seo"), dict) else {}
    title = str(seo.get("title") or page.get("title") or "ABLEHARBOR")
    description = str(seo.get("description") or "")
    canonical = SITE_URL + (route + "/" if route else "")
    document = re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", document, count=1, flags=re.I | re.S)

    def replace_meta(pattern: str, content: str) -> None:
        nonlocal document
        escaped = esc(content)
        if re.search(pattern, document, flags=re.I):
            document = re.sub(pattern, lambda m: m.group(1) + escaped + m.group(3), document, count=1, flags=re.I)

    replace_meta(r'(<meta\b(?=[^>]*\bname=["\']description["\'])[^>]*\bcontent=["\'])(.*?)(["\'][^>]*>)', description)
    replace_meta(r'(<meta\b(?=[^>]*\bproperty=["\']og:title["\'])[^>]*\bcontent=["\'])(.*?)(["\'][^>]*>)', title)
    replace_meta(r'(<meta\b(?=[^>]*\bproperty=["\']og:description["\'])[^>]*\bcontent=["\'])(.*?)(["\'][^>]*>)', description)
    replace_meta(r'(<meta\b(?=[^>]*\bproperty=["\']og:url["\'])[^>]*\bcontent=["\'])(.*?)(["\'][^>]*>)', canonical)
    replace_meta(r'(<link\b(?=[^>]*\brel=["\']canonical["\'])[^>]*\bhref=["\'])(.*?)(["\'][^>]*>)', canonical)
    image = str(seo.get("image") or "assets/ableharbor-logo.png")
    image_url = image if image.startswith(("https://", "http://")) else SITE_URL + image.lstrip("/")
    replace_meta(r'(<meta\b(?=[^>]*\bproperty=["\']og:image["\'])[^>]*\bcontent=["\'])(.*?)(["\'][^>]*>)', image_url)
    replace_meta(r'(<meta\b(?=[^>]*\bname=["\']twitter:title["\'])[^>]*\bcontent=["\'])(.*?)(["\'][^>]*>)', title)
    replace_meta(r'(<meta\b(?=[^>]*\bname=["\']twitter:description["\'])[^>]*\bcontent=["\'])(.*?)(["\'][^>]*>)', description)
    replace_meta(r'(<meta\b(?=[^>]*\bname=["\']twitter:image["\'])[^>]*\bcontent=["\'])(.*?)(["\'][^>]*>)', image_url)
    if page.get("visible", True) is False or page.get("status") != "published":
        if re.search(r'<meta\b(?=[^>]*\bname=["\']robots["\'])', document, flags=re.I):
            document = re.sub(r'(<meta\b(?=[^>]*\bname=["\']robots["\'])[^>]*\bcontent=["\'])(.*?)(["\'][^>]*>)', r'\1noindex,nofollow\3', document, count=1, flags=re.I)
        else:
            document = document.replace("</head>", '<meta name="robots" content="noindex,nofollow">\n</head>', 1)
        document = re.sub(r"<main\b(?![^>]*\bhidden\b)([^>]*)>", r"<main hidden\1>", document, count=1, flags=re.I)
    else:
        document = re.sub(r'(<meta\b(?=[^>]*\bname=["\']robots["\'])[^>]*\bcontent=["\'])(.*?)(["\'][^>]*>)', r'\1index,follow\3', document, count=1, flags=re.I)
        document = re.sub(r"<main\b([^>]*)\s+hidden(\s+[^>]*)?>", r"<main\1\2>", document, count=1, flags=re.I)
    active_targets = {str(section.get("targetId")) for section in page.get("sections", []) if section.get("targetId")}
    for removed_target in LEGACY_SECTION_IDS.get(str(page.get("slug")), set()) - active_targets:
        pattern = re.compile(r'(<(?:section|div)\b(?=[^>]*\bid=["\']' + re.escape(removed_target) + r'["\'])[^>]*)(>)', re.I)
        match = pattern.search(document)
        if match and not re.search(r"\bhidden\b", match.group(1)):
            document = document[:match.start(1)] + match.group(1) + " hidden" + document[match.end(1):]
    for section in page.get("sections", []):
        target_id = str(section.get("targetId") or "")
        if not target_id:
            continue
        pattern = re.compile(r'(<(?:section|div)\b(?=[^>]*\bid=["\']' + re.escape(target_id) + r'["\'])[^>]*)(>)', re.I)
        match = pattern.search(document)
        if not match:
            continue
        opening = match.group(1)
        if section.get("visible") is False:
            if not re.search(r"\bhidden\b", opening):
                opening += " hidden"
        else:
            opening = re.sub(r"\s+hidden\b", "", opening)
        document = document[:match.start(1)] + opening + document[match.end(1):]
    path.write_text(document, encoding="utf-8")


def main() -> None:
    pages = load_pages()
    previous_files = read_manifest()
    current_files: set[str] = set()
    outputs: dict[str, str] = {}

    site = load_site()
    for page in pages:
        if page.get("systemPage"):
            continue  # Homepage and /services/ retain their bespoke HTML/CSS shells.
        if page.get("status") != "published" or page.get("visible", True) is False:
            continue
        slug = page["slug"]
        route = route_for(slug)
        relative = f"{route}/index.html"
        target = safe_output_path(relative)

        # The well-known routes are deliberately CMS-managed. New /pages/* routes
        # must not overwrite a manually maintained page that the manifest does not own.
        if route.startswith("pages/") and target.exists() and relative not in previous_files:
            raise SystemExit(
                f"Cannot publish /{route}/ because {relative} already exists and is not CMS-managed. "
                "Move or rename that page first."
            )

        current_files.add(relative)
        outputs[relative] = render_page(page, route, pages, site)

    # Clean only files previously generated by this script plus the four known
    # CMS-managed legacy routes. Never recursively delete a route or assets folder.
    removable = (previous_files | CANONICAL_FILES) - current_files
    for relative in sorted(removable):
        target = safe_output_path(relative)
        if target.is_file():
            target.unlink()
            parent = target.parent
            while parent != ROOT and parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent

    for relative, page_html in outputs.items():
        target = safe_output_path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page_html, encoding="utf-8")

    MANIFEST_FILE.write_text(
        json.dumps({"generated_files": sorted(current_files)}, indent=2) + "\n",
        encoding="utf-8",
    )

    for page in pages:
        if page.get("systemPage") and page.get("slug") in {"home", "services"}:
            legacy_path = ROOT / ("index.html" if page["slug"] == "home" else "services/index.html")
            update_legacy_page(legacy_path, page, "" if page["slug"] == "home" else "services")

    # Keep CMS-created pages in the existing homepage nav/footer marker blocks.
    homepage_path = ROOT / "index.html"
    homepage = homepage_path.read_text(encoding="utf-8")
    custom_links = "".join(
        f'<a href="/pages/{esc(page["slug"])}/">'
        f'{esc(page.get("navLabel") or page["title"])}</a>'
        for page in pages
        if page.get("status") == "published" and page.get("visible", True) is not False and not page.get("systemPage") and page["slug"] not in CANONICAL_ROUTES
    )
    homepage = replace_marker_block(
        homepage, "<!-- CMS_PAGE_LINKS_START -->", "<!-- CMS_PAGE_LINKS_END -->", custom_links
    )
    homepage = replace_marker_block(
        homepage, "<!-- CMS_FOOTER_LINKS_START -->", "<!-- CMS_FOOTER_LINKS_END -->", custom_links
    )

    # If a built-in CMS page is unpublished/deleted, send remaining hard-coded
    # homepage links to the general services page instead of leaving a 404 link.
    published_slugs = {page["slug"] for page in pages if page.get("status") == "published" and page.get("visible", True)}
    for slug, route in CANONICAL_ROUTES.items():
        if slug in published_slugs:
            continue
        pattern = re.compile(r"href=([\"'])/?" + re.escape(route) + r"/?\1")
        homepage = pattern.sub('href="/services/"', homepage)

    homepage_path.write_text(homepage, encoding="utf-8")

    # Rebuild sitemap in a deterministic order, without duplicate canonical routes.
    routes: list[str] = []
    system_by_slug = {page.get("slug"): page for page in pages if page.get("systemPage")}
    for slug, route in [("home", ""), ("services", "services/")]:
        system_page = system_by_slug.get(slug)
        if system_page and system_page.get("status") == "published" and system_page.get("visible", True) is not False:
            routes.append(route)
    for page in pages:
        if page.get("status") == "published" and page.get("visible", True) is not False:
            if page.get("systemPage"):
                route = ("" if page["slug"] == "home" else "services/")
            else:
                route = route_for(page["slug"]) + "/"
            if route not in routes:
                routes.append(route)

    sitemap = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    sitemap.extend(f"  <url><loc>{SITE_URL}{esc(route)}</loc></url>" for route in routes)
    sitemap.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(sitemap) + "\n", encoding="utf-8")

    print(f"Built {len(current_files)} CMS page(s).")
    print(f"Verified source files: {len(outputs)} generated HTML file(s), sitemap refreshed.")


if __name__ == "__main__":
    main()
