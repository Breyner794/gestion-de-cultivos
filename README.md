# Sistema de Gestión de Cultivos

Producto mínimo viable (MVP) para controlar el ciclo productivo de un cultivo y las labores de campo: fumigaciones, abonadas, riegos, podas y cosechas.

El cliente llevaba todo en cuadernos y hojas de cálculo sueltas. Este sistema centraliza esa información y responde tres preguntas que antes no tenían respuesta: **cuándo se fumigó cada lote**, **cuánto falta para cosechar** y **cuánto ha costado el ciclo**.

---

## Tabla de contenido

- [Qué hace el sistema](#qué-hace-el-sistema)
- [Tecnologías](#tecnologías)
- [Instalación](#instalación)
- [Cómo ejecutar el proyecto](#cómo-ejecutar-el-proyecto)
- [Usuarios de prueba](#usuarios-de-prueba)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Modelo de datos](#modelo-de-datos)
- [Casos de uso implementados](#casos-de-uso-implementados)
- [Reglas de negocio](#reglas-de-negocio)
- [API](#api)
- [Preguntas frecuentes](#preguntas-frecuentes)

---

## Qué hace el sistema

| Módulo | Para qué sirve |
|---|---|
| **Empleados** | Registra a quienes ejecutan las labores: fumigadores, recolectores, agrónomos. |
| **Cultivos y lotes** | Define qué se siembra (con sus días de ciclo y periodo de carencia) y dónde. |
| **Ciclo productivo** | Abre un ciclo en un lote, calcula la fecha estimada de cosecha y muestra el avance. |
| **Labores de campo** | Registra fumigaciones, fertilizaciones, riegos y podas, con responsable, producto y costo. También permite programarlas a futuro. |
| **Cosechas** | Registra el kilaje recogido y calcula el rendimiento por hectárea. |
| **Reportes** | Historial de labores, costos por tipo, próximas labores y exportación a CSV o Excel. |

### Actores

- **Administrador** — usuario principal. Registra, programa y consulta todo.
- **Empleado** — responsable de las labores. Entra con su propia cuenta en modo consulta: ve únicamente las labores y cosechas donde figura como responsable.

> **Nota sobre el alcance original:** el documento de especificación no contemplaba un login, pero sí definía dos actores con responsabilidades distintas. Sin autenticación no habría forma de distinguirlos ni de proteger los datos, así que se añadió un login con dos roles. Es la única adición al alcance planteado.

---

## Tecnologías

| Capa | Herramienta | Versión |
|---|---|---|
| Backend | Python + Django | 3.13 · 5.2 LTS |
| API | Django REST Framework | 3.16 |
| Base de datos | PostgreSQL | 17 |
| Frontend | React + Vite | 19 · 8 |
| Estilos | Tailwind CSS | 4 |
| Componentes | shadcn/ui | — |
| Autenticación | JWT (SimpleJWT) | 5.5 |
| Exportación | openpyxl | 3.1 |

---

## Instalación

Solo se hace **una vez**. Si ya tienes el proyecto funcionando, salta a [Cómo ejecutar el proyecto](#cómo-ejecutar-el-proyecto).

### 1. Requisitos

Instala estos tres programas. En Windows, lo más rápido es abrir **PowerShell como administrador** y correr:

```bash
winget install Python.Python.3.13 --scope machine
```

```bash
winget install PostgreSQL.PostgreSQL.17
```

```bash
winget install OpenJS.NodeJS.LTS
```

En el instalador de PostgreSQL deja todo por defecto y, cuando pida la contraseña del usuario `postgres`, escribe `postgres`.

**Cierra y vuelve a abrir la terminal** antes de seguir. Los programas recién instalados no aparecen hasta que lo hagas.

Verifica que quedaron bien:

```bash
python --version
```

```bash
node --version
```

### 2. Clonar el repositorio

```bash
git clone <url-del-repositorio>
```

```bash
cd Sistema-gestion-cultivos
```

### 3. Crear la base de datos

```bash
powershell -ExecutionPolicy Bypass -File scripts/instalar-db.ps1
```

Esto crea la base `gestion_cultivos` y enciende el servidor. Si el script falla, mira [Preguntas frecuentes](#preguntas-frecuentes).

### 4. Preparar el backend

```bash
cd backend
```

```bash
python -m venv .venv
```

```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Copia el archivo de configuración:

```bash
copy .env.example .env
```

Si usaste otra contraseña para PostgreSQL, ábrelo y cámbiala en `DATABASE_URL`.

### 5. Crear las tablas y cargar datos de ejemplo

```bash
.venv\Scripts\python.exe manage.py migrate
```

```bash
.venv\Scripts\python.exe manage.py seed
```

El primer comando crea las tablas a partir de los modelos. El segundo carga dos cultivos, dos lotes, tres empleados, un ciclo en curso con labores y una cosecha, para que el sistema no se vea vacío la primera vez.

### 6. Preparar el frontend

```bash
cd ../frontend
```

```bash
npm install
```

---

## Cómo ejecutar el proyecto

Cada vez que vayas a trabajar necesitas **tres cosas encendidas**: la base de datos, el backend y el frontend. Abre una terminal para cada una.

### Terminal 1 — Base de datos

```bash
powershell -ExecutionPolicy Bypass -File scripts/iniciar-db.ps1
```

Solo tarda un segundo y se queda encendida. Para apagarla al terminar:

```bash
powershell -ExecutionPolicy Bypass -File scripts/detener-db.ps1
```

### Terminal 2 — Backend

```bash
cd backend
```

```bash
.venv\Scripts\python.exe manage.py runserver 8000
```

### Terminal 3 — Frontend

```bash
cd frontend
```

```bash
npm run dev
```

Abre **http://localhost:5173** en el navegador.

Puedes explorar la API desde el navegador en **http://localhost:8000/api/** y el panel de
administración de Django en **http://localhost:8000/admin/**.

---

## Usuarios de prueba

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@cultivos.com` | `admin123` |
| Empleado | `carlos@cultivos.com` | `empleado123` |

> Estas credenciales son solo para desarrollo. En un despliegue real hay que cambiarlas y generar una `SECRET_KEY` nueva.

---

## Estructura del proyecto

```
Sistema-gestion-cultivos/
├── backend/
│   ├── manage.py              Comandos de Django
│   ├── config/
│   │   ├── settings.py        Configuración del proyecto
│   │   └── urls.py            Rutas principales
│   ├── cultivos/              La aplicación del sistema
│   │   ├── models.py          Las siete tablas
│   │   ├── serializers.py     Validación de entrada y salida
│   │   ├── views.py           La lógica de cada módulo
│   │   ├── urls.py            Rutas de la API
│   │   ├── permissions.py     Control de acceso por rol
│   │   ├── exceptions.py      Formato uniforme de errores
│   │   ├── admin.py           Panel de administración
│   │   ├── migrations/        Historial de cambios en la base
│   │   └── management/commands/seed.py   Datos de ejemplo
│   ├── sql/schema.sql         Las tablas en SQL (solo referencia)
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   └── src/
│       ├── pages/             Una página por módulo
│       ├── components/        Layout y piezas reutilizables
│       ├── components/ui/     Componentes de shadcn/ui
│       ├── context/           Sesión del usuario
│       └── lib/api.js         Llamadas al backend
│
├── scripts/                   Encender y apagar PostgreSQL
├── context/                   Documento y diagrama originales
└── README.md
```

---

## Modelo de datos

```
cultivos ──< lotes ──< ciclos ──< labores >── empleados
                           │                      │
                           └──< cosechas >────────┘

usuarios >── empleados        (un empleado puede tener cuenta)
```

| Tabla | Guarda |
|---|---|
| `empleados` | Nombre, documento, cargo, teléfono. |
| `usuarios` | Cuentas de acceso, con rol y vínculo opcional a un empleado. |
| `cultivos` | Especie, variedad, días de ciclo y **periodo de carencia**. |
| `lotes` | Nombre, ubicación, área en hectáreas y a qué cultivo pertenece. |
| `ciclos` | Fecha de inicio, fecha estimada de cosecha, fecha real y estado. |
| `labores` | Tipo, fechas programada y ejecutada, producto, dosis, costo y responsable. |
| `cosechas` | Fecha, kilos, calidad y recolector. |

Las tablas las crea Django con `manage.py migrate`, a partir de `cultivos/models.py`. No hay que escribir SQL.

Si quieres ver el SQL que Django genera, está en [`backend/sql/schema.sql`](backend/sql/schema.sql), o lo puedes consultar en cualquier momento con:

```bash
.venv\Scripts\python.exe manage.py sqlmigrate cultivos 0001
```

### Panel de administración

Django trae un panel para ver y editar las tablas directamente, sin pasar por la aplicación. Está en **http://localhost:8000/admin/** y se entra con el usuario administrador. Es útil para corregir datos a mano o revisar qué quedó guardado.

---

## Casos de uso implementados

Corresponden al diagrama de casos de uso en `context/diagrama.jpeg`.

Todos están en `cultivos/views.py`, cada módulo en su propia clase.

| Módulo | Casos de uso | Clase |
|---|---|---|
| Empleados | CU-01, CU-02 | `EmpleadoViewSet` |
| Cultivos y lotes | CU-03 a CU-05 | `CultivoViewSet` · `LoteViewSet` |
| Ciclo productivo | CU-06 a CU-08 | `CicloViewSet` |
| Labores de campo | CU-09 a CU-16 | `LaborViewSet` |
| Cosechas | CU-17 a CU-19 | `CosechaViewSet` |
| Reportes | CU-20 a CU-25 | `ReportesViewSet` |

### Casos de uso de apoyo

Los tres casos amarillos del diagrama, que otros casos invocan:

| Caso de apoyo | Cómo se implementó |
|---|---|
| **Verificar periodo de carencia** `«include»` | `serializers.py` → `CosechaSerializer.verificar_periodo_carencia()`. Sin esta verificación la cosecha no se registra. |
| **Validar datos** `«include»` | Los serializers rechazan datos inválidos antes de llegar a la base de datos. |
| **Seleccionar empleado responsable** `«include»` | `serializers.py` → `LaborSerializer.validate()` comprueba que el empleado exista y esté activo. |
| **Exportar a CSV/Excel** `«extend»` | `ReportesViewSet.exportar_csv()` y `exportar_excel()`. Es opcional: los reportes funcionan completos sin exportarlos. |

---

## Reglas de negocio

Estas son las validaciones que el sistema aplica y que conviene conocer antes de probarlo:

1. **Periodo de carencia.** Si un lote se fumigó hace menos días que el periodo de carencia del cultivo, el sistema **bloquea el registro de la cosecha** y dice desde qué fecha se puede cosechar. Es el caso de uso `«include»` más importante del diagrama: protege la inocuidad de la fruta.

2. **Un ciclo activo por lote.** No se puede abrir un ciclo nuevo en un lote que ya tiene uno en curso.

3. **Ciclos cerrados.** No se registran labores ni cosechas en un ciclo cerrado.

4. **Fecha de cosecha calculada.** Al iniciar un ciclo, la fecha estimada sale de `fecha_inicio + días_ciclo del cultivo`. No se escribe a mano.

5. **Labor programada vs. ejecutada.** Si registras una labor sin fecha de ejecución queda como *programada* y aparece en "Próximas labores". Cuando se hace, se marca como ejecutada.

6. **Empleados y lotes no se borran, se desactivan.** Así no se pierde el historial de quién hizo qué.

7. **Permisos.** El administrador puede crear, editar y exportar. El empleado solo consulta, y únicamente lo suyo.

---

## API

Con el servidor encendido puedes recorrer la API desde el navegador en **http://localhost:8000/api/**: Django REST Framework genera una página por cada ruta donde se ven los datos y se pueden probar las peticiones.

| Método | Ruta | Qué hace |
|---|---|---|
| `POST` | `/api/auth/login` | Inicia sesión y devuelve el token |
| `GET` | `/api/auth/yo` | Datos del usuario conectado |
| `GET` `POST` `PUT` `DELETE` | `/api/empleados` | Gestión de empleados |
| `GET` `POST` `PUT` `DELETE` | `/api/cultivos` · `/api/lotes` | Cultivos y lotes |
| `GET` `POST` | `/api/ciclos` | Ciclos productivos |
| `GET` | `/api/ciclos/estado` | Días transcurridos y restantes |
| `POST` | `/api/ciclos/{id}/cerrar` | Cierra un ciclo |
| `GET` `POST` `PUT` `DELETE` | `/api/labores` | Labores de campo |
| `GET` | `/api/labores/proximas` | Labores programadas a futuro |
| `POST` | `/api/labores/{id}/ejecutar` | Marca una labor como hecha |
| `GET` `POST` `DELETE` | `/api/cosechas` | Cosechas |
| `GET` | `/api/cosechas/kilaje/{ciclo_id}` | Kilos totales y por hectárea |
| `GET` | `/api/reportes/resumen` | Cifras del panel |
| `GET` | `/api/reportes/ciclos` · `/costos` · `/historial` | Reportes |
| `GET` | `/api/reportes/exportar/csv` · `/excel` | Descarga de reportes |

Todas las rutas excepto `/api/auth/login` necesitan el encabezado `Authorization: Bearer <token>`.

---

## Preguntas frecuentes

**El backend dice `connection refused` o `no se pudo conectar`.**
La base de datos está apagada. Corre `scripts/iniciar-db.ps1`.

**El instalador de PostgreSQL falló con "Failed to initialise the database cluster with initdb".**
Es un problema conocido del instalador en Windows 11: intenta crear la base dentro de `C:\Program Files` con una cuenta sin permisos. Los programas sí quedaron instalados; solo falta la base. Corre `scripts/instalar-db.ps1`, que la crea en tu carpeta de usuario sin ese problema.

**PostgreSQL no arranca solo al prender el computador.**
Es a propósito: la base vive en tu carpeta de usuario y se enciende con `scripts/iniciar-db.ps1`. Si la quieres como servicio automático, abre PowerShell **como administrador** y corre:

```bash
& "C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe" register -N postgresql-17 -D "$env:USERPROFILE\PostgreSQL\17\data" -S auto
```

**El frontend carga pero no muestra datos.**
El backend está apagado. Revisa que la Terminal 2 esté corriendo en el puerto 8000.

**Cambié algo en `models.py` y la base no se actualizó.**
Django no cambia las tablas solo. Cada vez que modifiques un modelo hay que generar la migración y aplicarla:

```bash
.venv\Scripts\python.exe manage.py makemigrations
```

```bash
.venv\Scripts\python.exe manage.py migrate
```

El archivo que se crea en `cultivos/migrations/` **sí se sube al repositorio**: es el historial de cómo fue cambiando la base de datos.

**PowerShell dice que no puede ejecutar scripts.**
Usa los comandos tal como están en este README, con `-ExecutionPolicy Bypass`.

**Quiero empezar de cero con la base de datos.**
Borra la base y vuelve a cargar los datos:

```bash
psql -U postgres -c "DROP DATABASE gestion_cultivos;" -c "CREATE DATABASE gestion_cultivos;"
```

```bash
cd backend
```

```bash
.venv\Scripts\python.exe manage.py migrate
```

```bash
.venv\Scripts\python.exe manage.py seed
```

---

## Fuera del alcance del MVP

Según lo definido en la presentación del proyecto, estos puntos quedan por fuera:

- Despliegue en la nube o acceso multiusuario simultáneo
- Facturación electrónica
- Predicciones o analítica avanzada
- Aplicación móvil
- Ventas y clientes

---

**Autora del proyecto:** Sara Sofia
