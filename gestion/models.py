from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

'''
Este módulo define los modelos de datos para la aplicación de gestión de salas y 
eventos. Incluye las siguientes entidades principales:

1. Sala: Representa una sala disponible para eventos, con atributos como nombre,
tipo y capacidad.

2. Evento: Representa un evento agendado en una o varias salas, con atributos
como nombre, responsable, fecha y horario.

3. ReglaRecurrencia: Define las reglas de recurrencia para eventos que se repiten
en un patrón específico (diario, semanal, mensual, anual).

4. ServicioAdicional: Representa servicios adicionales que pueden ser requeridos
para un evento, como acomodo de mobiliario, equipo de sonido, etc.

5. Incidente: Representa incidentes reportados en una sala, como daño en equipo
o falla técnica.
'''

# -----------------------------------------
#  1. SALA
# -----------------------------------------

class Sala(models.Model):
    '''
    Representa una sala disponible para eventos. Cada sala tiene un nombre, 
    y una capacidad máxima y puede estar asociada a múltiples eventos a lo
    largo del tiempo. La capacidad se utiliza para validar que el número de
    asistentes de un evento no exceda la capacidad de la sala asignada. 
    '''

    nombre = models.CharField(max_length=100)
    capacidad = models.PositiveIntegerField(default=40)

    def __str__(self):
        return f"{self.nombre}"

    class Meta:
        verbose_name = 'Sala'
        verbose_name_plural = 'Salas'

# -----------------------------------------
#  2. EVENTO
# -----------------------------------------

class Evento(models.Model):
    '''
    Representa un evento agendado en una o varias salas. Cada evento tiene 
    un responsable, un nombre, número de asistentes, estado (confirmado, 
    cancelado, pendiente), fecha, hora de inicio y fin, y puede estar asociado 
    a una regla de recurrencia. Además, se pueden agregar notas adicionales 
    para el admin y servicios adicionales como acomodo, sonido, etc. 
    '''

    class EstadoEvento(models.TextChoices):
        CONFIRMADO = 'CONFIRMADO', 'Confirmado'
        CANCELADO = 'CANCELADO', 'Cancelado'
        PENDIENTE = 'PENDIENTE', 'Pendiente'

    nombre_responsable = models.CharField(max_length=200)
    correo_responsable = models.EmailField(blank=True)  
    nombre_evento = models.CharField(max_length=200)
    num_asistentes = models.PositiveIntegerField()
    estado = models.CharField(
        max_length=20,
        choices=EstadoEvento.choices,
        default=EstadoEvento.CONFIRMADO
    )

    fecha = models.DateField()
    hora_inicio = models.TimeField()  
    hora_fin = models.TimeField()  

    # Salas asignadas al evento (un evento puede ocupar varias salas)
    # Ahora usa modelo intermedio
    
    salas = models.ManyToManyField(
        Sala, 
        through='EventoSala', 
        related_name='eventos'
    )

    # Notas adicionales del admin
    notas = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nombre_evento} — {self.fecha} ({self.hora_inicio}–{self.hora_fin})"

    def clean(self):
        # Valida que el evento sea lunes a viernes
        if self.fecha and self.fecha.weekday() > 4:  
            raise ValidationError(_('Los eventos solo pueden agendarse de lunes a viernes.'))

        # Validar que el horario esté dentro del rango permitido y que hora_inicio < hora_fin
        from datetime import time
        apertura = time(8, 0)
        cierre   = time(19, 0)

        if self.hora_inicio and self.hora_fin:
            if self.hora_inicio < apertura or self.hora_fin > cierre:
                raise ValidationError(_('El horario debe estar dentro del rango 8:00 a.m. – 7:00 p.m.'))
            if self.hora_inicio >= self.hora_fin:
                raise ValidationError(_('La hora de inicio debe ser anterior a la hora de fin.'))

    class Meta:
        verbose_name        = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering            = ['fecha', 'hora_inicio']

# -----------------------------------------
#  3. EVENTO RECURRENTE
# -----------------------------------------

