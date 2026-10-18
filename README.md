# PDF Receipts Manager

Servicio centralizado que **convierte HTML en PDF**, le asigna un **número correlativo por proyecto**, lo guarda en **S3** y registra sus metadatos en **PostgreSQL**. Los proyectos consumidores le envían el HTML ya armado y reciben el número de documento y una URL prefirmada para descargar el PDF.

## Características

- Generación de PDF desde HTML con **WeasyPrint**.
- Numeración independiente por proyecto (`PREFIJO-000001`, `PREFIJO-000002`, …).
- Marcador `{{documentNumber}}` en el HTML, reemplazado por el número asignado.
- Almacenamiento en **S3** (LocalStack en desarrollo) con URLs prefirmadas de 1 hora.
- Autenticación por **API Key** (`X-API-KEY`); en base de datos solo se guarda el hash SHA-256.
- Aislamiento por proyecto: un proyecto no puede consultar documentos de otro.
- Protección contra SSRF: el HTML solo puede cargar recursos `data:` o de dominios autorizados.
- Límite de tamaño de petición (3 MB).
- CLI para crear, listar y revocar API Keys.

## Arquitectura

![Arquitectura](docs/arquitectura.svg)

| Componente | Archivo | Responsabilidad |
|---|---|---|
| API | `app/main.py` | Endpoints, middleware de tamaño, ciclo de vida |
| Seguridad | `app/security.py` | Valida `X-API-KEY` y resuelve el proyecto |
| Renderer | `app/services/renderer.py` | HTML → PDF con control de recursos externos |
| Storage | `app/services/storage.py` | Subida a S3 y URLs prefirmadas |
| Datos | `app/database/db.py` | Modelos, sesión y numeración por proyecto |
| CLI | `app/cli.py` | Administración de API Keys |
| Configuración | `app/config.py` | Variables de entorno (`pydantic-settings`) |

### Flujo de creación de un documento

![Secuencia](docs/sequence.svg)

## Modelo de datos

![Diagrama ER](docs/er.svg)

Las tablas (`api_clients`, `counters`, `documents`) se crean automáticamente al iniciar la aplicación y se relacionan lógicamente por la columna `project`, sin claves foráneas.

## API

![API](docs/api.svg)

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `POST` | `/documents` | Sí | Genera el PDF, lo sube a S3 y lo registra |
| `GET` | `/documents/{documentNumber}` | Sí | Devuelve el documento con una URL prefirmada nueva |
| `GET` | `/health` | No | Estado del servicio |

Documentación interactiva (Swagger) en `http://localhost:8000/docs`.

## Estructura del proyecto

```
.
├── app/
│   ├── cli.py              # Administración de API Keys
│   ├── config.py           # Settings desde .env
│   ├── main.py             # FastAPI: endpoints y middleware
│   ├── schemas.py          # DocumentRequest / DocumentResponse
│   ├── security.py         # Validación de API Key
│   ├── database/db.py      # Modelos SQLAlchemy y numeración
│   └── services/
│       ├── renderer.py     # WeasyPrint + SafeURLFetcher
│       └── storage.py      # boto3 / S3
├── tests/                  # pytest (sin S3 ni PDF reales)
├── docker-compose.yml      # PostgreSQL + LocalStack
├── requirements.txt
├── pytest.ini
└── .env.example
```

## Requisitos

- **Python 3.12 o superior** (el proyecto fue desarrollado con Python 3.14).
- **Docker** y **Docker Compose**.
- **Librerías del sistema para WeasyPrint** (Pango). Ver la [guía oficial de instalación](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html):
  - Debian/Ubuntu: `sudo apt install libpango-1.0-0 libpangoft2-1.0-0`
  - macOS: `brew install pango`
  - Windows: instalar el runtime de GTK/Pango indicado en la guía de WeasyPrint.
- Un **token de LocalStack** (`LOCALSTACK_AUTH_TOKEN`), que se obtiene desde la cuenta de LocalStack.

