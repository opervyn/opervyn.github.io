# ABLEHARBOR CMS — GitHub Pages

The CMS runs in the browser and stores content in this repository. GitHub Actions generates CMS-managed routes and deploys the static website to GitHub Pages.

- Public site: `https://ableharbor.github.io/`
- Repository: `ableharbor/ableharbor.github.io`
- Publishing branch: `main`
- Admin: `https://ableharbor.github.io/admin/`

## Content architecture

- `content/pages.json` contains every managed page, its SEO settings, visibility, ordered sections, section fields and repeatable items.
- `content/site.json` contains shared contact details, navigation, footer content and media alt-text metadata.
- `index.html` and `services/index.html` remain the original bespoke ABLEHARBOR layouts. They are now represented by the `home` and `services` system-page records in `content/pages.json`. The site script hydrates those existing sections from the CMS without replacing their design.
- `scripts/build_pages.py` generates the About, Data Entry, Virtual Assistant, NDA and custom CMS routes. It also updates legacy-page SEO metadata, hidden-section state and the sitemap.
- `.github/workflows/pages.yml` builds and deploys the repository root to GitHub Pages.

## Connect the CMS

1. Open `https://ableharbor.github.io/admin/`.
2. Create a fine-grained GitHub personal access token.
3. Set resource owner to `ableharbor` and repository access to `ableharbor.github.io` only.
4. Grant **Contents: Read and write**. Add **Actions: Read-only** if you want deployment status shown in the dashboard.
5. Paste the token into the CMS and connect.

The token is held in browser memory only. It is not stored in local storage or committed to the repository. Disconnect when finished. GitHub Pages is static hosting: the admin route is not a private server-side login and repository contents are public. Do not store confidential client information or secrets in the repository.

## Manage pages

- **Homepage:** Pages → Homepage. Edit its SEO and the existing sections without changing the original visual design.
- **Services overview:** Pages → Our Services. Its hero, service cards, onboarding process, FAQ and closing panel are CMS-managed.
- **Existing subpages:** About, Data Entry, Virtual Assistant and NDA & Confidentiality are editable in the same page editor.
- **New pages:** Create page, set a lowercase URL slug, edit SEO and sections, preview, then Save & publish.
- The homepage and `/services/` are reserved built-in routes. They cannot be deleted or renamed. Their visibility can be switched off; the generator then hides their main content, adds `noindex,nofollow`, and excludes them from the sitemap.
- Draft pages are not generated or listed in the sitemap. Deleting a CMS-managed page removes its generated route on the next build.

## Visual section builder

Add and edit the 15 reusable section types: Hero, Text, About/Introduction, Text + Image, Service Cards, Feature, Gallery, Statistics, Testimonials, Process/Steps, FAQ, Contact, Team/Founders, Logos/Partners and Custom Content.

Each section can be reordered by dragging its header, duplicated, deleted, collapsed and hidden/shown. Section-specific fields include images, alt text, captions, buttons and repeatable items. Repeatable cards, FAQs, testimonials, process steps, statistics, gallery entries, logos and team members support add, edit, delete, duplicate and reorder controls.

For the homepage and services overview, existing section IDs map CMS content to the current public markup. New sections use the CMS section presentation and inherit ABLEHARBOR theme colors and responsive layout rules. Existing public sections retain their existing classes and design.

## Navigation and footer

- Navigation → Header navigation and Footer navigation.
- Add, edit, delete and reorder links; configure dropdowns, submenu links, new-tab behavior and primary CTA styling.
- A live text preview shows the current header and footer link structure before saving.
- Footer headings, description, logo, copyright, lower notes, contact email and optional phone are editable under Site settings. Social and service links are managed through Footer navigation.
- Anchor links are kept on the homepage when used from other pages.

## Media library

- Upload PNG, JPEG, WebP or GIF images. Supported browser image formats are resized to a maximum 2000px edge and converted to WebP when the optimized result is smaller.
- Choose images from the library in section image fields, or enter an HTTPS URL / repository path.
- Set alt text, copy paths, replace section images and rename CMS-managed uploads. Renaming updates references in the CMS JSON before removing the old asset.
- Unused CMS-managed uploads can be deleted. Legacy assets are protected from rename/deletion because bespoke HTML may reference them directly.
- Image paths are checked against the media library when its listing is available. External images must use HTTPS.

## Save and publish

1. Connect with the fine-grained token.
2. Make changes and use Preview before publishing.
3. Select Save & publish. The CMS validates the page and commits `content/pages.json` or `content/site.json` to `main`.
4. GitHub Actions runs `scripts/build_pages.py`, assembles the Pages artifact and deploys it.
5. If the token has Actions read access, the CMS checks the workflow run for the saved commit. A successful content commit is not reported as a successful deployment unless GitHub reports a successful run.
6. If deployment status cannot be checked, open the repository's Actions tab and verify the latest Pages workflow manually.

Uploaded images are committed as repository assets. Each upload can trigger a build; the page content is not published until its JSON changes are saved.

## SEO and canonical URLs

The only canonical host is `https://ableharbor.github.io/`. The build updates canonical, Open Graph and Twitter metadata for the homepage and services overview, and generates canonical metadata for CMS-managed routes. `robots.txt` points to `https://ableharbor.github.io/sitemap.xml`. The sitemap is rebuilt from published, visible pages only.

Legacy image filenames containing the former project name are retained where existing markup still references them. They are asset filenames only and are not canonical URLs or public brand references.

## Local validation

Run from the repository root:

```bash
node --check admin/admin.js
node --check site.js
python -m py_compile scripts/build_pages.py
python scripts/build_pages.py
python -c "import json; json.load(open('content/site.json')); json.load(open('content/pages.json'))"
```

The build is deterministic and only removes previously generated routes plus the known CMS-managed route files. It does not recursively delete assets or unrelated content.

## Platform limitations

- GitHub Pages has no server-side CMS database, private admin authentication or secret storage. Repository content is public; protect the repository and token accordingly.
- GitHub API writes and the final hosted deployment require a valid user-supplied token and a successful GitHub Actions run. They cannot be verified from a local build.
- Existing legacy sections are hydrated in the browser from `content/pages.json`; the original HTML remains as the no-JavaScript fallback. SEO metadata and visibility state are also written into HTML during the build.
- Legacy assets are protected from rename/deletion because the CMS cannot safely rewrite every hard-coded reference in the bespoke public HTML.
