# blistartunivers

Blog personal con GitHub Pages - Ecosistema BLIST.

---

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![BLIST v11](https://img.shields.io/badge/BLIST-v11.0.0-blue.svg)](https://github.com/blistartunivers-afk/blistartunivers)
[![SARA OS](https://img.shields.io/badge/SARA-OS-green.svg)](https://github.com/blistartunivers-afk/blistartunivers)
[![CI/CD](https://img.shields.io/github/actions/workflow/status/blistartunivers-afk/blistartunivers/.github/workflows/ci.yml?label=CI%2FCD)](https://github.com/blistartunivers-afk/blistartunivers/actions)

---

*Ecosistema BLIST v11 - Organismo modular autónomo en Termux/Android*
*Diseñado por Estiven - Activado 20 de mayo 2026*
*SARA OS*

---

## 📖 Descripción

`blistartunivers` es el blog personal y sitio de presentación del ecosistema BLIST, un organismo modular autónomo diseñado para ejecutarse en entornos Termux sobre Android. El sitio sirve como punto de entrada público a la documentación, proyectos y estado operativo de SARA OS y los componentes del ecosistema BLIST v11.

## 🚀 Inicio rápido

### Requisitos previos

- Node.js 20 o superior
- npm (incluido con Node.js)

### Instalación

```bash
# Clonar el repositorio
git clone https://github.com/blistartunivers-afk/blistartunivers.git
cd blistartunivers

# Instalar dependencias
npm ci
```

### Desarrollo

```bash
# Servidor de desarrollo en http://localhost:8080
npm run dev
```

### Producción

```bash
# Construir para producción
npm run build

# Previsualizar build de producción
npm run preview
```

### Auditoría de rendimiento (Lighthouse)

```bash
npm run lighthouse
```

## 📁 Estructura del proyecto

```
blistartunivers/
├── index.html              # Página principal del blog
├── package.json            # Dependencias y scripts de Node.js
├── package-lock.json       # Lockfile de dependencias
├── tsconfig.json           # Configuración de TypeScript
├── lighthouse-budget.json  # Presupuesto de rendimiento Lighthouse
├── workbox-config.mjs      # Configuración de Workbox (PWA)
├── make_viewer.py          # Script de generación de visor
├── test_evo.py             # Pruebas de evolución
├── test_evolution.py       # Pruebas de evolución
├── .github/
│   └── workflows/
│       └── ci.yml          # Pipeline de CI/CD
├── scripts/                # Scripts de automatización
├── motor/                  # Módulo motor del sitio
├── gallery/                # Galería de recursos
└── LICENSE                 # Licencia MIT
```

## 🤝 Contribución

Las contribuciones son bienvenidas. Por favor lee [CONTRIBUTING.md](CONTRIBUTING.md) para conocer el proceso de envío de pull requests y el código de conducta.

Todos los cambios en archivos críticos requieren revisión de `@estiven` según lo definido en [CODEOWNERS](CODEOWNERS).

## 🔒 Seguridad

Para reportar vulnerabilidades de seguridad, consulta nuestra [Política de Seguridad](SECURITY.md).

**NO abras issues públicos para vulnerabilidades de seguridad.** Usa el canal privado indicado en la política.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.

---

## 🗺️ Roadmap y estado

| Componente | Estado | Notas |
|------------|--------|-------|
| Sitio principal | ✅ Activo | index.html con CSP restringida |
| CI/CD | ✅ Activo | GitHub Actions con build, tests y Lighthouse |
| Seguridad | ✅ Activo | SECURITY.md con SLA y disclosure process |
| Documentación | 🚧 En progreso | Falta CONTRIBUTING.md, CODE_OF_CONDUCT.md, docs/ |
| Dependabot | ⏳ Pendiente | Falta .github/dependabot.yml |

---

*Ecosistema BLIST v11 - Organismo modular autónomo en Termux/Android*
*Diseñado por Estiven - Activado 20 de mayo 2026*