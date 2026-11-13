"""
Pruebas de la app PodWave — Unidad 2 (MySQL) + Evaluación Sumativa 3.

Verifican el cumplimiento de los criterios de la Unidad 2:
  - 2.1.1 Configura la conexión a una base de datos (settings MySQL,
    migraciones, ORM).
  - 2.1.2 Utiliza el administrador de Django (registro de los 4 modelos,
    configuración y CRUD completo desde el panel).
  - 2.1.3 Codifica funciones que realicen operaciones CRUD sobre una base
    de datos (pistas Y listas, todo desde el sitio web en la parte 2).
  - Aprendizaje esperado U2 (heredado de la U1): usuarios, roles,
    sesiones de validación de acceso (login requerido + control de
    propiedad por dueño, U2-2).
  - Models normalizados: Genre, Track (FK PROTECT + slug), Playlist y
    PlaylistTrack (N:M con order y constraints).
  - Comando seed_demo: datos simulados de la U1 -> registros persistentes
    y usuario de prueba demo / demo1234.

Unidad 2, parte 2 (Evaluación Sumativa 3) — pruebas añadidas:
  - CRUD completo de Playlist desde el sitio (crear/consultar/modificar/
    eliminar, sin Django Admin).
  - Gestión de pistas dentro de la lista: agregar / quitar / reordenar.
  - Control de acceso por propiedad (404 para quien no es dueño).
  - Mensajes de confirmación/error del framework messages.

Ajustes de tests de la Unidad 1 (justificación de una línea):
  - Los tests que creaban Track con genre="texto" ahora crean primero la
    fila Genre (el género pasó de CharField con choices a ForeignKey).
  - El filtro por género usa ?genero=<slug> (catálogo normalizado).

Nota MySQL: la intercalación por omisión (utf8mb4, *_ai_ci) es INSENSIBLE
A ACENTOS, por lo que "Musica" colisiona con "Música" en los índices
únicos; hay un test que documenta ese comportamiento.

Ejecutar con:  python manage.py test
"""
from django.contrib import admin as django_admin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from .datos_simulados import (
    GENEROS_SUGERIDOS, LISTAS_DEMO, PISTAS_DEMO,
    pista_aleatoria, pistas_de_genero, resumen_por_genero,
)
from .forms import TrackForm
from .models import Genre, Playlist, PlaylistTrack, Track


def crear_genero(nombre='Tecnología'):
    """Crea (o recupera) un género del catálogo para los tests."""
    genre, _creado = Genre.objects.get_or_create(name=nombre)
    if not genre.slug:
        genre.save()
    return genre


def track_data(genero, **extras):
    """Datos válidos de pista: recibe la INSTANCIA de Genre (FK, Unidad 2)."""
    base = {
        'title': 'Episodio de prueba',
        'artist': 'Artista de prueba',
        'genre': genero.pk,
        'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
    }
    base.update(extras)
    return base


def archivo_audio(nombre='prueba.mp3'):
    """Archivo de audio simulado para las pruebas de subida."""
    return SimpleUploadedFile(nombre, b'datos simulados de audio mp3')


class DatosSimuladosTest(TestCase):
    """Pruebas de las estructuras de Python de la Unidad 1
    (criterio 1.1.1/1.1.2: variables, operaciones, decisiones, iteraciones)."""

    def test_pistas_demo_es_lista_de_diccionarios(self):
        self.assertIsInstance(PISTAS_DEMO, list)
        for pista in PISTAS_DEMO:
            self.assertIsInstance(pista, dict)
            for clave in ('title', 'artist', 'genre', 'filename', 'url'):
                self.assertIn(clave, pista)

    def test_generos_sugeridos_es_lista_de_tuplas(self):
        self.assertIsInstance(GENEROS_SUGERIDOS[0], tuple)
        self.assertEqual(GENEROS_SUGERIDOS[0][0], GENEROS_SUGERIDOS[0][1])

    def test_listas_demo_referencian_pistas_reales(self):
        """Unidad 2: cada lista de LISTAS_DEMO usa títulos de PISTAS_DEMO."""
        titulos = {p['title'] for p in PISTAS_DEMO}
        for lista in LISTAS_DEMO:
            self.assertIn('name', lista)
            self.assertIn('tracks', lista)
            for title in lista['tracks']:
                self.assertIn(title, titulos)

    def test_resumen_por_genero_cuenta_y_ordena(self):
        pistas = [
            {'genre': 'Música'}, {'genre': 'Música'}, {'genre': 'Ciencia'},
        ]
        resumen = resumen_por_genero(pistas)
        self.assertEqual(resumen[0], ('Música', 2))   # primero el más repetido
        self.assertEqual(resumen[1], ('Ciencia', 1))

    def test_resumen_por_genero_vacio(self):
        self.assertEqual(resumen_por_genero([]), [])

    def test_pista_aleatoria_maneja_lista_vacia(self):
        """Manejo de excepciones: lista vacía no lanza error al usuario."""
        resultado = pista_aleatoria([])
        self.assertEqual(resultado['title'], 'Sin pistas disponibles')

    def test_pistas_de_genero_filtra(self):
        filtradas = pistas_de_genero(PISTAS_DEMO, 'música')  # insensible a mayúsculas
        self.assertTrue(filtradas)
        self.assertTrue(all(p['genre'] == 'Música' for p in filtradas))

    def test_pistas_de_genero_sin_genero_devuelve_todas(self):
        self.assertEqual(len(pistas_de_genero(PISTAS_DEMO, '')), len(PISTAS_DEMO))


class GenreModelTest(TestCase):
    """Pruebas del catálogo normalizado de géneros (Unidad 2).

    Nota: la migración de datos 0004 ya crea los 8 géneros del catálogo
    de la Unidad 1 en la BD de pruebas, por eso estos tests usan nombres
    FUERA del catálogo (Filosofía, Arte, Gastronomía…).
    """

    def test_creacion_y_str(self):
        genre = Genre.objects.create(name='Filosofía')
        self.assertEqual(str(genre), 'Filosofía')

    def test_slug_autogenerado_desde_el_nombre(self):
        genre = Genre.objects.create(name='Filosofía')
        # save() del modelo completa el slug aunque venga vacío.
        self.assertEqual(genre.slug, 'filosofia')

    def test_orden_alfabetico(self):
        Genre.objects.create(name='Zetateca')
        Genre.objects.create(name='Arte')
        self.assertEqual(
            list(Genre.objects.filter(name__in=['Zetateca', 'Arte'])
                              .values_list('name', flat=True)),
            ['Arte', 'Zetateca'])

    def test_nombre_unico(self):
        Genre.objects.create(name='Filosofía')
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Genre.objects.create(name='Filosofía')

    def test_colision_de_acentos_mysql(self):
        """MySQL (utf8mb4 *_ai_ci) compara SIN acentos: "Gastronomia"
        colisiona con "Gastronomía" en el índice único de name. Se
        documenta para la defensa: es comportamiento del motor, no un
        bug del modelo."""
        Genre.objects.create(name='Gastronomía')
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Genre.objects.create(name='Gastronomia')


