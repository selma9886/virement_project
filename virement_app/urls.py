# urls.py (principal)
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('index/', views.index, name='index'),
    path('upload/', views.upload_file, name='upload'),
    path('confirm-corrections/', views.confirm_corrections, name='confirm_corrections'),
    path('process_corrections/', views.process_corrections, name='process_corrections'),
    path('generate-xml/', views.generate_xml, name='generate_xml'),
    path('download/<str:filename>/', views.download_file, name='download_file'),
    path('download_template/', views.download_template, name='download_template'),
    path('change-password/', views.change_password, name='change_password'),
]

# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)