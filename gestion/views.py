from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Sala, Evento

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