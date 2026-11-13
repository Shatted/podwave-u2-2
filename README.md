# PodWave — Plataforma de streaming de audio (Django 5 + MySQL)

Proyecto PodWave (originalmente una SPA en React, reconstruido en Django en
la Unidad 1), evolucionado en la Unidad 2 y entregado ahora en su **etapa
final: Evaluación Sumativa 3 (Unidad 2, parte 2)**:

- Unidad 2, parte 1: conexión a **MySQL 8**, modelos normalizados,
  migraciones (con migración de datos), Django Admin y comando de siembra.
- Unidad 2, parte 2 (**esta entrega**): **CRUD completo de pistas Y listas
  de reproducción desde las interfaces propias del sitio web** (sin
  depender de Django Admin), formularios con validaciones y mensajes de
  confirmación/error, autenticación con **control de acceso por dueño** y
  usuario de prueba documentado para la evaluación.

Tema oscuro original conservado, reproductor fijo inferior persistente.

## Problemática, objetivo, usuarios y alcance

- **Problemática:** las plataformas de audio tradicionales no permiten
  administrar catálogos propios de episodios con géneros y listas a
  medida; los archivos locales se pierden entre carpetas sin metadatos.
- **Objetivo:** plataforma web que centraliza la biblioteca de podcasts
  con persistencia real (MySQL), sesiones de usuario y gestión CRUD.
- **Usuarios:** oyentes (consulta pública de la biblioteca y de las
  listas) y usuarios registrados (agregar/editar/eliminar **sus** pistas
  y armar **sus** listas).
- **Roles:** anónimo (lectura), usuario autenticado (CRUD sobre sus
  pistas y listas propias) y superusuario (acceso total + Django Admin).
- **Alcance U2-2:** el CRUD pasa de "cualquier usuario autenticado" a
  **control de acceso por propiedad** (cada quien edita/elimina solo lo
  que creó, verificado en el servidor), las **listas se gestionan por
  completo desde el sitio** (crear, consultar, editar, eliminar y
  administrar sus pistas: agregar, quitar, reordenar) y cada operación
  entrega **mensajes de confirmación o error**.

## USUARIO DE PRUEBA para la evaluación (docente)

Tras ejecutar `python manage.py seed_demo` (paso 5 abajo), el sistema
queda con un usuario de prueba exclusivo para revisar las funcionalidades:

| Usuario | Contraseña | Uso |
|---|---|---|
| `demo` | `demo1234` | Dueño de los datos de demostración: 8 pistas y 3 listas. Inicia sesión con él para probar TODO el CRUD desde el sitio. |

La credencial es fija y determinista: `seed_demo` la re-establece en cada
corrida. Es una clave de **prueba exclusivamente** para la evaluación
(instrucción 9 de la evaluación), no una contraseña personal; puede
cambiarse con `--password` o `DJANGO_DEMO_PASSWORD`.

Para crear un superusuario adicional (Django Admin en `/admin/`):
`python manage.py createsuperuser`.

## Puesta en marcha desde cero

```bash
# 1) Crear y activar el entorno virtual
python -m venv venv
venv\Scripts\activate          # Windows (PowerShell: ver nota de ejecución*)
source venv/bin/activate       # macOS / Linux

# 2) Instalar dependencias (Django 5.2.18 LTS + mysqlclient + crispy)
pip install -r requirements.txt
```

**3) Crear la base de datos MySQL** (con utf8mb4 para acentos y emojis):

```sql
-- desde la consola de MySQL (mysql -u root -p)
CREATE DATABASE podwave CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'podwave_user'@'localhost' IDENTIFIED BY 'tu_contraseña';
GRANT ALL PRIVILEGES ON podwave.* TO 'podwave_user'@'localhost';
GRANT ALL PRIVILEGES ON `test_podwave`.* TO 'podwave_user'@'localhost';
FLUSH PRIVILEGES;
```

> El privilegio sobre `test_podwave` es necesario para que
> `python manage.py test` pueda crear la base de datos de pruebas.

**4) Configurar las variables de entorno** (nada va en el código):

```bash
cp .env.example .env    # Windows: copy .env.example .env
# Edita .env: DJANGO_SECRET_KEY, DB_USER, DB_PASSWORD…
```

Genera una clave segura con:
`python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

**5) Migrar, sembrar datos de demostración y arrancar:**

```bash
python manage.py migrate          # aplica 0001→0005 (incluye migración de datos)
python manage.py seed_demo        # catálogo U1 -> MySQL + usuario demo/demo1234
python manage.py runserver
```

Abrir http://127.0.0.1:8000/ · Biblioteca: `/tracks/` · Listas: `/playlists/`
· Admin: `/admin/` · **Iniciar sesión: demo / demo1234**.

> `seed_demo` es IDEMPOTENTE (puede ejecutarse dos veces sin duplicar) y
> además de los datos U1 (géneros, pistas, listas con su orden) garantiza
> el usuario de prueba `demo / demo1234`.

### ¿En GitHub Codespaces?

El proyecto **detecta automáticamente** el entorno de Codespaces (variable
`CODESPACE_NAME`) y confía en su dominio reenviado (`*.app.github.dev`),
tanto para `ALLOWED_HOSTS` como para el CSRF de los formularios. En el
codespace, MySQL puede instalarse con `sudo apt-get install mysql-server`
o usarse un servicio externo (los valores van igual en `.env`).

\* Si PowerShell bloquea la activación del venv:
`Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

