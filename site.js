(() => {
  const siteRoot = '/';
  const contentUrl = `${siteRoot}content/site.json`;

  function updateText(element, value) {
    const text = String(value);
    const firstText = Array.from(element.childNodes).find(node => node.nodeType === Node.TEXT_NODE);
    const lineBreak = Array.from(element.childNodes).find(
      node => node.nodeType === Node.ELEMENT_NODE && node.tagName === 'BR'
    );
    const accent = Array.from(element.children).find(child => child.tagName === 'SPAN');

    // Keep the existing visual hierarchy on editable headings without using innerHTML.
    if (firstText && lineBreak && accent) {
      const match = text.match(/^(.+?[.!?])\s+(.+)$/);
      firstText.textContent = match ? match[1] : text;
      accent.textContent = match ? match[2] : '';
      lineBreak.hidden = !match;
      return;
    }

    element.textContent = text;
  }

  fetch(contentUrl, { cache: 'no-store' })
    .then(response => {
      if (!response.ok) throw new Error(`Site settings unavailable (${response.status})`);
      return response.json();
    })
    .then(data => {
      document.querySelectorAll('[data-cms]').forEach(element => {
        const value = data[element.dataset.cms];
        if (typeof value === 'string') updateText(element, value);
      });

      if (data.seoTitle && location.pathname === '/') {
        document.title = data.seoTitle;
      }
      const description = document.querySelector('meta[name="description"]');
      if (description && data.seoDescription && location.pathname === '/') {
        description.content = data.seoDescription;
      }

      if (typeof data.contactEmail === 'string' && data.contactEmail.trim()) {
        document.querySelectorAll('[data-cms-email]').forEach(element => {
          element.href = `mailto:${data.contactEmail.trim()}`;
          // Keep CTA labels (for example, "Email ABLEHARBOR") intact; update address labels only.
          if (element.classList.contains('contact-email')) {
            const suffix = element.textContent.trim().endsWith('↗') ? ' ↗' : '';
            element.textContent = `${data.contactEmail.trim()}${suffix}`;
          }
        });
      }
    })
    .catch(error => {
      // The static HTML remains usable when the optional CMS settings file cannot load.
      console.warn('ABLEHARBOR site settings were not applied:', error.message);
    });
})();
