from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Sala, Evento
from .models import Sala, Evento, ReglaRecurrencia, ServicioAdicional
from .models import Sala, Evento, ReglaRecurrencia, ServicioAdicional, Incidente

'''
Vistas principales del sistema SalasMan.
Se encarga del login/logout del administrador y de construir
la vista de calendario semanal con todas las salas y eventos.
'''


# -----------------------------------------
#  CONSTANTES
# -----------------------------------------

BLOQUES_HORA = list(range(8, 19))
DIAS_SEMANA  = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']


# -----------------------------------------
#  AUXILIARES
# -----------------------------------------

'''
obtener_semana regresa una lista de 5 fechas (lunes a viernes)
según el desplazamiento de semanas recibido.
Por ejemplo: desplazamiento 0 = semana actual,
1 = siguiente semana, -1 = semana pasada.
'''

def obtener_semana(desplazamiento=0):
    hoy   = date.today()
    lunes = hoy - timedelta(days=hoy.weekday()) + timedelta(weeks=desplazamiento)
    return [lunes + timedelta(days=i) for i in range(5)]


'''
construir_cuadricula arma la cuadrícula del calendario.
Recibe los días de la semana, las salas y los eventos confirmados.
Devuelve una lista de filas, donde cada fila es un bloque horario
y cada celda contiene el evento que ocupa ese espacio (o None si está libre).

El campo 'rowspan' indica cuántos bloques ocupa el evento verticalmente.
El campo 'saltar' marca las celdas que no deben renderizarse porque
están cubiertas por el rowspan de una celda superior.
'''

def construir_cuadricula(dias, salas, eventos):

    # Inicializar la cuadrícula vacía con todas las combinaciones día/sala/hora
    cuadricula = {}
    for dia in dias:
        cuadricula[dia] = {}
        for sala in salas:
            cuadricula[dia][sala.id] = {
                hora: {
                    'evento':  None,
                    'rowspan': 1,
                    'saltar':  False,
                    'sala':    sala,
                    'dia':     dia,
                }
                for hora in BLOQUES_HORA
            }

    # Llenar la cuadrícula con los eventos confirmados
    for evento in eventos:
        h_inicio = evento.hora_inicio.hour
        h_fin = evento.hora_fin.hour
        duracion = h_fin - h_inicio

        for sala in evento.salas.all():
            if sala.id not in cuadricula.get(evento.fecha, {}):
                continue

            # Celda donde empieza el evento: guardar datos y rowspan
            if h_inicio in cuadricula[evento.fecha][sala.id]:
                cuadricula[evento.fecha][sala.id][h_inicio].update({
                    'evento':  evento,
                    'rowspan': duracion,
                })

            # Celdas siguientes: marcar como saltar para no renderizarlas
            for h in range(h_inicio + 1, h_fin):
                if h in cuadricula[evento.fecha][sala.id]:
                    cuadricula[evento.fecha][sala.id][h]['saltar'] = True

    # Convertir la cuadrícula a una lista de filas para el template
    filas = []
    for hora in BLOQUES_HORA:
        celdas = []
        for dia in dias:
            for sala in salas:
                celdas.append(cuadricula[dia][sala.id][hora])
        filas.append({
            'etiqueta_hora': f'{hora:02d}:00',
            'hora_fin':      f'{hora + 1:02d}:00',
            'celdas':        celdas,
        })

    return filas


# -----------------------------------------
#  1. LOGIN
# -----------------------------------------

'''
Vista de login del administrador.
Si el usuario ya tiene sesión activa, lo redirige directo al calendario.
Si las credenciales son incorrectas, muestra un mensaje de error.
Solo el superusuario o staff puede acceder al sistema.
'''

def vista_login(request):
    if request.user.is_authenticated:
        return redirect('gestion:calendario')

    if request.method == 'POST':
        usuario = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password'),
        )
        if usuario:
            login(request, usuario)
            return redirect('gestion:calendario')
        messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'gestion/login.html')


# -----------------------------------------
#  2. LOGOUT
# -----------------------------------------


def vista_logout(request):
    logout(request)
    return redirect('gestion:login')


# -----------------------------------------
#  3. CALENDARIO
# -----------------------------------------

