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
MANIFEST_FILE = ROOT / ".cms-generated-files.json"
SITE_URL = "https://opervyn.github.io/"

CANONICAL_ROUTES = {
    "about": "about",
    "data-entry": "services/data-entry",
    "virtual-assistant": "services/virtual-assistant",
    "nda-confidentiality": "nda-confidentiality",
}
CANONICAL_FILES = {f"{route}/index.html" for route in CANONICAL_ROUTES.values()}
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
        if not isinstance(page.get("sections", []), list):
            raise SystemExit(f"Page {slug!r} sections must be an array.")
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


def render_section(section: dict, base: str) -> str:
    section_type = section.get("type", "text")
    eyebrow = (
        f'<div class="section-kicker">{esc(section.get("eyebrow"))}</div>'
        if section.get("eyebrow")
        else ""
    )
    heading = f'<h2>{esc(section.get("heading"))}</h2>' if section.get("heading") else ""
    body = f'<p>{esc(section.get("body"))}</p>' if section.get("body") else ""

    if section_type == "hero":
        return (
            '<section class="seo-hero"><div class="eyebrow">'
            f'<span class="eyebrow-line"></span>{esc(section.get("eyebrow") or "ABLEHARBOR")}'
            f'</div><h1>{esc(section.get("heading"))}</h1>{body}</section>'
        )

    if section_type == "image":
        image = asset_url(section.get("image"), base)
        return (
            f'<section class="cms-image-section">{eyebrow}{heading}'
            f'<img src="{esc(image)}" alt="{esc(section.get("alt"))}" loading="lazy">'
            f'<p>{esc(section.get("caption"))}</p></section>'
        )

    if section_type in {"list", "cards", "feature", "faq", "steps"}:
        items = "".join(
            '<article class="cms-item">'
            f'<h3>{esc(item.get("title"))}</h3><p>{esc(item.get("body"))}</p></article>'
            for item in section.get("items", [])
            if isinstance(item, dict)
        )
        return f'<section class="seo-content-main">{eyebrow}{heading}<div class="cms-items">{items}</div></section>'

    if section_type == "founders":
        cards = "".join(
            '<article class="cms-founder">'
            f'<img src="{esc(asset_url(member.get("image"), base))}" '
            f'alt="{esc(member.get("alt") or member.get("name"))}" loading="lazy">'
            f'<h3>{esc(member.get("name"))}</h3>'
            f'<p>{esc(member.get("role") or "Founding Member")}</p></article>'
            for member in section.get("members", [])
            if isinstance(member, dict)
        )
        return (
            f'<section class="cms-founders">{eyebrow}{heading}{body}'
            f'<div class="cms-founder-grid">{cards}</div></section>'
        )

    if section_type == "cta":
        return (
            f'<section class="onboarding-panel">{eyebrow}{heading}{body}'
            f'<a class="btn btn-primary" href="{esc(safe_link(section.get("buttonUrl")))}">'
            f'{esc(section.get("buttonText") or "Contact ABLEHARBOR")} ↗</a></section>'
        )

    return f'<section class="seo-content-main">{eyebrow}{heading}{body}</section>'


PAGE_CSS = """\
.cms-page{max-width:1180px;margin:0 auto;padding:36px 28px 80px}
.cms-breadcrumb{font-size:12px;color:#718096;margin:0 0 28px}
.cms-breadcrumb a{color:inherit}
.cms-page .seo-hero{margin-bottom:26px}
.cms-page .seo-hero h1{max-width:900px}
.cms-page .seo-hero p{max-width:820px;line-height:1.8}
.cms-page .seo-content-main,.cms-page .cms-image-section,.cms-page .cms-founders{margin:26px 0;padding:28px;background:#fff;border:1px solid #e6ebf2;border-radius:14px}
.cms-page .cms-items{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}
.cms-page .cms-item{padding:20px;border:1px solid #e2e8f0;border-radius:10px;background:#fbfcfe}
.cms-page .cms-item h3{margin:0 0 9px}
.cms-page .cms-item p{margin:0;line-height:1.7}
.cms-page .cms-image-section img{display:block;max-width:100%;height:auto;border-radius:12px;margin-top:18px}
.cms-founder-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:18px;margin-top:22px}
.cms-founder{overflow:hidden;border:1px solid #e1e8f0;border-radius:13px;background:#fff;text-align:center;padding-bottom:18px}
.cms-founder img{width:100%;height:280px;object-fit:cover;object-position:center 25%}
.cms-founder h3{margin:15px 8px 5px}
.cms-founder p{margin:0;color:#718096;font-size:13px}
.cms-page .onboarding-panel{margin:26px 0}
@media(max-width:600px){.cms-page{padding:24px 16px 55px}.cms-page .seo-content-main,.cms-page .cms-image-section,.cms-page .cms-founders{padding:19px}.cms-founder img{height:240px}}
"""


