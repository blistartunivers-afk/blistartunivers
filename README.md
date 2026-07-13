# agentes

Repositorio de agentes autónomos del ecosistema BLIST/SARA OS.

## Agentes Disponibles

### agent_codeindex.py
Indexador y analizador de código fuente Python.

**Ubicación:** `blist-code-guru/blist_code_guru/agent_codeindex.py`

**Funciones:**
- Escanea `~/blist/` y `~/downloads/` buscando archivos `.py`
- Análisis AST: extrae funciones, clases, imports, líneas de código
- Detección de patrones problemáticos:
  - Funciones duplicadas
  - Imports sin usar
  - Archivos huérfanos (sin funciones ni clases)
- Comparación de cambios por SHA256
- Reporte Markdown automático
- Modo monitor continuo

**Uso:**
```bash
python agent_codeindex.py index      # Indexar una vez
python agent_codeindex.py query <keyword>  # Buscar en índice
python agent_codeindex.py monitor     # Monitorear cambios
```

**Salida:**
- `~/.local/.vault/codeindex.json` - Índice JSON
- `~/.local/.vault/codeindex_report.md` - Reporte Markdown

---
*Generado por SARA OS - BLIST v11 Triforce*
