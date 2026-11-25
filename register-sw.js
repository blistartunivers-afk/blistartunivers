if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register(new URL('./sw.js', import.meta.url))
      .catch(error => console.warn('No se pudo activar el modo sin conexión:', error));
  });
}
