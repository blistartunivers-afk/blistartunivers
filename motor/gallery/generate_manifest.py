#!/usr/bin/env python3
"""
Generador de MANIFEST.json + Thumbnails para Galería CPPN
- Analiza todos los archivos PGM/PNG en gallery/
- Calcula: Shannon entropy, Spatial entropy, unique grays, seed
- Genera thumbnails 128x128 WebP
- Escribe MANIFEST.json unificado
"""

import os
import json
import math
import hashlib
from pathlib import Path
from PIL import Image
import numpy as np

GALLERY_DIR = Path(__file__).parent
THUMB_DIR = GALLERY_DIR / "thumbs"
THUMB_DIR.mkdir(exist_ok=True)
THUMB_SIZE = (128, 128)

def shannon_entropy(img_array):
    """Entropía de Shannon de la distribución de intensidades."""
    hist, _ = np.histogram(img_array, bins=256, range=(0, 255), density=True)
    hist = hist[hist > 0]
    return -np.sum(hist * np.log2(hist))

def spatial_entropy(img_array):
    """Entropía espacial: entropía de gradientes (Laplaciano).
    Mide complejidad textural / detalle local."""
    # Gradientes Sobel simples
    gx = np.abs(np.roll(img_array, -1, axis=1) - np.roll(img_array, 1, axis=1))
    gy = np.abs(np.roll(img_array, -1, axis=0) - np.roll(img_array, 1, axis=0))
    grad = np.sqrt(gx**2 + gy**2).astype(np.uint8)
    hist, _ = np.histogram(grad, bins=256, range=(0, 255), density=True)
    hist = hist[hist > 0]
    return -np.sum(hist * np.log2(hist)) if len(hist) > 0 else 0.0

def unique_grays(img_array):
    """Número de valores de gris únicos."""
    return int(len(np.unique(img_array)))

def load_image_array(filepath):
    """Carga imagen (PGM o PNG) y devuelve array uint8 2D."""
    ext = filepath.suffix.lower()
    if ext == '.pgm':
        # Leer PGM (P2 texto o P5 binario)
        with open(filepath, 'rb') as f:
            header = f.readline().strip()
            if header not in (b'P2', b'P5'):
                raise ValueError(f"PGM inválido: {header}")
            # Saltar comentarios
            while True:
                line = f.readline()
                if not line.startswith(b'#'):
                    break
            w, h = map(int, line.split())
            maxval = int(f.readline().strip())
            
            if header == b'P5':
                data = np.frombuffer(f.read(), dtype=np.uint8 if maxval < 256 else np.uint16)
            else:
                data = np.fromstring(f.read().decode('ascii'), dtype=np.uint8 if maxval < 256 else np.uint16, sep=' ')
            
            if maxval > 255:
                data = (data.astype(np.float32) / maxval * 255).astype(np.uint8)
            return data.reshape((h, w))
    else:
        # PNG u otro formato soportado por PIL
        with Image.open(filepath) as im:
            if im.mode != 'L':
                im = im.convert('L')
            return np.array(im, dtype=np.uint8)

def generate_thumbnail(src_path, thumb_path):
    """Genera thumbnail 128x128 WebP."""
    try:
        with Image.open(src_path) as im:
            if im.mode != 'RGB':
                im = im.convert('RGB')
            im.thumbnail(THUMB_SIZE, Image.Resampling.LANCZOS)
            # Canvas cuadrado centrado
            canvas = Image.new('RGB', THUMB_SIZE, (15, 19, 16))  # --bg color
            x = (THUMB_SIZE[0] - im.width) // 2
            y = (THUMB_SIZE[1] - im.height) // 2
            canvas.paste(im, (x, y))
            canvas.save(thumb_path, 'WEBP', quality=80, method=6)
            return True
    except Exception as e:
        print(f"  ⚠ Thumbnail falló {src_path.name}: {e}")
        return False

