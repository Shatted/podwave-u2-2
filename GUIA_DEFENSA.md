# Guía de defensa técnica — PodWave (Django 5.2.18)

> Guía de preparación para la defensa técnica del proyecto (estructura
> de defensa de la Unidad 1: exposición grupal + preguntas individuales).
> Esta guía repasa esa estructura (B1–B5) y añade dos secciones
> específicas: **B6** (Evaluación Sumativa 2 parte 1: MySQL + Models +
> Django Admin) y **B7** (Evaluación Sumativa 3 / U2-2: CRUD de listas
> desde el sitio, mensajes, control de acceso y la PRESENTACIÓN Y DEMO
> según la Rúbrica B, que en esta etapa vale el 30% de la nota).
> Estúdiala con el proyecto abierto en VS Code y practica las
> modificaciones de la sección B4 hasta poder hacerlas sin consultar.

---

## B1. Comprensión de la arquitectura y flujo de Django (8 pts)

**Flujo request → URL → View → Template → response** (memorízalo con este
proyecto):

1. El navegador pide `GET /tracks/?genero=M%C3%BAsica`.
2. Django busca el patrón en `django_project/urls.py`, que incluye
   `pages.urls` y `podwave.urls` (orden de arriba hacia abajo).
3. `podwave/urls.py` coincide `tracks/` → llama
   `views.TrackListView.as_view()`.
4. La vista (lógica): `TrackListView` es una **vista genérica basada en
   clases (GCBV)**. `get_queryset()` lee el parámetro `genero` (variable +
   decisión) y filtra; `get_context_data()` arma el contexto
   (`tracks`, `generos`, `resumen_generos`…).
5. La vista renderiza `templates/podwave/track_list.html`, que **hereda**
   `base.html` (`{% extends %}` + `{% block content %}`) y recibe los datos
   **solo mediante el contexto** (nunca lógica en el HTML).
6. Django devuelve la respuesta HTTP al navegador.

**MVT aplicado (diferencias con MVC):**
- **Model** — `podwave/models.py`: clases `Genre`, `Track`, `Playlist` y
  `PlaylistTrack` (tablas **MySQL 8** vía ORM).
- **View** — `podwave/views.py`: prepara datos y coordina la respuesta
  (equivalente al "Controller" de MVC).
- **Template** — `templates/`: presentación pura.
- En MVC la "V" es la template y la "C" es la view de Django: el nombre
  cambia, la responsabilidad es la misma separación.

**Función de los archivos principales:**

| Archivo | Función |
|---|---|
| `manage.py` | Utilitario de comandos (runserver, migrate, test). |
| `django_project/settings.py` | Configuración: apps, BD, static/media, auth, CSRF. |
| `django_project/urls.py` | Enrutador raíz, incluye las URLs de cada app. |
| `podwave/urls.py` | Rutas del CRUD: `tracks/`, `tracks/<int:pk>/`… |
| `podwave/views.py` | 5 GCBV: ListView, DetailView, Create, Update, Delete. |
| `podwave/models.py` | Modelos `Genre`, `Track`, `Playlist`, `PlaylistTrack` (MySQL 8 vía ORM). |
| `podwave/forms.py` | `TrackForm` (ModelForm) con validaciones de servidor. |
| `podwave/datos_simulados.py` | Estructuras de Python (U1): `PISTAS_DEMO`, `GENEROS_SUGERIDOS`, funciones. |
| `podwave/admin.py` | Registro de los 4 modelos en Django Admin (listas, filtros, búsqueda, inline). |
| `accounts/` + `registration/` | Registro y login/logout (auth de Django). |
| `pages/` | Home y Acerca de. |
| `static/` | `css/podwave.css`, `js/player.js`, `img/favicon.svg`. |
| `media/audio/` | Archivos de audio subidos por los usuarios. |

---

## B2. Explicación del código y decisiones técnicas (8 pts)

**Estructuras de Python (U1) — `podwave/datos_simulados.py`:**
- `PISTAS_DEMO`: **lista de diccionarios** (catálogo demo). La recorre
  `seed_demo.py` con una **iteración** para poblar la BD con el ORM (U2).
- `GENEROS_SUGERIDOS`: **lista de tuplas**; alimenta las `choices` del
  modelo y el filtro por género de la biblioteca via contexto.
- `resumen_por_genero()`: función con **iteración + decisión + operación**
  que devuelve una lista de tuplas ordenada.
- `pista_aleatoria()`: **manejo de excepciones** (`IndexError` si la lista
  está vacía).
- Variables y operaciones: en todas las vistas (p. ej. `genero = ... .strip()`,
  `conteo[genero] += 1`).

