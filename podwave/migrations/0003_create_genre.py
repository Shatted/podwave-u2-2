# Migración de la Unidad 2: catálogo de géneros como tabla propia.
#
# Genre nace vacía; la migración de datos 0004 la puebla con los valores
# de los choices del CharField Track.genre de la Unidad 1.
# Generada manualmente con el mismo formato que produce makemigrations.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('podwave', '0002_track_audio_file_alter_track_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='Genre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40, unique=True, verbose_name='nombre')),
                ('slug', models.SlugField(max_length=50, unique=True, verbose_name='slug')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'género',
                'verbose_name_plural': 'géneros',
            },
        ),
    ]
