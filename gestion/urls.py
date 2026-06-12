from django.urls import path
from . import views

app_name = 'gestion'

urlpatterns = [
    path('', views.calendario, name='calendario'),
    path('login/', views.vista_login, name='login'),
    path('logout/', views.vista_logout, name='logout'),
    path('crear/', views.crear_evento, name='crear_evento'),    
    path('incidencias/', views.lista_incidencias, name='lista_incidencias'),
    path('incidencias/crear/', views.crear_incidencia, name='crear_incidencia'),
    path('evento/<int:evento_id>/', views.detalle_evento, name='detalle_evento'),
    path('evento/<int:evento_id>/editar/', views.editar_evento, name='editar_evento'),
    path('evento/<int:evento_id>/eliminar/', views.eliminar_evento, name='eliminar_evento'),
]