## Qué se añade en esta entrega (U2-2)

| Funcionalidad | Dónde | Detalle |
|---|---|---|
| CRUD de listas desde el sitio | `podwave/views.py` + `templates/podwave/playlist_*.html` | Crear (`/playlists/nueva/`), consultar (índice y detalle públicos), editar y eliminar (con confirmación), todo con `LoginRequiredMixin` + dueño |
| Gestión de pistas dentro de la lista | vistas de función | Agregar (desde el detalle de cada pista, select de listas propias), quitar (renumera posiciones) y subir/bajar (intercambio seguro de órdenes) |
| Mensajes de confirmación/error | `SuccessMessageMixin` + `MESSAGE_TAGS` | Alert Bootstrap tras cada operación y errores de validación visibles |
| Control de acceso por propiedad | `get_queryset()` filtrando por dueño | Editar/eliminar responde 404 a quien no es el dueño (pistas y listas); superusuario mantiene acceso total |
| Usuario de prueba | `seed_demo` | `demo / demo1234`, determinista y documentado en este README |

## ¿Cómo pruebo TODO el CRUD desde el sitio? (guion de demo)

1. **Entrar:** `/accounts/login/` con `demo / demo1234` (o un registro
   propio desde "Registrarse").
2. **CREATE pista:** navbar → "+ Agregar pista" → título, artista, género
   y archivo/URL → mensaje verde de confirmación.
3. **READ pista:** Biblioteca (`/tracks/`) y su filtro por género; el
   reproductor inferior suena al pulsar "Reproducir".
4. **UPDATE pista:** en la pista propia, "Editar" → cambiar el título →
   mensaje de confirmación.
5. **CREATE lista:** navbar → "Listas" → "+ Crear lista" → nombre.
6. **CREATE enlace N:M:** en el detalle de una pista, panel "Agregar a una
   lista" → elige una lista propia → la pista entra al final.
7. **UPDATE orden:** en el detalle de la lista, botones ▲/▼ para subir o
   bajar una posición (el orden se conserva en MySQL).
8. **DELETE enlace:** en el detalle de la lista, "Quitar" en cualquier
   fila (la pista NO se borra de la biblioteca, solo de esa lista).
9. **UPDATE / DELETE lista:** "Editar lista" cambia nombre/descripción;
   "Eliminar lista" pide confirmación y borra la lista y sus enlaces,
   no las pistas.
10. **Sesión:** "Cerrar sesión" (POST, Django 5) y vuelve el estado
    anónimo: las páginas públicas siguen visibles, las de gestión no.

## Modelo de datos

| Modelo | Descripción | Reglas clave |
|---|---|---|
| `Genre` | Catálogo de géneros (antes choices de U1) | `name` único + `slug` único autogenerado |
| `Track` | Pista de audio | FK a `Genre` con `on_delete=PROTECT`, `slug` único, auditoría (`created_by`) |
| `Playlist` | Lista de reproducción por usuario | FK `owner` con `on_delete=CASCADE`, nombre único por usuario, `get_absolute_url` |
| `PlaylistTrack` | Tabla intermedia N:M con `order` | constraints: pista única por lista y orden único por lista; utilidades `mover()` y renumeración |

**Cadena de migraciones** (aplicar en orden con `migrate`; esta entrega
NO añade migraciones: no hubo cambios de esquema):

```
0001_initial                                   (U1: Track con genre CharField+choices)
0002_track_audio_file_alter_track_url          (U1: audio_file + url)
0003_create_genre                              (U2: tabla Genre)
0004_normaliza_genero_pistas                   (U2: DATOS: choices -> filas Genre,
                                                FK en cada pista + slugs; reversible)
0005_playlists_slugs_y_campos_obligatorios     (U2: Playlist + PlaylistTrack,
                                                slug único, género obligatorio)
```

La migración **0004 conserva los datos de la Unidad 1**: una pista con
`genre='Ciencia'` (texto) termina apuntando a la fila `Genre('Ciencia')`.

### Zonas horarias (decisión de ingeniería)

El proyecto usa `USE_TZ = False` con `TIME_ZONE = 'America/Santiago'`:
las fechas se guardan y muestran en hora local chilena directamente.
La razón es la portabilidad: con `USE_TZ = True` y una zona local, el
Django Admin (`date_hierarchy` y el filtro por fecha) genera
`CONVERT_TZ()` con zonas horarias **nombradas**, y un MySQL recién
instalado **no trae las tablas de zonas horarias cargadas** (ni en
Windows, ni en macOS, ni en Linux): hay que cargarlas a mano con
`mysql_tzinfo_to_sql`. Sin ellas, los changelists de pistas y listas
devuelven error 500. Con `USE_TZ = False` no se genera `CONVERT_TZ` y
el proyecto funciona igual en cualquier instalación de MySQL, sin pasos
manuales extra (ver el comentario en `settings.py` y los tests de
regresión `AdminChangelistConDatosTest`).

