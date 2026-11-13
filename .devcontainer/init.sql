-- PodWave — grant extra del contenedor de desarrollo.
-- El entrypoint de la imagen MySQL crea `podwave_user` con privilegios
-- SOLO sobre `podwave` (MYSQL_DATABASE). `python manage.py test` crea y
-- descarta la base `test_podwave`, por lo que aquí se añade ese permiso.
GRANT ALL PRIVILEGES ON `test_podwave`.* TO 'podwave_user'@'%';
FLUSH PRIVILEGES;
