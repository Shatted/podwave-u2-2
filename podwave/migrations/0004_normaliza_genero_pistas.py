# Migración de DATOS de la Unidad 2: normaliza el género de las pistas.
#
# La Unidad 1 guardaba el género como CharField con choices. Esta migración:
#   1. Crea las filas de Genre a partir de los valores de aquellos choices
#      (los ocho géneros sugeridos del catálogo de la Unidad 1).
#   2. Añade la ForeignKey genre_nuevo y re-apunta CADA pista existente al
#      Genre equivalente (preserva los datos: una fila con genre='Ciencia'
#      queda con la FK al Genre 'Ciencia').
#   3. Genera el slug único de cada pista a partir de su título.
#   4. Elimina el CharField antiguo y renombra la FK a "genre".
#
# Es reversible: al migrar hacia atrás se restaura el texto del género.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

from django.utils.text import slugify

# Valores de los choices de la Unidad 1 (podwave/datos_simulados.py,
# GENEROS_SUGERIDOS). Se copian aquí para que la migración sea un registro
# histórico estable aunque cambie el módulo de datos simulados.
GENEROS_U1 = [
    'Tecnología', 'Historia', 'Música', 'Noticias',
    'Educación', 'Entretenimiento', 'Ciencia', 'Deportes',
]


def _slug_genero(nombre):
    """Slug de un género (mismo criterio que Genre.save())."""
    return slugify(nombre)[:50] or 'genero'


def normalizar(apps, schema_editor):
    """Choices (texto U1) -> filas de Genre + FK en cada pista + slugs."""
    Genre = apps.get_model('podwave', 'Genre')
    Track = apps.get_model('podwave', 'Track')

    # 1) Catálogo: los géneros sugeridos de la Unidad 1 pasan a ser filas.
    for nombre in GENEROS_U1:
        Genre.objects.get_or_create(
            name=nombre, defaults={'slug': _slug_genero(nombre)})

    # 2) Cada pista existente apunta al Genre equivalente (sin perder datos:
    #    un género desconocido también se conserva como fila nueva).
    for track in Track.objects.all():
        nombre = (track.genre or '').strip() or 'Tecnología'
        genre, _creada = Genre.objects.get_or_create(
            name=nombre, defaults={'slug': _slug_genero(nombre)})
        track.genre_nuevo = genre

        # 3) Slug único por pista, generado desde el título.
        if not track.slug:
            base = slugify(track.title)[:120] or 'pista'
            slug, sufijo = base, 2
            while Track.objects.filter(slug=slug).exclude(pk=track.pk).exists():
                slug = f'{base}-{sufijo}'
                sufijo += 1
            track.slug = slug

        track.save(update_fields=['genre_nuevo', 'slug'])


def deshacer(apps, schema_editor):
    """Reversa: copia el nombre del género de vuelta al CharField (U1)."""
    Genre = apps.get_model('podwave', 'Genre')
    Track = apps.get_model('podwave', 'Track')

    for track in Track.objects.select_related('genre_nuevo'):
        # El CharField original se restaura solo al revertir el RemoveField;
        # aquí solo devolvemos su valor texto desde la ForeignKey.
        if track.genre_nuevo_id:
            track.genre = track.genre_nuevo.name
        else:
            track.genre = 'Tecnología'   # default del CharField de la U1
        track.save(update_fields=['genre'])


class Migration(migrations.Migration):

    dependencies = [
        ('podwave', '0003_create_genre'),
    ]

    operations = [
        # Slug de pista: nace anulable y sin unicidad; se rellena con datos
        # y la migración 0005 lo hace único y obligatorio.
        migrations.AddField(
            model_name='track',
            name='slug',
            field=models.SlugField(blank=True, max_length=140, null=True, verbose_name='slug'),
        ),
        # FK nueva (temporal "genre_nuevo"): nace anulable, se rellena con
        # datos y luego sustituye al CharField antiguo.
        migrations.AddField(
            model_name='track',
            name='genre_nuevo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='tracks', to='podwave.genre', verbose_name='género'),
        ),
        # El related_name 'tracks' de created_by se libera a favor de la FK
        # de género (evita el choque de nombres inversos).
        migrations.AlterField(
            model_name='track',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pistas_creadas', to=settings.AUTH_USER_MODEL, verbose_name='creada por'),
        ),
        # --- Migración de datos propiamente tal ---
        migrations.RunPython(normalizar, deshacer),
        # Fuera el CharField con choices de la Unidad 1…
        migrations.RemoveField(
            model_name='track',
            name='genre',
        ),
        # …y la FK temporal pasa a llamarse "genre" (estado final del modelo).
        migrations.RenameField(
            model_name='track',
            old_name='genre_nuevo',
            new_name='genre',
        ),
    ]
