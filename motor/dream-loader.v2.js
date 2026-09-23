// ============================================
// DREAM LOADER · Motor de Imaginación CPPN
// Features: render, paletas, parallax 3D, modal,
//           header INDEX Fase 2 (paleta + ent_spatial),
//           filtro por paleta, badge de entropía
// ============================================

let dreamsCache = {}; // filename -> canvas
let indexMeta = {
    palette: null,         // paleta por defecto del INDEX
    entSpatialMin: null,   // mínimo entropía espacial del lote
    entSpatialAvg: null,   // promedio
    files: [],             // [{name, palette, entSpatial}]
};
let currentFilter = 'all';

/**
 * Parsea el INDEX.txt tolerando tanto la versión legacy
 * (solo nombres de archivo) como la Fase 2 con cabecera
 *   # Paleta por defecto: viridis
 *   # Entropía espacial (min, avg): 4.12, 4.65
 *   dream_xxx.png  palette=magma  ent_spatial=4.30
 */
function parseIndex(txt) {
    const meta = { palette: null, entSpatialMin: null, entSpatialAvg: null, files: [] };
    for (const rawLine of txt.split('\n')) {
        const line = rawLine.trim();
        if (!line) continue;
        if (line.startsWith('#')) {
            // Cabecera Fase 2
            const m1 = line.match(/paleta por defecto:\s*([\w-]+)/i);
            if (m1) meta.palette = m1[1].toLowerCase();
            // Tolera tanto "# Entropia espacial (min, avg): 0.00, 0.01"
            // como "# Entropia espacial: min=0.00, avg=0.01".
            // Regex: despues de ":" vienen los dos numeros.
            const m2 = line.match(/entrop[ií]a espacial.*?\)\s*:\s*([-\d.]+)\s*,\s*([-\d.]+)/i);
            if (m2) {
                meta.entSpatialMin = parseFloat(m2[1]);
                meta.entSpatialAvg = parseFloat(m2[2]);
            }
            continue;
        }
        // Extraer el primer token (nombre de archivo) y verificar sufijo.
        // Antes se hacia line.endsWith() sobre TODA la linea, lo cual falla
        // cuando hay " name.png palette=viridis ent_spatial=0.03"
        // (la línea termina en "0.03", no en ".png").
        const parts = line.split(/\s+/);
        const name = parts[0];
        if (!(name.endsWith('.pgm') || name.endsWith('.png'))) continue;
        // línea "name palette=viridis ent_spatial=4.20"
        let pal = meta.palette;
        let ent = null;
        for (const p of parts.slice(1)) {
            const [k, v] = p.split('=');
            if (k === 'palette' && v) pal = v.toLowerCase();
            if (k === 'ent_spatial' && v) ent = parseFloat(v);
        }
        meta.files.push({ name, palette: pal || 'raw', entSpatial: ent });
    }
    return meta;
}

function applyFilter(palette) {
    currentFilter = palette;
    document.querySelectorAll('.filter-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.filter === palette);
    });
    document.querySelectorAll('.dream').forEach(el => {
        const matches = (palette === 'all') || (el.dataset.palette === palette);
        el.dataset.paletteMismatch = (!matches).toString();
    });
}

async function loadDream(filename) {
    if (dreamsCache[filename]) {
        const cloned = document.createElement('canvas');
        cloned.width = dreamsCache[filename].width;
        cloned.height = dreamsCache[filename].height;
        cloned.getContext('2d').drawImage(dreamsCache[filename], 0, 0);
        return cloned;
    }
    // Cache-buster: fuerza descarga sin caché
    const resp = await fetch(`gallery/${filename}?t=${Date.now()}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status} al cargar ${filename}`);

    const isPNG = filename.toLowerCase().endsWith('.png');
    let canvas;
    if (isPNG) {
        // PNG: decodificación nativa del navegador (rápida).
        const blob = await resp.blob();
        const bitmap = await createImageBitmap(blob);
        canvas = document.createElement('canvas');
        canvas.width = bitmap.width;
        canvas.height = bitmap.height;
        canvas.getContext('2d').drawImage(bitmap, 0, 0);
    } else {
        // Legacy: .pgm parseado a mano (mantener para archivos antiguos).
        const buf = await resp.arrayBuffer();
        const pgm = parsePGM(buf);
        canvas = pgmToCanvas(pgm);
    }
    dreamsCache[filename] = canvas;

    const cloned = document.createElement('canvas');
    cloned.width = canvas.width;
    cloned.height = canvas.height;
    cloned.getContext('2d').drawImage(canvas, 0, 0);
    return cloned;
}