## Instalación

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio> pdf-receipts-manager
cd pdf-receipts-manager

# 2. Crear y activar el entorno virtual
python -m venv .venv
source .venv/bin/activate          # Linux / macOS
# .venv\Scripts\activate           # Windows (PowerShell / CMD)

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear el archivo de configuración
cp .env.example .env               # Windows: copy .env.example .env
```

## Configuración

Edita `.env`. Valores sugeridos para desarrollo local:

```env
# S3 (LocalStack)
AWS_ENDPOINT_URL=http://localhost:4566
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_REGION=us-east-1
S3_BUCKET=receipts
LOCALSTACK_AUTH_TOKEN=<tu-token-de-localstack>

# PostgreSQL
POSTGRES_USER=receipts
POSTGRES_PASSWORD=receipts
POSTGRES_DB=receipts
DATABASE_URL=postgresql+psycopg://receipts:receipts@localhost:5432/receipts

# Dominios desde los que el HTML puede cargar imágenes/CSS (separados por coma)
ALLOWED_ASSET_HOSTS=
```

| Variable | Obligatoria | Descripción |
|---|---|---|
| `DATABASE_URL` | Sí | URL de SQLAlchemy. Con el driver instalado usa `postgresql+psycopg://…` |
| `S3_BUCKET` | No (`receipts`) | Bucket donde se guardan los PDFs. Se crea solo si no existe |
| `AWS_ENDPOINT_URL` | No | Endpoint de S3. En desarrollo apunta a LocalStack; **déjalo vacío para usar AWS real** |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | No (`test`) | Credenciales de S3 |
| `AWS_REGION` | No (`us-east-1`) | Región de S3 |
| `ALLOWED_ASSET_HOSTS` | No | Hosts permitidos para recursos externos, p. ej. `cdn.miempresa.com,assets.miempresa.com`. Vacío = solo `data:` |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Para Docker | Credenciales con las que Docker Compose crea PostgreSQL |
| `LOCALSTACK_AUTH_TOKEN` | Para LocalStack | Token de autenticación de LocalStack |

> **Importante:** el `healthcheck` de PostgreSQL en `docker-compose.yml` está fijo a usuario y base `receipts`. Mantén `POSTGRES_USER=receipts` y `POSTGRES_DB=receipts`, o ajusta el `healthcheck`.

> Las URLs prefirmadas heredan el endpoint configurado: con LocalStack apuntan a `localhost:4566` y solo son accesibles desde tu máquina.

## Levantar el proyecto

```bash
# 1. Infraestructura (PostgreSQL + LocalStack)
docker compose up -d
docker compose ps                  # esperar a que postgres esté "healthy"

# 2. API
uvicorn app.main:app --reload --port 8000
```

Al iniciar, la aplicación **crea las tablas y el bucket** automáticamente.

Verificar:

```bash
curl http://localhost:8000/health
# {"status":"ok","bucket":"receipts"}
```

### Detener

```bash
docker compose down        # conserva los datos (volumen pgdata)
docker compose down -v     # elimina también los datos
```

## Crear API Keys para los proyectos

Cada proyecto consumidor necesita su propia API Key:

```bash
python -m app.cli create-client alfa     # crear
python -m app.cli list                   # listar (id, proyecto, estado, fecha)
python -m app.cli revoke 1               # revocar por id
```

> La clave (`rk_…`) **se muestra una sola vez**. Guárdala en un gestor de secretos; en la base solo queda su hash.

El nombre del proyecto admite letras, números, guion y guion bajo (máx. 50 caracteres).

## Uso

### Crear un documento

```bash
curl -X POST http://localhost:8000/documents \
  -H "X-API-KEY: rk_tu_clave" \
  -H "Content-Type: application/json" \
  -d '{
    "externalReference": "RES-2026-0001",
    "html": "<html><body><h1>Recibo {{documentNumber}}</h1></body></html>",
    "metadata": { "cliente": "Juan Pérez", "total": 150.00 }
  }'
```