class ReglaRecurrencia(models.Model):
    """
    Representa la regla de recurrencia para un evento. Cada regla de recurrencia
    está asociada a un evento base (a través de una relación OneToOne) y define 
    el tipo de recurrencia (diaria, semanal, mensual, anual) y la fecha hasta la 
    cual se repetirá el evento. 
    """

    class TipoRecurrencia(models.TextChoices):
        DIARIA = 'DIARIA', 'Diaria'
        SEMANAL = 'SEMANAL', 'Semanal'
        MENSUAL = 'MENSUAL', 'Mensual'
        ANUAL = 'ANUAL', 'Anual'
    
    evento_base = models.OneToOneField(
        Evento,
        on_delete=models.CASCADE,
        related_name='regla_recurrencia'
        ) 
    tipo = models.CharField(max_length=10, choices=TipoRecurrencia.choices)
    fecha_fin_serie = models.DateField()  # Hasta cuándo se repetirá el evento

    def __str__(self):
        return f"Recurrencia {self.tipo} -> {self.evento_base.nombre_evento} hasta {self.fecha_fin_serie}"

    class Meta:
        verbose_name = 'Regla de Recurrencia'
        verbose_name_plural = 'Reglas de Recurrencia'

# -----------------------------------------
#  4. SERVICIOS ADICIONALES  
# -----------------------------------------

class ServicioAdicional(models.Model):
    '''
    Representa un servicio adicional que puede ser requerido para un evento, 
    como acomodo de mobiliario, equipo de sonido, cafetería o videoconferencia. 
    Cada servicio adicional está asociado a un evento específico y puede incluir 
    notas detalladas sobre los requerimientos del servicio. Este modelo permite 
    gestionar de manera flexible los servicios adicionales que un evento pueda 
    necesitar, facilitando la organización y coordinación de los recursos necesarios 
    para la realización exitosa del evento.
    '''

    class TipoServicio(models.TextChoices):
        ACOMODO = 'ACOMODO', 'Acomodo de mobiliario'
        SONIDO = 'SONIDO', 'Equipo de sonido'
        CAFETERIA = 'CAFETERIA', 'Cafetería'
        VIDEOCONFERENCIA = 'VIDEOCONF', 'Videoconferencia'

    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name='servicios'
        )
    tipo   = models.CharField(max_length=20, choices=TipoServicio.choices)
    notas  = models.TextField(blank=True)  # Detalles específicos del servicio

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.evento.nombre_evento}"

    class Meta:
        verbose_name = 'Servicio Adicional'
        verbose_name_plural = 'Servicios Adicionales'

# -----------------------------------------
#  5. BITÁCORA DE INCIDENTES  
# -----------------------------------------

class Incidente(models.Model):
    '''
    Representa un incidente reportado en una sala, como daño en equipo, 
    falla técnica u otro tipo de problema.
    '''

    class TipoIncidente(models.TextChoices):
        DAÑO_EQUIPO  = 'DAÑO', 'Daño en equipo'
        FALLA_TECNICA = 'FALLA', 'Falla técnica'
        OTRO = 'OTRO', 'Otro'

    sala = models.ForeignKey(Sala, on_delete=models.CASCADE, related_name='incidentes')
    evento = models.ForeignKey(
        Evento,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='incidentes'
        )  # El incidente puede estar asociado a un evento específico o ser general
    tipo = models.CharField(max_length=20, choices=TipoIncidente.choices)
    descripcion = models.TextField()
    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_tipo_display()} en {self.sala} — {self.fecha}"

    class Meta:
        verbose_name = 'Incidente'
        verbose_name_plural = 'Incidentes'
        ordering = ['-fecha']

# -----------------------------------------
#  6. ACOMODO
# -----------------------------------------

class Acomodo(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Acomodo'
        verbose_name_plural = 'Acomodos'

# Modelo intermedio para relacionar Evento con Sala
class EventoSala(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE)
    sala = models.ForeignKey(Sala, on_delete=models.CASCADE)
    acomodo = models.ForeignKey(Acomodo, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('evento', 'sala')
        verbose_name = 'Sala Asignada'
        verbose_name_plural = 'Salas Asignadas'

    def __str__(self):
        return f"{self.sala.nombre} - {self.acomodo.nombre if self.acomodo else 'Sin acomodo'}"