class TrackModelTest(TestCase):
    """Pruebas del modelo Track (criterio 2.1.1: persistencia en MySQL vía ORM)."""

    def setUp(self):
        self.genero = crear_genero('Tecnología')

    def test_creacion_de_pista(self):
        track = Track.objects.create(
            title='Episodio de prueba', artist='Artista de prueba',
            genre=self.genero,
            url='https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3')
        self.assertEqual(Track.objects.count(), 1)
        self.assertEqual(str(track), 'Episodio de prueba — Artista de prueba')

    def test_orden_mas_reciente_primero(self):
        first = Track.objects.create(title='Primera', artist='A',
                                     genre=self.genero, url='https://a.com/1.mp3')
        second = Track.objects.create(title='Segunda', artist='B',
                                      genre=self.genero, url='https://a.com/2.mp3')
        self.assertEqual(Track.objects.first(), second)
        self.assertNotEqual(Track.objects.first(), first)

    def test_get_absolute_url(self):
        track = Track.objects.create(
            title='Episodio de prueba', artist='Artista de prueba',
            genre=self.genero, url='https://a.com/1.mp3')
        self.assertEqual(
            track.get_absolute_url(), reverse('track_detail', kwargs={'pk': track.pk}))

    def test_audio_url_prefiere_archivo_local(self):
        """Si hay archivo subido, el reproductor usa ese (no la URL)."""
        track = Track.objects.create(
            title='Local', artist='A', genre=self.genero, url='https://a.com/1.mp3')
        track.audio_file.name = 'audio/mi-cancion.mp3'
        self.assertEqual(track.audio_url, '/media/audio/mi-cancion.mp3')
        self.assertTrue(track.is_local)

    def test_audio_url_con_enlace_externo(self):
        url = 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3'
        track = Track.objects.create(
            title='Externa', artist='A', genre=self.genero, url=url)
        self.assertEqual(track.audio_url, url)
        self.assertFalse(track.is_local)

    def test_slug_autogenerado_desde_el_titulo(self):
        track = Track.objects.create(
            title='Historia de la Computación — Ep. 3', artist='X',
            genre=self.genero, url='https://a.com/1.mp3')
        self.assertEqual(track.slug, 'historia-de-la-computacion-ep-3')

    def test_slug_unico_con_titulos_repetidos(self):
        """Títulos repetidos generan slugs numerados: -2, -3…"""
        uno = Track.objects.create(title='Repetida', artist='A',
                                   genre=self.genero, url='https://a.com/1.mp3')
        dos = Track.objects.create(title='Repetida', artist='B',
                                   genre=self.genero, url='https://a.com/2.mp3')
        self.assertEqual(uno.slug, 'repetida')
        self.assertEqual(dos.slug, 'repetida-2')

    def test_genero_protegido_con_pistas(self):
        """on_delete=PROTECT: no se puede borrar un género con pistas."""
        Track.objects.create(title='Pista', artist='A',
                             genre=self.genero, url='https://a.com/1.mp3')
        with self.assertRaises(ProtectedError):
            self.genero.delete()
        # El género sigue existiendo.
        self.assertTrue(Genre.objects.filter(pk=self.genero.pk).exists())

    def test_validacion_exige_fuente_de_audio(self):
        """clean() del modelo: archivo o URL, al menos una."""
        track = Track(title='Sin fuente', artist='A', genre=self.genero)
        with self.assertRaises(ValidationError):
            track.full_clean()

    def test_genero_accesible_desde_la_pista(self):
        """La FK normalizada: pista.genre es una fila de Genre."""
        track = Track.objects.create(title='FK', artist='A',
                                     genre=self.genero, url='https://a.com/1.mp3')
        self.assertEqual(track.genre.name, 'Tecnología')
        self.assertEqual(track.genre.tracks.count(), 1)  # related_name


class PlaylistModelTest(TestCase):
    """Pruebas del modelo Playlist (N:M a través de PlaylistTrack)."""

    def setUp(self):
        self.user = User.objects.create_user(username='lista', password='clave12345')
        self.genero = crear_genero('Música')

    def _pista(self, titulo):
        return Track.objects.create(
            title=titulo, artist='A', genre=self.genero, url='https://a.com/x.mp3')

    def test_creacion_y_str(self):
        playlist = Playlist.objects.create(
            owner=self.user, name='Mis favoritas')
        self.assertEqual(str(playlist), 'Mis favoritas')

    def test_nombre_unico_por_usuario(self):
        Playlist.objects.create(owner=self.user, name='Favoritas')
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Playlist.objects.create(owner=self.user, name='Favoritas')

    def test_cascade_al_borrar_al_dueno(self):
        """on_delete=CASCADE: sin dueño no existe la lista."""
        Playlist.objects.create(owner=self.user, name='Favoritas')
        self.user.delete()
        self.assertEqual(Playlist.objects.count(), 0)

    def test_relacion_usuario_playlists(self):
        """related_name='playlists': usuario.playlists -> sus listas."""
        Playlist.objects.create(owner=self.user, name='Favoritas')
        self.assertEqual(self.user.playlists.count(), 1)

    def test_m2m_through_cuenta_pistas(self):
        """La M2M tracks se lee A TRAVÉS de la tabla intermedia."""
        playlist = Playlist.objects.create(owner=self.user, name='Favoritas')
        t1, t2 = self._pista('Uno'), self._pista('Dos')
        PlaylistTrack.objects.create(playlist=playlist, track=t1, order=1)
        PlaylistTrack.objects.create(playlist=playlist, track=t2, order=2)
        self.assertEqual(playlist.tracks.count(), 2)
        # Y desde el lado de la pista (related_name='listas').
        self.assertEqual(t1.listas.count(), 1)


