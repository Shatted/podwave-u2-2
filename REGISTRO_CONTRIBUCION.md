# Registro de contribución — Evaluación Sumativa 3 (U2-2)

**Proyecto:** PodWave (Django 5.2.18 + MySQL 8)
**Integrantes:** Manzano y Vilca
**Unidad:** U2 — Programación Back End · Parte 2 (CRUD completo desde el
sitio web, sesiones, control de acceso y seguridad básica)

> Registro honesto de la participación de cada integrante durante la
> elaboración de esta entrega. Las horas son estimadas. Completar los
> nombres de pila antes de la entrega final.

## Distribución del trabajo de ESTA etapa (U2-2)

| Integrante | Responsabilidad principal | Evidencias |
|---|---|---|
| **[Nombre] Manzano** | Seguridad y acceso: control de propiedad en pistas y listas (`get_queryset()` por dueño en `views.py`), verificación doble (plantilla + servidor), `MESSAGE_TAGS`, usuario de prueba determinista `demo/demo1234` en `seed_demo.py`, README con credenciales de evaluación | Commits de `views.py` (get_queryset por dueño), `seed_demo.py`, `settings.py`, `README.md` |
| **[Nombre] Vilca** | CRUD de listas desde el sitio: `PlaylistForm`/`AddToPlaylistForm` (`forms.py`), vistas y URLs de playlists, utilidades de orden en `models.py` (`mover`, `siguiente_orden`, `renumerar_pistas`), plantillas `playlist_*.html` (4 nuevas) y ajustes de `track_detail`/`track_list`/`base.html` | Commits de `forms.py`, `views.py` (Playlist*), `urls.py`, `models.py`, plantillas nuevas |
| **Ambos** | Mensajes de confirmación/error (`SuccessMessageMixin` + bloque en `base.html`), tests nuevos (107 en total), verificación final (check 0 issues, migrate, seed idempotente, suite completa OK), `GUIA_DEFENSA.md` y `ANEXO_USO_IA.md` | Sesiones de trabajo conjunto; revisión cruzada del código del otro |

## Bitácora resumida de esta etapa

1. **Análisis del instrumento U2-2 y de la Rúbrica A** (conjunto): se
   identificaron los 8 criterios y las 12 evidencias mínimas; el análisis
   de brechas sobre la entrega U2-1 marcó tres puntos débiles: CRUD de
   listas desde el sitio, mensajes de retroalimentación y control de
   acceso por propiedad.
2. **CRUD de Playlist desde el sitio** (Vilca): ListView/DetailView
   públicos, Create/Update/Delete con confirmación; 4 plantillas nuevas
   con el mismo lenguaje visual (cards oscuras, botones accent/ghost).
3. **Gestión de pistas dentro de la lista** (Vilca): agregar desde el
   detalle de la pista (select con las listas propias), quitar con
   renumeración automática 1..n y subir/bajar una posición con
   intercambio seguro de órdenes (tres pasos, para no violar el
   constraint `orden_unico_por_lista`).
4. **Control de acceso por propiedad** (Manzano): `get_queryset()`
   filtrando por `created_by`/`owner` en los 4 Update/Delete; quien no
   es dueño recibe 404 (probado con tests); el superusuario conserva
   acceso total, coherente con el rol del proyecto.
5. **Mensajes de confirmación/error** (conjunto):
   `SuccessMessageMixin` en los 6 CRUD (en Django 5.2 DeleteView pasa
   por `form_valid`, documentado en el código), `MESSAGE_TAGS` alineado
   con Bootstrap y bloque de alertas en `base.html`.
6. **Usuario de prueba determinista** (Manzano): `seed_demo` fija
   `demo / demo1234` en cada corrida (credencial de evaluación, no un
   secreto); README con tabla de acceso para el docente.
7. **Tests** (conjunto): 31 pruebas nuevas (107 en total): CRUD de
   listas, agregar/quitar/reordenar, propiedad (404 a no dueños),
   mensajes y restauración de la clave demo.
8. **Verificación final** (conjunto): `check` 0 issues,
   `makemigrations --check` sin cambios (no hubo cambios de esquema),
   migrate 0001→0005, seed ×2 idempotente con demo/demo1234, 107/107
   tests OK y recorrida funcional completa de todas las páginas.

## Declaración

Ambos integrantes revisamos el código entregado, entendemos su
funcionamiento y estamos en condiciones de explicarlo y modificarlo en la
defensa técnica y la demostración funcional.

- Firma Integrante 1 (Manzano): ______________________
- Firma Integrante 2 (Vilca): ______________________
- Fecha: ______________________