**Packages externos (criterio 1.1.3):** `django` 5.2.17,
`django-crispy-forms` + `crispy-bootstrap5` (ver `requirements.txt`).

**Decisiones clave que debes saber justificar:**

1. **¿Por qué vistas genéricas (GCBV) y no funciones (FBV)?** Menos código
   repetido para CRUD estándar; ListView/DetailView/CreateView ya traen
   paginación, contexto y manejo de formulario (contenido U2).
2. **¿Por qué `audio_file` (FileField) Y `url`?** El usuario puede subir su
   música (se guarda en `media/audio/`, se sirve local → reproducción
   inmediata) o pegar un enlace externo; el modelo exige al menos una
   fuente (`clean()`).
3. **¿Por qué validar en el servidor si React ya validaba?** La validación
   del navegador se salta fácilmente; el servidor es la barrera real
   (mismo espíritu que `validators.js`: bloquea `javascript:`, `ftp://`).
4. **¿Por qué el logout es un `<form>` POST?** Django 5 exige POST para
   `LogoutView` (GET devuelve 405); además CSRF protege el cierre de sesión.
5. **¿Por qué `LoginRequiredMixin`?** Criterio 2.1.3: crear/editar/eliminar
   exigen sesión; sin sesión redirige al login (`?next=`).
6. **¿Por qué sessionStorage en player.js?** En una SPA el player nunca se
   desmonta; en Django (MPA) cada clic recarga la página, así que se guarda
   pista/minuto/estado y se restauran en la siguiente carga.
7. **¿Por qué secret key por variable de entorno?** No versionar secretos
   si el repo es público (instrucción 9 de la evaluación U2-1:
   credenciales, contraseñas y tokens fuera del código).

---

## B3. Preguntas técnicas probables (8 pts) — practica en voz alta

1. ¿Qué hace `python manage.py migrate`? — Aplica las migraciones
   (`0001_initial`, `0002_track_audio_file…`): traduce los modelos a tablas
   SQL en el servidor **MySQL** (base `podwave`, charset utf8mb4).
2. ¿Diferencia entre `makemigrations` y `migrate`? — El primero GENERA el
   plan (archivos Python), el segundo lo EJECUTA contra la BD.
3. ¿Qué es un QuerySet? ¿Es una lista? — Es perezoso (lazy): no toca la BD
   hasta evaluarse; es iterable como lista, pero es SQL encapsulado.
4. ¿Qué hace `{% csrf_token %}`?** — Inserta el token que Django exige en
   todo POST para frenar Cross-Site Request Forgery.
5. ¿Para qué sirve `get_context_data()`? — Añadir variables extra al
   contexto que recibe la plantilla (p. ej. `generos`, `total_tracks`).
6. ¿Qué es un context processor? — Función que inyecta variables a TODAS
   las plantillas (`track_counter` muestra "N pistas" en el navbar).
7. ¿Qué pasa si un visitante sin sesión entra a `/tracks/nueva/`? —
   `LoginRequiredMixin` redirige a `/accounts/login/?next=/tracks/nueva/`.
8. ¿Dónde viven los estáticos vs. los media? — `static/` = assets del
   desarrollador (CSS/JS/img); `media/` = archivos subidos por usuarios.
9. ¿Por qué `{% static %}` y no rutas duras? — Respeta `STATIC_URL` y
   evita romper rutas al desplegar.
10. ¿Cómo probarías el proyecto? — `python manage.py test` (76 pruebas:
    modelo, formularios, vistas, sesiones, subida de archivos, admin
    con datos y CRUD por el panel, seed).
11. ¿Qué es MVT y en qué se diferencia de MVC? — Ver B1.
12. ¿Cómo filtras por género y por qué no usas SQL crudo? —
    `queryset.filter(genre__slug=genero)` con el ORM: portable y seguro contra
    inyección SQL.

---

## B4. Practica estas modificaciones en vivo (8 pts)

El docente puede pedirte un cambio pequeño. Practica estas (10 min c/u):

1. **Cambiar el orden de la biblioteca** (más antiguas primero):
   `models.py` → `ordering = ['created_at']` → recargar.
2. **Cambiar la paginación:** `views.py` → `paginate_by = 6` → otro número.
3. **Cambiar el máximo de archivo:** `settings.py` → `TRACK_MAX_FILE_BYTES`.
4. **Agregar un género (U2):** desde `/admin/podwave/genre/` (el slug se
   completa solo) o `Genre.objects.create(name='...')` en el shell —
   aparece solo en el filtro y el formulario (¡ventaja de la tabla
   normalizada!).