function parsePGM(buffer) {
    const data = new Uint8Array(buffer);
    const text = new TextDecoder('ascii').decode(data);
    const tokens = text.split(/\s+/);

    // Magic: P2 (texto) o P5 (binario)
    const magic = tokens[0];

    // Saltar magic
    let idx = 1;
    while (idx < tokens.length && (tokens[idx].startsWith('#') || tokens[idx] === '')) idx++;

    const w = parseInt(tokens[idx++]);
    const h = parseInt(tokens[idx++]);
    const maxval = parseInt(tokens[idx++]);

    if (magic === 'P5') {
        // Binario: el resto es w*h bytes crudos
        const headerBytes = data.length - (w * h);
        const pixels = data.slice(headerBytes);
        return { w, h, data: pixels };
    } else if (magic === 'P2') {
        // Texto ASCII: parsear números
        const pixels = new Uint8Array(w * h);
        for (let p = 0; p < w * h && idx < tokens.length; p++) {
            pixels[p] = parseInt(tokens[idx++]);
        }
        return { w, h, data: pixels };
    } else {
        throw new Error(`PGM formato desconocido: ${magic}`);
    }
}

function pgmToCanvas({ w, h, data }) {
    const canvas = document.createElement('canvas');
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d');
    const img = ctx.createImageData(w, h);
    for (let p = 0; p < w * h; p++) {
        const v = data[p];
        const o = p * 4;
        img.data[o]   = v;
        img.data[o+1] = v;
        img.data[o+2] = v;
        img.data[o+3] = 255;
    }
    ctx.putImageData(img, 0, 0);
    return canvas;
}

async function renderGallery() {
    const gallery = document.getElementById('gallery');
    const status = document.getElementById('status');

    if (status) status.textContent = '⟳ Conectando al repositorio neural...';

    try {
        const resp = await fetch('gallery/INDEX.txt');
        if (!resp.ok) throw new Error('INDEX.txt no encontrado');
        const txt = await resp.text();

        // Fase 2: parsear el INDEX tolerando cabecera legacy y enriquecida.
        function renderMetaPanel() {
            const regime = document.getElementById('regime');
            if (regime && indexMeta.palette) {
                regime.textContent = `● ${indexMeta.palette}`;
            }
            const bars = document.getElementById('bars');
            if (bars && indexMeta.entSpatialAvg !== null) {
                bars.innerHTML = `<div class="barRow"><span class="barName">Entropía</span><div class="barTrack"><div class="barFill" style="width:${(indexMeta.entSpatialAvg/5)*100}%"></div></div><span class="barPct">${indexMeta.entSpatialAvg.toFixed(2)}</span></div>`;
            }
        }
        const parsed = parseIndex(txt);
        indexMeta = parsed;
        renderMetaPanel();

        const files = parsed.files.map(f => f.name);

        if (files.length === 0) {
            gallery.innerHTML = '<p>Galería aún sin sueños. Espera al primer ciclo.</p>';
            if (status) status.remove();
            return;
        }

        if (status) status.textContent = `⟳ Decodificando ${files.length} sueños CPPN...`;

        gallery.innerHTML = '';
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            if (status) status.textContent = `⟳ Renderizando sueño ${i + 1}/${files.length}...`;

            const wrap = document.createElement('div');
            wrap.className = 'dream';
            wrap.style.setProperty('--i', i);
            wrap.dataset.file = file;

            const canvas = await loadDream(file);
            canvas.style.cursor = 'zoom-in';

            // Debug: detectar canvas vacío (todo gris/negro)
            const ctx = canvas.getContext('2d');
            const sample = ctx.getImageData(canvas.width/2, canvas.height/2, 1, 1).data;
            const isEmpty = (sample[0] === 0 && sample[1] === 0 && sample[2] === 0);
            if (isEmpty) {
                const err = document.createElement('p');
                err.textContent = '⚠ Canvas vacío en ' + file;
                err.style.color = '#ff5577';
                err.style.fontSize = '10px';
                wrap.appendChild(err);
                console.error('Canvas vacío:', file);
            }

            wrap.appendChild(canvas);

            const caption = document.createElement('p');
            caption.textContent = file;
            wrap.appendChild(caption);

            gallery.appendChild(wrap);
        }

        if (status) {
            status.textContent = `✓ ${files.length} sueños cultivados`;
            status.style.color = 'var(--neon)';
            status.style.borderColor = 'var(--neon)';
            status.style.animation = 'none';
            setTimeout(() => status.remove(), 3000);
        }

        initParallax();
        initModal();
    } catch (err) {
        gallery.innerHTML = `<p style="color:#ff5577">Error: ${err.message}</p>`;
        if (status) status.textContent = '✗ Error de carga';
        console.error('dream-loader:', err);
    }
}