Respuesta `201`:

```json
{
  "documentNumber": "ALF-000001",
  "externalReference": "RES-2026-0001",
  "pdfUrl": "http://localhost:4566/receipts/alfa/2026/ALF-000001.pdf?X-Amz-..."
}
```

### Consultar un documento

```bash
curl http://localhost:8000/documents/ALF-000001 -H "X-API-KEY: rk_tu_clave"
```

Devuelve el mismo formato con una `pdfUrl` renovada (válida 1 hora).

### Códigos de respuesta

| Código | Motivo |
|---|---|
| `201` / `200` | Operación exitosa |
| `401` | API Key inválida, ausente o revocada |
| `404` | Documento inexistente o de otro proyecto |
| `413` | Cuerpo mayor a 3 MB |
| `422` | Cuerpo inválido (campos faltantes o fuera de límite) |

### Recursos en el HTML

- Imágenes y estilos incrustados con `data:` siempre funcionan.
- Recursos `http/https` solo se cargan si el host está en `ALLOWED_ASSET_HOSTS`.
- No se siguen redirecciones y cualquier otro protocolo (`file://`, etc.) se rechaza.

## Proyectos consumidores

Este servicio es consumido por otros proyectos mediante HTTP. Cada uno recibe su propia API Key y su propia numeración.

| Proyecto | Identificador | API Key | Numeración | Ruta en S3 |
|---|---|---|---|---|
| **Proyecto A** | `alfa` | Propia | `ALF-000001…` | `alfa/<año>/` |
| **Proyecto B** | `beta` | Propia | `BET-000001…` | `beta/<año>/` |
| **Proyecto N** | `…` | Propia | `…` | `…/<año>/` |

### Cómo integrar un proyecto nuevo

1. Registrar el proyecto: `python -m app.cli create-client <identificador>`.
2. Guardar la API Key en la configuración segura del proyecto consumidor.
3. Enviar `POST /documents` con `externalReference` (su propio identificador del recibo), `html` y, opcionalmente, `metadata`.
4. Guardar el `documentNumber` devuelto y usar `GET /documents/{documentNumber}` cuando necesite una URL nueva.

Ejemplo desde un proyecto consumidor (Node.js 18+):

```js
const res = await fetch(`${process.env.RECEIPTS_API_URL}/documents`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-API-KEY": process.env.RECEIPTS_API_KEY,
  },
  body: JSON.stringify({
    externalReference: "ORDEN-1234",
    html: "<html><body><h1>Recibo {{documentNumber}}</h1></body></html>",
    metadata: { origen: "proyecto-a" },
  }),
});

if (!res.ok) throw new Error(`Error ${res.status}`);
const { documentNumber, pdfUrl } = await res.json();
```

> **Prefijo del número:** el prefijo son las **3 primeras letras** del identificador en mayúsculas. Dos proyectos cuyos identificadores comiencen igual (p. ej. `proyecto-a` y `proyecto-b` → `PRO`) generarían el mismo número y chocarían con la restricción única de `document_number`. Usa identificadores con prefijos distintos (`alfa`, `beta`, …).

## Pruebas

```bash
pytest
```

Las pruebas usan SQLite en memoria y simulan el renderizado y S3, por lo que no requieren Docker ni WeasyPrint funcionando.

## Consideraciones para producción

- Dejar `AWS_ENDPOINT_URL` vacío y usar credenciales/roles reales de AWS.
- Cambiar las credenciales de PostgreSQL y no versionar `.env`.
- Publicar la API detrás de HTTPS.
- Definir `ALLOWED_ASSET_HOSTS` solo con dominios de confianza.
- Las tablas se crean con `create_all`; si el esquema va a evolucionar, considerar migraciones (p. ej. Alembic).
