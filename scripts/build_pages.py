#!/usr/bin/env python3
import json, html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'content/pages.json').read_text(encoding='utf-8'))
BASE='../' * 2
def e(v): return html.escape(str(v or ''), quote=True)
def asset_url(v):
    v=str(v or '')
    return v if v.startswith(('http://','https://','/')) else BASE+v
def section(s):
    t=s.get('type','text'); eyebrow=f'<div class="section-kicker">{e(s.get("eyebrow"))}</div>' if s.get('eyebrow') else ''; heading=f'<h2>{e(s.get("heading"))}</h2>' if s.get('heading') else ''; body=f'<p>{e(s.get("body"))}</p>' if s.get('body') else ''
    if t=='hero': return f'<section class="seo-hero"><div class="eyebrow"><span class="eyebrow-line"></span>{e(s.get("eyebrow") or "OPERVYN")}</div><h1>{e(s.get("heading"))}</h1>{body}</section>'
    if t=='image': return f'<section class="cms-image-section">{eyebrow}{heading}<img src="{e(asset_url(s.get("image","")))}" alt="{e(s.get("alt"))}"><p>{e(s.get("caption"))}</p></section>'
    if t in ('list','cards'):
        items=''.join(f'<article class="cms-item"><h3>{e(i.get("title"))}</h3><p>{e(i.get("body"))}</p></article>' for i in s.get('items',[]))
        return f'<section class="seo-content-main">{eyebrow}{heading}<div class="cms-items">{items}</div></section>'
    if t=='founders':
        cards=''.join(f'<article class="cms-founder"><img src="{e(asset_url(m.get("image","")))}" alt="{e(m.get("alt") or m.get("name"))}"><h3>{e(m.get("name"))}</h3><p>{e(m.get("role") or "Founding Member")}</p></article>' for m in s.get('members',[]))
        return f'<section class="cms-founders">{eyebrow}{heading}{body}<div class="cms-founder-grid">{cards}</div></section>'
    if t=='cta': return f'<section class="onboarding-panel">{eyebrow}{heading}{body}<a class="btn btn-primary" href="{e(s.get("buttonUrl") or "mailto:opervyn.business@gmail.com")}">{e(s.get("buttonText") or "Contact OPERVYN")} ↗</a></section>'
    return f'<section class="seo-content-main">{eyebrow}{heading}{body}</section>'
css='.cms-page{max-width:1180px;margin:0 auto;padding:36px 28px 80px}.cms-breadcrumb{font-size:12px;color:#718096;margin:0 0 28px}.cms-breadcrumb a{color:inherit}.cms-page .seo-hero{margin-bottom:26px}.cms-page .seo-hero h1{max-width:900px}.cms-page .seo-hero p{max-width:820px;line-height:1.8}.cms-page .seo-content-main,.cms-page .cms-image-section,.cms-page .cms-founders{margin:26px 0;padding:28px;background:#fff;border:1px solid #e6ebf2;border-radius:14px}.cms-page .cms-items{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}.cms-page .cms-item{padding:20px;border:1px solid #e2e8f0;border-radius:10px;background:#fbfcfe}.cms-page .cms-item h3{margin:0 0 9px}.cms-page .cms-item p{margin:0;line-height:1.7}.cms-page .cms-image-section img{display:block;max-width:100%;height:auto;border-radius:12px;margin-top:18px}.cms-founder-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:18px;margin-top:22px}.cms-founder{overflow:hidden;border:1px solid #e1e8f0;border-radius:13px;background:#fff;text-align:center;padding-bottom:18px}.cms-founder img{width:100%;height:280px;object-fit:cover;object-position:center 25%}.cms-founder h3{margin:15px 8px 5px}.cms-founder p{margin:0;color:#718096;font-size:13px}.cms-page .onboarding-panel{margin:26px 0}@media(max-width:600px){.cms-page{padding:24px 16px 55px}.cms-page .seo-content-main,.cms-page .cms-image-section,.cms-page .cms-founders{padding:19px}.cms-founder img{height:240px}}'
# Remove prior generated page output so deleted or draft pages disappear on rebuild.
import shutil
for old in ['about','nda-confidentiality','services/data-entry','services/virtual-assistant','pages']:
    target=ROOT/old
    if target.exists(): shutil.rmtree(target)
