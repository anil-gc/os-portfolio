(() => {
  const opener = document.querySelector('[data-drawer-open]');
  const drawer = document.querySelector('#workspace-navigation');
  const main = document.querySelector('[data-workspace-main]');
  const backdrop = document.querySelector('.drawer-backdrop');
  if (!opener || !drawer || !main || !backdrop) return;

  const mobile = window.matchMedia('(max-width: 900px)');
  const closeButton = drawer.querySelector('[data-drawer-close]');
  let open = false;
  const focusable = () => [...drawer.querySelectorAll('a[href], button:not([disabled]), input:not([type="hidden"])')]
    .filter((element) => element.getClientRects().length > 0);

  function setOpen(value, restoreFocus = true) {
    open = value && mobile.matches;
    document.body.classList.toggle('drawer-open', open);
    opener.setAttribute('aria-expanded', String(open));
    backdrop.hidden = !open;
    main.inert = open;
    drawer.inert = mobile.matches && !open;
    if (open) {
      drawer.setAttribute('role', 'dialog');
      drawer.setAttribute('aria-modal', 'true');
      closeButton.focus();
    } else {
      drawer.removeAttribute('role');
      drawer.removeAttribute('aria-modal');
      if (restoreFocus && mobile.matches) opener.focus();
    }
  }

  document.body.classList.add('drawer-ready');
  opener.hidden = false;
  closeButton.hidden = false;
  setOpen(false, false);
  opener.addEventListener('click', () => setOpen(true));
  document.querySelectorAll('[data-drawer-close]').forEach((button) => {
    button.addEventListener('click', () => setOpen(false));
  });
  document.addEventListener('keydown', (event) => {
    if (!open) return;
    if (event.key === 'Escape') {
      event.preventDefault();
      setOpen(false);
    }
    if (event.key === 'Tab') {
      const items = focusable();
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  });
  mobile.addEventListener('change', () => {
    const focusWasInDrawer = drawer.contains(document.activeElement);
    const focusWasOnOpener = document.activeElement === opener;
    setOpen(false, false);
    if (mobile.matches && focusWasInDrawer) opener.focus();
    if (!mobile.matches && (focusWasOnOpener || document.activeElement === closeButton)) {
      drawer.querySelector('a').focus();
    }
  });
  window.addEventListener('pageshow', () => setOpen(false, false));
})();
