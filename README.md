# Sistema de Gestión Empresarial

Sistema web integral para la administración de negocios: cuentas, compras, reportes, cierre de caja y más.

## Descripción General

**MANA** es un sistema de gestión empresarial desarrollado con Django, orientado a pequeñas y medianas empresas que necesitan centralizar el control de sus operaciones: usuarios, negocios, compras, reportes financieros y cierre de caja, todo desde una interfaz web moderna y responsiva.

---

## Stack Tecnológico

### Backend
| Tecnología | Versión | Descripción |
|---|---|---|
| **Python** | 3.x | Lenguaje principal |
| **Django** | Latest | Framework web backend |
| **SQLite3** | — | Base de datos de desarrollo |
| **Gunicorn** | Latest | Servidor WSGI para producción |

### Frontend
| Tecnología | Descripción |
|---|---|
| **HTML5 / CSS3** | Estructura y estilos de las vistas |
| **JavaScript (Vanilla)** | Interactividad del cliente |
| **Django Templates** | Motor de plantillas del lado del servidor |
| **Bootstrap / Custom CSS** | Diseño responsivo y componentes UI |

### Infraestructura & DevOps
| Tecnología | Descripción |
|---|---|
| **Procfile** | Configuración para despliegue en Heroku / Railway |
| **runtime.txt** | Especificación de versión de Python en producción |
| **python-dotenv** | Gestión de variables de entorno |
| **.gitignore** | Exclusión de archivos sensibles del repositorio |

---

## Módulos del Sistema

### `accounts` — Gestión de Usuarios
- Registro, inicio de sesión y cierre de sesión
- Control de acceso y permisos por rol
- Perfil de usuario

### `businesses` — Gestión de Negocios
- Creación y administración de negocios/sucursales
- Asociación de usuarios a negocios específicos
- Configuración general del negocio

### `purchases` — Compras
- Registro de compras y proveedores
- Historial y trazabilidad de adquisiciones
- Gestión de productos e inventario básico

### `cash_closing` — Cierre de Caja
- Registro de cierres de caja diarios
- Balance entre ingresos y egresos
- Historial de cierres por fecha y negocio

### `reports` — Reportes
- Reportes financieros por período
- Exportación y visualización de datos
- Indicadores clave de gestión (KPIs)
- Filtros avanzados por fecha, negocio o categoría

### `core` — Núcleo del Sistema
- Modelos base compartidos
- Utilidades globales y mixins
- Configuraciones transversales

### `dashboard` — Panel Principal
- Vista resumen con métricas en tiempo real
- Acceso rápido a los módulos principales
- Gráficas de actividad reciente

### `bancos` — Panel Principal
- Vista resumen con métricas en tiempo real
- Vista de todos los bancons ingresados
- Actividad de ingresos y egresos por banco

---

## Estructura del Proyecto

```
MANA-PROJECT/
│
├── apps/
│   ├── accounts/         # Gestión de usuarios y autenticación
│   ├── businesses/        # Administración de negocios
│   ├── cash_closing/      # Cierre de caja
│   ├── core/              # Lógica central compartida
│   ├── dashboard/         # Panel de control principal
│   ├── purchases/         # Módulo de compras
│   ├── reports/           # Reportes y estadísticas
│   └── __init__.py
│
├── config/                # Configuración de Django (settings, urls, wsgi, asgi)
├── static/                # Archivos estáticos (CSS, JS, imágenes)
├── templates/             # Plantillas HTML globales
├── venv/                  # Entorno virtual (excluido del repo)
│
├── .env                   # Variables de entorno (NO subir al repo)
├── .env.example           # Ejemplo de variables de entorno
├── .gitignore
├── db.sqlite3             # Base de datos SQLite (desarrollo)
├── manage.py              # CLI de Django
├── Procfile               # Configuración de despliegue
├── requirements.txt       # Dependencias del proyecto
└── runtime.txt            # Versión de Python para producción
```

---

## Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/mana-project.git
cd mana-project
```

### 2. Crear y activar entorno virtual
```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
cp .env.example .env
# Edita .env con tus valores reales
```

### 5. Aplicar migraciones
```bash
python manage.py migrate
```

### 6. Crear superusuario (opcional)
```bash
python manage.py createsuperuser
```

### 7. Recolectar archivos estáticos
```bash
python manage.py collectstatic
```

---

## Variables de Entorno

Copia `.env.example` como `.env` y configura los siguientes valores:

```env
SECRET_KEY=tu_clave_secreta_de_django
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

```

> ⚠️ **Nunca subas el archivo `.env` al repositorio.**

---

## Ejecución

### Desarrollo local
```bash
python manage.py runserver
```
Accede en: [http://127.0.0.1:8000](http://127.0.0.1:8000)

### Con Gunicorn (producción local)
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

---

## Despliegue

Este proyecto está preparado para desplegarse en plataformas como **Railway**, **Heroku** o **Render**.

### Railway / Heroku
El archivo `Procfile` ya está configurado:
```
web: gunicorn config.wsgi:application
```

El archivo `runtime.txt` especifica la versión de Python:
```
python-3.x.x
```

Asegúrate de configurar las variables de entorno `SECRET_KEY`, `DEBUG=False` y `ALLOWED_HOSTS` en el panel de tu plataforma.

---

## Base de Datos

| Entorno | Motor | Descripción |
|---|---|---|
| **Desarrollo** | SQLite3 | Archivo local `db.sqlite3`, sin configuración adicional |
| **Producción** | PostgreSQL (recomendado) | Configurable vía `DATABASE_URL` en las variables de entorno |

### Migraciones
```bash
# Crear nuevas migraciones tras cambios en modelos
python manage.py makemigrations

# Aplicar migraciones pendientes
python manage.py migrate
```

---

## Autores

Desarrollado con JUAN CAMILO POSADA ANTURÍ - KELLYN ANDREA ARAMBURO VALENCIA

---

*Este sistema fue diseñado para facilitar la gestión operativa y financiera de negocios, con un enfoque en simplicidad, trazabilidad y control.*