# Proyecto-BD

Instrucciones para que todos tengamos la misma base y tener conectado la base de datos con PostgreSQL.

````markdown

### 1. Setup inicial

```bash
# Clonar el repositorio

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
.\venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
````

---

### 2. Crear el archivo .env 

Por seguridad, el archivo `.env` no se debe subir a GitHub, entonces cada quien debe crear el suyo.

1. En la carpeta principal del proyecto, crea un archivo llamado `.env`.
2. Copia y pega esto:

```env
DB_NAME=salasman_db
DB_USER=postgres
DB_PASSWORD=TU_CONTRASEÑA
DB_HOST=localhost
DB_PORT=5432

SECRET_KEY=django-insecure-salasman-local-key
DEBUG=True
```

Cambia `TU_CONTRASEÑA` por tu contraseña de PostgreSQL.

Para el `SECRET_KEY` puedes pedirle a django que te genere una segura en la terminal usando lo siguiente: 

```text
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

---

### 3. Crear la base de datos

1. Abre **pgAdmin 4**.
2. Crea una base de datos llamada:

```text
salasman_db
```

3. Verifica que el nombre sea igual al que pusiste en `DB_NAME`.

---

### 4. Configurar la base de datos

En la terminal de VS Code ejecuta:

```bash
# Crear tablas
python manage.py migrate

# Crear usuario administrador
python manage.py createsuperuser
```

---

### 5. Ejecutar el proyecto

```bash
python manage.py runserver
```

Después abre:

* App: [http://127.0.0.1:8000](http://127.0.0.1:8000)
* Admin: [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)

---

## Notas importantes

* Si haces cambios en `models.py`, usa:

```bash
python manage.py makemigrations
python manage.py migrate
```

* No subas el archivo `.env` a GitHub.
```