'''
Vista principal del sistema. Muestra la cuadrícula semanal de lunes a viernes
con las 3 salas como columnas y los bloques horarios como filas.

Recibe el parámetro 'semana' desde la URL (?semana=1) para navegar
entre semanas. El valor 0 siempre es la semana actual.

Solo muestra eventos con estado CONFIRMADO.
Requiere que el administrador tenga sesión activa.
'''

@login_required(login_url='gestion:login')
def calendario(request):
    desplazamiento = int(request.GET.get('semana', 0))
    dias           = obtener_semana(desplazamiento)
    salas          = Sala.objects.all().order_by('nombre')

    eventos = (
        Evento.objects
        .filter(fecha__range=[dias[0], dias[-1]], estado='CONFIRMADO')
        .prefetch_related('salas')
    )

    filas = construir_cuadricula(dias, salas, eventos)

    # Armar lista de días con nombre en español y fecha formateada
    datos_dias = [
        {
            'fecha':     d,
            'nombre':    DIAS_SEMANA[d.weekday()],
            'fecha_str': d.strftime('%d/%m'),
        }
        for d in dias
    ]

    contexto = {
        'datos_dias': datos_dias,
        'salas': salas,
        'filas': filas,
        'desplazamiento': desplazamiento,
        'semana_previa': desplazamiento - 1,
        'semana_siguiente': desplazamiento + 1,
        'etiqueta_semana': f"{dias[0].strftime('%d %b')} – {dias[-1].strftime('%d %b %Y')}",
    }
    return render(request, 'gestion/calendario.html', contexto)

# -----------------------------------------
#  4. CREAR EVENTO
# -----------------------------------------

'''
Vista para crear un nuevo evento.
Muestra un formulario con todos los campos del modelo Evento.
Si el formulario es válido, guarda el evento y redirige al calendario.
'''

@login_required(login_url='gestion:login')
def crear_evento(request):
    salas = Sala.objects.all().order_by('nombre')
    if request.method == 'POST':
        nombre_evento = request.POST.get('nombre_evento')
        nombre_responsable = request.POST.get('nombre_responsable')
        correo_responsable = request.POST.get('correo_responsable')
        num_asistentes = request.POST.get('num_asistentes')
        fecha = request.POST.get('fecha')
        hora_inicio = request.POST.get('hora_inicio')
        hora_fin = request.POST.get('hora_fin')
        salas_ids = request.POST.getlist('salas')
        notas = request.POST.get('notas')

        try:
            evento = Evento(
                nombre_evento=nombre_evento,
                nombre_responsable=nombre_responsable,
                correo_responsable=correo_responsable,
                num_asistentes=num_asistentes,
                fecha=fecha,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                notas=notas,
            )
            evento.full_clean()
            evento.save()
            evento.salas.set(salas_ids)

            recurrencia = request.POST.get('recurrencia')
            fecha_fin_serie = request.POST.get('fecha_fin_serie')
            if recurrencia and fecha_fin_serie:
                ReglaRecurrencia.objects.create(
                    evento_base=evento,
                    tipo=recurrencia,
                    fecha_fin_serie=fecha_fin_serie,
                )

            servicios_ids = request.POST.getlist('servicios')
            for tipo in servicios_ids:
                ServicioAdicional.objects.create(
                    evento=evento,
                    tipo=tipo,
                )

            return redirect('gestion:calendario')
        except Exception as e:
            contexto = {'salas': salas, 'errores': e.message_dict if hasattr(e, 'message_dict') else {'error': [str(e)]}}
            return render(request, 'gestion/crear_evento.html', contexto)

    contexto = {'salas': salas}
    return render(request, 'gestion/crear_evento.html', contexto)
# -----------------------------------------
#  5. LISTA DE INCIDENCIAS
# -----------------------------------------

'''
Vista para listar todas las incidencias reportadas.
Muestra la lista ordenada por fecha descendente.
'''

@login_required(login_url='gestion:login')
def lista_incidencias(request):
    incidencias = Incidente.objects.all().select_related('sala', 'evento')
    contexto = {'incidencias': incidencias}
    return render(request, 'gestion/lista_incidencias.html', contexto)