for p in data.get('pages',[]):
    if p.get('status')!='published': continue
    slug=p['slug']; route={'data-entry':'services/data-entry','virtual-assistant':'services/virtual-assistant','nda-confidentiality':'nda-confidentiality','about':'about'}.get(slug, f'pages/{slug}'); BASE='../' * len(route.split('/')); out=ROOT/route/'index.html'; out.parent.mkdir(parents=True,exist_ok=True)
    nav=''.join(f'<a href="{BASE}{({'data-entry':'services/data-entry','virtual-assistant':'services/virtual-assistant','nda-confidentiality':'nda-confidentiality','about':'about'}.get(q['slug'], 'pages/'+q['slug']))}/">{e(q.get("navLabel") or q["title"])}</a>' for q in data['pages'] if q.get('status')=='published')
    body=''.join(section(s) for s in p.get('sections',[])); seo=p.get('seo',{})
    page=f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(seo.get('title') or p['title'])}</title><meta name="description" content="{e(seo.get('description'))}"><link rel="canonical" href="https://opervyn.github.io/{e(route)}/"><link rel="icon" href="{BASE}assets/opervyn-logo-new.png"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Montserrat:wght@500;600;700;800&display=swap" rel="stylesheet"><link rel="stylesheet" href="{BASE}styles.css"><link rel="stylesheet" href="{BASE}theme-redesign.css"><style>{css}</style></head><body><header class="site-header"><a aria-label="OPERVYN home" class="brand" href="{BASE}"><img alt="OPERVYN — Your Offshore Operations Partner" src="{BASE}assets/opervyn-logo-new.webp"></a><button aria-expanded="false" aria-label="Open navigation" class="menu-toggle"><span></span><span></span><span></span></button><nav class="nav"><a href="{BASE}">Home</a><a href="{BASE}services/">Our Services</a>{nav}<a href="mailto:opervyn.business@gmail.com">Contact</a></nav></header><main class="cms-page"><p class="cms-breadcrumb"><a href="{BASE}">Home</a> &nbsp;›&nbsp; {e(p['title'])}</p>{body}</main><footer class="footer"><div class="seo-footer-links"><a href="{BASE}services/">Our Services</a><a href="{BASE}services/data-entry/">Data Entry</a><a href="{BASE}services/virtual-assistant/">Virtual Assistant</a><a href="{BASE}nda-confidentiality/">NDA &amp; Confidentiality</a>{nav}</div><div class="footer-main"><a aria-label="OPERVYN home" class="brand footer-brand" href="{BASE}"><img alt="OPERVYN — Your Offshore Operations Partner" src="{BASE}assets/opervyn-logo-new.webp"></a><p>OPERVYN — Your Offshore Operations Partner.</p></div><div class="footer-bottom"><span>Remote-first operations support from Bangladesh</span><span>© OPERVYN. All rights reserved.</span><span>Data Entry · Virtual Assistant</span><span><a href="mailto:opervyn.business@gmail.com">Email ↗</a></span></div></footer><script src="{BASE}script.js"></script></body></html>"""
    out.write_text(page,encoding='utf-8')

# Add links for CMS-created pages to the existing homepage navigation and footer.
home=ROOT/'index.html'; home_html=home.read_text(encoding='utf-8')
new_links=[]
for q in data.get('pages',[]):
    if q.get('status')!='published' or q.get('slug') in ('about','data-entry','virtual-assistant','nda-confidentiality'): continue
    new_links.append(f'<a href="/pages/{e(q["slug"])}/">{e(q.get("navLabel") or q["title"])}</a>')
links=''.join(new_links)
for start,end in [('<!-- CMS_PAGE_LINKS_START -->','<!-- CMS_PAGE_LINKS_END -->'),('<!-- CMS_FOOTER_LINKS_START -->','<!-- CMS_FOOTER_LINKS_END -->')]:
    a=home_html.find(start); b=home_html.find(end)
    if a>=0 and b>a: home_html=home_html[:a+len(start)]+links+home_html[b:]
home.write_text(home_html,encoding='utf-8')
# Refresh sitemap entries for published CMS pages.
sitemap=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for route in ['', 'services/', 'services/data-entry/', 'services/virtual-assistant/', 'nda-confidentiality/']:
    sitemap.append(f'<url><loc>https://opervyn.github.io/{route}</loc></url>')
for q in data.get('pages',[]):
    if q.get('status')!='published': continue
    route={'about':'about','data-entry':'services/data-entry','virtual-assistant':'services/virtual-assistant','nda-confidentiality':'nda-confidentiality'}.get(q['slug'],'pages/'+q['slug'])
    sitemap.append(f'<url><loc>https://opervyn.github.io/{e(route)}/</loc></url>')
sitemap.append('</urlset>')
(ROOT/'sitemap.xml').write_text('\n'.join(sitemap)+'\n',encoding='utf-8')