// === CURSOR PARALLAX 3D ===
function initParallax() {
    const dreams = document.querySelectorAll('.dream');
    dreams.forEach(dream => {
        dream.addEventListener('mousemove', (e) => {
            const rect = dream.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / rect.width  - 0.5) * 2;
            const y = ((e.clientY - rect.top)  / rect.height - 0.5) * 2;

            const rotY = x * 8;   // tilt horizontal
            const rotX = -y * 8;  // tilt vertical

            dream.style.transform =
                `scale(1.04) translateY(-4px) ` +
                `rotateX(${rotX}deg) rotateY(${rotY}deg)`;

            // Actualizar posición del glow
            const mx = ((e.clientX - rect.left) / rect.width)  * 100;
            const my = ((e.clientY - rect.top)  / rect.height) * 100;
            dream.style.setProperty('--mx', mx + '%');
            dream.style.setProperty('--my', my + '%');
        });

        dream.addEventListener('mouseleave', () => {
            dream.style.transform = '';
        });
    });
}

// === MODAL ZOOM ===
function initModal() {
    const modal = document.getElementById('modal');
    const modalCanvas = document.getElementById('modal-canvas');
    const modalCaption = document.getElementById('modal-caption');
    const modalClose = document.getElementById('modal-close');

    document.querySelectorAll('.dream canvas').forEach(cv => {
        cv.addEventListener('click', () => {
            const wrap = cv.closest('.dream');
            const filename = wrap.dataset.file;
            const original = dreamsCache[filename];

            if (original) {
                modalCanvas.width = original.width;
                modalCanvas.height = original.height;
                modalCanvas.getContext('2d').drawImage(original, 0, 0);
            }
            modalCaption.textContent = filename;
            modal.classList.add('active');
        });
    });

    const closeModal = () => modal.classList.remove('active');
    modal.addEventListener('click', closeModal);
    modalClose.addEventListener('click', (e) => { e.stopPropagation(); closeModal(); });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });
}

// === SELECTOR DE PALETAS ===
function initPalettes() {
    const buttons = document.querySelectorAll('.palette-btn');
    const saved = localStorage.getItem('cppn-palette') || 'neon';
    applyPalette(saved);

    buttons.forEach(b => {
        if (b.dataset.set === saved) b.classList.add('active');
        else b.classList.remove('active');

        b.addEventListener('click', () => {
            applyPalette(b.dataset.set);
            buttons.forEach(x => x.classList.remove('active'));
            b.classList.add('active');
            localStorage.setItem('cppn-palette', b.dataset.set);
        });
    });
}