5. **Cambiar el texto del navbar:** `templates/base.html`.
6. **Hacer que el home muestre 6 últimas pistas:** `pages/views.py`
   (contexto `latest_tracks`) o consulta equivalente.
7. **Renombrar una ruta:** `podwave/urls.py` (p. ej. `tracks/` →
   `biblioteca/`) + `{% url %}` se encarga del resto.

> Truco: tras cada cambio ejecuta `python manage.py test` para demostrar
> que no rompiste nada — impresiona en la defensa.

---

## B5. Aporte individual y código asistido por IA (8 pts)

- Completa `ANEXO_USO_IA.md` (herramienta, prompts, apoyo, tus correcciones).
- Regla de oro: **solo declara como tuyo lo que puedes explicar y modificar
  en vivo.** Repasa B1–B4 hasta dominar el código.
- Si trabajas en equipo (2–3): adjunta el registro de contribución
  individual (evidencia mínima de la evaluación).

---

## Checklist final de entrega (evidencias mínimas del instrumento U2-2)

- [ ] Código fuente completo del proyecto Django 5.2.18 (zip), con versión
      compatible y soportada del framework.
- [ ] Proyecto ejecutable (`python manage.py runserver`) con todas las
      páginas y funcionalidades operativas.
- [ ] Configuración funcional de conexión a MySQL (variables de entorno).
- [ ] Models y migraciones 0001→0005 correspondientes a las entidades.
- [ ] CRUD completo de PISTAS y LISTAS desde las interfaces propias del
      sitio (sin depender de Django Admin).
- [ ] Formularios con validaciones y mensajes de confirmación/error.
- [ ] Persistencia verificada en MySQL tras cada operación.
- [ ] Inicio/cierre de sesión y control de acceso según dueño y roles.
- [ ] Estructura ordenada: Views, Templates, URLs y componentes.
- [ ] README.md con instalación, MySQL, migraciones, ejecución y
      credenciales de prueba (demo / demo1234).
- [ ] Usuario de prueba reproducible para el docente.
- [ ] (Equipos) Registro de contribución individual.
- [ ] Anexo de uso de IA (corresponde: se usó en las tres etapas).
- [ ] Ensayo de la demo en vivo (guion del README, 10 pasos) y ensayo de
      la conclusión individual: aporte + dificultad + aprendizaje +
      mejora futura justificada.

---

## B6. Evaluación Sumativa 2 — Parte 1: MySQL + Models + Admin

Sección específica de la entrega anterior. Domina estos puntos además de
B1–B5.

### Conexión MySQL (settings.py)

- `DATABASES['default']`: `ENGINE django.db.backends.mysql` vía
  **mysqlclient**; `NAME/USER/PASSWORD/HOST/PORT` desde **variables de
  entorno** (`DB_NAME`…), `OPTIONS {'charset': 'utf8mb4'}`.
- El `.env` lo carga una función propia (sin python-dotenv) y **no se
  versiona** (`.gitignore`). Si falta `DJANGO_SECRET_KEY` el proyecto no
  arranca: no existe clave insegura por omisión (instrucción 9).
- ¿Por qué utf8mb4 y no utf8? — utf8 de MySQL es 3 bytes y no soporta
  emojis ni algunos caracteres; utf8mb4 sí.
