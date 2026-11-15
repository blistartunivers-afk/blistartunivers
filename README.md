# BlistArt Univers

Sitio de Estiven sobre el ecosistema BLIST, Sara y sus experimentos visuales. El sitio se publica con GitHub Pages en [BlistArt Univers](https://blistartunivers-afk.github.io/blistartunivers/).

## Qué contiene

- `index.html`: página principal.
- `motor/` y `gallery/`: visualizaciones y galería del motor de imaginación.
- `scripts/build.mjs`: generación de la versión optimizada del sitio.
- `test_evo.py` y `test_evolution.py`: pruebas de componentes de evolución.

## Desarrollo local

Se necesita Node.js para los comandos de `package.json`:

```bash
npm ci
npm run dev
```

El servidor local usa el puerto 8080. Para generar `dist/`, ejecuta `npm run build`; `npm run preview` sirve esa carpeta. El sitio también puede inspeccionarse directamente desde `index.html`.

## Proyectos relacionados

- [BLIST Core](https://github.com/blistartunivers-afk/blist-core): núcleo de Sara y BLIST v11.
- [Motor de Imaginación](https://github.com/blistartunivers-afk/motor-imaginacion): experimentos generativos.
- [BLIST Neuro](https://github.com/blistartunivers-afk/blist-neuro): curso interactivo sobre el sistema nervioso.
