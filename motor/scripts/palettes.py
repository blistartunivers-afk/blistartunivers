"""
Motor de Imaginación — Paletas perceptualmente uniformes.

Look-up tables de 256 stops para 5 paletas de la familia matplotlib
(viridis, plasma, inferno, magma) más turbo (Google AI). Todas son
de dominio público y se codifican manualmente a partir de sus puntos
de control conocidas, sin dependencia externa.

La idea es simple: el CPPN produce una *intensidad* escalar [0.0, 1.0]
y la paleta la convierte a RGB. Esto garantiza percepción uniforme y
resulta en imágenes muchísimo más armoniosas que RGB independiente.

Uso:
    from palettes import get_palette, list_palettes
    lut = get_palette("viridis")
    rgb = lut[int(value * 255)]      # O(1) por pixel

Las paletas son inmutables; se cachean al primer acceso.
"""
from functools import lru_cache
import math


# ---------------------------------------------------------------------------
# Paletas
# ---------------------------------------------------------------------------

def _build_lut(stops):
    """Interpola linealmente una lista de (r, g, b) en [0, 1] a 256 stops."""
    lut = []
    n = len(stops) - 1
    for i in range(256):
        t = i / 255.0 * n
        lo = int(t)
        hi = min(lo + 1, n)
        f = t - lo
        r = stops[lo][0] * (1 - f) + stops[hi][0] * f
        g = stops[lo][1] * (1 - f) + stops[hi][1] * f
        b = stops[lo][2] * (1 - f) + stops[hi][2] * f
        lut.append((int(r * 255), int(g * 255), int(b * 255)))
    return tuple(lut)


# Puntos de control (r, g, b) en [0, 1] seleccionados de cada familia.
# Todos son de dominio público / CC0.

_VIRIDIS_STOPS = [
    (0.267, 0.005, 0.329),   # 0.0  - dark purple
    (0.282, 0.140, 0.458),   # 0.13
    (0.254, 0.265, 0.530),   # 0.25
    (0.207, 0.372, 0.553),   # 0.38
    (0.164, 0.471, 0.558),   # 0.5
    (0.128, 0.567, 0.551),   # 0.63
    (0.135, 0.659, 0.518),   # 0.75
    (0.267, 0.749, 0.441),   # 0.88
    (0.478, 0.821, 0.318),   # 1.0  - yellow-green
    (0.993, 0.906, 0.144),   # extremo (en realidad viridis llega hasta amarillo)
]

_PLASMA_STOPS = [
    (0.050, 0.030, 0.528),   # 0.0  - dark blue
    (0.418, 0.020, 0.643),   # 0.14
    (0.661, 0.071, 0.633),   # 0.28
    (0.836, 0.184, 0.518),   # 0.42
    (0.957, 0.314, 0.385),   # 0.57
    (0.988, 0.498, 0.249),   # 0.71
    (0.969, 0.706, 0.169),   # 0.85
    (0.940, 0.975, 0.131),   # 1.0  - bright yellow
]

_INFERNO_STOPS = [
    (0.001, 0.001, 0.014),   # 0.0  - near black
    (0.211, 0.066, 0.332),   # 0.14
    (0.450, 0.097, 0.452),   # 0.28
    (0.671, 0.149, 0.451),   # 0.43
    (0.831, 0.232, 0.349),   # 0.57
    (0.945, 0.376, 0.180),   # 0.71
    (0.987, 0.586, 0.069),   # 0.85
    (0.988, 0.998, 0.645),   # 1.0  - pale yellow
]

_MAGMA_STOPS = [
    (0.001, 0.001, 0.014),   # 0.0  - near black
    (0.180, 0.064, 0.351),   # 0.14
    (0.401, 0.082, 0.483),   # 0.28
    (0.609, 0.135, 0.522),   # 0.43
    (0.793, 0.213, 0.466),   # 0.57
    (0.927, 0.343, 0.357),   # 0.71
    (0.987, 0.541, 0.240),   # 0.85
    (0.987, 0.991, 0.749),   # 1.0  - cream
]

_TURBO_STOPS = [
    (0.189, 0.072, 0.235),   # 0.0  - dark blue/purple
    (0.247, 0.529, 0.788),   # 0.14 - blue
    (0.137, 0.831, 0.870),   # 0.28 - cyan
    (0.498, 0.964, 0.474),   # 0.42 - green
    (0.937, 0.929, 0.180),   # 0.57 - yellow
    (0.961, 0.541, 0.137),   # 0.71 - orange
    (0.788, 0.180, 0.149),   # 0.85 - red
    (0.474, 0.015, 0.027),   # 1.0  - dark red
]