function applyPalette(name) {
    if (name === 'neon') document.documentElement.removeAttribute('data-palette');
    else document.documentElement.setAttribute('data-palette', name);
}

// === INIT ===


// ============================================
// DREAM LOADER v3 - NUEVA IMPLEMENTACIÓN
// ============================================

let manifest = null;
let allItems = [];
let filteredItems = [];
let currentFilter = { palette: 'all', shannonMin: null, shannonMax: null, spatialMin: null, spatialMax: null, seedMin: null, seedMax: null, search: '' };
let currentSort = { key: 'seed', dir: 'desc' };
let dreamsCache = {};
let thumbCache = {};
let observer = null;
let visibleCount = 0;
const BATCH_SIZE = 12;

async function initGallery() {
    const gallery = document.getElementById('gallery');
    const status = document.getElementById('status');
    if (status) status.textContent = '⟳ Cargando manifiesto neural...';
    try {
        const resp = await fetch('gallery/MANIFEST.json');
        if (!resp.ok) throw new Error('MANIFEST.json no encontrado');
        manifest = await resp.json();
        allItems = manifest.items;
        populatePaletteFilters();
        applyFilters();
        await renderBatch();
        setupVirtualization();
        setupEventListeners();
        renderMetaPanel();
        if (status) { status.textContent = '✓ ' + allItems.length + ' sueños en el repositorio'; status.style.color = 'var(--neon)'; status.style.borderColor = 'var(--neon)'; setTimeout(() => status.remove(), 3000); }
    } catch (err) { console.error(err); if (status) status.textContent = '✗ Error: ' + err.message; gallery.innerHTML = '<p>No se pudo cargar la galería.</p>'; }
}

function populatePaletteFilters() {
    const container = document.getElementById('palette-filters');
    if (!container) return;
    const palettes = [...new Set(allItems.map(i => i.palette).filter(Boolean))].sort();
    container.innerHTML = '';
    const btnAll = document.createElement('button');
    btnAll.className = 'filter-btn active'; btnAll.dataset.filter = 'all'; btnAll.textContent = 'Todas'; container.appendChild(btnAll);
    palettes.forEach(p => { const btn = document.createElement('button'); btn.className = 'filter-btn'; btn.dataset.filter = p; btn.textContent = p; container.appendChild(btn); });
}

function applyFilters() {
    filteredItems = allItems.filter(item => {
        if (currentFilter.palette !== 'all' && item.palette !== currentFilter.palette) return false;
        if (currentFilter.shannonMin !== null && item.entropy_shannon < currentFilter.shannonMin) return false;
        if (currentFilter.shannonMax !== null && item.entropy_shannon > currentFilter.shannonMax) return false;
        if (currentFilter.spatialMin !== null && item.entropy_spatial < currentFilter.spatialMin) return false;
        if (currentFilter.spatialMax !== null && item.entropy_spatial > currentFilter.spatialMax) return false;
        if (currentFilter.seedMin !== null && item.seed < currentFilter.seedMin) return false;
        if (currentFilter.seedMax !== null && item.seed > currentFilter.seedMax) return false;
        if (currentFilter.search) { const q = currentFilter.search.toLowerCase(); if (!item.filename.toLowerCase().includes(q) && !String(item.seed).includes(q)) return false; }
        return true;
    });
    filteredItems.sort((a, b) => { let va = a[currentSort.key], vb = b[currentSort.key]; if (typeof va === 'string') va = va.toLowerCase(); if (typeof vb === 'string') vb = vb.toLowerCase(); const cmp = va < vb ? -1 : va > vb ? 1 : 0; return currentSort.dir === 'asc' ? cmp : -cmp; });
    visibleCount = 0; document.getElementById('gallery').innerHTML = '';
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.toggle('active', b.dataset.filter === currentFilter.palette));
    updateSortUI(); renderBatch();
}

