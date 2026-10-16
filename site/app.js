(() => {
  const button = document.querySelector('.menu-toggle');
  const menu = document.querySelector('#mobile-navigation');
  const closeMenu = () => {
    button.setAttribute('aria-expanded', 'false');
    button.setAttribute('aria-label', 'Open navigation menu');
    menu.hidden = true;
  };
  button.addEventListener('click', () => {
    const open = button.getAttribute('aria-expanded') !== 'true';
    button.setAttribute('aria-expanded', String(open));
    button.setAttribute('aria-label', open ? 'Close navigation menu' : 'Open navigation menu');
    menu.hidden = !open;
  });
  menu.addEventListener('click', event => {
    if (event.target.closest('a')) closeMenu();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !menu.hidden) { closeMenu(); button.focus(); }
  });
  document.addEventListener('click', event => {
    if (!menu.hidden && !event.target.closest('.site-header')) closeMenu();
  });
  window.matchMedia('(min-width: 768px)').addEventListener('change', event => {
    if (event.matches) closeMenu();
  });
  if ('IntersectionObserver' in window) {
    const sections = [...document.querySelectorAll('main > section[id]:not(#home)')];
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        document.querySelectorAll('.desktop-nav a').forEach(link => {
          if (link.hash === '#' + entry.target.id) link.setAttribute('aria-current', 'location');
          else link.removeAttribute('aria-current');
        });
      }
    }, { rootMargin: '-15% 0px -65% 0px', threshold: 0 });
    sections.forEach(section => observer.observe(section));
    if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      const reveal = new IntersectionObserver(entries => {
        for (const entry of entries) if (entry.isIntersecting) {
          entry.target.classList.add('reveal-once');
          reveal.unobserve(entry.target);
        }
      }, { threshold: 0.03 });
      document.querySelectorAll('.expertise-card, .project-card').forEach(card => reveal.observe(card));
    }
  }
})();