# Cividis (colorblind-safe, perceptually uniform) - matplotlib CC0
_CIVIDIS_STOPS = [
    (0.002, 0.009, 0.174),   # 0.0  - dark blue
    (0.008, 0.159, 0.372),   # 0.14
    (0.040, 0.278, 0.497),   # 0.28
    (0.113, 0.391, 0.569),   # 0.42
    (0.231, 0.498, 0.594),   # 0.57
    (0.400, 0.606, 0.571),   # 0.71
    (0.627, 0.715, 0.486),   # 0.85
    (0.894, 0.831, 0.345),   # 1.0  - yellow
]

# Twilight (diverging, colorblind-safe) - matplotlib CC0
_TWILIGHT_STOPS = [
    (0.255, 0.007, 0.358),   # 0.0  - dark purple
    (0.421, 0.074, 0.557),   # 0.14
    (0.589, 0.158, 0.644),   # 0.28
    (0.727, 0.282, 0.620),   # 0.42
    (0.827, 0.447, 0.498),   # 0.57 - center (white-ish)
    (0.827, 0.447, 0.498),   # 0.71 - symmetric
    (0.727, 0.282, 0.620),   # 0.85
    (0.589, 0.158, 0.644),   # 1.0
]


# ---------------------------------------------------------------------------
# Registro y acceso
# ---------------------------------------------------------------------------

REGISTRY = {
    "viridis": _VIRIDIS_STOPS,
    "plasma":  _PLASMA_STOPS,
    "inferno": _INFERNO_STOPS,
    "magma":   _MAGMA_STOPS,
    "turbo":   _TURBO_STOPS,
    "cividis": _CIVIDIS_STOPS,
    "twilight": _TWILIGHT_STOPS,
}


def list_palettes():
    """Devuelve la lista de paletas disponibles (excluyendo 'raw')."""
    return sorted(REGISTRY.keys())


@lru_cache(maxsize=None)
def get_palette(name):
    """Devuelve la look-up table de 256 entradas para la paleta indicada.

    `name="raw"` retorna None (señal para no aplicar paleta).
    """
    if name == "raw":
        return None
    if name not in REGISTRY:
        raise ValueError(
            f"Paleta '{name}' desconocida. Disponibles: {list_palettes()} + raw"
        )
    return _build_lut(REGISTRY[name])


def apply_palette(value, lut):
    """Mappea un escalar [0.0, 1.0] a (r, g, b) usando la LUT.

    Si `lut is None`, devuelve `(value*255, value*255, value*255)` (gris).
    """
    if lut is None:
        g = max(0, min(255, int(value * 255)))
        return (g, g, g)
    idx = max(0, min(255, int(value * 255)))
    return lut[idx]


# ---------------------------------------------------------------------------
# Métrica: entropía espacial 2D
# ---------------------------------------------------------------------------

def spatial_entropy_2d(intensity):
    """Entropía espacial 2D: varianza local 3x3 normalizada -> 8 bines -> Shannon.

    Para cada pixel interior computo la varianza local en su vecindad
    3x3 (incluyendo el centro, n=9 muestras). La varianza se normaliza
    por el espaciado de píxeles al cuadrado (h²) para ser invariante
    a la resolución. Esa varianza normalizada cuantizada a 8 niveles
    va a un histograma y se calcula Shannon.

    Detecta patrones independientemente de su valor absoluto y resolución:
    dos imágenes pueden tener el mismo Shannon global pero diferente
    complejidad espacial.

    Args:
        intensity: list[list[float]] matriz [h][w] con valores [0.0, 1.0].

    Returns:
        float: entropía espacial en bits. Rango típico [0.0, 3.0].
    """
    h = len(intensity)
    w = len(intensity[0])
    if h < 3 or w < 3:
        return 0.0
    # Espaciado en coordenadas normalizadas [-1, 1] (CPPN usa este espacio)
    hx = 2.0 / w
    hy = 2.0 / h
    h2 = hx * hy  # área del pixel en espacio normalizado
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
            # Normalizar por h² para invariancia a resolución
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


# Alias retrocompatible (algunos tests pueden llamarla asi).
_spatial_entropy_2d = spatial_entropy_2d