## ¿Cómo agrego MI PROPIA música?

1. Inicia sesión y pulsa **"+ Agregar pista"** (navbar) o `/tracks/nueva/`.
2. Completa **título**, **artista** y **género** (un select con el
   catálogo de la tabla Genre).
3. Sube un archivo (.mp3/.wav/.ogg/.m4a/.flac, máx. 20 MB) **o** pega una
   URL `http(s)://` directa a un audio público. Al menos una de las dos.

El archivo queda en `media/audio/` y se sirve localmente (reproducción
inmediata). El reproductor fijo recuerda pista y minuto exacto al navegar.
Después arma tus listas: "Listas → + Crear lista" y agrega esta pista
desde su propio detalle.

## Tests

```bash
python manage.py test     # 107 pruebas: datos simulados (U1), modelos normalizados
                          # (Genre/Track/Playlist/PlaylistTrack), formularios,
                          # CRUD de pistas Y LISTAS desde el sitio, gestión de
                          # pistas dentro de la lista (agregar/quitar/reordenar),
                          # filtro por slug, subida de archivos, sesiones,
                          # CONTROL DE ACCESO POR PROPIEDAD (404 a no dueños),
                          # MENSAJES de confirmación/error, usuario de prueba
                          # demo/demo1234, Django Admin (changelists con datos y
                          # CRUD completo por el panel) y comando seed_demo
```

## Estructura principal

```
django_project/
├── manage.py, requirements.txt, .env.example
├── ANEXO_USO_IA.md              # anexo de uso de IA (evidencia mínima de la evaluación)
├── GUIA_DEFENSA.md              # preparación de la defensa y la presentación (Rúbrica B)
├── REGISTRO_CONTRIBUCION.md     # registro de contribución por integrante
├── media/audio/                 # archivos de audio (8 pistas demo incluidas)
├── static/                      # css/podwave.css · js/player.js · img/favicon.svg
├── templates/
│   ├── base.html                # + bloque de mensajes del framework messages (U2-2)
│   ├── podwave/track_*.html     # CRUD de pistas (U1/U2, con botones por dueño)
│   └── podwave/playlist_*.html  # CRUD de listas: list, detail, form, delete (U2-2)
├── podwave/                     # app principal
│   ├── models.py                # Genre, Track, Playlist (+siguiente_orden, renumerar),
│   │                            # PlaylistTrack (+mover: intercambio seguro de órdenes)
│   ├── views.py                 # CRUD de pistas y LISTAS + add/remove/move (U2-2)
│   ├── forms.py                 # TrackForm, PlaylistForm, AddToPlaylistForm
│   ├── admin.py                 # 4 ModelAdmin + inline (N:M con orden)
│   ├── migrations/0001…0005     # 0004 = migración de datos (U1 -> FK)
│   ├── management/commands/seed_demo.py   # datos U1 -> MySQL + demo/demo1234
│   ├── datos_simulados.py       # estructuras de Python (U1) + LISTAS_DEMO
│   ├── context_processors.py, urls.py, tests.py (107 pruebas)
├── accounts/                    # registro de usuarios (SignUpView)
├── pages/                       # home y about (documento de proyecto)
└── django_project/              # settings.py (MySQL por variables de entorno,
                                 # MESSAGE_TAGS alineados con Bootstrap)
```

## Seguridad (instrucción 9 de la evaluación)

- **Ninguna credencial en el código**: base de datos, `SECRET_KEY` y
  `DEBUG` se leen de variables de entorno (`.env` en desarrollo; ver
  `.env.example`). Si falta `DJANGO_SECRET_KEY` la aplicación no arranca
  (no existe clave insegura "por omisión"). `.env` está en `.gitignore`.
- La única credencial "visible" es la del **usuario de prueba** para la
  evaluación (`demo / demo1234`, `PASSWORD_DEMO_POR_DEFECTO` en
  `seed_demo.py`): es de acceso de prueba, no un secreto real.
- Sesiones y protección CSRF de Django en todos los formularios
  (incluidas las acciones POST de mover/quitar en las listas).
- **Control de acceso por propiedad** (U2-2): las vistas de edición y
  eliminación filtran por dueño; quien no lo es recibe 404.
- Subida de audio restringida: extensiones permitidas y máximo 20 MB.

## Notas de la Unidad 1 (se mantienen)

- **Datos simulados:** `podwave/datos_simulados.py` define el catálogo como
  estructuras de Python (lista de diccionarios `PISTAS_DEMO` y lista de
  tuplas `GENEROS_SUGERIDOS`) con funciones que usan variables,
  operaciones, decisiones, iteraciones y manejo de excepciones. En la
  Unidad 2 esas estructuras alimentan la migración de datos y el comando
  `seed_demo`: los datos simulados se vuelven registros persistentes.
