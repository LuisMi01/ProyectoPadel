# Base de datos

Una sola base de datos PostgreSQL con **dos esquemas**. El razonamiento completo está en el documento
"Base de datos: dos esquemas" (17/11/2026); aquí queda lo necesario para trabajar con el código.

| Esquema | Contenido | Código |
|---|---|---|
| `public` | Datos limpios que usa la aplicación: catálogo, usuarios, recomendaciones, analítica y registro de tareas. | `app/models/catalogo.py`, `usuarios.py`, `recomendaciones.py`, `sistema.py` |
| `staging` | Catálogos de las tiendas tal como llegan, antes de normalizar. | `app/models/staging.py` |

Por qué un esquema y no otra base de datos: permite claves foráneas entre los dos lados, normalizar en
una sola transacción (si falla, `public` queda con los datos del día anterior), una sola copia de
seguridad y una sola herramienta de migraciones.

## Tablas

`public` (21): `familia_modelo`, `modelo`, `sku`, `tienda`, `oferta`, `precio_historico`, `vocab_map`,
`usuario`, `sesion`, `token_acceso`, `pala_guardada`, `alerta_precio`, `recomendacion`, `rec_shown`,
`rec_click`, `comision`, `feedback`, `explicacion_cache`, `events`, `metrica_diaria`, `job_run`.

`staging` (3):

| Tabla | Para qué | Relaciones |
|---|---|---|
| `importacion` | Una fila por cada descarga del catálogo de una tienda. `estado`: `en_curso`, `correcta`, `fallida`, `descartada`. | `tienda` 1:N `importacion` (CASCADE) |
| `producto_feed` | Un producto recibido; `datos` (JSONB) lo guarda tal como llega. | `importacion` 1:N (CASCADE); `sku` 0..1:N (SET NULL) |
| `revision_pendiente` | Lo que el sistema no resuelve solo. `motivo`: `emparejamiento_dudoso`, `pala_nueva`, `precio_anomalo`. `estado`: `pendiente`, `aprobado`, `rechazado`. `propuesta` (JSONB): ficha que propone la IA para una pala nueva (`jobs.daily.extract_specs`). | `producto_feed` 1:N (CASCADE) |

Cambios en `public` respecto al primer modelo:

- `modelo`: `nombre` y `slug` (único) de la ficha (`/palas/<slug>/`).
- `tienda`: `plantilla_enlace`, `id_afiliado`, `parametro_subid` para construir el enlace de afiliado
  (`app/domain/afiliacion.py::enlace_afiliado`). La plantilla admite `{url}`, `{id_afiliado}` y
  `{subid}`; el subid es el `rec_click.id`, que permite atribuir la comisión. Sin plantilla, si hay
  `parametro_subid` se añade a la URL del producto. `feed_url`, `feed_formato` y `feed_campos`:
  dónde está el feed de la tienda y qué columna es cada dato.
- `oferta`: `disponibilidad` (`stock`, `ultimas`, `agotada`, como en la web), `referencia` del producto
  en el feed (única por tienda) y `enlace_fallos` (semanas seguidas con la página caída).
- `rec_click`: `origen` (`recomendacion`, `ficha`, `catalogo`, `cuenta`, `palas_guardadas`,
  `alerta_precio`). `recomendacion_id` y `posicion` pasan a ser opcionales, porque hay clics que no
  vienen de una recomendación.
- `vocab_map`: traduce valores de cada tienda a uno único (`campo`, `valor_origen` → `valor`). Con
  `tienda_id` vacío la traducción vale para todas; una sola genérica por campo y valor
  (`UNIQUE NULLS NOT DISTINCT`, PostgreSQL 15+).

## Flujo de importación (`jobs.daily.import_feed` → `app/services/importacion.py`)

1. Crear `importacion` en estado `en_curso`.
2. Guardar cada producto en `producto_feed.datos` exactamente como llega.
3. Si el catálogo trae muchos menos productos de lo normal: `descartada`, no se publica nada.
4. Emparejar con un SKU (EAN → marca/año/familia → nombre parecido). Si hay dudas o la pala no existe,
   crear `revision_pendiente`.
5. Unificar valores con `vocab_map`; precios de texto a número; stock a `disponibilidad`.
6. Publicar en `oferta` (`ON CONFLICT (sku_id, tienda_id) DO UPDATE`) y añadir `precio_historico` si
   cambia el precio. Un cambio extremo va a revisión.
7. Marcar `correcta` o `fallida`.

Cada tienda tendrá un adaptador en Python que conoce sus nombres de campo (`titulo`/`name`,
`precio`/`price`…). La consulta de publicación del documento está probada en
`tests/test_base_de_datos.py::test_consulta_de_publicacion_del_documento`.

## Retención

`jobs.daily.cleanup` borra las importaciones de más de **30 días** (`STAGING_DIAS`; y en cascada sus
productos y revisiones), salvo las que aún tienen alguna revisión `pendiente`.

## Migraciones

```bash
docker compose up -d
cd backend
uv run alembic upgrade head                        # aplica de 0001_inicial a la última
uv run alembic revision --autogenerate -m "..."    # tras cambiar app/models/ (ve public y staging)
uv run alembic check                               # ¿modelos y migraciones coinciden?
```

- Las tablas de `staging` se declaran con `{"schema": "staging"}` y las claves hacia `public` sin
  prefijo (`ForeignKey("tienda.id")`).
- Valores cerrados (estados, motivos, orígenes): `StrEnum` en Python + `CHECK` en la base de datos
  (`app.db.base.en`), no tipos `ENUM` de PostgreSQL, para que añadir un valor sea una migración simple.
- La CI aplica las migraciones en un PostgreSQL real, ejecuta los tests de base de datos, las deshace,
  las rehace y comprueba con `alembic check` que no falta ninguna.

## Permisos (al desplegar)

Para que la API no pueda leer los datos en bruto, en producción se usan dos roles:

```sql
CREATE ROLE padel_api LOGIN PASSWORD '…';      -- la API
CREATE ROLE padel_jobs LOGIN PASSWORD '…';     -- tareas programadas y migraciones
GRANT USAGE ON SCHEMA public TO padel_api;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO padel_api;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO padel_api;
-- padel_api no recibe nada sobre el esquema staging.
```

Los roles dependen del entorno, así que no van en las migraciones.
