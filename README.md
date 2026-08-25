# Wiki del proyecto — Robot Autónomo de Laboratorio (BFMC)

Sitio que centraliza toda la documentación del proyecto de tesis.
Publicado en <https://robot-autonomo-de-laboratorio-bfmc.github.io/>

Hecho con [MkDocs Material](https://squidfunk.github.io/mkdocs-material/).
Se despliega solo en cada push a `main` (ver `.github/workflows/deploy.yml`).

## Editar localmente

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve     # http://127.0.0.1:8000 con recarga automática
```

## Estructura

```
docs/
├── index.md              Portada
├── timeline.md           Bitácora del proyecto
├── arquitectura/         SAD de VCU y Brain + protocolo UART
├── vision/               Modelo YOLOv8 e informes de entrenamiento
└── archivo/              Material que no vive en ningún repo de código
```

## Importar contenido externo

En `scripts/` hay tres utilidades sin dependencias externas, para traer material que
vive fuera de los repositorios:

| Script | Para qué |
|---|---|
| `notion_import.py <url> <destino>` | Baja una página de Notion publicada (y sus subpáginas e imágenes) y la convierte a Markdown |
| `docx_import.py <archivo.docx> <destino>` | Parte un `.docx` en una página por capítulo, extrayendo figuras y tablas |
| `pptx_outline.py <archivo.pptx> [salida]` | Saca el texto de una presentación como esquema, para que sea indexable |
| `strip_mailto.py <archivos...>` | Quita enlaces `mailto:` de PDF y OOXML antes de publicarlos |

Todos imprimen al final las líneas para pegar en el `nav:` de `mkdocs.yml`.
Las imágenes quedan guardadas en el repositorio, de modo que el contenido no dependa
de que la fuente original siga existiendo.

## Para agregar una página

1. Creá el `.md` dentro de `docs/`.
2. Agregalo al `nav:` de `mkdocs.yml`.
3. Commit y push. El build corre con `--strict`, así que un link roto falla el deploy.

## Nota sobre duplicación

Los documentos de `docs/arquitectura/` y `docs/vision/` son copias de los README y
los informes de los repos `brain`, `embedded` y `vision-artificial`. Como el proyecto
está cerrado (último commit: 18-dic-2025), no hay riesgo de desincronización. Si
alguno de esos repos volviera a moverse, esta wiki pasa a ser la fuente de verdad y
los README de cada repo se reducen a instrucciones de ejecución + link acá.
