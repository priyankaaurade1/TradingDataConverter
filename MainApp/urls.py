from django.urls import path
from .views import upload_csv, download_json

urlpatterns = [
    path('', upload_csv, name='upload_csv'),
    path('download/<str:file_name>/', download_json, name='download_json'),
]
