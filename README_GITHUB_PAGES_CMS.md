# OPERVYN — GitHub Pages Full Page CMS (৳0 hosting)

This package is prepared for `https://github.com/opervyn/opervyn-website`. It keeps the existing OPERVYN CSS theme and fonts (Inter + Montserrat), and adds a GitHub-backed visual CMS for page content.

## What the CMS manages

- Homepage copy and SEO fields in `content/site.json`.
- Existing About, Data Entry, Virtual Assistant and NDA page content through the page editor.
- Create new pages, edit page titles/slugs, save drafts or publish, and delete pages.
- Add, edit, remove and reorder page sections: hero, text, image, list, cards, call-to-action and founding-member profiles.
- Edit per-page SEO title and meta description.
- Upload images (PNG/JPG/WebP/GIF, max 5 MB) directly to the repository Assets folder from the CMS.
- Preview a page before publishing.
- Every generated page uses the same shared OPERVYN stylesheets, logo, typography and responsive layout. New pages use `/pages/<slug>/`.

The Data Entry, Virtual Assistant, NDA and About pages are generated from `content/pages.json` and replace the corresponding static page routes during the GitHub Actions build. New pages are generated under `/pages/<slug>/`.

## Important architecture and security

GitHub Pages is static hosting. It cannot run a traditional server-side CMS, private backend sessions or a private database. This CMS is a browser-based editor that reads and writes JSON/files through the GitHub API. Anyone can open `/admin/`; only a person with a valid repository-scoped GitHub token can publish. The token is held in memory only, not local storage and not committed. This is not server-side authentication.

For free GitHub Pages hosting, the repository generally needs to be public. Treat every committed file as public. Never put client data, confidential files, passwords or tokens in the repository.

## One-time setup

1. Confirm the repository is `opervyn/opervyn-website` and its default branch is `main`.
2. Extract this ZIP and upload **the contents of the extracted folder** to the repository root, replacing old files when GitHub asks. Do not upload the outer ZIP as one file.
3. In GitHub, open **Settings → Pages** and choose **GitHub Actions** as the source.
4. Open **Actions** and wait for `Deploy OPERVYN to GitHub Pages` to complete successfully.
5. Website: `https://opervyn.github.io/opervyn-website/`  
   CMS: `https://opervyn.github.io/opervyn-website/admin/`

## Create a GitHub token

1. GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token.
2. Resource owner: `opervyn`.
3. Repository access: **Only select repositories** → `opervyn-website`.
4. Repository permissions: **Contents: Read and write**. Metadata remains read-only.
5. Use an expiry date. Paste the token into the CMS and connect. Never send it to anyone or put it in a website file.
6. Disconnect after editing; closing the CMS page also clears the in-memory token.

## Editing and publishing

- Use **Pages → Edit page** to manage page sections and SEO.
- Use **Create page** for a new page; it starts as a draft. Change status to Published when ready.
- The page preview is a local preview. **Save & publish** commits JSON and any uploaded assets to GitHub. The Actions workflow generates the pages and deploys them.
- A published new page appears at `/pages/<slug>/` and is linked from CMS-managed page navigation.
- Homepage text is managed under **Site settings**.

## Validation status

The page generator, JSON and admin JavaScript are syntax-checked in this package. Deployment to the user's GitHub repository has not been performed. The first upload and GitHub Actions run are still required before the CMS is live. GitHub Pages rebuilds after each CMS commit.
