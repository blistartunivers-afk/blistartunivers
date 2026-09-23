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
window.addEventListener('DOMContentLoaded', () => {
    initPalettes();
    renderGallery();
});