def extract_seed(filename):
    """Extrae seed numérico del nombre dream_XXXXXXXX.ext"""
    import re
    m = re.search(r'dream_(\d+)', filename)
    return int(m.group(1)) if m else None

def main():
    print(f"🔍 Escaneando {GALLERY_DIR}...")
    
    # Buscar todos los archivos de imagen
    image_files = []
    for ext in ('.pgm', '.png', '.jpg', '.jpeg', '.webp'):
        image_files.extend(GALLERY_DIR.glob(f"*{ext}"))
    
    image_files = sorted([f for f in image_files if f.name != 'INDEX.txt' and f.name != 'METADATA.json' and f.name != 'MANIFEST.json'])
    print(f"📁 Encontrados {len(image_files)} archivos de imagen")
    
    items = []
    palette_default = "viridis"
    ent_spatial_vals = []
    ent_shannon_vals = []
    
    for i, img_path in enumerate(image_files):
        print(f"  [{i+1}/{len(image_files)}] Procesando {img_path.name}...")
        
        try:
            arr = load_image_array(img_path)
            
            # Métricas
            ent_shannon = float(shannon_entropy(arr))
            ent_spatial = float(spatial_entropy(arr))
            uniq = unique_grays(arr)
            seed = extract_seed(img_path.name)
            
            ent_shannon_vals.append(ent_shannon)
            ent_spatial_vals.append(ent_spatial)
            
            # Paleta: intentar inferir del INDEX.txt o usar default
            palette = palette_default
            
            # Thumbnail
            thumb_name = img_path.stem + ".webp"
            thumb_path = THUMB_DIR / thumb_name
            generate_thumbnail(img_path, thumb_path)
            
            item = {
                "seed": seed,
                "filename": img_path.name,
                "thumbnail": f"thumbs/{thumb_name}",
                "width": int(arr.shape[1]),
                "height": int(arr.shape[0]),
                "entropy_shannon": round(ent_shannon, 6),
                "entropy_spatial": round(ent_spatial, 6),
                "unique_grays": uniq,
                "palette": palette,
                "size_bytes": img_path.stat().st_size
            }
            items.append(item)
            
            print(f"    ✓ Shannon={ent_shannon:.3f} Spatial={ent_spatial:.3f} Unique={uniq} Seed={seed}")
            
        except Exception as e:
            print(f"    ✗ ERROR: {e}")
            continue
    
    # Estadísticas globales
    manifest = {
        "palette": palette_default,
        "width": 512,
        "height": 512,
        "count": len(items),
        "avg_entropy_shannon": round(float(np.mean(ent_shannon_vals)), 6) if ent_shannon_vals else 0,
        "avg_entropy_spatial": round(float(np.mean(ent_spatial_vals)), 6) if ent_spatial_vals else 0,
        "min_entropy_shannon": round(float(np.min(ent_shannon_vals)), 6) if ent_shannon_vals else 0,
        "max_entropy_shannon": round(float(np.max(ent_shannon_vals)), 6) if ent_shannon_vals else 0,
        "min_entropy_spatial": round(float(np.min(ent_spatial_vals)), 6) if ent_spatial_vals else 0,
        "max_entropy_spatial": round(float(np.max(ent_spatial_vals)), 6) if ent_spatial_vals else 0,
        "items": items
    }
    
    # Escribir MANIFEST.json
    manifest_path = GALLERY_DIR / "MANIFEST.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n✅ MANIFEST.json escrito: {manifest_path}")
    print(f"📊 Total items: {len(items)}")
    print(f"📈 Shannon: avg={manifest['avg_entropy_shannon']:.3f} min={manifest['min_entropy_shannon']:.3f} max={manifest['max_entropy_shannon']:.3f}")
    print(f"📈 Spatial: avg={manifest['avg_entropy_spatial']:.3f} min={manifest['min_entropy_spatial']:.3f} max={manifest['max_entropy_spatial']:.3f}")
    print(f"🖼️ Thumbnails en: {THUMB_DIR}")

if __name__ == "__main__":
    main()