def render_page(page: dict, route: str, all_pages: list[dict]) -> str:
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
      <a href="{base}">Home</a><a href="{base}services/">Our Services</a>{nav_links}
      <a data-cms-email="true" href="mailto:ableharbor.operation@gmail.com">Contact</a>
    </nav>
  </header>
  <main class="cms-page">
    <p class="cms-breadcrumb"><a href="{base}">Home</a> &nbsp;›&nbsp; {esc(page["title"])}</p>
    {body}
  </main>
  <footer class="footer">
    <div class="seo-footer-links">
      <a href="{base}services/">Our Services</a>
      <a href="{base}services/data-entry/">Data Entry</a>
      <a href="{base}services/virtual-assistant/">Virtual Assistant</a>
      <a href="{base}nda-confidentiality/">NDA &amp; Confidentiality</a>{nav_links}
    </div>
    <div class="footer-main">
      <a aria-label="ABLEHARBOR home" class="brand footer-brand" href="{base}">
        <img alt="ABLEHARBOR — Your Offshore Operations Partner" src="{base}assets/ableharbor-logo.png">
      </a>
      <p>ABLEHARBOR — Your Offshore Operations Partner.</p>
    </div>
    <div class="footer-bottom">
      <span>Remote-first operations support from Bangladesh</span>
      <span>© ABLEHARBOR. All rights reserved.</span>
      <span>Data Entry · Virtual Assistant</span>
      <span><a data-cms-email="true" href="mailto:ableharbor.operation@gmail.com">Email ↗</a></span>
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


def main() -> None:
    pages = load_pages()
    previous_files = read_manifest()
    current_files: set[str] = set()
    outputs: dict[str, str] = {}

    for page in pages:
        if page.get("status") != "published":
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
        outputs[relative] = render_page(page, route, pages)

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

    # Keep CMS-created pages in the existing homepage nav/footer marker blocks.
    homepage_path = ROOT / "index.html"
    homepage = homepage_path.read_text(encoding="utf-8")
    custom_links = "".join(
        f'<a href="/pages/{esc(page["slug"])}/">'
        f'{esc(page.get("navLabel") or page["title"])}</a>'
        for page in pages
        if page.get("status") == "published" and page["slug"] not in CANONICAL_ROUTES
    )
    homepage = replace_marker_block(
        homepage, "<!-- CMS_PAGE_LINKS_START -->", "<!-- CMS_PAGE_LINKS_END -->", custom_links
    )
    homepage = replace_marker_block(
        homepage, "<!-- CMS_FOOTER_LINKS_START -->", "<!-- CMS_FOOTER_LINKS_END -->", custom_links
    )

    # If a built-in CMS page is unpublished/deleted, send remaining hard-coded
    # homepage links to the general services page instead of leaving a 404 link.
    published_slugs = {page["slug"] for page in pages if page.get("status") == "published"}
    for slug, route in CANONICAL_ROUTES.items():
        if slug in published_slugs:
            continue
        pattern = re.compile(r"href=([\"'])/?" + re.escape(route) + r"/?\1")
        homepage = pattern.sub('href="/services/"', homepage)

    homepage_path.write_text(homepage, encoding="utf-8")

    # Rebuild sitemap in a deterministic order, without duplicate canonical routes.
    routes: list[str] = []
    for route in ["", "services/"]:
        if route not in routes:
            routes.append(route)
    for page in pages:
        if page.get("status") == "published":
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
