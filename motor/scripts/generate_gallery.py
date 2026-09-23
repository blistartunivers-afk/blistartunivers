"""
Motor de Imaginación — Generador autónomo de sueños CPPN.

Genera una o varias imágenes (PNG/PGM) a partir de una red CPPN
(Compositional Pattern Producing Network) con activaciones compuestas
y selección estocástica por neurona.

Uso:
    python scripts/generate_gallery.py                       # 1 sueño PNG, 256x256
    python scripts/generate_gallery.py --count 8             # 8 sueños (workflow)
    python scripts/generate_gallery.py --format pgm          # retrocompat .pgm
    python scripts/generate_gallery.py --width 512 --height 512
"""
import argparse
import math
import os
import random
import sys
from datetime import datetime

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None  # Se permite .pgm puro sin Pillow

try:
    # Intento 1: import relativo (cuando se importa como paquete `scripts`).
    from .palettes import get_palette, apply_palette, list_palettes
    from .palettes import spatial_entropy_2d as _spatial_entropy_palettes
except (ImportError, ValueError):
    try:
        # Intento 2: import absoluto (cuando se ejecuta como script directo).
        import os as _os, sys as _sys
        _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
        from palettes import get_palette, apply_palette, list_palettes  # type: ignore
        from palettes import spatial_entropy_2d as _spatial_entropy_palettes  # type: ignore
    except ImportError:  # pragma: no cover
        # Fallback final: si el modulo de paletas no esta disponible, modo raw.
        get_palette = None  # type: ignore
        apply_palette = None  # type: ignore
        list_palettes = lambda: ["raw"]  # type: ignore
        _spatial_entropy_palettes = None  # type: ignore


# ---------------------------------------------------------------------------
# Núcleo CPPN
# ---------------------------------------------------------------------------

def _softsign(v):
    return v / (1.0 + abs(v))


def _gauss(v):
    return math.exp(-v * v)


# Catálogo de funciones de activación (cumple lo prometido en el README).
ACTIVATIONS = [math.sin, math.cos, math.tanh, _gauss, _softsign]


def _cppn_intensity(width, height, seed):
    """Núcleo CPPN puro: devuelve una matriz 2D con intensidad [0.0, 1.0].

    Esta función NO aplica ninguna paleta. Es el output crudo y la base
    sobre la cual la paleta perceptualmente uniforme mapea a RGB.

    Args:
        width:  ancho en pixeles.
        height: alto en pixeles.
        seed:   semilla (None para no determinismo).

    Returns:
        list[list[float]]: matriz [height][width] con valores en [0.0, 1.0].
    """
    if seed is not None:
        random.seed(seed)

    # Pesos de la red CPPN: 4 -> 8 -> 8 -> 1 (intensidad escalar).
    # Antes emitia 3 valores (RGB crudo), ahora 1 -> la paleta decide el color.
    w1 = [[random.uniform(-2, 2) for _ in range(4)] for _ in range(8)]
    w2 = [[random.uniform(-2, 2) for _ in range(8)] for _ in range(8)]
    w3 = [[random.uniform(-2, 2) for _ in range(8)] for _ in range(1)]

    out = [[0.0] * width for _ in range(height)]

    # Selección determinista de funciones por capa (estable y reproducible).
    l1_funcs = [ACTIVATIONS[hash((0, i)) % len(ACTIVATIONS)] for i in range(8)]
    l2_funcs = [ACTIVATIONS[hash((1, i)) % len(ACTIVATIONS)] for i in range(8)]

    for py in range(height):
        y = (py / height) * 2.0 - 1.0
        for px in range(width):
            x = (px / width) * 2.0 - 1.0
            r = math.sqrt(x * x + y * y)

            inp = [x, y, r, 1.0]

            # Capa 1
            l1 = []
            for i, node_weights in enumerate(w1):
                val = sum(w * iv for w, iv in zip(node_weights, inp))
                try:
                    l1.append(l1_funcs[i](val))
                except Exception:
                    l1.append(0.0)

            # Capa 2
            l2 = []
            for i, node_weights in enumerate(w2):
                val = sum(w * iv for w, iv in zip(node_weights, l1))
                try:
                    l2.append(l2_funcs[i](val))
                except Exception:
                    l2.append(0.0)

            # Capa 3 -> intensidad escalar (tanh -> [-1,1] -> [0,1])
            val = sum(w * iv for w, iv in zip(w3[0], l2))
            out[py][px] = (math.tanh(val) + 1.0) * 0.5

    return out


def _intensity_to_pixels(intensity, lut):
    """Convierte matriz de intensidades a matriz de pixeles RGB.

    Si lut is None, aplica escala de grises pura (mantiene la firma RGB
    de la fase 1 para retrocompatibilidad con todos los tests).
    """
    h = len(intensity)
    w = len(intensity[0])
    pixels = [[None] * w for _ in range(h)]
    for py in range(h):
        for px in range(w):
            pixels[py][px] = apply_palette(intensity[py][px], lut)
    return pixels


