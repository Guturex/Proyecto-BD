from django.urls import path
from . import views

app_name = 'gestion'

urlpatterns = [
    path('', views.calendario, name='calendario'),
    path('login/', views.vista_login, name='login'),
    path('logout/', views.vista_logout, name='logout'),
]