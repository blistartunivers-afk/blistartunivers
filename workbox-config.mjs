import { injectManifest } from 'workbox-build';
import { readFileSync, writeFileSync } from 'fs';

const ROOT = '/data/data/com.termux/files/home/blistartunivers';
const DIST = `${ROOT}/dist`;

async function generateServiceWorker() {
  console.log('Generando Service Worker con Workbox (injectManifest)...');
  
  const { count, size, warnings } = await injectManifest({
    swSrc: `${ROOT}/scripts/sw-template.js`,
    swDest: `${DIST}/sw.js`,
    globDirectory: DIST,
    globPatterns: [
      '**/*.{html,js,css,json,ico,png,pgm,txt,woff2}'
    ],
    globIgnores: [
      '**/node_modules/**',
      '**/manifest.json',
      '**/sw.js',
      '**/workbox-*.js'
    ],
    maximumFileSizeToCacheInBytes: 5 * 1024 * 1024, // 5MB
    manifestTransforms: [
      (manifestEntries) => {
        // Add revision hashes from our manifest.json
        const customManifest = JSON.parse(readFileSync(`${DIST}/manifest.json`, 'utf-8'));
        const hashMap = customManifest.files || {};
        
        const transformed = manifestEntries.map(entry => {
          const hash = hashMap[entry.url];
          if (hash) {
            return { ...entry, revision: hash };
          }
          return entry;
        });
        return { manifest: transformed, warnings: [] };
      }
    ],
  });
  
  if (warnings.length > 0) {
    console.warn('Warnings:', warnings);
  }
  
  console.log(`Service Worker generado: ${count} archivos, ${(size / 1024).toFixed(1)} KB`);
}

generateServiceWorker().catch(err => {
  console.error('Error generando SW:', err);
  process.exit(1);
});