# -----------------------------------------
#  6. CREAR INCIDENCIA
# -----------------------------------------

'''
Vista para reportar una nueva incidencia.
Muestra un formulario con sala, evento, tipo y descripción.
'''

@login_required(login_url='gestion:login')
def crear_incidencia(request):
    salas = Sala.objects.all().order_by('nombre')
    eventos = Evento.objects.all().order_by('-fecha')
    if request.method == 'POST':
        try:
            sala_id = request.POST.get('sala')
            evento_id = request.POST.get('evento')
            tipo = request.POST.get('tipo')
            descripcion = request.POST.get('descripcion')

            incidencia = Incidente(
                sala_id=sala_id,
                evento_id=evento_id if evento_id else None,
                tipo=tipo,
                descripcion=descripcion,
            )
            incidencia.save()
            return redirect('gestion:lista_incidencias')
        except Exception as e:
            contexto = {'salas': salas, 'eventos': eventos, 'error': str(e)}
            return render(request, 'gestion/crear_incidencia.html', contexto)

    contexto = {'salas': salas, 'eventos': eventos}
    return render(request, 'gestion/crear_incidencia.html', contexto)
# -----------------------------------------
#  7. DETALLE DE EVENTO
# -----------------------------------------

'''
Vista para ver el detalle de un evento específico.
Muestra toda la información del evento, sus salas, servicios y recurrencia.
'''

@login_required(login_url='gestion:login')
def detalle_evento(request, evento_id):
    evento = Evento.objects.prefetch_related('salas', 'servicios').select_related('regla_recurrencia').get(id=evento_id)
    contexto = {'evento': evento}
    return render(request, 'gestion/detalle_evento.html', contexto)
# -----------------------------------------
#  8. EDITAR EVENTO
# -----------------------------------------

'''
Vista para editar un evento existente.
Carga los datos actuales en el formulario y los actualiza al hacer POST.
'''

@login_required(login_url='gestion:login')
def editar_evento(request, evento_id):
    evento = Evento.objects.prefetch_related('salas', 'servicios').select_related('regla_recurrencia').get(id=evento_id)
    salas = Sala.objects.all().order_by('nombre')

    if request.method == 'POST':
        try:
            evento.nombre_evento = request.POST.get('nombre_evento')
            evento.nombre_responsable = request.POST.get('nombre_responsable')
            evento.correo_responsable = request.POST.get('correo_responsable')
            evento.num_asistentes = request.POST.get('num_asistentes')
            evento.fecha = request.POST.get('fecha')
            evento.hora_inicio = request.POST.get('hora_inicio')
            evento.hora_fin = request.POST.get('hora_fin')
            evento.notas = request.POST.get('notas')
            evento.full_clean()
            evento.save()
            evento.salas.set(request.POST.getlist('salas'))

            recurrencia = request.POST.get('recurrencia')
            fecha_fin_serie = request.POST.get('fecha_fin_serie')
            if recurrencia and fecha_fin_serie:
                ReglaRecurrencia.objects.update_or_create(
                    evento_base=evento,
                    defaults={'tipo': recurrencia, 'fecha_fin_serie': fecha_fin_serie}
                )
            else:
                ReglaRecurrencia.objects.filter(evento_base=evento).delete()

            evento.servicios.all().delete()
            for tipo in request.POST.getlist('servicios'):
                ServicioAdicional.objects.create(evento=evento, tipo=tipo)

            return redirect('gestion:detalle_evento', evento_id=evento.id)
        except Exception as e:
            contexto = {'evento': evento, 'salas': salas, 'errores': e.message_dict if hasattr(e, 'message_dict') else {'error': [str(e)]}}
            return render(request, 'gestion/editar_evento.html', contexto)

    contexto = {'evento': evento, 'salas': salas}
    return render(request, 'gestion/editar_evento.html', contexto)  
# -----------------------------------------
#  9. ELIMINAR EVENTO
# -----------------------------------------

'''
Vista para eliminar un evento existente.
Solicita confirmación antes de eliminar.
'''