def _shannon_entropy_from_intensity(intensity):
    """Shannon sobre 256 bines de la intensidad (0..255 cuantizado)."""
    h = len(intensity)
    w = len(intensity[0])
    histogram = [0] * 256
    for py in range(h):
        for px in range(w):
            histogram[max(0, min(255, int(intensity[py][px] * 255)))] += 1
    total = w * h
    entropy = 0.0
    for count in histogram:
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy, sum(1 for c in histogram if c > 0)


def _spatial_entropy(intensity):
    """Entropía espacial 2D: varianza local 3x3 normalizada -> bines -> Shannon.

    Fallback in-line (idéntica lógica a palettes.spatial_entropy_2d).
    Normaliza por h² para invariancia a resolución.
    """
    if _spatial_entropy_palettes is not None:
        return _spatial_entropy_palettes(intensity)

    h = len(intensity)
    w = len(intensity[0])
    if h < 3 or w < 3:
        return 0.0
    hx = 2.0 / w
    hy = 2.0 / h
    h2 = hx * hy
    hist = [0] * 8
    for py in range(1, h - 1):
        for px in range(1, w - 1):
            c = intensity[py][px]
            var = 0.0
            n = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    var += (intensity[py + dy][px + dx] - c) ** 2
                    n += 1
            var /= n
            var_norm = var / h2 if h2 > 0 else 0.0
            hist[min(7, int(var_norm * 256))] += 1
    total = sum(hist)
    if total == 0:
        return 0.0
    e = 0.0
    for c in hist:
        if c > 0:
            p = c / total
            e -= p * math.log2(p)
    return e


def generate_cppn_image(width=256, height=256, seed=None, palette="raw"):
    """Genera una imagen CPPN y devuelve (pixels, entropy_shannon, metadata).

    Args:
        width:   ancho en pixeles.
        height:  alto en pixeles.
        seed:    semilla determinista.
        palette: nombre de paleta perceptualmente uniforme o "raw"
                 (RGB crudo retrocompatible con Fase 1).

    Returns:
        pixels:  list[list[tuple[int,int,int]]] matriz RGB.
        entropy: float — entropia de Shannon sobre intensidades.
        metadata: dict con seed, dims, entropias, paleta usada.
    """
    intensity = _cppn_intensity(width, height, seed)

    if get_palette is not None and palette != "raw":
        lut = get_palette(palette)
    else:
        lut = None

    pixels = _intensity_to_pixels(intensity, lut)
    entropy, unique = _shannon_entropy_from_intensity(intensity)
    spatial_e = _spatial_entropy(intensity)

    metadata = {
        "seed": seed,
        "width": width,
        "height": height,
        "entropy_shannon": entropy,
        "unique_grays": unique,
        "entropy_spatial": spatial_e,
        "palette": palette,
    }
    return pixels, entropy, metadata


# ---------------------------------------------------------------------------
# Exportadores
# ---------------------------------------------------------------------------

def save_pgm(pixels, filename, width, height):
    """Guarda en formato PGM (P2, ASCII). Retrocompatibilidad."""
    with open(filename, "w") as f:
        f.write("P2\n")
        f.write(f"{width} {height}\n")
        f.write("255\n")
        for row in pixels:
            row_strs = []
            for (r, g, b) in row:
                gray = int(0.299 * r + 0.587 * g + 0.114 * b)
                row_strs.append(str(gray))
            f.write(" ".join(row_strs) + "\n")


