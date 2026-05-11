from django.contrib import admin
from django.utils.html import format_html
from .models import Sala, Evento, ReglaRecurrencia, ServicioAdicional, Incidente


# ─────────────────────────────────────────
#  1. SALA
# ─────────────────────────────────────────

@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'tipo', 'capacidad')
    list_filter   = ('tipo',)
    search_fields = ('nombre',)


# ─────────────────────────────────────────
#  2. SERVICIOS e INCIDENTES como inlines
#  (aparecen dentro del formulario del Evento)
# ─────────────────────────────────────────

class ServicioAdicionalInline(admin.TabularInline):
    model  = ServicioAdicional
    extra  = 1   # Muestra 1 fila vacía lista para llenar
    fields = ('tipo', 'notas')


class IncidenteInline(admin.TabularInline):
    model  = Incidente
    extra  = 0   # Solo muestra incidentes existentes, no filas vacías
    fields = ('sala', 'tipo', 'descripcion', 'fecha')
    readonly_fields = ('fecha',)


class ReglaRecurrenciaInline(admin.StackedInline):
    model  = ReglaRecurrencia
    extra  = 0
    fields = ('tipo', 'fecha_fin_serie')


# ─────────────────────────────────────────
#  3. EVENTO  (la entidad principal que se gestiona)
# ─────────────────────────────────────────

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

    list_filter   = ('estado', 'fecha', 'salas')
    search_fields = ('nombre_evento', 'nombre_responsable', 'correo_responsable')
    date_hierarchy = 'fecha'   # Navegador por fecha arriba de la lista
    ordering      = ['fecha', 'hora_inicio']

    # Organización del formulario de edición en secciones
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
        ('Salas Asignadas', {
            'fields': ('salas',),
            'description': 'Selecciona 1 sala (≤40 asistentes), 2 salas (41–80) o 3 salas (81–120).'
        }),
        ('Notas', {
            'fields': ('notas',),
            'classes': ('collapse',)  # Sección colapsable
        }),
    )

    # Los inlines aparecen al final del formulario del evento
    inlines = [ReglaRecurrenciaInline, ServicioAdicionalInline, IncidenteInline]

    # Columna personalizada que muestra las salas como texto legible
    def salas_asignadas(self, obj):
        salas = obj.salas.all()
        if not salas:
            return '—'
        return ', '.join([s.nombre for s in salas])
    salas_asignadas.short_description = 'Salas'


# ─────────────────────────────────────────
#  4. INCIDENTES (para reportar problemas en las salas)
#    Se pueden agregar desde el formulario del Evento o aquí directamente
# ─────────────────────────────────────────

@admin.register(Incidente)
class IncidenteAdmin(admin.ModelAdmin):
    list_display  = ('sala', 'tipo', 'descripcion', 'evento', 'fecha')
    list_filter   = ('tipo', 'sala', 'fecha')
    search_fields = ('descripcion',)
    readonly_fields = ('fecha',)


# ─────────────────────────────────────────
#  5. TÍTULO DEL PANEL
# ─────────────────────────────────────────

admin.site.site_header  = 'SalasMan — Administración'
admin.site.site_title   = 'SalasMan'
admin.site.index_title  = 'Panel de Gestión de Salas'