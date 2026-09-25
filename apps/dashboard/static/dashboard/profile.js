(() => {
  const input = document.querySelector('#id_avatar');
  const preview = document.querySelector('[data-profile-preview]');
  const caption = document.querySelector('[data-preview-caption]');
  if (!input || !preview || !caption) return;
  const current = preview.getAttribute('src');
  const currentCaption = caption.textContent;
  let pending;
  input.addEventListener('change', () => {
    if (pending) URL.revokeObjectURL(pending);
    const file = input.files[0];
    if (file && ['image/jpeg', 'image/png', 'image/webp'].includes(file.type) && file.size <= 5 * 1024 * 1024) {
      pending = URL.createObjectURL(file);
      preview.src = pending;
      preview.hidden = false;
      caption.textContent = 'Selected photo — save changes to publish it.';
    } else {
      if (current) preview.src = current;
      else preview.removeAttribute('src');
      preview.hidden = !current;
      caption.textContent = file ? 'Choose a JPEG, PNG, or WebP photo up to 5 MB.' : currentCaption;
    }
  });
})();
