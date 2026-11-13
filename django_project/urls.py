"""
URLconf principal del proyecto PodWave (Unidad 1 y Unidad 2).

El orden de los patrones importa: Django los evalúa de arriba a abajo.
  - admin/      -> panel de administración de Django
  - accounts/   -> autenticación (login/logout) + registro (signup)
  - ''          -> app pages (home/about) y app podwave (CRUD de pistas)
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Autenticación: LoginView y LogoutView incorporados de Django.
    path('accounts/', include('django.contrib.auth.urls')),
    # Registro de nuevos usuarios (app accounts).
    path('accounts/', include('accounts.urls')),
    # Páginas estáticas (pages) y CRUD de pistas (podwave).
    path('', include('pages.urls')),
    path('', include('podwave.urls')),
]

# Media files (audio subido por los usuarios) durante el desarrollo.
# En producción se sirven desde el servidor web (nginx/Apache/S3).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
