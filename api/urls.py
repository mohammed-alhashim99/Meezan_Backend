from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_file, name='upload'),
    path('categorize/', views.categorize_transactions, name='categorize'),
    path('insights/', views.get_insights, name='insights'),
    path('health/', views.health_check, name='health'),
]