function updateSortUI() { document.querySelectorAll('.sort-btn').forEach(b => { const active = b.dataset.sort === currentSort.key; b.classList.toggle('active', active); b.textContent = b.dataset.label + (active ? (currentSort.dir === 'asc' ? ' ↑' : ' ↓') : ''); }); }

async function renderBatch() {
    const gallery = document.getElementById('gallery');
    const nextItems = filteredItems.slice(visibleCount, visibleCount + BATCH_SIZE);
    if (nextItems.length === 0) { if (observer) observer.disconnect(); return; }
    for (const item of nextItems) { const wrap = createDreamElement(item); gallery.appendChild(wrap); loadThumbnail(item, wrap); }
    visibleCount += nextItems.length;
    if (observer) { const lastEl = gallery.lastElementChild; if (lastEl) observer.observe(lastEl); }
}

function createDreamElement(item) {
    const wrap = document.createElement('div'); wrap.className = 'dream'; wrap.dataset.file = item.filename; wrap.dataset.seed = item.seed; wrap.dataset.palette = item.palette || 'unknown'; wrap.dataset.shannon = item.entropy_shannon.toFixed(3); wrap.dataset.spatial = item.entropy_spatial.toFixed(3);
    const placeholder = document.createElement('div'); placeholder.className = 'thumb-placeholder'; placeholder.style.aspectRatio = '1/1'; placeholder.style.background = 'var(--panel)'; placeholder.style.borderRadius = '12px'; placeholder.style.border = '1px solid var(--border)'; wrap.appendChild(placeholder);
    const caption = document.createElement('p'); caption.className = 'dream-caption mono'; caption.textContent = item.filename; wrap.appendChild(caption);
    wrap.addEventListener('click', () => openModal(item)); return wrap;
}

async function loadThumbnail(item, wrap) {
    if (thumbCache[item.filename]) { applyThumbnail(wrap, thumbCache[item.filename]); return; }
    try { const resp = await fetch('gallery/' + item.thumbnail + '?t=' + Date.now()); if (!resp.ok) throw new Error('Thumbnail 404'); const blob = await resp.blob(); const bitmap = await createImageBitmap(blob); const canvas = document.createElement('canvas'); canvas.width = bitmap.width; canvas.height = bitmap.height; canvas.getContext('2d').drawImage(bitmap, 0, 0); thumbCache[item.filename] = canvas; applyThumbnail(wrap, canvas); } catch (e) { console.warn('Thumb failed:', item.filename, e); }
}

function applyThumbnail(wrap, canvas) { const placeholder = wrap.querySelector('.thumb-placeholder'); if (placeholder) { canvas.style.width = '100%'; canvas.style.height = '100%'; canvas.style.borderRadius = '12px'; canvas.style.border = '1px solid var(--border)'; canvas.style.objectFit = 'cover'; placeholder.replaceWith(canvas); } }

function setupVirtualization() { observer = new IntersectionObserver((entries) => { entries.forEach(entry => { if (entry.isIntersecting) { observer.unobserve(entry.target); renderBatch(); } }); }, { rootMargin: '200px' }); }