- **¿Por qué `USE_TZ = False`?** — Con `USE_TZ=True` y zona local, el
  admin (`date_hierarchy` y filtro por fecha) genera `CONVERT_TZ()` con
  zonas NOMBRADAS; MySQL recién instalado NO trae las tablas de zonas
  horarias (se cargan a mano con `mysql_tzinfo_to_sql`), así que los
  changelists de Track y Playlist caen con 500 ("Database returned an
  invalid datetime value"). Con `USE_TZ=False` no hay `CONVERT_TZ`, las
  horas son locales de Santiago y el proyecto funciona en cualquier
  MySQL (decisión documentada en `settings.py` y con tests de regresión
  `AdminChangelistConDatosTest`, que renderizan los changelists CON
  datos: con tablas vacías el error no aparece).

### Modelos normalizados

- `Genre`: tabla nueva; `name` único + `slug` único autogenerado en
  `save()`.
- `Track.genre`: **ForeignKey con on_delete=PROTECT** — nunca se borra un
  género que tiene pistas (integridad referencial). related_name=
  'tracks' → `genero.tracks`.
- `Track.slug`: único, `editable=False`, se genera desde el título y se
  des-ambigua con sufijos (-2, -3…).
- `Playlist`: dueño (CASCADE, related_name='playlists'), nombre único
  por usuario (UniqueConstraint owner+name).
- `PlaylistTrack`: **tabla intermedia de la N:M** con `order`
  (PositiveIntegerField). Constraints: pista única por lista y orden
  único por lista.

### Migraciones (¡la parte estrella de la defensa!)

- 0003 crea la tabla `Genre`.
- **0004 es una migración de DATOS** (`RunPython`): recorre los valores
  de los choices de la U1 y crea las filas de Genre; añade la FK
  `genre_nuevo`, re-apunta cada pista existente (¡sin perder datos!),
  genera los slugs, elimina el CharField y renombra la FK. Es
  **reversible** (la función `deshacer` copia el nombre de vuelta).
- 0005 (generada con makemigrations) crea Playlist/PlaylistTrack y hace
  único el slug y obligatorio el género.
- ¿Cómo se probó? — Retrocediendo a 0002, insertando una pista con
  `genre='Ciencia'` (texto) por SQL y volviendo a migrar: la fila quedó
  con FK a `Genre('Ciencia')` y su slug.

### Django Admin (podwave/admin.py)

- 4 ModelAdmin (Genre, Track, Playlist, PlaylistTrack) + inline.
- `list_display` / `list_filter` / `search_fields` en todos; `date_
  hierarchy` en Track y Playlist; `prepopulated_fields` para el slug del
  género; `fieldsets` y `readonly_fields` (slug, fechas) en Track.
- **Pregunta trampa:** ¿por qué no `filter_horizontal` para las pistas de
  una Playlist? — Porque la M2M usa `through=PlaylistTrack` y Django
  lanza **admin.E013**; se usa un **inline** que además permite editar el
  ORDEN de cada pista (algo que filter_horizontal no permite).

### Comando seed_demo

- `python manage.py seed_demo [--password X]` — reemplaza al script de
  la U1. **Idempotente** (get_or_create): ejecutarlo 2 veces no duplica.
- Transforma `GENEROS_SUGERIDOS` + `PISTAS_DEMO` + `LISTAS_DEMO`
  (estructuras de Python de la U1) en registros persistentes → evidencia
  8 de la rúbrica.

### Datos verificados en la entrega (U2-1)

- `manage.py check` → 0 issues · `makemigrations --check` → No changes.
- `migrate` 0001→0005 OK sobre MySQL 8.4 real.
- Seed ×2 idempotente: 8 géneros, 8 pistas (con archivo local), 3 listas,
  8 enlaces N:M.
- **76/76 tests OK** (la BD de pruebas `test_podwave` se crea sola),
  incluidos changelists del admin CON DATOS y CRUD completo por el panel
  (instrucción 7 del instrumento).
- Páginas y panel /admin respondiendo 200 (verificado con sesión real:
  índice, los 4 changelists, alta, edición y borrado).

(Nota de la U2-2: los números actuales del proyecto son 107 tests y la
contraseña de prueba demo/demo1234; ver la sección B7.)

---

## B7. Evaluación Sumativa 3 (U2-2) — CRUD desde el sitio + presentación

Sección específica de la entrega final. Domina estos puntos además de
B1–B6.

### CRUD de listas de reproducción desde el propio sitio (criterio 3, 12 pts)

- La entrega U2-1 gestionaba las listas solo por el Django Admin. En esta
  etapa el CRUD completo vive en el sitio: **crear** (`/playlists/nueva/`),
  **consultar** (índice `/playlists/` y detalle público), **modificar**
  (`/playlists/<pk>/editar/`) y **eliminar** (`/playlists/<pk>/eliminar/`,
  con página de confirmación).
- Además la relación N:M se administra en vivo: **agregar pista** a una
  lista propia desde el detalle de la pista (select filtrado por dueño),
  **quitarla** y **subir/bajar una posición** desde el detalle de la lista.
- Vistas: `PlaylistListView`, `PlaylistDetailView`, `PlaylistCreateView`,
  `PlaylistUpdateView`, `PlaylistDeleteView` (GCBV) + las vistas de función
  `track_add_to_playlist`, `playlist_remove_track` y `playlist_move_track`
  (POST + `@login_required` + `@require_POST`).
- **Pregunta trampa:** ¿por qué el intercambio de órdenes se hace en tres
  pasos? — Por el constraint `orden_unico_por_lista`: si guardaras primero
  la vecina con el orden de esta, MySQL rechazaría la fila duplicada. Se
  libera un hueco temporal (order=0), se mueve la vecina y se cierra.
- `Playlist.siguiente_orden()` asigna el nuevo enlace al final (máximo+1)
  y `renumerar_pistas()` deja los órdenes 1..n tras quitar una pista.

### Mensajes de confirmación y error (criterio 5)

- `SuccessMessageMixin` en los 6 CRUD (crear/editar/eliminar de pistas y
  listas). En Django 5.2 `BaseDeleteView.post()` pasa por `form_valid()`,
  así que el mixin funciona también en DeleteView.
- `MESSAGE_TAGS` (settings.py) alinea las etiquetas de Django con las
  clases de Bootstrap: `error -> danger` (alert-danger).
- El bloque `{% if messages %}` de `base.html` muestra los alert con
  botón de cerrar (dismissible) en TODAS las páginas por herencia.
- Errores de validación: el formulario re-renderiza con los errores y en
  las vistas de función se agregan `messages.error(...)`.

### Control de acceso por propiedad (criterio 6)

- `get_queryset()` de los 4 Update/Delete filtra por dueño: `created_by`
  (pistas) y `owner` (listas). Quien no es dueño recibe **404** (no basta
  con esconder el botón: la vista lo vuelve a verificar en el servidor).
- El superusuario mantiene acceso total (rol definido en el proyecto).
- `PlaylistCreateView.form_valid()` fija el `owner` desde la **sesión**,
  nunca desde el formulario: nadie crea listas a nombre de otro.
- `AddToPlaylistForm` inyecta el queryset con las listas propias del
  usuario: una lista ajena no pasa la validación del servidor.
- Los botones de gestión se renderizan solo para el dueño
  (`user.is_superuser or track.created_by == user`, `es_dueno` en el
  contexto del detalle de la lista).

### Usuario de prueba y reproducibilidad (criterio 8 / instrucción 9)

- `seed_demo` fija el usuario **demo / demo1234** en cada corrida
  (determinista, documentado en el README con tabla de acceso).
- Es una credencial de PRUEBA exclusiva para la evaluación, no una clave
  personal; las credenciales reales siguen solo en variables de entorno.
- Demostrar: `python manage.py seed_demo` dos veces no duplica datos
  (idempotente con get_or_create) y siempre restaura demo/demo1234.

### Datos verificados en esta entrega

- `manage.py check` → 0 issues · `makemigrations --check` → No changes
  (no hubo cambios de esquema: solo código, plantillas y tests).
- **107/107 tests OK** (76 heredados + 31 nuevos: CRUD de listas,
  add/remove/move, propiedad 404, mensajes y restauración de demo).
- Recorrida funcional completa con sesión demo: crear lista → agregar
  pista → reordenar → quitar → editar → eliminar → cerrar sesión.

### Presentación y demo (Rúbrica B — 30% de la nota)

La presentación tiene un componente GRUPAL (10 pts: G1 problemática y
  solución, G2 demo funcional del CRUD, G3 organización y tiempo) y otro
  INDIVIDUAL (20 pts: I1 dominio técnico, I2 voz, I3 postura, I4
  autonomía frente a los apuntes, I5 demostración individual + conclusión).

**Guion sugerido (reparto equilibrado, en vivo y con el sistema corriendo):**

1. **G1 (grupo):** problemática, objetivo, usuarios/roles y alcance, y cómo
   la solución implementada los cubre (README, sección "Problemática…").
2. **G2 (grupo, por turnos):** demo en vivo siguiendo el guion del README:
   login demo → biblioteca → crear pista → editar → crear lista → agregar
   pista a la lista → reordenar → quitar → eliminar lista (las pistas
   sobreviven) → cerrar sesión. Capturas y videos NO reemplazan la demo.
3. **G3:** intro → demo → conclusiones individuales, dentro del tiempo.
4. **I5 (cada uno):** demostrar UNA funcionalidad propio + conclusión con
   los 4 elementos exigidos: **aporte concreto, una dificultad técnica,
   aprendizajes adquiridos y una mejora futura JUSTIFICADA**.
   Ideas de mejora: API REST (viene en U3), paginación de listas,
   compartir listas públicas con URL fija, buscar dentro de una lista.
5. **I4:** NO leer las diapositivas: el instrumento avisa que la lectura
   frecuente LIMITA el puntaje del criterio a 2 de 4. Palabras clave solo.

**Reparto de la demo (equipo de 2, ajustable):**

- Integrante 1 (Manzano): login/logout + CRUD de PISTAS en vivo + su
  conclusión individual.
- Integrante 2 (Vilca): CRUD de LISTAS en vivo (crear → agregar →
  reordenar → quitar → eliminar) + su conclusión individual.
- La explicación de problemática/objetivo (G1) se reparte entre ambos.
