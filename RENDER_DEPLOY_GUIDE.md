# Guía de Deploy en Render - Sistema de Subvenciones v1.0

## Paso 1: Crear la Base de Datos PostgreSQL (PRIMERO)

⚠️ **IMPORTANTE**: Debes crear la base de datos ANTES que el backend.

1. Ve a https://render.com/dashboard
2. Click **"New +"** (arriba a la derecha) → **"PostgreSQL"**
3. Configura la base de datos:
   - **Name**: `subvenciones-db` (o el nombre que prefieras)
   - **Database**: `subvenciones` (nombre de la BD)
   - **User**: `subvenciones_user` (usuario)
   - **Region**: Frankfurt (más cercano a España) o elegir según tu preferencia
   - **PostgreSQL Version**: 15 (o la más reciente)
   - **Instance Type**: Free (para empezar)
4. Click **"Create Database"**
5. Espera unos segundos a que se cree (verás un loading)

### Obtener la URL de la Base de Datos

Una vez creada, verás la página de la base de datos. Busca la sección **"Connections"**:

✅ **TUS URLs (ya creadas)**:
- **Internal Database URL**:
  ```
  postgresql://subvenciones_user:a8S19xndHHpvLNbrxcPv9Ql1vkpYuR57@dpg-d3tn0t49c44c73e61ogg-a/subvenciones
  ```
- **External Database URL**:
  ```
  postgresql://subvenciones_user:a8S19xndHHpvLNbrxcPv9Ql1vkpYuR57@dpg-d3tn0t49c44c73e61ogg-a.frankfurt-postgres.render.com/subvenciones
  ```

⚠️ **USA LA INTERNAL DATABASE URL** para el backend en Render (más rápida).

⚠️ **USA LA EXTERNAL DATABASE URL** solo si necesitas conectarte desde tu computadora local.

---

## Paso 2: Crear el Web Service (Backend)

1. Click **"New +"** → **"Web Service"**
2. Selecciona **"Build and deploy from a Git repository"** → **"Next"**
3. Conecta tu GitHub:
   - Si es la primera vez, click **"Connect GitHub"** y autoriza Render
   - Busca y selecciona: `pakonekone/subvenciones-v1`
   - Click **"Connect"**

### Configurar el Web Service

Completa el formulario con estos valores:

**Básico**:
- **Name**: `subvenciones-backend` (aparecerá en la URL)
- **Region**: Frankfurt (mismo que la BD)
- **Branch**: `main`
- **Root Directory**: `backend` ⚠️ **MUY IMPORTANTE**
- **Runtime**: Python 3

**Build & Deploy**:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Instance Type**:
- **Free** (para empezar)

❌ **NO HAGAS CLICK EN "Create Web Service" TODAVÍA**

---

## Paso 3: Configurar Variables de Entorno

Antes de crear el servicio, baja hasta la sección **"Environment Variables"**.

Click en **"Add Environment Variable"** para cada una:

### Variables Requeridas

| Key | Value | Notas |
|-----|-------|-------|
| `DATABASE_URL` | `postgresql://subvenciones_user:a8S19xndHHpvLNbrxcPv9Ql1vkpYuR57@dpg-d3tn0t49c44c73e61ogg-a/subvenciones` | ⚠️ TU URL INTERNAL del Paso 1 |
| `CORS_ORIGINS` | `http://localhost:3000` | Actualizaremos después con la URL de Vercel |
| `SECRET_KEY` | (ver abajo) | Genera una clave segura |
| `N8N_WEBHOOK_URL` | `https://nokodo10.app.n8n.cloud/webhook/boe-grants` | Tu webhook de N8n |
| `BDNS_MAX_RESULTS` | `100` | Límite de resultados |
| `MIN_RELEVANCE_SCORE` | `0.0` | Score mínimo (0.0 = desactivado) |
| `LOG_LEVEL` | `INFO` | Nivel de logs |
| `DB_ECHO` | `false` | No mostrar SQL en logs |
| `API_PORT` | `$PORT` | Render lo asigna automáticamente |

### Generar SECRET_KEY

En tu terminal local ejecuta:
```bash
openssl rand -hex 32
```

Copia el resultado y pégalo como valor de `SECRET_KEY`.

Ejemplo de resultado: `a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456`

---

## Paso 4: Crear y Desplegar

