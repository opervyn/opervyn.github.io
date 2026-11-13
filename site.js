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
      a.href = String(item.url).startsWith('#') && location.pathname !== '/' ? safeUrl('/' + item.url) : safeUrl(item.url);
      if (a.href.toLowerCase().startsWith('mailto:')) a.dataset.cmsEmail = 'true';
      if (item.cta) a.className = 'nav-cta';
      if (item.newTab) { a.target = '_blank'; a.rel = 'noopener noreferrer'; }
      if (Array.isArray(item.children) && item.children.length) {
        const details = document.createElement('details');
        details.className = 'cms-nav-dropdown';
        const summary = document.createElement('summary');
        const parentLink=document.createElement('a');parentLink.textContent=item.label;parentLink.href=String(item.url).startsWith('#')&&location.pathname!=='/'?safeUrl('/'+item.url):safeUrl(item.url);if(item.newTab){parentLink.target='_blank';parentLink.rel='noopener noreferrer';}summary.append(parentLink);
        const submenu = document.createElement('div');
        submenu.className = 'cms-nav-submenu';
        item.children.forEach(child => {
          if (!child || !child.label || !child.url) return;
          const sub = document.createElement('a');
          sub.textContent = child.label;
          sub.href = String(child.url).startsWith('#') && location.pathname !== '/' ? safeUrl('/' + child.url) : safeUrl(child.url);
          if (child.newTab) { sub.target = '_blank'; sub.rel = 'noopener noreferrer'; }
          submenu.append(sub);
        });
        details.append(summary, submenu);
        host.append(details);
        return;
      }
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

  function safePopupUrl(value) {
    const url = String(value || '').trim();
    return /^(https:\/\/|mailto:|tel:|\/|#)/i.test(url) && !url.startsWith('//') ? url : '#';
  }

  function renderOfferPopup(config, contactEmail) {
    if (!config || config.enabled === false || new URLSearchParams(location.search).has('popupPreview')) return;
    const cooldownKey = 'ableharbor_offer_last_shown_v1';
    const frequency = Math.max(1, Math.min(10080, Number(config.frequencyMinutes) || 60)) * 60 * 1000;
    const delay = Math.max(0, Math.min(60, Number(config.delaySeconds) || 0)) * 1000;
    try {
      const lastShown = Number(localStorage.getItem(cooldownKey) || 0);
      if (lastShown && Date.now() - lastShown < frequency) return;
    } catch (error) {
      // Storage may be unavailable in privacy modes; this visit can still receive the offer.
    }

    const create = (tag, className, text) => {
      const node = document.createElement(tag);
      if (className) node.className = className;
      if (text !== undefined) node.textContent = text;
      return node;
    };
    const dialog = create('dialog', `ah-offer-dialog ah-offer-${config.animation || 'fade-scale'}`);
    dialog.setAttribute('aria-labelledby', 'ah-offer-title');
    dialog.setAttribute('aria-describedby', 'ah-offer-intro');
    const shell = create('div', 'ah-offer-shell');
    const header = create('header', 'ah-offer-top');
    header.append(create('span', 'ah-offer-kicker', 'SPECIAL OFFER · ABLEHARBOR'));
    const title = create('h2', 'ah-offer-title', config.title || 'NEED A DEDICATED DATA ENTRY AGENT?');
    title.id = 'ah-offer-title';
    const headline = create('p', 'ah-offer-headline', config.headline || 'JUST $3.99/HOUR!');
    const close = create('button', 'ah-offer-close', '×');
    close.type = 'button'; close.setAttribute('aria-label', 'Close offer');
    header.append(title, headline, close);

    const content = create('div', 'ah-offer-content');
    const intro = create('p', 'ah-offer-intro', config.intro || ''); intro.id = 'ah-offer-intro';
    content.append(intro);
    if (Array.isArray(config.steps) && config.steps.length) {
      content.append(create('h3', 'ah-offer-section-title', config.stepsTitle || 'How It Works'));
      const list = create('ol', 'ah-offer-steps');
      config.steps.forEach(item => { if (String(item).trim()) list.append(create('li', '', item)); });
      content.append(list);
    }
    if (Array.isArray(config.benefits) && config.benefits.length) {
      content.append(create('h3', 'ah-offer-section-title', config.benefitsTitle || 'WHY ABLEHARBOR?'));
      const list = create('ul', 'ah-offer-benefits');
      config.benefits.forEach(item => { if (String(item).trim()) list.append(create('li', '', item)); });
      content.append(list);
    }
    if (config.closing) {
      const closing = create('div', 'ah-offer-closing');
      String(config.closing).split(/\n\s*\n/).forEach(paragraph => {
        if (paragraph.trim()) closing.append(create('p', '', paragraph.trim()));
      });
      content.append(closing);
    }
    const tagline = create('p', 'ah-offer-tagline', 'You Train. We Execute.');
    const cta = create('a', `ah-offer-cta ah-cta-${config.ctaEffect || 'shine'}`, config.ctaText || 'Contact ABLEHARBOR Today');
    cta.href = safePopupUrl(config.ctaUrl || `mailto:${contactEmail || 'ableharbor.operation@gmail.com'}?subject=Dedicated%20Data%20Entry%20Support%20Inquiry`);
    cta.append(create('span', 'ah-offer-cta-arrow', '↗'));
    if (cta.href.toLowerCase().startsWith('mailto:')) cta.dataset.cmsEmail = 'true';
    if (/^https:\/\//i.test(cta.href)) { cta.target = '_blank'; cta.rel = 'noopener noreferrer'; }
    content.append(tagline, cta);
    shell.append(header, content); dialog.append(shell); document.body.append(dialog);

    let closeTimer = 0;
    const dismiss = () => {
      if (!dialog.open) return;
      dialog.classList.add('ah-offer-closing');
      closeTimer = window.setTimeout(() => { dialog.close(); dialog.remove(); }, 180);
    };
    close.addEventListener('click', dismiss);
    dialog.addEventListener('click', event => { if (event.target === dialog) dismiss(); });
    dialog.addEventListener('cancel', event => { event.preventDefault(); dismiss(); });
    dialog.addEventListener('close', () => { window.clearTimeout(closeTimer); document.body.classList.remove('ah-offer-open'); });
    window.setTimeout(() => {
      if (!dialog.isConnected) return;
      try { localStorage.setItem(cooldownKey, String(Date.now())); } catch (error) {}
      document.body.classList.add('ah-offer-open');
      dialog.showModal();
      const focusable = dialog.querySelector('.ah-offer-close'); if (focusable) focusable.focus();
    }, delay);
  }

  fetch(contentUrl, { cache: 'no-store' })
    .then(response => { if (!response.ok) throw new Error(`Site settings unavailable (${response.status})`); return response.json(); })
    .then(data => {
      if (location.pathname !== '/') {
        document.querySelectorAll('[data-cms]').forEach(element => {
          const value = data[element.dataset.cms];
          if (typeof value === 'string') updateText(element, value);
        });
      }
      if (data.navigation) {
        renderLinks(document.querySelector('.site-header .nav'), data.navigation.header);
        renderLinks(document.querySelector('.seo-footer-links'), data.navigation.footer);
      }
      if (data.contactEmail) setupEmailLinks(data.contactEmail);
      renderOfferPopup(data.promoPopup, data.contactEmail);
      if (data.mediaAlt) document.querySelectorAll('img').forEach(img=>{try{const path=new URL(img.src,location.href).pathname.replace(/^\//,'');if(typeof data.mediaAlt[path]==='string'&&data.mediaAlt[path].trim())img.alt=data.mediaAlt[path].trim();}catch{}});
      if (data.footer) {
        const footer = data.footer;
        const description = document.querySelector('.footer-main > p'); if (description && footer.description) description.textContent = footer.description;
        if (footer.heading) { const host=document.querySelector('.footer-main'); if(host){let heading=host.querySelector('.footer-heading');if(!heading){heading=document.createElement('h3');heading.className='footer-heading';host.prepend(heading);}heading.textContent=footer.heading;} }
        const bottom = document.querySelector('.footer-bottom');
        if (bottom) { const spans = bottom.querySelectorAll(':scope > span'); if (spans[0] && footer.bottomNote) spans[0].textContent = footer.bottomNote; if (spans[1] && footer.copyright) spans[1].textContent = footer.copyright; if (spans[2] && footer.serviceNote) spans[2].textContent = footer.serviceNote; }
        if (footer.logo) document.querySelectorAll('.footer-brand img').forEach(img => img.src = footer.logo.startsWith('http') ? footer.logo : '/' + footer.logo.replace(/^\//,''));
        if (footer.phone) { const bottom = document.querySelector('.footer-bottom'); if (bottom) { let phone=bottom.querySelector('[data-cms-phone]'); if(!phone){phone=document.createElement('a');phone.dataset.cmsPhone='true';bottom.append(phone);} phone.href='tel:'+String(footer.phone).replace(/[^+0-9]/g,'');phone.textContent=footer.phone; } }
      }
    })
    .catch(error => {
      console.warn('ABLEHARBOR site settings were not applied:', error.message);
      setupEmailLinks('ableharbor.operation@gmail.com');
    });
})();

/* CMS-managed legacy page sections. The existing ABLEHARBOR section classes and
   layout remain intact; this layer only applies content, visibility and ordering. */
(() => {
  const esc = value => String(value ?? '');
  const setText = (node, value) => { if (node && typeof value === 'string') node.textContent = value; };
  const safeHref = value => /^(https?:\/\/|mailto:|tel:|\/|#)/i.test(String(value || '')) && !String(value).startsWith('//') ? String(value) : '#';
  const make = (tag, className, text) => { const el = document.createElement(tag); if (className) el.className = className; if (text !== undefined) el.textContent = text; return el; };

  function updateSectionContent(section, target) {
    const heading = section.heading;
    const body = section.body;
    const eyebrow = section.eyebrow;
    const kicker = target.querySelector('.section-kicker, .eyebrow');
    if (kicker && typeof eyebrow === 'string') {
      const line = kicker.querySelector('.eyebrow-line');
      if (line) { kicker.replaceChildren(line, document.createTextNode(eyebrow)); }
      else kicker.textContent = eyebrow;
      kicker.hidden = !eyebrow.trim();
    }
    const h1 = target.querySelector(':scope > .hero-content h1, :scope > h1, :scope .section-heading h2, :scope > h2, :scope .intro-grid h2, :scope .contact-copy h2, :scope .remote-copy h2');
    if (h1 && typeof heading === 'string') {
      h1.hidden = !heading.trim();
      const spans = h1.querySelectorAll('span');
      if (spans.length) { let parts = heading.split(/\s*(?:\n|(?<=\.)\s+)/).filter(Boolean); if(parts.length<2){const words=heading.trim().split(/\s+/);const midpoint=Math.max(1,Math.ceil(words.length/2));parts=[words.slice(0,midpoint).join(' '),words.slice(midpoint).join(' ')];} h1.replaceChildren(document.createTextNode(parts.shift() || heading)); const span=make('span','',parts.join(' '));span.hidden=!span.textContent;h1.append(span); }
      else h1.textContent = heading;
    }
    if (section.targetId === 'home') { setText(target.querySelector('.hero-tagline'), body); setText(target.querySelector('.hero-desc'), section.description); }
    if (section.targetId === 'about' && typeof section.detail === 'string') setText(target.querySelector('.intro-grid > div > p:nth-of-type(2)'), section.detail);
    if (typeof body === 'string') {
      const candidates = target.querySelectorAll(':scope > p, :scope .hero-content > p, :scope .section-heading > p, :scope .intro-grid > div > p, :scope .remote-copy > p, :scope .team-copy > p, :scope .founder-heading > p');
      if (candidates.length) { candidates[0].textContent = body; candidates[0].hidden = !body.trim(); }
    }
    if (section.targetId === 'services-model' && Array.isArray(section.items)) {
      const content = target.querySelector('.seo-content-main'); if (content) { const heads=content.querySelectorAll('h3'); const paras=content.querySelectorAll('p'); section.items.forEach((item,index)=>{ setText(heads[index], `${index+1}. ${item.title||''}`); setText(paras[index], item.body||item.description||''); }); for(let i=section.items.length;i<heads.length;i++){heads[i].hidden=true;if(paras[i])paras[i].hidden=true;} }
    }
    if (section.buttonText && section.buttonUrl) { const button=target.querySelector('.team-copy a, .hero-actions a, .contact-form .submit-btn'); if(button){button.textContent=section.buttonText+' ↗';button.href=safeHref(section.buttonUrl);} }
    if (Array.isArray(section.items)) {
      const host = target.querySelector('.service-grid, .service-category-grid, .process-line, .seo-directory-grid');
      if (host && ['service-cards','process','steps','feature'].includes(section.type)) {
        const existing = [...host.children];
        section.items.forEach((item, index) => {
          const card = existing[index];
          if (!card) return;
          setText(card.querySelector('h2, h3, .seo-directory-card > span'), item.title);
          const p = card.querySelector('p'); setText(p, item.body || item.description);
          const icon=card.querySelector('.service-icon, .process-symbol');if(icon&&item.icon)setText(icon,item.icon);
          if(item.image){let image=card.querySelector(':scope > .cms-item-image');if(!image){image=make('img','cms-item-image');card.insertBefore(image,card.firstChild);}image.src=safeHref(item.image.startsWith('http')?item.image:'/'+item.image.replace(/^\//,''));image.alt=item.alt||item.title||'';image.loading='lazy';}
          if (item.link && card.matches('a')) card.href = safeHref(item.link);
          const cardLink=card.querySelector('a.card-link, a.text-link');if(cardLink&&item.link)cardLink.href=safeHref(item.link);if(cardLink&&item.linkLabel)cardLink.textContent=item.linkLabel;
          const list = card.querySelector('ul'); if (list && Array.isArray(item.features)) { list.replaceChildren(); item.features.forEach(feature => list.append(make('li','',feature))); }
        });
        existing.slice(section.items.length).forEach(node => node.hidden = true);
        existing.slice(0, section.items.length).forEach(node => node.hidden = false);
      }
    }
    if (section.type === 'faq' && Array.isArray(section.items)) {
      const host = target.querySelector('.faq-list, .seo-faq');
      if (host) { host.querySelectorAll('details').forEach(node => node.remove()); section.items.forEach(item => { const details=make('details'); const summary=make('summary','',item.title||'Question'); if (target.id === 'faq') summary.append(make('span','','+')); if(item.icon)details.append(make('div','cms-added-icon',item.icon));if(item.image){const image=make('img','cms-item-image');image.src=safeHref(item.image.startsWith('http')?item.image:'/'+item.image.replace(/^\//,''));image.alt=item.alt||item.title||'';image.loading='lazy';details.append(image);}details.append(summary,make('p','',item.body||item.description||'')); host.append(details); }); }
    }
    if (Array.isArray(section.members)) {
      const host = target.querySelector('.founder-grid');
      if (host) [...host.children].forEach((card, index) => {
        const member = section.members[index]; if (!member) { card.hidden = true; return; } card.hidden = false;
        setText(card.querySelector('h2, h3'), member.name); setText(card.querySelector('.founder-bio'), member.bio);
        const role = card.querySelector('.founder-eyebrow, .photo-caption'); setText(role, member.role);
        const img = card.querySelector('img'); if (img && member.image) { img.src = safeHref(member.image.startsWith('http') ? member.image : '/' + member.image.replace(/^\//,'')); img.alt = member.alt || member.name || ''; }
      });
    }
  }

  function appendNewSection(section) {
    const wrap = make('section', `section cms-added-section cms-added-${section.type || 'text'}`);
    if (section.id) wrap.id = `cms-${section.id.replace(/[^a-z0-9_-]/gi,'')}`;
    if (section.eyebrow) wrap.append(make('div','section-kicker',section.eyebrow));
    if (section.heading) wrap.append(make('h2','',section.heading));
    if (section.body) wrap.append(make('p','cms-added-intro',section.body));
    if (section.image) { const img=make('img','cms-added-feature-image'); img.src=safeHref(section.image.startsWith('http')?section.image:'/'+section.image.replace(/^\//,'')); img.alt=section.alt||section.heading||''; img.loading='lazy'; wrap.append(img); }
    const items = Array.isArray(section.items) ? section.items : [];
    if (section.type === 'faq') {
      const list=make('div','cms-added-faq'); items.forEach(item=>{const d=make('details');d.append(make('summary','',item.title||'Question'),make('p','',item.body||item.description||''));list.append(d);});wrap.append(list);
    } else if (items.length) {
      const grid=make('div',`cms-added-grid cms-added-grid-${section.type||'cards'}`);
      items.forEach((item,index)=>{
        if(section.type==='gallery') { const figure=make('figure','cms-added-gallery-item'); if(item.image){const img=make('img');img.src=safeHref(item.image.startsWith('http')?item.image:'/'+item.image.replace(/^\//,''));img.alt=item.alt||item.title||'';img.loading='lazy';figure.append(img);} if(item.caption||item.title)figure.append(make('figcaption','',item.caption||item.title));grid.append(figure);return; }
        if(section.type==='stats') { const stat=make('article','cms-added-stat');stat.append(make('strong','',item.value||item.title||''),make('span','',item.label||item.body||''));grid.append(stat);return; }
        if(section.type==='logos') { const logo=make('div','cms-added-logo');if(item.image){const img=make('img');img.src=safeHref(item.image.startsWith('http')?item.image:'/'+item.image.replace(/^\//,''));img.alt=item.alt||item.name||item.title||'';logo.append(img);}logo.append(make('span','',item.name||item.title||''));grid.append(logo);return; }
        const card=make('article',`cms-added-card${section.type==='testimonials'?' cms-added-quote':''}`);
        if(item.image){const img=make('img','cms-added-card-image');img.src=safeHref(item.image.startsWith('http')?item.image:'/'+item.image.replace(/^\//,''));img.alt=item.alt||item.title||'';img.loading='lazy';card.append(img);}
        if(item.icon)card.append(make('div','cms-added-icon',item.icon));
        if(item.title||item.name)card.append(make('h3','',item.title||item.name));
        if(item.body||item.description||item.quote)card.append(make('p','',item.body||item.description||item.quote));
        if(item.role)card.append(make('small','',item.role));
        if(item.value)card.append(make('strong','cms-added-value',item.value));
        if(Array.isArray(item.features)&&item.features.length){const ul=make('ul');item.features.forEach(value=>ul.append(make('li','',value)));card.append(ul);}
        if(item.link){const a=make('a','text-link',item.linkLabel||'Learn more ↗');a.href=safeHref(item.link);card.append(a);}
        grid.append(card);
      });
      wrap.append(grid);
    }
    if (Array.isArray(section.members)) {
      const grid=make('div','cms-added-grid cms-added-grid-team'); section.members.forEach(member=>{const card=make('article','cms-added-card cms-added-member');if(member.image){const img=make('img','cms-added-card-image');img.src=safeHref(member.image.startsWith('http')?member.image:'/'+member.image.replace(/^\//,''));img.alt=member.alt||member.name||'';img.loading='lazy';card.append(img);}card.append(make('h3','',member.name||''),make('small','',member.role||''),make('p','',member.bio||''));grid.append(card);});wrap.append(grid);
    }
    if (section.buttonText && section.buttonUrl) { const a=make('a','btn btn-primary',section.buttonText+' ↗');a.href=safeHref(section.buttonUrl);wrap.append(a); }
    return wrap;
  }

  async function applyPageBuilder() {
    const path = location.pathname.replace(/\/+$/,'') || '/';
    if (path !== '/' && path !== '/services') return;
    try {
      const response = await fetch('/content/pages.json', {cache:'no-store'}); if (!response.ok) return;
      const data = await response.json(); const slug = path === '/' ? 'home' : 'services';
      const page = (data.pages || []).find(item => item.slug === slug && item.systemPage);
      if (!page) return;
      const main = document.querySelector('main'); if (!main) return;
      if (page.visible === false) { main.hidden = true; let robots=document.querySelector('meta[name="robots"]');if(!robots){robots=document.createElement('meta');robots.name='robots';document.head.append(robots);}robots.content='noindex,nofollow';return; }
      const ordered = [];
      (page.sections || []).forEach(section => {
        if (section.visible === false) { const target = section.targetId && document.getElementById(section.targetId); if (target) target.hidden = true; return; }
        const target = section.targetId && document.getElementById(section.targetId);
        if (target) { target.hidden = false; updateSectionContent(section,target); ordered.push(target); }
        else { const added = appendNewSection(section); if (added) ordered.push(added); }
      });
      // Reorder only managed legacy sections; non-managed structural nodes remain in place.
      if (path === '/' || path === '/services') ordered.forEach(node => main.append(node));
      const seo = page.seo || {}; if (seo.title) document.title = seo.title;
      const description = document.querySelector('meta[name="description"]'); if (description && seo.description) description.content = seo.description;
      if (seo.image) { ['og:image','twitter:image'].forEach(property=>{const meta=document.querySelector(`meta[property="${property}"],meta[name="${property}"]`);if(meta)meta.content=seo.image.startsWith('http')?seo.image:'https://ableharbor.github.io/'+seo.image.replace(/^\//,'');}); }
      const canonical = document.querySelector('link[rel="canonical"]'); if (canonical) canonical.href = `https://ableharbor.github.io${path === '/' ? '/' : '/services/'}`;
      const ogTitle=document.querySelector('meta[property="og:title"]');if(ogTitle&&seo.title)ogTitle.content=seo.title;
      const ogDescription=document.querySelector('meta[property="og:description"]');if(ogDescription&&seo.description)ogDescription.content=seo.description;
      const ogUrl=document.querySelector('meta[property="og:url"]');if(ogUrl)ogUrl.content=`https://ableharbor.github.io${path === '/' ? '/' : '/services/'}`;
    } catch (error) { console.warn('ABLEHARBOR page content could not be applied:', error); }
  }
  applyPageBuilder();
})();
