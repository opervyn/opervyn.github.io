(() => {
  const repo = 'opervyn-website';
  const base = location.hostname === 'opervyn.github.io' ? `/${repo}/` : '/';
  const fullUrl = `${location.origin}${base}`;
  // GitHub Pages project sites live below /<repo>/; normalize source-root links and assets.
  document.querySelectorAll('[href^="/"]').forEach(el => {
    const value = el.getAttribute('href');
    if (value && !value.startsWith('//') && !value.startsWith(base)) el.setAttribute('href', base + value.replace(/^\/+/, ''));
  });
  document.querySelectorAll('[src^="/"]').forEach(el => {
    const value = el.getAttribute('src');
    if (value && !value.startsWith('//') && !value.startsWith(base)) el.setAttribute('src', base + value.replace(/^\/+/, ''));
  });
  const root = document.documentElement;
  const path = location.pathname.replace(base, '/');
  const jsonPath = `${base}content/site.json`;
  fetch(jsonPath, {cache:'no-store'}).then(r => r.ok ? r.json() : null).then(data => {
    if (!data) return;
    document.querySelectorAll('[data-cms]').forEach(el => {
      const value = data[el.dataset.cms];
      if (typeof value === 'string') el.textContent = value;
    });
    if (data.seoTitle && path === '/') document.title = data.seoTitle;
    const desc = document.querySelector('meta[name="description"]');
    if (desc && data.seoDescription && path === '/') desc.content = data.seoDescription;
    document.querySelectorAll('[data-cms-email]').forEach(el => {el.textContent=data.contactEmail;el.href=`mailto:${data.contactEmail}`;});
  }).catch(() => {});
})();
