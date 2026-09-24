(() => {
  const input = document.querySelector('#id_image_url');
  const image = document.querySelector('[data-image-preview]');
  const status = document.querySelector('[data-image-preview-status]');
  if (!input || !image || !status) return;
  let timer;
  function preview() {
    image.hidden = true;
    image.removeAttribute('src');
    const value = input.value.trim();
    if (!value) {
      status.textContent = 'No image selected. Your portfolio will use its built-in artwork.';
      return;
    }
    try {
      const url = new URL(value);
      if (!['http:', 'https:'].includes(url.protocol)) throw new Error('Invalid URL');
      status.textContent = 'Loading preview…';
      image.src = url.href;
    } catch {
      status.textContent = 'Enter a complete HTTP or HTTPS image URL to preview it.';
    }
  }
  image.addEventListener('load', () => {
    image.hidden = false;
    status.textContent = 'Image preview. Save the project to apply changes.';
  });
  image.addEventListener('error', () => {
    image.hidden = true;
    status.textContent = 'Preview unavailable. Check that the URL points to an accessible image.';
  });
  input.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(preview, 350);
  });
  preview();
})();
