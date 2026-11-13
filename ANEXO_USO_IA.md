# Anexo — Uso de herramientas de inteligencia artificial

> La evaluación exige como evidencia mínima un anexo de uso de IA
> ("únicamente cuando corresponda") que indique herramienta, prompts o
> instrucciones principales, tipo de apoyo recibido y modificaciones o
> correcciones realizadas. El uso de IA no reemplaza la responsabilidad
> sobre el código entregado: en la defensa técnica deberás poder explicar
> y modificar cualquier fragmento.

## 1. Herramienta utilizada

- **Herramienta:** GLM (asistente Super Z) de Z.ai, vía chat web.
- **Periodo de uso:** Unidad 1 (septiembre de 2026), Unidad 2 parte 1
  (octubre de 2026) y Unidad 2 parte 2 / Evaluación Sumativa 3
  (noviembre de 2026), en sesiones de trabajo del proyecto.
- **Modalidad:** chat conversacional con acceso al código del proyecto.

## 2. Prompts o instrucciones principales (resumen)

1. "Analiza el ZIP de la Unidad 1, el instrumento de la Evaluación
   Sumativa 2 (parte 1) y la rúbrica; entrega la transformación completa
   del proyecto a MySQL + Models + migraciones + Django Admin, con todo el
   código archivo por archivo y sin teoría."
2. "Conecta el proyecto a MySQL usando variables de entorno para todas
   las credenciales: nada de contraseñas hardcodeadas ni claves
   inseguras por omisión."
3. "Normaliza el género: los choices del CharField de la Unidad 1 deben
   pasar a una tabla Genre con ForeignKey, sin perder los datos que ya
   existen."
4. "Agrega playlists con relación muchos-a-muchos a Track usando una
   tabla intermedia con campo orden."
5. "Registra los cuatro modelos en el Django Admin con todas las
   opciones: list_display, list_filter, search_fields, prepopulated,
   date_hierarchy, fieldsets y el manejo de la N:M."
6. "Convierte el seed de la Unidad 1 en un comando de gestión
   idempotente y ajusta los tests de la Unidad 1 que chocaban con los
   cambios."

U2-2 / Evaluación Sumativa 3:

7. "Analiza los archivos: el ZIP de la entrega U2-1 y el PDF del
   instrumento de la Evaluación Sumativa 3; identifica las brechas contra
   la Rúbrica A y entrega un análisis criterio por criterio."
8. "Implementa los cambios" — sobre el plan de 5 puntos acordado:
   CRUD completo de Playlist desde el sitio, mensajes de
   confirmación/error con el framework messages, control de acceso por
   propiedad (dueño), usuario de prueba determinista documentado en el
   README y actualización de la documentación de la entrega.

## 3. Tipo de apoyo recibido

- Análisis del proyecto de la Unidad 1 (apps, modelo Track, plantillas,
  tests) y del instrumento + rúbrica de la U2-1.
- Configuración de la conexión MySQL en `settings.py` con lectura de
  variables de entorno desde un `.env` sin dependencias externas.
- Redacción de los modelos normalizados (`Genre`, `Track` con FK PROTECT
  y slug, `Playlist`, `PlaylistTrack` con `order` y constraints) y de las
  migraciones 0003–0005, incluida la migración de datos 0004.
- Registro completo de los modelos en el Django Admin (incluida la
  decisión de usar inline en lugar de `filter_horizontal` por el error
  admin.E013 de las relaciones through).
- Conversión del script `seed_demo.py` de la Unidad 1 en el comando de
  gestión `podwave/management/commands/seed_demo.py`.
- Adaptación de la suite de tests a la base MySQL y ampliación a 72
  pruebas; documentación (README, este anexo, guía de defensa).

U2-2 / Evaluación Sumativa 3:

- Análisis de brechas entre la entrega U2-1 y la Rúbrica A del
  instrumento U2-2 (criterio por criterio, con puntajes en juego).
- Código del CRUD de listas desde el sitio: `PlaylistForm` y
  `AddToPlaylistForm`, vistas genéricas de Playlist, vistas de función
  para agregar/quitar/reordenar pistas y 4 plantillas `playlist_*.html`
  con el lenguaje visual existente.
- Utilidades de orden en `models.py` (`mover`, `siguiente_orden`,
  `renumerar_pistas`) con intercambio en tres pasos para respetar el
  constraint `orden_unico_por_lista`.
- Integración del framework `messages` (`SuccessMessageMixin`,
  `MESSAGE_TAGS`, bloque de alertas en `base.html`).
- Filtro de propiedad por dueño en los `get_queryset()` de los
  Update/Delete y botones condicionales en las plantillas.
- Cambio de `seed_demo` a credencial de prueba determinista
  (demo/demo1234) y reescritura del README para esta etapa.
- 31 tests nuevos (107 en total) y verificación completa de la entrega
  (check, migraciones, seed idempotente, suite completa).

## 4. Modificaciones o correcciones realizadas por el estudiante

- Ejecución del proyecto en local sobre MySQL 8: creación de la base
  `podwave` (utf8mb4), del usuario y de sus privilegios.
- Revisión del código generado: verificación de que ninguna credencial
  quedó en el código (instrucción 9) y de que el `.env` está ignorado por
  git.
- Pruebas manuales de la app: navegación, filtro por género, subida de
  audio, reproducción y gestión de pistas y listas en /admin/.
- Corrección propia: al crear géneros de prueba con acentos duplicados
  ("Musica" vs "Música") se detectó que la intercalación de MySQL
  (utf8mb4, insensible a acentos) rechaza la segunda fila por el índice
  único; se documentó el comportamiento y se ajustó el test
  correspondiente (`test_colision_de_acentos_mysql`).
- Aportes propios: definición de los nombres de las listas de
  reproducción de demostración (LISTAS_DEMO) y revisión de los textos de
  las plantillas.

U2-2 / Evaluación Sumativa 3:

- Revisión del análisis de brechas contra la Rúbrica A antes de aceptar
  el plan de trabajo (se priorizó por puntaje: primero el CRUD de listas,
  12 pts; luego mensajes y control de acceso, 4 pts cada uno).
- Pruebas manuales del CRUD de listas desde el sitio: crear, agregar,
  reordenar, quitar, editar y eliminar listas con datos reales en MySQL,
  verificando que las pistas sobreviven a la eliminación de la lista.
- Revisión del control de acceso: intentos de editar/eliminar pistas y
  listas ajenas por URL directa (verificada la respuesta 404).
- Aportes propios: decisión de mantener la consulta de listas pública
  (coherente con el rol "oyentes" del proyecto) reservando la gestión
  al dueño, y elección del guion de demostración del README (orden de
  las 10 pruebas).

## 5. Declaración

Declaro que revisé el código entregado, que entiendo su funcionamiento y
que puedo explicarlo y modificarlo en la defensa técnica.

- Nombre: [completar al firmar]
- Fecha: [completar al firmar]
- Firma: ______________________
