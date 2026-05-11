from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# ─────────────────────────────────────────
#  1. SALA
# ─────────────────────────────────────────

class Sala(models.Model):

    class TipoSala(models.TextChoices):
        AULA       = 'AULA',       'Aula (Sillas y mesas)'
        AUDITORIO  = 'AUDITORIO',  'Auditorio (Sillas)'
        HERRADURA  = 'HERRADURA',  'Herradura (Configuración en U)'

    nombre    = models.CharField(max_length=100)
    tipo      = models.CharField(max_length=20, choices=TipoSala.choices)
    capacidad = models.PositiveIntegerField(default=40)

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

    class Meta:
        verbose_name      = 'Sala'
        verbose_name_plural = 'Salas'


# ─────────────────────────────────────────
#  2. EVENTO
# ─────────────────────────────────────────

class Evento(models.Model):

    class EstadoEvento(models.TextChoices):
        CONFIRMADO = 'CONFIRMADO', 'Confirmado'
        CANCELADO  = 'CANCELADO',  'Cancelado'
        PENDIENTE  = 'PENDIENTE',  'Pendiente'

    # Datos del responsable y el evento
    nombre_responsable = models.CharField(max_length=200)
    correo_responsable = models.EmailField(blank=True)  # Para comunicación por correo
    nombre_evento      = models.CharField(max_length=200)
    num_asistentes     = models.PositiveIntegerField()
    estado             = models.CharField(
                            max_length=20,
                            choices=EstadoEvento.choices,
                            default=EstadoEvento.CONFIRMADO
                        )

    # Fecha y bloques horarios (8am–7pm en bloques de 1 hora)
    fecha      = models.DateField()
    hora_inicio = models.TimeField()  # Ej: 08:00
    hora_fin    = models.TimeField()  # Ej: 13:00

    # Salas asignadas (puede ser 1, 2 o 3 según asistentes)
    salas = models.ManyToManyField(Sala, related_name='eventos')

    # Notas adicionales del admin
    notas = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nombre_evento} — {self.fecha} ({self.hora_inicio}–{self.hora_fin})"

    def clean(self):
        # Validar que el evento sea lunes a viernes
        if self.fecha and self.fecha.weekday() > 4:  # 5=sábado, 6=domingo
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


# ─────────────────────────────────────────
#  3. EVENTO RECURRENTE
# ─────────────────────────────────────────

class ReglaRecurrencia(models.Model):
    """
    Define el patrón de repetición de un evento base.
    Cada instancia generada se guarda como un Evento independiente
    con referencia a esta regla — así un conflicto en una fecha
    solo cancela esa instancia, no toda la serie.
    """

    class TipoRecurrencia(models.TextChoices):
        DIARIA   = 'DIARIA',   'Diaria'
        SEMANAL  = 'SEMANAL',  'Semanal'
        MENSUAL  = 'MENSUAL',  'Mensual'
        ANUAL    = 'ANUAL',    'Anual'

    evento_base    = models.OneToOneField(
                        Evento,
                        on_delete=models.CASCADE,
                        related_name='recurrencia'
                    )
    tipo           = models.CharField(max_length=10, choices=TipoRecurrencia.choices)
    fecha_fin_serie = models.DateField()  # Hasta cuándo se repite

    def __str__(self):
        return f"Recurrencia {self.tipo} → {self.evento_base.nombre_evento} hasta {self.fecha_fin_serie}"

    class Meta:
        verbose_name        = 'Regla de Recurrencia'
        verbose_name_plural = 'Reglas de Recurrencia'


# ─────────────────────────────────────────
#  4. SERVICIOS ADICIONALES  (Fase 2)
# ─────────────────────────────────────────

class ServicioAdicional(models.Model):

    class TipoServicio(models.TextChoices):
        ACOMODO         = 'ACOMODO',        'Acomodo de mobiliario'
        SONIDO          = 'SONIDO',         'Equipo de sonido'
        CAFETERIA       = 'CAFETERIA',      'Cafetería'
        VIDEOCONFERENCIA = 'VIDEOCONF',     'Videoconferencia'

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
        verbose_name        = 'Servicio Adicional'
        verbose_name_plural = 'Servicios Adicionales'


# ─────────────────────────────────────────
#  5. BITÁCORA DE INCIDENTES  (Fase 2)
# ─────────────────────────────────────────

class Incidente(models.Model):

    class TipoIncidente(models.TextChoices):
        DAÑO_EQUIPO  = 'DAÑO',    'Daño en equipo'
        FALLA_TECNICA = 'FALLA',  'Falla técnica'
        OTRO         = 'OTRO',    'Otro'

    sala        = models.ForeignKey(Sala, on_delete=models.CASCADE, related_name='incidentes')
    evento      = models.ForeignKey(
                    Evento,
                    on_delete=models.SET_NULL,
                    null=True, blank=True,
                    related_name='incidentes'
                  )  # El incidente puede estar asociado a un evento específico o ser general
    tipo        = models.CharField(max_length=20, choices=TipoIncidente.choices)
    descripcion = models.TextField()
    fecha       = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_tipo_display()} en {self.sala} — {self.fecha}"

    class Meta:
        verbose_name        = 'Incidente'
        verbose_name_plural = 'Incidentes'
        ordering            = ['-fecha']