1. Ahora sí, click **"Create Web Service"**
2. Render comenzará a construir y desplegar tu backend
3. Verás los logs en tiempo real (tomará 2-5 minutos)
4. Cuando termine, verás: **"Your service is live 🎉"**

Tu backend estará disponible en:
```
https://subvenciones-backend.onrender.com
```

### Verificar que Funciona

Abre en tu navegador:
```
https://subvenciones-backend.onrender.com/docs
```

Deberías ver la interfaz de FastAPI con toda la documentación de la API.

---

## Paso 5: Ejecutar Migraciones de Base de Datos

⚠️ **IMPORTANTE**: Debes correr las migraciones de Alembic para crear las tablas.

### Opción A: Usar el Shell de Render (Recomendado)

1. En el dashboard de Render, ve a tu servicio **"subvenciones-backend"**
2. En el menú lateral, click **"Shell"** (icono de terminal)
3. Se abrirá una terminal web
4. Ejecuta estos comandos:

```bash
cd backend
alembic upgrade head
```

Deberías ver algo como:
```
INFO  [alembic.runtime.migration] Running upgrade -> 001_add_bdns_documents_column, add bdns documents
```

### Opción B: Crear un Script de Deploy

Si la Shell no funciona, podemos añadir las migraciones al build command:

1. Ve a **Settings** → **Build & Deploy**
2. Cambia **Build Command** a:
```bash
pip install -r requirements.txt && cd /opt/render/project/src/backend && alembic upgrade head
```
3. Click **"Save Changes"**
4. Render redesplegará automáticamente

---

## Paso 6: Verificar Base de Datos

Para verificar que las tablas se crearon:

1. Ve al dashboard de tu PostgreSQL database
2. Click en **"Connect"** → **"External Connection"**
3. Copia el comando psql y ejecútalo en tu terminal local (necesitas tener psql instalado)

O usa un cliente como DBeaver o pgAdmin:
- Host: `dpg-d3tn0t49c44c73e61ogg-a.frankfurt-postgres.render.com`
- Port: `5432`
- Database: `subvenciones`
- User: `subvenciones_user`
- Password: `a8S19xndHHpvLNbrxcPv9Ql1vkpYuR57`

Ejecuta:
```sql
\dt
```

Deberías ver tablas como: `grants`, `webhook_history`, etc.

---

## Paso 7: Deploy Frontend en Vercel

Ahora que el backend está funcionando, vamos con el frontend.

1. Ve a https://vercel.com
2. Click **"Add New..."** → **"Project"**
3. Click **"Import Git Repository"**
4. Busca `pakonekone/subvenciones-v1` y click **"Import"**

### Configurar el Proyecto

**Framework Preset**: Vite (debería detectarlo automáticamente)

**Root Directory**:
- Click **"Edit"**
- Escribe: `frontend`
- Click el checkmark ✓

**Build Settings** (debería autocompletarse):
- Build Command: `npm run build`
- Output Directory: `dist`
- Install Command: `npm install`

### Environment Variables

Click **"Environment Variables"** y añade:

| Name | Value |
|------|-------|
| `VITE_API_URL` | `https://subvenciones-backend.onrender.com` |

⚠️ Reemplaza con tu URL real de Render (sin `/` al final)

### Deploy

1. Click **"Deploy"**
2. Vercel construirá y desplegará (toma 1-2 minutos)
3. Te dará una URL como: `https://subvenciones-v1-xxx.vercel.app`

---

## Paso 8: Actualizar CORS en el Backend

Ahora que tienes la URL de Vercel, debes permitirla en el backend:

1. Ve a Render dashboard → **subvenciones-backend**
2. Click **"Environment"** en el menú lateral
3. Busca `CORS_ORIGINS`
4. Click el icono de editar (lápiz)
5. Cambia el valor a:
```
https://subvenciones-v1-xxx.vercel.app,http://localhost:3000
```
⚠️ Usa tu URL real de Vercel (sin `/` al final)

6. Click **"Save Changes"**
7. Render redesplegará automáticamente (1-2 minutos)

---

## Paso 9: Probar Todo el Sistema

### 1. Probar el Backend

Abre: `https://subvenciones-backend.onrender.com/docs`
- Deberías ver FastAPI docs
- Prueba endpoint: `/api/v1/health` (debería devolver `{"status": "healthy"}`)

### 2. Probar el Frontend