class PlaylistTrackModelTest(TestCase):
    """Pruebas de la tabla intermedia N:M (con campo order)."""

    def setUp(self):
        self.user = User.objects.create_user(username='pt', password='clave12345')
        self.genero = crear_genero('Historia')
        self.playlist = Playlist.objects.create(owner=self.user, name='Historia')
        self.t1 = Track.objects.create(
            title='Batallas', artist='A', genre=self.genero, url='https://a.com/1.mp3')
        self.t2 = Track.objects.create(
            title='Imperios', artist='B', genre=self.genero, url='https://a.com/2.mp3')

    def test_creacion_y_str(self):
        pt = PlaylistTrack.objects.create(
            playlist=self.playlist, track=self.t1, order=1)
        self.assertEqual(str(pt), '1. Batallas')

    def test_orden_por_defecto(self):
        pt = PlaylistTrack.objects.create(playlist=self.playlist, track=self.t1)
        self.assertEqual(pt.order, 1)

    def test_pista_unica_por_lista(self):
        """La misma pista no se repite dentro de una lista (constraint)."""
        PlaylistTrack.objects.create(playlist=self.playlist, track=self.t1, order=1)
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                PlaylistTrack.objects.create(
                    playlist=self.playlist, track=self.t1, order=2)

    def test_orden_unico_por_lista(self):
        """No hay dos pistas en la misma posición (constraint)."""
        PlaylistTrack.objects.create(playlist=self.playlist, track=self.t1, order=1)
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                PlaylistTrack.objects.create(
                    playlist=self.playlist, track=self.t2, order=1)

    def test_ordering_por_orden(self):
        PlaylistTrack.objects.create(playlist=self.playlist, track=self.t1, order=2)
        PlaylistTrack.objects.create(playlist=self.playlist, track=self.t2, order=1)
        self.assertEqual(
            list(self.playlist.pistas.values_list('track__title', flat=True)),
            ['Imperios', 'Batallas'])

    def test_cascade_al_borrar_pista(self):
        """Al borrar la pista se borra su fila intermedia, no la lista."""
        PlaylistTrack.objects.create(playlist=self.playlist, track=self.t1, order=1)
        self.t1.delete()
        self.assertEqual(PlaylistTrack.objects.count(), 0)
        self.assertTrue(
            Playlist.objects.filter(pk=self.playlist.pk).exists())


