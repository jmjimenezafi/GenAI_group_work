# Gen AI Trabajo

Proyecto para verificacion de afirmaciones y deteccion de fake news con dos caminos de resolucion:

- **RAG local** sobre Qdrant con claims historicos ya almacenados.
- **Busqueda web** con analisis LLM cuando el RAG no puede responder.

El sistema genera un reporte final en Markdown y, ademas, puede convertir ese reporte en un `new_claims.csv` para volver a alimentar la base de datos.

## Que hace el proyecto

- Verifica una afirmacion introducida por consola.
- Decide primero si la base RAG local puede responder.
- Si el RAG es suficiente, genera un reporte directo.
- Si no es suficiente, busca informacion en internet, resume articulos, clasifica fuentes y cruza hechos.
- Genera un reporte final en Markdown.
- Extrae una fila estructurada para `data/new_claims.csv`.
- Permite subir esas nuevas claims a Qdrant de forma automatica.

## Arquitectura general

1. `main.py` ejecuta el flujo principal.
2. `utils/workflow.py` define el grafo de LangGraph.
3. `utils/rag/rag_agent.py` consulta Qdrant y decide si el RAG puede responder.
4. Si el RAG responde, `utils/rag/rag_report_generator.py` genera el reporte.
5. Si el RAG no responde, el flujo pasa por:
   - busqueda web,
   - resumen de articulos,
   - clasificacion de fuentes,
   - cruce de hechos,
   - reporte final.
6. `utils/agents/report_csv_parser.py` convierte el reporte en una fila CSV.
7. `utils/rag/main_qdrant_upsert.py` sube `new_claims.csv` a Qdrant.

## Requisitos

- Python 3.12 o superior.
- `uv` instalado.
- Clave de OpenAI.
- Clave de Tavily.

## Setup recomendado con uv

### 1. Crear el entorno

```bash
uv venv
```

### 2. Instalar dependencias

```bash
uv sync
```

### 3. Activar el entorno en Windows

```powershell
.\.venv\Scripts\activate
```

Tambien puedes ejecutar sin activar el entorno:

```bash
uv run python main.py
```

## Variables de entorno

Copia `.env-example` a `.env` y rellena los valores.

### Minimas

- `OPENAI_API_KEY`
- `TAVILY_API_KEY`

### Recomendadas

- `OPENAI_MODEL` = `gpt-4o-mini`
- `QDRANT_PATH` = `data/qdrant`
- `SEARCH_MAX_RESULTS` = `10`
- `SEARCH_DEPTH` = `advanced`
- `SEARCH_TIMEOUT_SECONDS` = `6`
- `SEARCH_USER_AGENT` = `gen-ai-trabajo/1.0`
- `FACTS_MAX_DOC_CHARS` = `10000`
- `FACTS_MAX_ARTICLE_FACTS` = `10`
- `EMBEDDING_MODEL_NAME` = `all-MiniLM-L6-v2`

### Sobre `QDRANT_PATH`

Si quieres que la base de datos quede dentro del proyecto, usa:

```env
QDRANT_PATH=data/qdrant
```

Si pones una ruta relativa distinta, recuerda que se interpreta respecto al directorio desde el que lanzas el script.

## Uso del verificador

### Ejecutar el flujo principal

```bash
python main.py
```

El programa pedira una query por consola, ejecutara el grafo y generara:

- `report_output.md`: reporte final en Markdown.
- `data/new_claims.csv`: una fila lista para subirse a Qdrant.

### Ejecutar la subida a Qdrant

Una vez tengas `data/new_claims.csv`, ejecuta:

```bash
python utils/rag/main_qdrant_upsert.py
```

Este script:

- carga las claims nuevas en Qdrant,
- actualiza `data/claims.csv`,
- y **borra `data/new_claims.csv` al terminar correctamente**.

## Ciclo de `new_claims.csv`

El ciclo esperado es este:

1. `main.py` genera `data/new_claims.csv` a partir del reporte.
2. `main_qdrant_upsert.py` lee ese archivo y lo inserta en Qdrant.
3. Si la subida se completa bien, `new_claims.csv` se elimina automaticamente.
4. `claims.csv` queda como historico acumulado.

### Importante

- `new_claims.csv` es un archivo temporal.
- No debes reutilizarlo sin haberlo regenerado.
- Si el script de subida se ejecuta dos veces sobre el mismo `new_claims.csv`, duplicaras registros.

## Datos

- `data/claims.csv`: historico principal de claims.
- `data/new_claims.csv`: batch temporal a subir a Qdrant.
- `data/qdrant`: almacenamiento local de la base vectorial Qdrant.

## Salida del sistema

El reporte final se guarda en Markdown y contiene:

- veredicto,
- confianza,
- resumen de evidencia,
- contradicciones detectadas,
- conclusion final.

## Notas de funcionamiento

- Si el RAG puede responder, se evita la busqueda web para ahorrar coste y tiempo.
- Si el RAG no puede responder, el sistema cae al flujo web.
- La busqueda web puede ser mas lenta porque descarga y procesa articulos.
- Las referencias de los reportes usan URLs como enlaces Markdown.

## Estructura resumida

- `main.py`: entrada principal.
- `utils/workflow.py`: grafo LangGraph.
- `utils/rag/`: RAG, Qdrant y reporte RAG.
- `utils/agents/`: busqueda, resumen, clasificacion y reporte web.
- `data/`: claims y base local.

## Consejos practicos

- Mantén `data/new_claims.csv` como archivo temporal.
- Revisa `report_output.md` si quieres inspeccionar la salida antes de subirla a Qdrant.
- Si cambias `OPENAI_MODEL`, asegúrate de que tu cuenta tenga acceso a ese modelo.

## Comandos rapidos

```bash
uv sync
python main.py
python utils/rag/main_qdrant_upsert.py
```

## Resolucion de problemas

### No encuentra la API de OpenAI

Revisa que `OPENAI_API_KEY` este bien definida en `.env`.

### No encuentra la API de Tavily

Revisa que `TAVILY_API_KEY` este bien definida en `.env`.

### Qdrant no guarda donde esperabas

Comprueba `QDRANT_PATH` en `.env` y usa una ruta relativa al directorio de ejecucion, o una ruta absoluta.

### `new_claims.csv` no desaparece

Eso significa que la subida a Qdrant no se completo correctamente. El archivo solo se borra si la ingesta termina bien.
