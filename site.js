(() => {
  const contentUrl = '/content/site.json';
  const isMobile = () => window.matchMedia('(max-width: 767px), (pointer: coarse)').matches || /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent);

  function updateText(element, value) {
    const text = String(value);
    const firstText = Array.from(element.childNodes).find(node => node.nodeType === Node.TEXT_NODE);
    const lineBreak = Array.from(element.childNodes).find(node => node.nodeType === Node.ELEMENT_NODE && node.tagName === 'BR');
    const accent = Array.from(element.children).find(child => child.tagName === 'SPAN');
    if (firstText && lineBreak && accent) {
      const match = text.match(/^(.+?[.!?])\s+(.+)$/);
      firstText.textContent = match ? match[1] : text;
      accent.textContent = match ? match[2] : '';
      lineBreak.hidden = !match;
      return;
    }
    element.textContent = text;
  }

  function safeUrl(url) {
    const value = String(url || '#').trim();
    return /^(https?:|mailto:|tel:|\/|#)/i.test(value) && !value.startsWith('//') ? value : '#';
  }

  function renderLinks(host, links) {
    if (!host || !Array.isArray(links)) return;
    host.replaceChildren();
    links.forEach(item => {
      if (!item || !item.label || !item.url) return;
      const a = document.createElement('a');
      a.textContent = item.label + (item.cta ? ' ↗' : '');
      a.href = safeUrl(item.url);
      if (a.href.toLowerCase().startsWith('mailto:')) a.dataset.cmsEmail = 'true';
      if (item.cta) a.className = 'nav-cta';
      if (item.newTab) { a.target = '_blank'; a.rel = 'noopener noreferrer'; }
      host.append(a);
    });
  }

  function setupEmailLinks(email) {
    const address = String(email || 'ableharbor.operation@gmail.com').trim();
    document.querySelectorAll('[data-cms-email]').forEach(anchor => {
      const prior = anchor.getAttribute('href') || '';
      const query = prior.includes('?') ? prior.slice(prior.indexOf('?')) : '';
      const subject = query.match(/[?&]subject=([^&]*)/i);
      const subjectText = subject ? decodeURIComponent(subject[1].replace(/\+/g, ' ')) : '';
      const mailto = `mailto:${address}${subjectText ? `?subject=${encodeURIComponent(subjectText)}` : query}`;
      anchor.href = mailto; // no-JS fallback and native mobile behavior
      if (anchor.classList.contains('contact-email')) { const suffix = anchor.textContent.trim().endsWith('↗') ? ' ↗' : ''; anchor.textContent = address + suffix; }
      anchor.addEventListener('click', event => {
        if (isMobile()) return; // preserve the native mail app on phones/tablets
        event.preventDefault();
        const compose = new URL('https://mail.google.com/mail/');
        compose.searchParams.set('view', 'cm');
        compose.searchParams.set('to', address);
        if (subjectText) compose.searchParams.set('su', subjectText);
        window.open(compose.toString(), '_blank', 'noopener,noreferrer');
      });
    });
  }

  fetch(contentUrl, { cache: 'no-store' })
    .then(response => { if (!response.ok) throw new Error(`Site settings unavailable (${response.status})`); return response.json(); })
    .then(data => {
      document.querySelectorAll('[data-cms]').forEach(element => {
        const value = data[element.dataset.cms];
        if (typeof value === 'string') updateText(element, value);
      });
      if (data.seoTitle && location.pathname === '/') document.title = data.seoTitle;
      const description = document.querySelector('meta[name="description"]');
      if (description && data.seoDescription && location.pathname === '/') description.content = data.seoDescription;
      if (data.navigation) {
        renderLinks(document.querySelector('.site-header .nav'), data.navigation.header);
        renderLinks(document.querySelector('.seo-footer-links'), data.navigation.footer);
      }
      if (data.contactEmail) setupEmailLinks(data.contactEmail);
    })
    .catch(error => {
      console.warn('ABLEHARBOR site settings were not applied:', error.message);
      setupEmailLinks('ableharbor.operation@gmail.com');
    });
})();