class TrackFormTest(TestCase):
    """Pruebas de validación del formulario (equivalentes a validators.js)."""

    def setUp(self):
        self.genero = crear_genero('Tecnología')

    def test_datos_validos(self):
        form = TrackForm(data=track_data(self.genero))
        self.assertTrue(form.is_valid(), form.errors)

    def test_titulo_vacio_rechazado(self):
        form = TrackForm(data=track_data(self.genero, title=''))
        self.assertFalse(form.is_valid())

    def test_titulo_largo_rechazado(self):
        form = TrackForm(data=track_data(self.genero, title='x' * 121))
        self.assertFalse(form.is_valid())

    def test_url_javascript_rechazada(self):
        form = TrackForm(data=track_data(self.genero, url='javascript:alert(1)'))
        self.assertFalse(form.is_valid())

    def test_url_ftp_rechazada_por_validacion_custom(self):
        """clean_url solo permite http/https (como isValidAudioUrl en React)."""
        form = TrackForm(data=track_data(self.genero, url='ftp://ejemplo.com/audio.mp3'))
        self.assertFalse(form.is_valid())
        self.assertIn('La URL no es válida', form.errors['url'][0])

    def test_genero_invalido_rechazado(self):
        """Unidad 2: el select espera la pk de un Genre existente."""
        form = TrackForm(data=track_data(self.genero, genre='Género inexistente'))
        self.assertFalse(form.is_valid())
        self.assertIn('genre', form.errors)

    def test_genero_vacio_rechazado(self):
        form = TrackForm(data=track_data(self.genero, genre=''))
        self.assertFalse(form.is_valid())
        self.assertIn('genre', form.errors)

    # --- Fuente del audio: archivo subido y/o URL ---

    def test_archivo_sin_url_es_valido(self):
        """Subir solo el archivo (sin URL) también es una pista válida."""
        form = TrackForm(
            data={'title': 'Mi canción', 'artist': 'Yo',
                  'genre': crear_genero('Música').pk, 'url': ''},
            files={'audio_file': archivo_audio()})
        self.assertTrue(form.is_valid(), form.errors)

    def test_sin_archivo_y_sin_url_rechazado(self):
        """Al menos una fuente de audio es obligatoria."""
        form = TrackForm(data={
            'title': 'Mi canción', 'artist': 'Yo',
            'genre': crear_genero('Música').pk, 'url': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('Sube un archivo de audio o escribe una URL', str(form.non_field_errors()))

    def test_extension_no_audio_rechazada(self):
        form = TrackForm(
            data={'title': 'Mi canción', 'artist': 'Yo',
                  'genre': crear_genero('Música').pk, 'url': ''},
            files={'audio_file': archivo_audio('virus.exe')})
        self.assertFalse(form.is_valid())
        self.assertIn('audio_file', form.errors)


class TrackViewsTest(TestCase):
    """Pruebas de vistas: CRUD y sesiones (criterios 2.1.1 y 2.1.3)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='tester', password='clave12345')
        self.genero = crear_genero('Tecnología')
        self.genero_musica = crear_genero('Música')
        self.track = Track.objects.create(
            title='Episodio de prueba', artist='Artista de prueba',
            genre=self.genero, created_by=self.user,
            url='https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3')

    # --- Lectura pública ---

    def test_lista_publica(self):
        response = self.client.get(reverse('track_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Episodio de prueba')

    def test_filtro_por_genero(self):
        """Unidad 2: el parámetro ?genero=<slug> filtra por el catálogo."""
        Track.objects.create(
            title='Otra pista', artist='Otro', genre=self.genero_musica,
            url='https://a.com/m.mp3')
        response = self.client.get(
            reverse('track_list'), {'genero': self.genero_musica.slug})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Otra pista')
        self.assertNotContains(response, 'Episodio de prueba')
        # El filtro y el resumen llegan al template mediante el contexto.
        self.assertIn('generos', response.context)
        self.assertEqual(response.context['genero_activo'], self.genero_musica.slug)
        self.assertTrue(response.context['resumen_generos'])

    def test_detalle_publico(self):
        response = self.client.get(
            reverse('track_detail', kwargs={'pk': self.track.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Artista de prueba')

    # --- Crear requiere sesión iniciada (usuarios y roles del proyecto) ---

    def test_crear_sin_sesion_redirige_a_login(self):
        response = self.client.get(reverse('track_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_crear_con_sesion(self):
        self.client.login(username='tester', password='clave12345')
        response = self.client.post(reverse('track_create'),
                                    track_data(self.genero,
                                               title='Pista nueva desde el test'))
        # 302: redirige al detalle de la pista creada (get_absolute_url).
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Track.objects.count(), 2)
        nueva = Track.objects.get(title='Pista nueva desde el test')
        self.assertEqual(nueva.created_by, self.user)
        self.assertEqual(nueva.genre, self.genero)

    def test_crear_subiendo_archivo_de_audio(self):
        """El CreateView acepta multipart/form-data y guarda media/audio/."""
        import shutil
        import tempfile
        tmp = tempfile.mkdtemp()
        try:
            with self.settings(MEDIA_ROOT=tmp):
                self.client.login(username='tester', password='clave12345')
                response = self.client.post(
                    reverse('track_create'),
                    {'title': 'Mi canción subida', 'artist': 'Yo',
                     'genre': crear_genero('Música').pk, 'url': '',
                     'audio_file': archivo_audio('mi-cancion.mp3')})
                self.assertEqual(response.status_code, 302)
                track = Track.objects.get(title='Mi canción subida')
                self.assertTrue(track.audio_file)
                self.assertTrue(track.audio_file.name.startswith('audio/'))
                self.assertTrue(track.is_local)
                self.assertEqual(track.audio_url, track.audio_file.url)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # --- Actualizar requiere sesión ---

    def test_editar_sin_sesion_redirige_a_login(self):
        response = self.client.get(
            reverse('track_update', kwargs={'pk': self.track.pk}))
        self.assertEqual(response.status_code, 302)

    def test_editar_con_sesion(self):
        self.client.login(username='tester', password='clave12345')
        response = self.client.post(
            reverse('track_update', kwargs={'pk': self.track.pk}),
            track_data(self.genero, title='Título editado'))
        self.assertEqual(response.status_code, 302)
        self.track.refresh_from_db()
        self.assertEqual(self.track.title, 'Título editado')

    # --- Eliminar requiere sesión ---

    def test_eliminar_sin_sesion_redirige_a_login(self):
        response = self.client.get(
            reverse('track_delete', kwargs={'pk': self.track.pk}))
        self.assertEqual(response.status_code, 302)

    def test_eliminar_con_sesion(self):
        self.client.login(username='tester', password='clave12345')
        response = self.client.post(
            reverse('track_delete', kwargs={'pk': self.track.pk}))
        self.assertEqual(response.status_code, 302)  # redirect a la biblioteca
        self.assertEqual(Track.objects.count(), 0)


class SessionFlowTest(TestCase):
    """Pruebas del ciclo login/logout (usuarios, roles y sesiones,
    aprendizaje esperado de la Unidad 2; conservadas de la Unidad 1).

    Desde Django 5, LogoutView SOLO acepta POST: un enlace GET simple
    (p.ej. <a href="/accounts/logout/">) devuelve 405 Method Not Allowed.
    Por eso la plantilla base.html usa un <form method="post">.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='tester', password='clave12345')

    def test_login_correcto_redirige_a_biblioteca(self):
        response = self.client.post('/accounts/login/', {
            'username': 'tester',
            'password': 'clave12345',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('track_list'))

    def test_logout_por_post_cierra_la_sesion(self):
        self.client.login(username='tester', password='clave12345')
        response = self.client.post(reverse('logout'))
        # 302 al home (LOGOUT_REDIRECT_URL) y la sesión queda cerrada.
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('home'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_por_get_rechazado_405(self):
        """Django 5 rechaza el logout por GET (405), como documenta el error."""
        self.client.login(username='tester', password='clave12345')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 405)
        # La sesión sigue activa: el GET no cerró nada.
        self.assertIn('_auth_user_id', self.client.session)

    def test_tras_logout_las_paginas_protegidas_piden_login(self):
        self.client.login(username='tester', password='clave12345')
        self.client.post(reverse('logout'))
        response = self.client.get(reverse('track_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])


class AdminConfigTest(TestCase):
    """Pruebas del registro de los 4 modelos en el Django Admin (U2-1)."""

    def test_encabezados_personalizados(self):
        self.assertEqual(django_admin.site.site_header, 'Administración PodWave')
        self.assertEqual(django_admin.site.site_title, 'PodWave Admin')

    def test_cuatro_modelos_registrados(self):
        for modelo in (Genre, Track, Playlist, PlaylistTrack):
            self.assertIn(modelo, django_admin.site._registry)

    def test_track_list_display(self):
        admin_track = django_admin.site._registry[Track]
        for campo in ('title', 'artist', 'genre', 'created_by', 'created_at'):
            self.assertIn(campo, admin_track.list_display)

    def test_track_filtros_y_busqueda(self):
        admin_track = django_admin.site._registry[Track]
        self.assertIn('genre', admin_track.list_filter)
        self.assertIn('created_at', admin_track.list_filter)
        self.assertIn('title', admin_track.search_fields)
        self.assertIn('genre__name', admin_track.search_fields)

    def test_track_date_hierarchy_y_fieldsets(self):
        admin_track = django_admin.site._registry[Track]
        self.assertEqual(admin_track.date_hierarchy, 'created_at')
        self.assertIsNotNone(admin_track.fieldsets)

    def test_genre_prepopulated_slug(self):
        admin_genre = django_admin.site._registry[Genre]
        self.assertEqual(admin_genre.prepopulated_fields, {'slug': ('name',)})

    def test_playlist_list_display_e_inline(self):
        admin_playlist = django_admin.site._registry[Playlist]
        for campo in ('name', 'owner', 'created_at'):
            self.assertIn(campo, admin_playlist.list_display)
        # El inline permite gestionar las pistas (con orden) dentro de la
        # lista. NO se usa filter_horizontal: la M2M es through= y Django
        # lanza admin.E013 (documentado en podwave/admin.py).
        self.assertTrue(len(admin_playlist.inlines) >= 1)

    def test_playlist_sin_filter_horizontal(self):
        """Evidencia de la decisión: inline en lugar de filter_horizontal."""
        admin_playlist = django_admin.site._registry[Playlist]
        self.assertEqual(list(admin_playlist.filter_horizontal), [])

    def test_playlisttrack_inline_configurado(self):
        """El inline usa la tabla intermedia y edita el orden."""
        from podwave.admin import PlaylistTrackInline
        self.assertEqual(PlaylistTrackInline.model, PlaylistTrack)
        self.assertIn('order', PlaylistTrackInline.fields)

    def test_admin_pages_responden(self):
        """El superusuario ve el índice y los changelists (200)."""
        admin_user = User.objects.create_superuser(
            username='admin', password='clave12345', email='admin@example.com')
        self.client.force_login(admin_user)
        self.assertEqual(self.client.get('/admin/').status_code, 200)
        for url in ('/admin/podwave/genre/',
                    '/admin/podwave/track/',
                    '/admin/podwave/playlist/',
                    '/admin/podwave/playlisttrack/'):
            self.assertEqual(self.client.get(url).status_code, 200, url)


class AdminChangelistConDatosTest(TestCase):
    """Renderiza los changelists del admin CON DATOS en las tablas.

    Regresión de la entrega: con USE_TZ=True y TIME_ZONE local, un MySQL
    sin tablas de zonas horarias (instalación por omisión en Windows,
    macOS y Linux) hace que date_hierarchy y el filtro por fecha lancen
    CONVERT_TZ() -> NULL y los changelists de Track y Playlist devuelvan
    500 ("Database returned an invalid datetime value"). Con tablas
    VACÍAS el error no aparece (las fechas nunca se extraen), por eso el
    test crea datos antes de consultar. USE_TZ=False en settings.py
    elimina CONVERT_TZ y hace el proyecto portable a cualquier MySQL.
    """

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = User.objects.create_superuser(
            username='admin', password='clave12345', email='admin@example.com')
        cls.genero = Genre.objects.create(name='Ciencia Ficción')
        cls.track = Track.objects.create(
            title='Podcast de prueba con datos', artist='Autor de prueba',
            genre=cls.genero, url='https://ejemplo.com/audio.mp3',
            created_by=cls.admin_user,
        )
        cls.lista = Playlist.objects.create(
            owner=cls.admin_user, name='Lista de prueba')
        PlaylistTrack.objects.create(
            playlist=cls.lista, track=cls.track, order=1)

    def test_changelists_con_datos(self):
        """Los 4 changelists renderizan 200 con filas en las tablas."""
        self.client.force_login(self.admin_user)
        for url in ('/admin/podwave/genre/',
                    '/admin/podwave/track/',
                    '/admin/podwave/playlist/',
                    '/admin/podwave/playlisttrack/'):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

    def test_changelist_track_con_filtro_y_jerarquia_de_fechas(self):
        """date_hierarchy y los filtros de fecha/género renderizan 200."""
        self.client.force_login(self.admin_user)
        anio = self.track.created_at.year
        urls = (
            # date_hierarchy: drill-down año -> mes.
            f'/admin/podwave/track/?created_at__year={anio}',
            # Filtro por fecha del changelist (DateFieldListFilter).
            f'/admin/podwave/track/?created_at__year={anio}&created_at__month={self.track.created_at.month}',
            # list_filter por género (FK).
            f'/admin/podwave/track/?genre__id__exact={self.genero.pk}',
            # Playlist también tiene date_hierarchy.
            f'/admin/podwave/playlist/?created_at__year={anio}',
        )
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)


class AdminCRUDFlowTest(TestCase):
    """Instrucción 7 del instrumento: ingresar, visualizar, modificar y
    eliminar registros desde Django Admin (todo por el panel, sin SQL)."""

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = User.objects.create_superuser(
            username='admin', password='clave12345', email='admin@example.com')

    def test_alta_visualizacion_edicion_y_baja_de_un_genero(self):
        self.client.force_login(self.admin_user)

        # INGRESAR: formulario de alta del changelist de Genre.
        response = self.client.post(
            '/admin/podwave/genre/add/',
            {'name': 'Género desde el admin', 'slug': 'genero-admin'})
        self.assertEqual(response.status_code, 302)
        genero = Genre.objects.get(name='Género desde el admin')
        self.assertEqual(genero.slug, 'genero-admin')

        # VISUALIZAR: changelist y página de edición.
        self.assertEqual(
            self.client.get('/admin/podwave/genre/').status_code, 200)
        self.assertContains(
            self.client.get(f'/admin/podwave/genre/{genero.pk}/change/'),
            'Género desde el admin')

        # MODIFICAR: cambio del nombre por el panel.
        response = self.client.post(
            f'/admin/podwave/genre/{genero.pk}/change/',
            {'name': 'Género renombrado', 'slug': 'genero-admin'})
        self.assertEqual(response.status_code, 302)
        genero.refresh_from_db()
        self.assertEqual(genero.name, 'Género renombrado')

        # ELIMINAR: página de confirmación y borrado definitivo
        # (el botón del admin envía post="yes"; un POST vacío no confirma).
        self.assertEqual(
            self.client.get(
                f'/admin/podwave/genre/{genero.pk}/delete/').status_code, 200)
        response = self.client.post(
            f'/admin/podwave/genre/{genero.pk}/delete/', {'post': 'yes'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Genre.objects.filter(pk=genero.pk).exists())

    def test_alta_y_baja_de_una_pista_por_el_panel(self):
        """La entidad principal (Track) también se gestiona desde /admin/."""
        self.client.force_login(self.admin_user)
        genero = Genre.objects.create(name='Documental')

        # INGRESAR una pista (el slug lo genera el modelo, no el formulario).
        response = self.client.post(
            '/admin/podwave/track/add/',
            {'title': 'Episodio creado desde el admin',
             'artist': 'Productor Invitado',
             'genre': str(genero.pk),
             'audio_file': '',
             'url': 'https://ejemplo.com/episodio.mp3'})
        self.assertEqual(response.status_code, 302)
        pista = Track.objects.get(title='Episodio creado desde el admin')
        self.assertEqual(pista.genre, genero)
        self.assertTrue(pista.slug)   # generado automáticamente en save()

        # ELIMINAR la pista desde el panel (confirmación con post="yes").
        response = self.client.post(
            f'/admin/podwave/track/{pista.pk}/delete/', {'post': 'yes'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Track.objects.filter(pk=pista.pk).exists())


class SeedCommandTest(TestCase):
    """Pruebas del comando seed_demo: datos simulados U1 -> MySQL (U2)."""

    def test_seed_crea_el_catalogo(self):
        call_command('seed_demo', '--password', 'ClaveDemo123')
        self.assertEqual(Genre.objects.count(), 8)   # GENEROS_SUGERIDOS
        self.assertEqual(Track.objects.count(), 8)   # PISTAS_DEMO
        self.assertEqual(Playlist.objects.count(), 3)  # LISTAS_DEMO

    def test_seed_idempotente(self):
        """Ejecutar dos veces no duplica nada (get_or_create)."""
        call_command('seed_demo', '--password', 'ClaveDemo123')
        call_command('seed_demo', '--password', 'ClaveDemo123')
        self.assertEqual(Genre.objects.count(), 8)
        self.assertEqual(Track.objects.count(), 8)
        self.assertEqual(Playlist.objects.count(), 3)
        self.assertEqual(PlaylistTrack.objects.count(), 8)  # 3+2+3 enlaces

    def test_seed_cada_pista_tiene_fuente_de_audio(self):
        """Archivo local (si existe media/audio) o URL remota: siempre una."""
        call_command('seed_demo', '--password', 'ClaveDemo123')
        for track in Track.objects.all():
            self.assertTrue(track.audio_file or track.url,
                            f'{track.title} sin fuente de audio')
            self.assertIsNotNone(track.genre)  # FK poblada
            self.assertTrue(track.slug)        # slug generado

    def test_seed_crea_usuario_demo(self):
        self.assertFalse(User.objects.filter(username='demo').exists())
        call_command('seed_demo', '--password', 'ClaveDemo123')
        demo = User.objects.get(username='demo')
        # Las listas quedan ligadas a su dueño por CASCADE.
        self.assertEqual(demo.playlists.count(), 3)


# ---------------------------------------------------------------------------
# Unidad 2, parte 2 — Evaluación Sumativa 3 (U2-2)
#
# Pruebas de lo añadido en esta entrega:
#   - CRUD completo de las LISTAS desde el propio sitio web (criterio 3).
#   - Gestión de pistas dentro de la lista (agregar / quitar / reordenar).
#   - Control de acceso por PROPIEDAD en pistas y listas (criterio 6).
#   - Mensajes de confirmación/error del framework messages (criterio 5).
#   - Usuario de prueba determinista demo / demo1234 (instrucción 9).
# ---------------------------------------------------------------------------

class PlaylistViewsTest(TestCase):
    """CRUD de listas de reproducción desde el sitio web (criterio 3, U2-2)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='tester', password='clave12345')
        self.otro = User.objects.create_user(
            username='intruso', password='clave12345')
        self.playlist = Playlist.objects.create(
            owner=self.user, name='Lista de prueba',
            description='Para los tests de U2-2')

    # --- Read público ---

    def test_indice_de_listas_publico(self):
        response = self.client.get(reverse('playlist_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lista de prueba')
        # Contador de pistas por lista via annotate (no N+1).
        self.assertEqual(response.context['playlists'][0].num_pistas, 0)

    def test_detalle_publico_muestra_pistas_en_orden(self):
        genero = crear_genero('Tecnología')
        t1 = Track.objects.create(title='A', artist='X', genre=genero, url='https://a.com/1.mp3')
        t2 = Track.objects.create(title='B', artist='X', genre=genero, url='https://a.com/2.mp3')
        PlaylistTrack.objects.create(playlist=self.playlist, track=t1, order=1)
        PlaylistTrack.objects.create(playlist=self.playlist, track=t2, order=2)
        response = self.client.get(
            reverse('playlist_detail', kwargs={'pk': self.playlist.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A')
        self.assertContains(response, 'B')
        # El contexto llega en orden (Meta.ordering de PlaylistTrack).
        self.assertEqual(
            [e.track.title for e in response.context['enlaces']], ['A', 'B'])
        # Sin sesión: nadie ve los botones de gestión del dueño.
        self.assertFalse(response.context['es_dueno'])
        self.assertNotContains(response, 'track-actions')  # template no usa

    def test_indice_con_lista_vacia(self):
        """Estado vacío del índice cuando no hay listas."""
        Playlist.objects.all().delete()
        response = self.client.get(reverse('playlist_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No hay listas todavía')

    # --- Create requiere sesión ---

    def test_crear_sin_sesion_redirige_a_login(self):
        response = self.client.get(reverse('playlist_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_crear_con_sesion(self):
        self.client.login(username='tester', password='clave12345')
        response = self.client.post(reverse('playlist_create'),
                                     {'name': 'Mi nueva lista',
                                      'description': 'Creada desde el test'})
        # 302 al detalle de la lista creada (get_absolute_url del modelo).
        self.assertEqual(response.status_code, 302)
        lista = Playlist.objects.get(name='Mi nueva lista')
        self.assertEqual(lista.owner, self.user)  # dueño desde la sesión
        self.assertEqual(
            response['Location'], reverse('playlist_detail',
                                          kwargs={'pk': lista.pk}))

    def test_crear_nombre_invalido_rechazado(self):
        """Validación del formulario: nombre obligatorio (criterio 5)."""
        self.client.login(username='tester', password='clave12345')
        response = self.client.post(reverse('playlist_create'),
                                     {'name': '', 'description': ''})
        self.assertEqual(response.status_code, 200)  # re-render con errores
        self.assertFalse(
            Playlist.objects.filter(owner=self.user).count() > 1)

    # --- Update: dueño solamente (control de acceso, criterio 6) ---

    def test_editar_con_sesion(self):
        self.client.login(username='tester', password='clave12345')
        response = self.client.post(
            reverse('playlist_update', kwargs={'pk': self.playlist.pk}),
            {'name': 'Lista renombrada', 'description': 'editada'})
        self.assertEqual(response.status_code, 302)
        self.playlist.refresh_from_db()
        self.assertEqual(self.playlist.name, 'Lista renombrada')

    def test_editar_lista_de_otro_usuario_404(self):
        """Un usuario autenticado NO puede editar listas ajenas."""
        self.client.login(username='intruso', password='clave12345')
        response = self.client.get(
            reverse('playlist_update', kwargs={'pk': self.playlist.pk}))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(
            reverse('playlist_update', kwargs={'pk': self.playlist.pk}),
            {'name': 'hackeada', 'description': ''})
        self.assertEqual(response.status_code, 404)
        self.playlist.refresh_from_db()
        self.assertEqual(self.playlist.name, 'Lista de prueba')

    # --- Delete: dueño solamente ---

    def test_eliminar_lista_de_otro_usuario_404(self):
        self.client.login(username='intruso', password='clave12345')
        response = self.client.post(
            reverse('playlist_delete', kwargs={'pk': self.playlist.pk}))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            Playlist.objects.filter(pk=self.playlist.pk).exists())

    def test_eliminar_con_sesion_mantiene_pistas(self):
        """Borrar la lista borra sus enlaces, NO las pistas (CASCADE)."""
        genero = crear_genero('Tecnología')
        t1 = Track.objects.create(title='A', artist='X', genre=genero, url='https://a.com/1.mp3')
        PlaylistTrack.objects.create(playlist=self.playlist, track=t1, order=1)
        self.client.login(username='tester', password='clave12345')
        response = self.client.post(
            reverse('playlist_delete', kwargs={'pk': self.playlist.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('playlist_list'))
        self.assertFalse(
            Playlist.objects.filter(pk=self.playlist.pk).exists())
        self.assertFalse(PlaylistTrack.objects.exists())  # intermedia vacía
        self.assertTrue(Track.objects.filter(pk=t1.pk).exists())  # pista viva


class PlaylistTrackViewsTest(TestCase):
    """Gestión de pistas dentro de una lista (N:M con orden, U2-2)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='tester', password='clave12345')
        self.playlist = Playlist.objects.create(
            owner=self.user, name='Mi lista ordenada')
        self.genero = crear_genero('Tecnología')
        self.tracks = [
            Track.objects.create(
                title=f'Episodio {i}', artist='Artista', genre=self.genero,
                url=f'https://a.com/{i}.mp3')
            for i in range(1, 4)   # tres pistas: 1, 2, 3
        ]

    def _agregar(self, track, playlist=None):
        self.client.post(
            reverse('track_add_to_playlist', kwargs={'pk': track.pk}),
            {'playlist': (playlist or self.playlist).pk})

    def test_agregar_pista_a_lista(self):
        self.client.login(username='tester', password='clave12345')
        self._agregar(self.tracks[0])
        enlace = PlaylistTrack.objects.get(
            playlist=self.playlist, track=self.tracks[0])
        self.assertEqual(enlace.order, 1)  # primera pista -> orden 1

    def test_agregar_varias_pistas_ordena_al_final(self):
        """El orden se asigna automáticamente: máximo actual + 1."""
        self.client.login(username='tester', password='clave12345')
        for track in self.tracks:
            self._agregar(track)
        self.assertEqual(
            [e.order for e in self.playlist.pistas.all()], [1, 2, 3])

    def test_agregar_pista_repetida_no_duplica(self):
        """get_or_create respeta el constraint pista_unica_por_lista."""
        self.client.login(username='tester', password='clave12345')
        self._agregar(self.tracks[0])
        self._agregar(self.tracks[0])
        self.assertEqual(self.playlist.pistas.count(), 1)

    def test_agregar_a_lista_propia_requerido(self):
        """El select solo ofrece listas propias: una lista ajena no pasa."""
        otro = User.objects.create_user(username='otro', password='clave12345')
        lista_ajena = Playlist.objects.create(owner=otro, name='Ajena')
        self.client.login(username='tester', password='clave12345')
        response = self.client.post(
            reverse('track_add_to_playlist', kwargs={'pk': self.tracks[0].pk}),
            {'playlist': lista_ajena.pk}, follow=True)
        # El formulario invalida la lista ajena: mensaje de error, sin enlace.
        self.assertIn(
            b'elige una lista v\xc3\xa1lida', response.content)
        self.assertFalse(PlaylistTrack.objects.exists())

    def test_agregar_sin_sesion_redirige_a_login(self):
        response = self.client.post(
            reverse('track_add_to_playlist', kwargs={'pk': self.tracks[0].pk}),
            {'playlist': self.playlist.pk})
        self.assertEqual(response.status_code, 302)

    def test_quitar_pista_y_renumerar(self):
        """Quitar la del medio deja los órdenes 1 y 2 (sin huecos)."""
        self.client.login(username='tester', password='clave12345')
        for i, track in enumerate(self.tracks, start=1):
            PlaylistTrack.objects.create(
                playlist=self.playlist, track=track, order=i)
        response = self.client.post(
            reverse('playlist_remove_track',
                    kwargs={'pk': self.playlist.pk,
                            'track_pk': self.tracks[1].pk}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            [(e.track.title, e.order) for e in self.playlist.pistas.all()],
            [('Episodio 1', 1), ('Episodio 3', 2)])

    def test_quitar_de_lista_de_otro_404(self):
        otro = User.objects.create_user(username='otro', password='clave12345')
        PlaylistTrack.objects.create(
            playlist=self.playlist, track=self.tracks[0], order=1)
        self.client.login(username='otro', password='clave12345')
        response = self.client.post(
            reverse('playlist_remove_track',
                    kwargs={'pk': self.playlist.pk,
                            'track_pk': self.tracks[0].pk}))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.playlist.pistas.count(), 1)

    def test_mover_pista_abajo(self):
        self.client.login(username='tester', password='clave12345')
        for i, track in enumerate(self.tracks[:2], start=1):
            PlaylistTrack.objects.create(
                playlist=self.playlist, track=track, order=i)
        response = self.client.post(
            reverse('playlist_move_track',
                    kwargs={'pk': self.playlist.pk,
                            'track_pk': self.tracks[0].pk,
                            'direccion': 'abajo'}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            [(e.track.title, e.order) for e in self.playlist.pistas.all()],
            [('Episodio 2', 1), ('Episodio 1', 2)])

    def test_mover_primera_pista_arriba_no_hace_nada(self):
        """En el extremo: mensaje informativo y orden intacto."""
        self.client.login(username='tester', password='clave12345')
        PlaylistTrack.objects.create(
            playlist=self.playlist, track=self.tracks[0], order=1)
        response = self.client.post(
            reverse('playlist_move_track',
                    kwargs={'pk': self.playlist.pk,
                            'track_pk': self.tracks[0].pk,
                            'direccion': 'arriba'}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'ya est\xc3\xa1 en el extremo', response.content)
        self.assertEqual(
            self.playlist.pistas.get(track=self.tracks[0]).order, 1)

    def test_direccion_invalida_404(self):
        self.client.login(username='tester', password='clave12345')
        PlaylistTrack.objects.create(
            playlist=self.playlist, track=self.tracks[0], order=1)
        response = self.client.post(
            reverse('playlist_move_track',
                    kwargs={'pk': self.playlist.pk,
                            'track_pk': self.tracks[0].pk,
                            'direccion': 'diagonal'}))
        self.assertEqual(response.status_code, 404)


class TrackOwnershipTest(TestCase):
    """Control de acceso por propiedad en PISTAS (criterio 6, U2-2)."""

    def setUp(self):
        self.dueno = User.objects.create_user(
            username='dueno', password='clave12345')
        self.intruso = User.objects.create_user(
            username='intruso', password='clave12345')
        self.track = Track.objects.create(
            title='Pista del dueño', artist='Artista',
            genre=crear_genero('Tecnología'),
            created_by=self.dueno, url='https://a.com/audio.mp3')

    def test_editar_pista_de_otro_usuario_404(self):
        self.client.login(username='intruso', password='clave12345')
        response = self.client.get(
            reverse('track_update', kwargs={'pk': self.track.pk}))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(
            reverse('track_update', kwargs={'pk': self.track.pk}),
            track_data(crear_genero('Tecnología'), title='Hackeada'))
        self.assertEqual(response.status_code, 404)
        self.track.refresh_from_db()
        self.assertEqual(self.track.title, 'Pista del dueño')

    def test_eliminar_pista_de_otro_usuario_404(self):
        self.client.login(username='intruso', password='clave12345')
        response = self.client.post(
            reverse('track_delete', kwargs={'pk': self.track.pk}))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Track.objects.filter(pk=self.track.pk).exists())

    def test_superusuario_edita_cualquier_pista(self):
        """Rol superusuario (definido en el proyecto): acceso total."""
        admin = User.objects.create_superuser(
            username='admin', password='clave12345', email='a@example.com')
        self.client.force_login(admin)
        response = self.client.get(
            reverse('track_update', kwargs={'pk': self.track.pk}))
        self.assertEqual(response.status_code, 200)

    def test_botones_de_gestion_solo_para_el_dueno(self):
        """La plantilla no muestra editar/eliminar a quien no es dueño."""
        self.client.login(username='intruso', password='clave12345')
        response = self.client.get(
            reverse('track_detail', kwargs={'pk': self.track.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response, reverse('track_update', kwargs={'pk': self.track.pk}))
        self.assertNotContains(
            response, reverse('track_delete', kwargs={'pk': self.track.pk}))
        # Y sí los ve el dueño.
        self.client.login(username='dueno', password='clave12345')
        response = self.client.get(
            reverse('track_detail', kwargs={'pk': self.track.pk}))
        self.assertContains(
            response, reverse('track_update', kwargs={'pk': self.track.pk}))


class MensajesFeedbackTest(TestCase):
    """Mensajes de confirmación/error tras cada operación (criterio 5)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='tester', password='clave12345')
        self.genero = crear_genero('Tecnología')

    def test_mensaje_tras_crear_pista(self):
        self.client.login(username='tester', password='clave12345')
        response = self.client.post(
            reverse('track_create'),
            track_data(self.genero, title='Pista con mensaje'),
            follow=True)
        self.assertContains(response, 'alert-success')
        self.assertContains(response, 'agregada a la biblioteca')

    def test_mensaje_tras_eliminar_pista(self):
        """DeleteView + SuccessMessageMixin (Django 5.2 pasa por form_valid)."""
        track = Track.objects.create(
            title='Efímera', artist='X', genre=self.genero,
            created_by=self.user, url='https://a.com/x.mp3')
        self.client.login(username='tester', password='clave12345')
        response = self.client.post(
            reverse('track_delete', kwargs={'pk': track.pk}), follow=True)
        self.assertContains(response, 'Pista eliminada de la biblioteca')

    def test_mensaje_tras_crear_y_eliminar_lista(self):
        self.client.login(username='tester', password='clave12345')
        response = self.client.post(
            reverse('playlist_create'), {'name': 'Lista con mensaje'},
            follow=True)
        self.assertContains(response, 'Lista \u00abLista con mensaje\u00bb creada')
        lista = Playlist.objects.get(name='Lista con mensaje')
        response = self.client.post(
            reverse('playlist_delete', kwargs={'pk': lista.pk}), follow=True)
        self.assertContains(response, 'Lista eliminada')

    def test_errores_de_validacion_en_el_formulario(self):
        """El formulario re-renderiza con los errores visibles."""
        self.client.login(username='tester', password='clave12345')
        response = self.client.post(reverse('playlist_create'), {'name': ''})
        self.assertContains(response, 'obligatorio')

    def test_errores_del_select_de_lista(self):
        track = Track.objects.create(
            title='T', artist='A', genre=self.genero,
            created_by=self.user, url='https://a.com/t.mp3')
        self.client.login(username='tester', password='clave12345')
        response = self.client.post(
            reverse('track_add_to_playlist', kwargs={'pk': track.pk}),
            {'playlist': ''}, follow=True)
        self.assertContains(response, 'alert-danger')


class UsuarioPruebaTest(TestCase):
    """Usuario de prueba determinista demo / demo1234 (instrucción 9)."""

    def test_seed_crea_demo_con_clave_por_defecto(self):
        call_command('seed_demo')
        demo = User.objects.get(username='demo')
        self.assertTrue(demo.check_password('demo1234'))

    def test_clave_por_defecto_se_restaura_en_cada_corrida(self):
        """Si la clave se corrompe, seed_demo la deja determinista otra vez."""
        call_command('seed_demo')
        demo = User.objects.get(username='demo')
        demo.set_password('otraclave123')
        demo.save(update_fields=['password'])
        call_command('seed_demo')
        demo.refresh_from_db()
        self.assertTrue(demo.check_password('demo1234'))