function setupEventListeners() {
    document.getElementById('palette-filters')?.addEventListener('click', (e) => { const btn = e.target.closest('.filter-btn'); if (btn) { currentFilter.palette = btn.dataset.filter; applyFilters(); } });
    document.querySelectorAll('.sort-btn').forEach(btn => { btn.addEventListener('click', () => { if (currentSort.key === btn.dataset.sort) { currentSort.dir = currentSort.dir === 'asc' ? 'desc' : 'asc'; } else { currentSort.key = btn.dataset.sort; currentSort.dir = 'desc'; } applyFilters(); }); });
    const searchBox = document.getElementById('search-box'); if (searchBox) { let debounce; searchBox.addEventListener('input', () => { clearTimeout(debounce); debounce = setTimeout(() => { currentFilter.search = searchBox.value; applyFilters(); }, 200); }); }
    ['shannon', 'spatial', 'seed'].forEach(prefix => { const minEl = document.getElementById(prefix + '-min'); const maxEl = document.getElementById(prefix + '-max'); if (minEl) minEl.addEventListener('change', () => { currentFilter[prefix + 'Min'] = minEl.value ? parseFloat(minEl.value) : null; applyFilters(); }); if (maxEl) maxEl.addEventListener('change', () => { currentFilter[prefix + 'Max'] = maxEl.value ? parseFloat(maxEl.value) : null; applyFilters(); }); });
    document.getElementById('clear-filters')?.addEventListener('click', () => { currentFilter = { palette: 'all', shannonMin: null, shannonMax: null, spatialMin: null, spatialMax: null, seedMin: null, seedMax: null, search: '' }; document.getElementById('search-box').value = ''; ['shannon', 'spatial', 'seed'].forEach(p => { document.getElementById(p + '-min').value = ''; document.getElementById(p + '-max').value = ''; }); applyFilters(); });
    const countEl = document.getElementById('gallery-count'); if (countEl) countEl.textContent = filteredItems.length + ' sueños';
}

async function loadFullImage(filename) { if (dreamsCache[filename]) return cloneCanvas(dreamsCache[filename]); const item = allItems.find(i => i.filename === filename); if (!item) throw new Error('Item no encontrado'); const isPNG = filename.toLowerCase().endsWith('.png'); const resp = await fetch('gallery/' + filename + '?t=' + Date.now()); if (!resp.ok) throw new Error('HTTP ' + resp.status); let canvas; if (isPNG) { const blob = await resp.blob(); const bitmap = await createImageBitmap(blob); canvas = document.createElement('canvas'); canvas.width = bitmap.width; canvas.height = bitmap.height; canvas.getContext('2d').drawImage(bitmap, 0, 0); } else { const buf = await resp.arrayBuffer(); const pgm = parsePGM(buf); canvas = pgmToCanvas(pgm); } dreamsCache[filename] = canvas; return cloneCanvas(canvas); }

function cloneCanvas(src) { const c = document.createElement('canvas'); c.width = src.width; c.height = src.height; c.getContext('2d').drawImage(src, 0, 0); return c; }

function parsePGM(buffer) { const data = new Uint8Array(buffer); const text = new TextDecoder('ascii').decode(data); const tokens = text.split(/\s+/); const magic = tokens[0]; let idx = 1; while (idx < tokens.length && (tokens[idx].startsWith('#') || tokens[idx] === '')) idx++; const w = parseInt(tokens[idx++]); const h = parseInt(tokens[idx++]); const maxval = parseInt(tokens[idx++]); if (magic === 'P5') { const headerBytes = data.length - (w * h); const pixels = data.slice(headerBytes); return { w, h, data: pixels }; } else if (magic === 'P2') { const pixels = new Uint8Array(w * h); for (let p = 0; p < w * h && idx < tokens.length; p++) { pixels[p] = parseInt(tokens[idx++]); } return { w, h, data: pixels }; } else { throw new Error('PGM formato desconocido: ' + magic); } }

function pgmToCanvas({ w, h, data }) { const canvas = document.createElement('canvas'); canvas.width = w; canvas.height = h; const ctx = canvas.getContext('2d'); const img = ctx.createImageData(w, h); for (let p = 0; p < w * h; p++) { const v = data[p]; const o = p * 4; img.data[o] = v; img.data[o+1] = v; img.data[o+2] = v; img.data[o+3] = 255; } ctx.putImageData(img, 0, 0); return canvas; }