Abre tu URL de Vercel: `https://subvenciones-v1-xxx.vercel.app`
- Deberías ver la interfaz de grants
- Abre el inspector del navegador (F12) → Console
- No deberían haber errores de CORS

### 3. Probar Captura de Grants

En el frontend:
1. Click en **"Capturar Subvenciones"**
2. Selecciona BDNS
3. Configura fechas (ej: última semana)
4. Click **"Capturar"**
5. Espera unos segundos
6. Los grants deberían aparecer en la tabla

---

## ⚠️ Problemas Comunes y Soluciones

### Error: "Failed to connect to database"

**Causa**: La DATABASE_URL está mal configurada.

**Solución**:
1. Verifica que `DATABASE_URL` sea exactamente:
   ```
   postgresql://subvenciones_user:a8S19xndHHpvLNbrxcPv9Ql1vkpYuR57@dpg-d3tn0t49c44c73e61ogg-a/subvenciones
   ```
2. Ve al web service → Environment → Edita `DATABASE_URL`
3. Asegúrate de que NO tenga espacios al principio o final
4. Guarda cambios y espera redeploy

### Error: "CORS policy" en el navegador

**Causa**: El backend no permite el origen del frontend.

**Solución**:
1. Verifica que `CORS_ORIGINS` incluye tu URL de Vercel
2. No debe tener `/` al final
3. No debe tener espacios extra
4. Ejemplo correcto: `https://app.vercel.app,http://localhost:3000`

### Backend muy lento en el primer request

**Causa**: Render Free tier hiberna el servicio después de 15 minutos de inactividad.

**Solución**:
- Primera carga toma 30-60 segundos (es normal)
- Considera upgrade a plan pagado ($7/mes) si necesitas mejor performance
- O usa un servicio de "keep-alive" como UptimeRobot (gratis)

### Las migraciones no se ejecutaron

**Solución**:
1. Ve a Shell en Render
2. Ejecuta manualmente:
```bash
cd backend
alembic current  # Ver migración actual
alembic upgrade head  # Aplicar migraciones
```

### Frontend no encuentra el backend

**Solución**:
1. Verifica que `VITE_API_URL` está configurado en Vercel
2. Redespliega el frontend en Vercel después de cambiar variables
3. Abre DevTools → Network para ver a qué URL está llamando

---

## 📊 Resumen de URLs

Después de completar todos los pasos:

| Servicio | URL | Uso |
|----------|-----|-----|
| Backend API | `https://subvenciones-backend.onrender.com` | API REST |
| Backend Docs | `https://subvenciones-backend.onrender.com/docs` | Documentación Swagger |
| Frontend | `https://subvenciones-v1-xxx.vercel.app` | Aplicación web |
| Database | `dpg-xxx.frankfurt-postgres.render.com` | PostgreSQL (interno) |

---

## 💰 Costos (Free Tier)

**Render Free**:
- ✅ PostgreSQL: 1GB storage, 90 días de retención de backups
- ✅ Web Service: 750 horas/mes (suficiente si solo tienes 1 servicio)
- ⚠️ Se hiberna después de 15 min de inactividad
- ⚠️ 100GB de ancho de banda/mes

**Vercel Free**:
- ✅ Despliegues ilimitados
- ✅ Dominio custom
- ✅ SSL automático
- ✅ 100GB ancho de banda/mes

**Upgrade recomendado** (si vas a producción):
- Render Starter: $7/mes (sin hibernación, mejor performance)
- Vercel Pro: $20/mes (más builds, mejor analytics)

---

## 🔐 Seguridad Post-Deploy

1. **Cambia SECRET_KEY** periódicamente
2. **Activa 2FA** en Render y Vercel
3. **No compartas** las variables de entorno
4. **Configura backups** de la BD (automático en Render)
5. **Monitorea logs** regularmente para detectar errores

---

## 📈 Próximos Pasos

- [ ] Configura un dominio custom en Vercel
- [ ] Añade monitoreo (Sentry, LogRocket)
- [ ] Configura N8n para análisis de grants
- [ ] Prueba la exportación a Google Sheets
- [ ] Configura backups manuales de la BD

---

## 🆘 ¿Necesitas Ayuda?

- **Logs del Backend**: Render dashboard → Logs tab
- **Logs del Frontend**: Vercel dashboard → Deployments → Runtime Logs
- **Database**: Render dashboard → PostgreSQL → Logs

Si encuentras errores, revisa los logs primero. La mayoría de problemas se resuelven ahí.
