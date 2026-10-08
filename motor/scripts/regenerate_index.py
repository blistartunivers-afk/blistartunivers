"""
Regenera INDEX.txt, MANIFEST.json y METADATA.json desde la galería.
Escanea motor/gallery/ y reconstruye metadatos completos.
"""
import json
import os
import sys
from pathlib import Path
from PIL import Image
import math

GALLERY_DIR = Path(__file__).parent.parent / "gallery"
THUMBS_DIR = GALLERY_DIR / "thumbs"
THUMBS_DIR.mkdir(exist_ok=True)

INDEX_TXT = GALLERY_DIR / "INDEX.txt"
MANIFEST_JSON = GALLERY_DIR / "MANIFEST.json"
METADATA_JSON = GALLERY_DIR / "METADATA.json"


def compute_entropy_shannon(img_array):
    """Entropía de Shannon de imagen (0-255)."""
    hist = [0] * 256
    total = img_array.size
    for v in img_array.flatten():
        hist[v] += 1
    entropy = 0.0
    for count in hist:
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy


def compute_entropy_spatial(img_array):
    """Entropía espacial 2D (gradiente promedio)."""
    h, w = img_array.shape
    if h < 3 or w < 3:
        return 0.0
    spatial_sum = 0.0
    count = 0
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            dx = float(img_array[y, x + 1]) - float(img_array[y, x - 1])
            dy = float(img_array[y + 1, x]) - float(img_array[y - 1, x])
            spatial_sum += math.sqrt(dx * dx + dy * dy)
            count += 1
    return spatial_sum / count if count > 0 else 0.0


def compute_unique_grays(img_array):
    return len(set(img_array.flatten()))


def generate_thumbnail(src_path, thumb_path, size=(128, 128)):
    try:
        with Image.open(src_path) as img:
            img.thumbnail(size, Image.LANCZOS)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(thumb_path, 'WEBP', quality=80, method=6)
        return True
    except Exception as e:
        print(f"  [WARN] Thumbnail failed for {src_path.name}: {e}", file=sys.stderr)
        return False


def parse_filename(filename):
    """Extrae seed del nombre: dream_12345.png -> 12345"""
    stem = Path(filename).stem
    if stem.startswith('dream_'):
        try:
            return int(stem.split('_')[1])
        except (IndexError, ValueError):
            pass
    return None


def main():
    print(f"[+] Escaneando galería: {GALLERY_DIR}")
    
    # Buscar archivos de imagen
    image_files = []
    for ext in ('.png', '.pgm', '.jpg', '.jpeg', '.webp'):
        image_files.extend(GALLERY_DIR.glob(f"*{ext}"))
    
    if not image_files:
        print("[!] No se encontraron imágenes en la galería")
        return 1
    
    image_files.sort(key=lambda p: p.stat().st_mtime)
    
    items = []
    all_shannon = []
    all_spatial = []
    palettes_used = {}
    
    print(f"[+] Procesando {len(image_files)} archivos...")
    
    for img_path in image_files:
        try:
            with Image.open(img_path) as img:
                if img.mode != 'L':
                    img_gray = img.convert('L')
                else:
                    img_gray = img
                arr = np.array(img_gray)
                
                width, height = img.size
                seed = parse_filename(img_path.name)
                
                shannon = compute_entropy_shannon(arr)
                spatial = compute_entropy_spatial(arr)
                unique = compute_unique_grays(arr)
                
                all_shannon.append(shannon)
                all_spatial.append(spatial)
                
                # Detectar paleta por nombre o usar 'viridis' por defecto
                palette = 'viridis'
                palettes_used[palette] = palettes_used.get(palette, 0) + 1
                
                # Generar thumbnail
                thumb_name = f"thumbs/{img_path.stem}.webp"
                thumb_path = GALLERY_DIR / thumb_name
                generate_thumbnail(img_path, thumb_path)
                
                size_bytes = img_path.stat().st_size
                
                items.append({
                    "seed": seed,
                    "filename": img_path.name,
                    "thumbnail": thumb_name,
                    "width": width,
                    "height": height,
                    "entropy_shannon": round(shannon, 6),
                    "entropy_spatial": round(spatial, 6),
                    "unique_grays": unique,
                    "palette": palette,
                    "size_bytes": size_bytes
                })
                
                print(f"  [+] {img_path.name}  shannon={shannon:.3f} spatial={spatial:.3f} palette={palette} unique={unique}")
        
        except Exception as e:
            print(f"  [ERROR] {img_path.name}: {e}", file=sys.stderr)
    
    if not items:
        print("[!] No se procesó ninguna imagen válida")
        return 1
    
    # Paleta por defecto (la más usada)
    default_palette = max(palettes_used, key=palettes_used.get) if palettes_used else 'viridis'
    
    # Estadísticas globales
    avg_shannon = sum(all_shannon) / len(all_shannon)
    avg_spatial = sum(all_spatial) / len(all_spatial)
    min_shannon = min(all_shannon)
    max_shannon = max(all_shannon)
    min_spatial = min(all_spatial)
    max_spatial = max(all_spatial)
    
    # Escribir MANIFEST.json
    manifest = {
        "palette": default_palette,
        "width": items[0]["width"] if items else 512,
        "height": items[0]["height"] if items else 512,
        "count": len(items),
        "avg_entropy_shannon": round(avg_shannon, 6),
        "avg_entropy_spatial": round(avg_spatial, 6),
        "min_entropy_shannon": round(min_shannon, 6),
        "max_entropy_shannon": round(max_shannon, 6),
        "min_entropy_spatial": round(min_spatial, 6),
        "max_entropy_spatial": round(max_spatial, 6),
        "items": items
    }
    
    with open(MANIFEST_JSON, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"[+] MANIFEST.json escrito: {len(items)} items")
    
    # Escribir INDEX.txt (formato Fase 2)
    with open(INDEX_TXT, 'w') as f:
        f.write(f"# Motor de Imaginación — Índice de galería\n")
        f.write(f"# Paleta por defecto: {default_palette}\n")
        f.write(f"# Dimensión: {manifest['width']}x{manifest['height']}\n")
        f.write(f"# Total archivos: {len(items)}\n")
        f.write(f"# Entropía espacial (min, avg): {min_spatial:.2f}, {avg_spatial:.2f}\n")
        for item in items:
            f.write(f"{item['filename']} palette={item['palette']} ent_spatial={item['entropy_spatial']:.2f}\n")
    print(f"[+] INDEX.txt escrito")
    
    # Escribir METADATA.json (resumen ligero)
    metadata = {
        "version": 2,
        "default_palette": default_palette,
        "dimensions": f"{manifest['width']}x{manifest['height']}",
        "total_files": len(items),
        "entropy_shannon": {"avg": round(avg_shannon, 3), "min": round(min_shannon, 3), "max": round(max_shannon, 3)},
        "entropy_spatial": {"avg": round(avg_spatial, 3), "min": round(min_spatial, 3), "max": round(max_spatial, 3)},
        "palettes": palettes_used
    }
    
    with open(METADATA_JSON, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"[+] METADATA.json escrito")
    
    print(f"\n[✓] Regeneración completa")
    print(f"    Promedio Shannon: {avg_shannon:.3f}")
    print(f"    Promedio Espacial: {avg_spatial:.3f}")
    print(f"    Paleta por defecto: {default_palette}")
    
    return 0

if __name__ == "__main__":
    import numpy as np
    sys.exit(main())
