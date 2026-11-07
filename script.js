const menuButton=document.querySelector('.menu-toggle');const nav=document.querySelector('.nav');
menuButton?.addEventListener('click',()=>{const open=nav.classList.toggle('open');menuButton.setAttribute('aria-expanded',String(open));});
nav?.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{nav.classList.remove('open');menuButton?.setAttribute('aria-expanded','false');}));
document.querySelectorAll('.filter').forEach(button=>button.addEventListener('click',()=>{document.querySelectorAll('.filter').forEach(b=>b.classList.remove('active'));button.classList.add('active');const filter=button.dataset.filter;document.querySelectorAll('.work-card').forEach(card=>card.classList.toggle('hidden',filter!=='all'&&card.dataset.category!==filter));}));
const yearNode=document.querySelector('#year');if(yearNode)yearNode.textContent=new Date().getFullYear();
