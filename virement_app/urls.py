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
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('user-dashboard/', views.user_dashboard, name='user_dashboard'),
    path('index/', views.index, name='index'),
    path('upload/', views.upload_file, name='upload'),
    path('confirm-corrections/', views.confirm_corrections, name='confirm_corrections'),
    path('process_corrections/', views.process_corrections, name='process_corrections'),
    path('generate-xml/', views.generate_xml, name='generate_xml'),
    path('download/<str:filename>/', views.download_file, name='download_file'),
    path('download_template/', views.download_template, name='download_template'),
    path('change-password/', views.change_password, name='change_password'),
    path("generated_files/", views.generated_files, name="generated-files"),
    path('manage_users/', views.manage_users, name='manage_users'),
    path('toggle_validation/<int:user_id>/', views.toggle_validation, name='toggle_validation'),
    path('toggle_file_access/<int:user_id>/', views.toggle_file_access, name='toggle_file_access'),
    path('my_generated_files/', views.my_generated_files, name='my_generated_files'),
    path('send_file_email/', views.send_file_email, name='send_file_email'),
    path('ask-send-email/<int:file_id>/', views.ask_send_email, name='ask_send_email'),
    path('send-email-form/<int:file_id>/', views.send_email_form, name='send_email_form'),
    path('skip-send-email/<int:file_id>/', views.skip_send_email, name='skip_send_email'),
    path('serve-file/<str:filename>/', views.serve_file, name='serve_file'),
    path('email-history/', views.email_history, name='email_history'),
    path("my-emails/", views.user_email, name="user_email"),
    path('serve-file/<str:filename>/', views.serve_file, name='serve_file'), 
    path('download/<str:filename>/', views.download_file, name='download_file'),
    path('delete-file/<int:id>/', views.delete_generated_file, name='delete_file'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    # path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),

    path('add-user/', views.add_user_view, name='add_user'),
    # path('api/get-users/', views.get_users_list, name='get_users_list'),
    # path('api/get-user-permissions/<int:user_id>/', views.get_user_permissions_view, name='get_user_permissions'),
    # path('edit-user/<int:user_id>/', views.edit_user_view, name='edit_user'),
    # path('add-user/', views.add_user_view, name='add_user'),

    path('edit-user/<int:user_id>/', views.edit_user_view, name='edit_user'),
    path('api/get-user-permissions/<int:user_id>/', views.get_user_permissions_view, name='get_user_permissions'),
    path('api/get-users/', views.get_users_list, name='get_users_list'),
    # path('api/revoke-comptable-access/<int:user_id>/', views.revoke_comptable_access, name='revoke_comptable_access'),
    # path('api/add-users-to-comptable/<int:comptable_id>/', views.add_users_to_comptable, name='add_users_to_comptable'),

    path("verify-xml/", views.verify_xml, name="verify_xml"),
    path("verify-xml/upload/", views.upload_xml_for_check, name="upload_xml_for_check"),
    path("verify-xml/apply/", views.apply_xml_corrections, name="apply_xml_corrections"),


    





]

# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)