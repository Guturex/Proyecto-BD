from django.contrib import admin
from django.utils.html import format_html
from .models import Sala, Evento, ReglaRecurrencia, ServicioAdicional, Incidente, Acomodo, EventoSala

'''
Registro de modelos en el admin de Django para gestionar Salas, Eventos, Reglas 
de Recurrencia, Servicios Adicionales e Incidentes. Se incluyen configuraciones 
personalizadas para mejorar la visualización y facilitar la administración de los 
datos relacionados con la gestión de salas y eventos en la plataforma SalasMan.
'''

# -----------------------------------------
#  1. SALA
# -----------------------------------------

'''
El modelo Sala se registra con una configuración personalizada que muestra el nombre,
tipo y capacidad en la lista de salas. Se habilitan filtros por tipo de sala y una
barra de búsqueda por nombre para facilitar la localización de salas específicas.
'''

@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'capacidad')
    list_filter = ('tipo',)
    search_fields = ('nombre',)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# -----------------------------------------
#  2. SERVICIOS e INCIDENTES (para agregar desde el formulario del Evento)
# -----------------------------------------

'''
Los modelos ServicioAdicional e Incidente se configuran como inlines dentro del 
formulario del Evento, lo que permite agregar servicios adicionales e incidentes 
relacionados directamente al crear o editar un evento. Esto mejora la usabilidad 
al mantener toda la información relevante en un solo lugar.
'''

class ServicioAdicionalInline(admin.TabularInline):
    model = ServicioAdicional
    extra = 1  
    fields = ('tipo', 'notas')


class IncidenteInline(admin.TabularInline):
    model = Incidente
    extra = 0   # Solo muestra incidentes existentes, no filas vacías
    fields = ('sala', 'tipo', 'descripcion', 'fecha')
    readonly_fields = ('fecha',)


class ReglaRecurrenciaInline(admin.StackedInline):
    model = ReglaRecurrencia
    extra = 0
    fields = ('tipo', 'fecha_fin_serie')

# ----------------------------------------- 
#  3. ACOMODO
# -----------------------------------------

@admin.register(Acomodo)
class AcomodoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

class EventoSalaInline(admin.TabularInline):
    model = EventoSala
    extra = 1

# -----------------------------------------
#  4. EVENTO  
# -----------------------------------------

'''
El modelo Evento se registra con una configuración personalizada que muestra 
información clave como el nombre del evento, responsable, fecha, horario, número 
de asistentes, salas asignadas y estado en la lista de eventos. Se habilitan 
filtros por estado, fecha y salas, así como una barra de búsqueda por nombre del 
evento y responsable.
'''

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):

    list_display = (
        'nombre_evento',
        'nombre_responsable',
        'fecha',
        'hora_inicio',
        'hora_fin',
        'num_asistentes',
        'salas_asignadas',   
        'estado',
    )

    list_filter = ('estado', 'fecha', 'salas')
    search_fields = ('nombre_evento', 'nombre_responsable', 'correo_responsable')
    date_hierarchy = 'fecha'   # Navegador por fecha arriba de la lista
    ordering = ['fecha', 'hora_inicio']

    fieldsets = (
        ('Información del Evento', {
            'fields': (
                'nombre_evento',
                'nombre_responsable',
                'correo_responsable',
                'num_asistentes',
                'estado',
            )
        }),
        ('Fecha y Horario', {
            'fields': ('fecha', 'hora_inicio', 'hora_fin')
        }),
        ('Notas', {
            'fields': ('notas',),
            'classes': ('collapse',)  
        }),
    )

    inlines = [ReglaRecurrenciaInline, ServicioAdicionalInline, IncidenteInline, EventoSalaInline]

    def salas_asignadas(self, obj):
        salas = obj.salas.all()
        if not salas:
            return '—'
        return ', '.join([s.nombre for s in salas])
    salas_asignadas.short_description = 'Salas'


# -----------------------------------------
#  5. INCIDENTES (para reportar problemas en las salas)
#    Se pueden agregar desde el formulario del Evento o aquí directamente
# -----------------------------------------

'''
El modelo Incidente se registra con una configuración personalizada que muestra 
la sala, tipo de incidente, descripción, evento asociado (si aplica) y fecha en 
la lista de incidentes. Se habilitan filtros por tipo de incidente, sala y fecha, 
así como una barra de búsqueda por descripción. Además, la fecha del incidente se 
muestra como un campo de solo lectura para preservar la integridad de la información.
'''

@admin.register(Incidente)
class IncidenteAdmin(admin.ModelAdmin):
    list_display = ('sala', 'tipo', 'descripcion', 'evento', 'fecha')
    list_filter = ('tipo', 'sala', 'fecha')
    search_fields = ('descripcion',)
    readonly_fields = ('fecha',)


# ----------------------------------------- 
#  6. TÍTULO DEL PANEL
# -----------------------------------------

admin.site.site_header = 'SalasMan — Administración'
admin.site.site_title = 'SalasMan'
admin.site.index_title = 'Panel de Gestión de Salas'