@login_required(login_url='gestion:login')
def eliminar_evento(request, evento_id):
    evento = Evento.objects.get(id=evento_id)
    if request.method == 'POST':
        evento.delete()
        return redirect('gestion:calendario')
    contexto = {'evento': evento}
    return render(request, 'gestion/eliminar_evento.html', contexto)


# -----------------------------------------
#  10. ADMINISTRACIÓN DE SALAS
# -----------------------------------------

@login_required(login_url='gestion:login')
def admin_salas(request):
    salas = Sala.objects.all().order_by('nombre')
    contexto = {
        'salas': salas,
        'puede_agregar': request.user.is_superuser,
    }
    return render(request, 'gestion/admin_salas.html', contexto)


@login_required(login_url='gestion:login')
@user_passes_test(lambda u: u.is_superuser, login_url='gestion:admin_salas')
def crear_sala(request):
    tipos = Sala.TipoSala.choices

    if request.method == 'POST':
        try:
            sala = Sala(
                nombre=request.POST.get('nombre'),
                tipo=request.POST.get('tipo'),
                capacidad=request.POST.get('capacidad'),
            )
            sala.full_clean()
            sala.save()
            messages.success(request, f'Sala "{sala.nombre}" creada correctamente.')
            return redirect('gestion:admin_salas')
        except Exception as e:
            errores = e.message_dict if hasattr(e, 'message_dict') else {'error': [str(e)]}
            return render(request, 'gestion/crear_sala.html', {'tipos': tipos, 'errores': errores})

    return render(request, 'gestion/crear_sala.html', {'tipos': tipos})


@login_required(login_url='gestion:login')
@user_passes_test(lambda u: u.is_superuser, login_url='gestion:admin_salas')
def eliminar_sala(request, sala_id):
    sala = Sala.objects.get(id=sala_id)
    num_incidencias = sala.incidentes.count()
    num_eventos = sala.eventos.count()

    if request.method == 'POST':
        nombre = sala.nombre
        sala.delete()
        msg = f'Sala "{nombre}" eliminada correctamente.'
        if num_incidencias:
            msg += f' Se eliminaron {num_incidencias} incidencia(s) asociada(s) en cascada.'
        messages.success(request, msg)
        return redirect('gestion:admin_salas')

    contexto = {
        'sala': sala,
        'num_incidencias': num_incidencias,
        'num_eventos': num_eventos,
        'hay_cascada': num_incidencias > 0,
    }
    return render(request, 'gestion/eliminar_sala.html', contexto)

# -----------------------------------------
#  11. EDITAR INCIDENCIA
# -----------------------------------------

@login_required(login_url='gestion:login')
@user_passes_test(lambda u: u.is_superuser, login_url='gestion:lista_incidencias')
def editar_incidencia(request, incidencia_id):
    incidencia = Incidente.objects.select_related('sala', 'evento').get(id=incidencia_id)
    salas = Sala.objects.all().order_by('nombre')
    eventos = Evento.objects.all().order_by('-fecha')

    if request.method == 'POST':
        try:
            sala_id = request.POST.get('sala')
            evento_id = request.POST.get('evento')

            incidencia.sala_id = sala_id
            incidencia.evento_id = evento_id if evento_id else None
            incidencia.tipo = request.POST.get('tipo')
            incidencia.descripcion = request.POST.get('descripcion')

            incidencia.save()
            return redirect('gestion:lista_incidencias')
        except Exception as e:
            contexto = {'incidencia': incidencia, 'salas': salas, 'eventos': eventos, 'error': str(e)}
            return render(request, 'gestion/editar_incidencia.html', contexto)

    contexto = {'incidencia': incidencia, 'salas': salas, 'eventos': eventos}
    return render(request, 'gestion/editar_incidencia.html', contexto)


# -----------------------------------------
#  12. ELIMINAR INCIDENCIA
# -----------------------------------------

@login_required(login_url='gestion:login')
@user_passes_test(lambda u: u.is_superuser, login_url='gestion:lista_incidencias')
def eliminar_incidencia(request, incidencia_id):
    incidencia = Incidente.objects.get(id=incidencia_id)
    if request.method == 'POST':
        incidencia.delete()
        return redirect('gestion:lista_incidencias')
        
    return redirect('gestion:lista_incidencias')