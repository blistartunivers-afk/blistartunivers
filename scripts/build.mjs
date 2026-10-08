import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync, rmSync } from 'fs';
import { join } from 'path';
import { minify } from 'terser';
import { minify as minifyHtml } from 'html-minifier-terser';
import postcss from 'postcss';
import cssnano from 'cssnano';
import { execSync } from 'child_process';

const ROOT = '/data/data/com.termux/files/home/blistartunivers';
const DIST = join(ROOT, 'dist');
const MOTOR = join(ROOT, 'motor');
const GALLERY = join(MOTOR, 'gallery');

async function minifyJs(code) {
  const result = await minify(code, {
    compress: { passes: 2, ecma: 2020 },
    mangle: { toplevel: true },
    format: { comments: false }
  });
  return result.code;
}

async function minifyCss(code) {
  const result = await postcss([cssnano({ preset: 'default' })]).process(code, { from: undefined });
  return result.css;
}

async function minifyHtmlFile(inputPath, outputPath) {
  const html = readFileSync(inputPath, 'utf-8');
  const minified = await minifyHtml(html, {
    collapseWhitespace: true,
    removeComments: true,
    minifyCSS: true,
    minifyJS: true,
    removeAttributeQuotes: true,
    useShortDoctype: true,
    keepClosingSlash: true
  });
  writeFileSync(outputPath, minified);
}

function copyDir(src, dest) {
  if (!existsSync(dest)) mkdirSync(dest, { recursive: true });
  for (const entry of readdirSync(src, { withFileTypes: true })) {
    const srcPath = join(src, entry.name);
    const destPath = join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      writeFileSync(destPath, readFileSync(srcPath));
    }
  }
}

function hashFile(content) {
  let hash = 0;
  for (let i = 0; i < content.length; i++) {
    hash = ((hash << 5) - hash) + content.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash).toString(36).substring(0, 8);
}

async function compileTypeScript() {
  console.log('  Compilando TypeScript...');
  try {
    execSync('npx tsc --project tsconfig.json', { cwd: ROOT, stdio: 'inherit' });
    console.log('  ✓ TypeScript compilado');
  } catch (e) {
    console.error('  ✗ Error compilando TypeScript:', e.message);
    throw e;
  }
}

async function processMotorHtml(html) {
  let result = html;
  
  const styleRegex = /<style>([\s\S]*?)<\/style>/g;
  const styleMatches = [...html.matchAll(styleRegex)];
  
  for (const match of styleMatches.reverse()) {
    const fullMatch = match[0];
    const cssContent = match[1];
    const minifiedCss = await minifyCss(cssContent);
    const replacement = `<style>${minifiedCss}</style>`;
    result = result.slice(0, match.index) + replacement + result.slice(match.index + fullMatch.length);
  }
  
  const scriptRegex = /<script>([\s\S]*?)<\/script>/g;
  const scriptMatches = [...html.matchAll(scriptRegex)];
  
  for (const match of scriptMatches.reverse()) {
    const fullMatch = match[0];
    const jsContent = match[1];
    if (jsContent.trim().startsWith('import') || 
        jsContent.trim().startsWith('export') ||
        jsContent.includes('`') ||
        jsContent.includes('<div') ||
        jsContent.includes('<canvas') ||
        jsContent.length > 50000) continue;
    try {
      const minifiedJs = await minifyJs(jsContent);
      const replacement = `<script>${minifiedJs}</script>`;
      result = result.slice(0, match.index) + replacement + result.slice(match.index + fullMatch.length);
    } catch (e) {
      console.warn('  Skipping script minification:', e.message);
    }
  }
  
  return result;
}

async function build() {
  console.log('Iniciando build...');
  
  if (existsSync(DIST)) {
    rmSync(DIST, { recursive: true, force: true });
  }
  mkdirSync(DIST, { recursive: true });
  mkdirSync(join(DIST, 'motor'), { recursive: true });
  mkdirSync(join(DIST, 'motor', 'gallery'), { recursive: true });
  
  // 1. Compilar TypeScript primero
  await compileTypeScript();
  
  const swRegistration = `<script>if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js').then(r=>console.log('[SW] Registered:',r.scope)).catch(e=>console.warn('[SW] Registration failed:',e))}</script>`;
  
  console.log('  Minificando index.html (root)...');
  await minifyHtmlFile(join(ROOT, 'index.html'), join(DIST, 'index.html'));
  
  let rootHtml = readFileSync(join(DIST, 'index.html'), 'utf-8');
  rootHtml = rootHtml.replace('</body>', swRegistration + '</body>');
  writeFileSync(join(DIST, 'index.html'), rootHtml);
  
  console.log('  Procesando motor/index.html...');
  const motorHtml = readFileSync(join(MOTOR, 'index.html'), 'utf-8');
  const processedMotorHtml = await processMotorHtml(motorHtml);
  
  const finalMotorHtml = await minifyHtml(processedMotorHtml, {
    collapseWhitespace: true,
    removeComments: true,
    minifyCSS: false,
    minifyJS: false,
    removeAttributeQuotes: true,
    useShortDoctype: true,
    keepClosingSlash: true
  });
  
  const finalMotorHtmlWithSw = finalMotorHtml.replace('</body>', swRegistration + '</body>');
  writeFileSync(join(DIST, 'motor', 'index.html'), finalMotorHtmlWithSw);
  
  console.log('  Minificando dream-loader.v2.js (compilado)...');
  const loaderJs = readFileSync(join(MOTOR, 'dream-loader.v2.js'), 'utf-8');
  const minifiedLoader = await minifyJs(loaderJs);
  writeFileSync(join(DIST, 'motor', 'dream-loader.v2.js'), minifiedLoader);
  
  console.log('  Minificando cppn-engine.js (compilado)...');
  const engineJs = readFileSync(join(MOTOR, 'cppn-engine.js'), 'utf-8');
  const minifiedEngine = await minifyJs(engineJs);
  writeFileSync(join(DIST, 'motor', 'cppn-engine.js'), minifiedEngine);
  
  console.log('  Copiando galeria...');
  copyDir(GALLERY, join(DIST, 'motor', 'gallery'));
  
  console.log('  Copiando scripts del motor...');
  copyDir(join(MOTOR, 'scripts'), join(DIST, 'motor', 'scripts'));
  
  console.log('  Copiando evolution-viewer.html...');
  writeFileSync(join(DIST, 'motor', 'evolution-viewer.html'), readFileSync(join(MOTOR, 'evolution-viewer.html')));
  
  if (existsSync(join(ROOT, 'assets'))) {
    copyDir(join(ROOT, 'assets'), join(DIST, 'assets'));
  }
  
  const manifest = {
    version: '11.0.0',
    built: new Date().toISOString(),
    files: {
      'index.html': hashFile(readFileSync(join(DIST, 'index.html'), 'utf-8')),
      'motor/index.html': hashFile(readFileSync(join(DIST, 'motor', 'index.html'), 'utf-8')),
      'motor/dream-loader.v2.js': hashFile(readFileSync(join(DIST, 'motor', 'dream-loader.v2.js'), 'utf-8')),
      'motor/cppn-engine.js': hashFile(readFileSync(join(DIST, 'motor', 'cppn-engine.js'), 'utf-8')),
    }
  };
  writeFileSync(join(DIST, 'manifest.json'), JSON.stringify(manifest, null, 2));
  
  console.log('\n✓ Build completado en', DIST);
  console.log('  Archivos:', Object.keys(manifest.files).length);
}

build().catch(e => { console.error('Build falló:', e); process.exit(1); });