async function openModal(item) { const overlay = document.createElement('div'); overlay.className = 'modal-overlay'; overlay.innerHTML = '<div class="modal">' + '<button class="modal-close" aria-label="Cerrar">✕</button>' + '<div class="modal-content">' + '<canvas class="modal-canvas"></canvas>' + '<div class="modal-meta"></div>' + '</div>' + '</div>'; document.body.appendChild(overlay); document.body.style.overflow = 'hidden'; function closeModal() { document.removeEventListener('keydown', escHandler); document.body.style.overflow = ''; overlay.remove(); } overlay.querySelector('.modal-close').onclick = closeModal; overlay.onclick = (e) => { if (e.target === overlay) closeModal(); }; const escHandler = (e) => { if (e.key === 'Escape') closeModal(); }; document.addEventListener('keydown', escHandler); const canvasEl = overlay.querySelector('.modal-canvas'); const metaEl = overlay.querySelector('.modal-meta'); metaEl.innerHTML = '<div class="loading">⟳ Cargando sueño completo...</div>'; try { const canvas = await loadFullImage(item.filename); canvasEl.width = canvas.width; canvasEl.height = canvas.height; canvasEl.getContext('2d').drawImage(canvas, 0, 0); renderModalMeta(metaEl, item); } catch (e) { metaEl.innerHTML = '<div class="error">✗ Error: ' + e.message + '</div>'; } }

function renderModalMeta(container, item) { const shareUrl = location.origin + location.pathname + '?seed=' + item.seed; container.innerHTML = '<div class="meta-grid">' + '<div class="meta-row"><span class="meta-label">Archivo</span><span class="meta-value mono">' + item.filename + '</span></div>' + '<div class="meta-row"><span class="meta-label">Seed</span><span class="meta-value mono">' + item.seed + '</span></div>' + '<div class="meta-row"><span class="meta-label">Paleta</span><span class="meta-value">' + item.palette + '</span></div>' + '<div class="meta-row"><span class="meta-label">Dimensiones</span><span class="meta-value mono">' + item.width + '×' + item.height + '</span></div>' + '<div class="meta-row"><span class="meta-label">Entropía Shannon</span><span class="meta-value"><strong>' + item.entropy_shannon.toFixed(4) + '</strong> bits</span></div>' + '<div class="meta-row"><span class="meta-label">Entropía Espacial</span><span class="meta-value"><strong>' + item.entropy_spatial.toFixed(4) + '</strong></span></div>' + '<div class="meta-row"><span class="meta-label">Grises únicos</span><span class="meta-value mono">' + item.unique_grays + ' / 256</span></div>' + '<div class="meta-row"><span class="meta-label">Tamaño</span><span class="meta-value mono">' + (item.size_bytes/1024).toFixed(1) + ' KB</span></div>' + '</div>' + '<div class="modal-actions">' + '<button class="btn-share" onclick="navigator.clipboard.writeText(\ + shareUrl + '')">📋 Copiar enlace</button>' + '<button class="btn-load" onclick="loadDreamInMotor(\ + item.filename + '')">🧠 Cargar en Motor</button>' + '</div>'; }

function renderMetaPanel() { if (!manifest) return; const regime = document.getElementById('regime'); if (regime && manifest.palette) regime.textContent = '● ' + manifest.palette; const bars = document.getElementById('bars'); if (bars && manifest.avg_entropy_spatial !== null) { bars.innerHTML = '<div class="barRow"><span class="barName">Shannon</span><div class="barTrack"><div class="barFill" style="width:' + Math.min(100, (manifest.avg_entropy_shannon/8)*100) + '%"></div></div><span class="barPct">' + manifest.avg_entropy_shannon.toFixed(2) + '</span></div>' + '<div class="barRow"><span class="barName">Espacial</span><div class="barTrack"><div class="barFill" style="width:' + Math.min(100, (manifest.avg_entropy_spatial/5)*100) + '%"></div></div><span class="barPct">' + manifest.avg_entropy_spatial.toFixed(2) + '</span></div>'; } }

// === INIT ===
window.addEventListener('DOMContentLoaded', () => {
    initGallery();
});
