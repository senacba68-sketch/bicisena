# Bicisena – despliegue correcto (Render) y ejecución local

Este ZIP ya viene corregido para que:
- NO dependa de localhost en producción
- Use variables de entorno (DB_HOST, DB_USER, etc) o DATABASE_URL
- Tenga endpoint de salud `/` para verificar el servicio

---

## 1) Ejecutar en LOCAL (XAMPP / MySQL)

### A. Requisitos
- Python 3.10+ instalado
- MySQL corriendo (XAMPP)

### B. Crear entorno e instalar dependencias
En la carpeta raíz (donde está `requirements.txt`):

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### C. Configurar variables de entorno
Copia `.env.example` como `.env` y ajusta:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=TU_PASSWORD
DB_NAME=bicisena
API_URL=http://127.0.0.1:8000
```

Luego, en Windows (PowerShell) puedes cargarlo rápido así:
```powershell
Get-Content .env | ForEach-Object {
  if($_ -match "^(.*?)=(.*)$"){ [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) }
}
```

### D. Levantar el API
Entra a la carpeta `bicisena` y ejecuta:

```bash
cd bicisena
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Abre:
- Swagger: `http://127.0.0.1:8000/docs`

---

## 2) Desplegar en RENDER (para que funcione desde cualquier dispositivo)

### Importante (causa del problema original)
Render NO puede conectarse a tu MySQL local de XAMPP.
Necesitas un MySQL en la nube (Railway / PlanetScale / Aiven / etc).

### A. Crear base de datos MySQL en la nube
Crea una base en uno de esos proveedores y obtén:
- Host
- Puerto (normalmente 3306)
- Usuario
- Password
- Nombre de base

### B. Crear el servicio Web en Render
- Tipo: **Web Service**
- Runtime: **Python**
- Root Directory: (vacío) o donde esté `requirements.txt`
- Build Command:
```bash
pip install -r requirements.txt
```

- Start Command (**muy importante**):
```bash
cd bicisena && uvicorn main:app --host 0.0.0.0 --port 10000
```

### C. Variables de entorno en Render
En Render → **Environment** agrega:

**Opción 1 (recomendada):**
- DATABASE_URL = `mysql://USER:PASSWORD@HOST:3306/NOMBRE_BD`

**Opción 2 (separadas):**
- DB_HOST = ...
- DB_PORT = 3306
- DB_USER = ...
- DB_PASSWORD = ...
- DB_NAME = ...

Opcional:
- API_URL = `https://TU-SERVICIO.onrender.com`

### D. Probar que está vivo
Abre en el navegador la URL de Render:
- `/` debe responder: `{"status":"ok","service":"bicisena-api"}`
- `/docs` debe abrir Swagger

---

## 3) Errores comunes (y solución)

### “Can't connect to MySQL server on '127.0.0.1'”
➡️ Significa que no configuraste variables de entorno y está usando local.
Solución: configura DATABASE_URL o DB_HOST/DB_USER/DB_PASSWORD/DB_NAME.

### Swagger abre pero endpoints fallan
➡️ Casi siempre es BD.
Revisa variables en Render y que la BD permita conexiones externas.

---

Si quieres, me dices cuál proveedor vas a usar (Railway/PlanetScale/Aiven) y te doy
los valores exactos que debes copiar en Render.