def save_png(pixels, filename, width, height):
    """Guarda en formato PNG RGB. Requiere Pillow."""
    if Image is None:
        raise RuntimeError(
            "Pillow no está instalado. Ejecuta: pip install -r requirements.txt"
        )
    img = Image.new("RGB", (width, height))
    img.putdata([px for row in pixels for px in row])
    img.save(filename, format="PNG", optimize=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Generador autónomo de sueños CPPN."
    )
    p.add_argument("--count", type=int, default=1,
                   help="Número de sueños a generar (default: 1).")
    p.add_argument("--width", type=int, default=256,
                   help="Ancho en píxeles (default: 256).")
    p.add_argument("--height", type=int, default=256,
                   help="Alto en píxeles (default: 256).")
    p.add_argument("--out-dir", default="gallery",
                   help="Directorio de salida (default: gallery).")
    p.add_argument("--format", choices=("png", "pgm"), default="png",
                   help="Formato de imagen (default: png).")
    p.add_argument("--palette", default="viridis",
                   help="Paleta perceptualmente uniforme: "
                        + ", ".join(list_palettes()) + " o 'raw' "
                        "(default: viridis).")
    p.add_argument("--seed-base", type=int, default=None,
                   help="Seed base. Si se omite, usa timestamp.")
    p.add_argument("--update-index", action="store_true",
                   help="Reescribir gallery/INDEX.txt con todos los archivos.")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)

    base_seed = args.seed_base or int(datetime.now().timestamp())
    written = []
    entropies = []
    spatial_entropies = []
    metas = []

    for i in range(args.count):
        # Cada sueño tiene seed determinista derivada del base + índice.
        seed = base_seed + i
        pixels, entropy, meta = generate_cppn_image(
            args.width, args.height, seed=seed, palette=args.palette
        )
        ext = "png" if args.format == "png" else "pgm"
        filename = f"dream_{seed}.{ext}"
        filepath = os.path.join(args.out_dir, filename)

        if args.format == "png":
            save_png(pixels, filepath, args.width, args.height)
        else:
            save_pgm(pixels, filepath, args.width, args.height)

        written.append(filename)
        entropies.append(entropy)
        spatial_entropies.append(meta.get("entropy_spatial", 0.0))
        metas.append(meta)
        print(
            f"  [+] {filename}  "
            f"entropy={entropy:.3f}  "
            f"spatial={meta.get('entropy_spatial', 0.0):.3f}  "
            f"palette={args.palette}  "
            f"unique_grays={meta['unique_grays']}"
        )

    avg_entropy = sum(entropies) / max(1, len(entropies))
    avg_spatial = sum(spatial_entropies) / max(1, len(spatial_entropies))
    print(f"\n✓ {len(written)} sueños generados en '{args.out_dir}/'")
    print(f"  Entropía Shannon promedio:    {avg_entropy:.3f}")
    print(f"  Entropía espacial 2D promedio: {avg_spatial:.3f}")

    if args.update_index:
        index_path = os.path.join(args.out_dir, "INDEX.txt")
        # Listar todos los archivos existentes (incluyendo legacy .pgm).
        existing = sorted(
            f for f in os.listdir(args.out_dir)
            if f.startswith("dream_") and (f.endswith(".png") or f.endswith(".pgm"))
        )
        # Calcular min/avg de entropia espacial del lote actual para la cabecera.
        # Los legacy .pgm no tienen ent_spatial (no se midio), quedan con 0.0.
        valid_sp = [e for e in spatial_entropies if e > 0] or [0.0]
        ent_min = min(valid_sp)
        ent_avg = avg_spatial

        with open(index_path, "w") as f:
            f.write(f"# Motor de Imaginacion — Indice de galeria\n")
            f.write(f"# Paleta por defecto: {args.palette}\n")
            f.write(f"# Dimension: {args.width}x{args.height}\n")
            f.write(f"# Total archivos: {len(existing)}\n")
            f.write(f"# Entropia espacial (min, avg): {ent_min:.2f}, {ent_avg:.2f}\n")
            # Enriquecer cada línea con palette + ent_spatial si está disponible.
            ent_by_seed = {m["seed"]: m.get("entropy_spatial", 0.0) for m in metas}
            for name in existing:
                # Extraer seed del nombre (dream_<seed>.png|pgm).
                try:
                    seed = int(name.split("_")[1].split(".")[0])
                except (IndexError, ValueError):
                    f.write(name + "\n")
                    continue
                ent = ent_by_seed.get(seed, 0.0)
                if ent > 0:
                    f.write(f"{name} palette={args.palette} ent_spatial={ent:.2f}\n")
                else:
                    # Legacy sin medir — solo el nombre, parseIndex cae al default.
                    f.write(name + "\n")
        print(f"  Índice actualizado: {index_path} ({len(existing)} archivos)")

        # Sidecar con metadata rica (incluye entropia espacial por imagen).
        meta_path = os.path.join(args.out_dir, "METADATA.json")
        with open(meta_path, "w") as f:
            import json
            json.dump(
                {
                    "palette": args.palette,
                    "width": args.width,
                    "height": args.height,
                    "count": args.count,
                    "avg_entropy_shannon": avg_entropy,
                    "avg_entropy_spatial": avg_spatial,
                    "items": [
                        {
                            "seed": m["seed"],
                            "filename": f"dream_{m['seed']}.{args.format}",
                            "entropy_shannon": m["entropy_shannon"],
                            "entropy_spatial": m.get("entropy_spatial", 0.0),
                            "unique_grays": m["unique_grays"],
                        }
                        for m in metas
                    ],
                },
                f, indent=2,
            )
        print(f"  Metadata JSON:    {meta_path}")

    return 0 if all(e > 3.0 for e in entropies) else 1


if __name__ == "__main__":
    sys.exit(main())
