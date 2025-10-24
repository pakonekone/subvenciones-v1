# 🚀 Checklist de Deploy - Guía Rápida

Sigue estos pasos en orden. ✅ Marca cada uno cuando lo completes.

---

## PARTE 1: RENDER (Backend + Database)

### 🗄️ Paso 1: PostgreSQL (5 minutos)

- [x] ~~Ir a https://render.com/dashboard~~
- [x] ~~Click **"New +"** → **"PostgreSQL"~~**
- [x] ~~Name: `subvenciones-db`~~
- [x] ~~Database: `subvenciones`~~
- [x] ~~Region: Frankfurt~~
- [x] ~~Click **"Create Database"~~**
- [x] ✅ **YA TIENES LA BD**: `postgresql://subvenciones_user:a8S19xndHHpvLNbrxcPv9Ql1vkpYuR57@dpg-d3tn0t49c44c73e61ogg-a/subvenciones`

---

### 🖥️ Paso 2: Web Service (10 minutos)

- [ ] Click **"New +"** → **"Web Service"**
- [ ] Conectar GitHub → Seleccionar `pakonekone/subvenciones-v1`
- [ ] Name: `subvenciones-backend`
- [ ] Region: Frankfurt
- [ ] Branch: `main`
- [ ] **Root Directory**: `backend` ⚠️ IMPORTANTE
- [ ] Runtime: Python 3
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Instance Type: Free

---

### 🔑 Paso 3: Variables de Entorno

Añadir estas variables ANTES de crear el servicio:

- [ ] `DATABASE_URL` = `postgresql://subvenciones_user:a8S19xndHHpvLNbrxcPv9Ql1vkpYuR57@dpg-d3tn0t49c44c73e61ogg-a/subvenciones`
- [ ] `CORS_ORIGINS` = `http://localhost:3000`
- [ ] `SECRET_KEY` = `<generar con: openssl rand -hex 32>`
- [ ] `N8N_WEBHOOK_URL` = `https://nokodo10.app.n8n.cloud/webhook/boe-grants`
- [ ] `BDNS_MAX_RESULTS` = `100`
- [ ] `MIN_RELEVANCE_SCORE` = `0.0`
- [ ] `LOG_LEVEL` = `INFO`

⚠️ **NO añadas API_PORT o PORT** - Render los asigna automáticamente

**Ahora sí**:
- [ ] Click **"Create Web Service"**
- [ ] Esperar 2-5 minutos (ver logs)
- [ ] **COPIAR URL**: `https://subvenciones-backend.onrender.com`

---

### 🔧 Paso 4: Migraciones

- [ ] En Render dashboard → `subvenciones-backend` → **"Shell"**
- [ ] Ejecutar:
  ```bash
  cd backend
  alembic upgrade head
  ```
- [ ] Verificar que dice: "Running upgrade..."

---

### ✅ Paso 5: Verificar Backend

- [ ] Abrir: `https://subvenciones-backend.onrender.com/docs`
- [ ] Deberías ver FastAPI Swagger UI
- [ ] Probar endpoint `/api/v1/health` (debería devolver `{"status": "healthy"}`)

---

## PARTE 2: VERCEL (Frontend)

### 🎨 Paso 6: Deploy Frontend (5 minutos)

- [ ] Ir a https://vercel.com
- [ ] Click **"Add New..."** → **"Project"**
- [ ] Import `pakonekone/subvenciones-v1`
- [ ] Framework Preset: Vite
- [ ] **Root Directory**: `frontend` ⚠️ IMPORTANTE (click Edit)
- [ ] Build Command: `npm run build`
- [ ] Output Directory: `dist`

---

### 🔑 Paso 7: Variable de Entorno

- [ ] En Environment Variables, añadir:
  - Name: `VITE_API_URL`
  - Value: `https://subvenciones-backend.onrender.com` (tu URL de Render)
- [ ] Click **"Deploy"**
- [ ] Esperar 1-2 minutos
- [ ] **COPIAR URL**: `https://subvenciones-v1-xxx.vercel.app`

---

## PARTE 3: CONEXIÓN FINAL

### 🔗 Paso 8: Actualizar CORS (2 minutos)

- [ ] Ir a Render → `subvenciones-backend` → **"Environment"**
- [ ] Buscar `CORS_ORIGINS`
- [ ] Click editar (lápiz)
- [ ] Cambiar a: `https://subvenciones-v1-xxx.vercel.app,http://localhost:3000`
  (⚠️ Usar tu URL real de Vercel)
- [ ] Click **"Save Changes"**
- [ ] Esperar 1-2 minutos (redeploy automático)

---

### 🧪 Paso 9: Pruebas Finales

- [ ] Abrir tu URL de Vercel
- [ ] F12 → Console (no debería haber errores CORS)
- [ ] Click **"Capturar Subvenciones"**
- [ ] Seleccionar BDNS
- [ ] Configurar fechas (ej: última semana)
- [ ] Click **"Capturar"**
- [ ] Verificar que aparecen grants en la tabla

---

## 🎉 ¡LISTO!

Si todos los checkboxes están marcados, tu aplicación está 100% funcional en producción.

### 📋 Tus URLs Finales:

```
Frontend:  https://subvenciones-v1-xxx.vercel.app
Backend:   https://subvenciones-backend.onrender.com
API Docs:  https://subvenciones-backend.onrender.com/docs
```

---

## ⚠️ Si Algo Falla

| Problema | Solución |
|----------|----------|
| Error: "Failed to connect to database" | Verifica DATABASE_URL en Render Environment |
| Error: "CORS policy" | Verifica CORS_ORIGINS incluye tu URL de Vercel sin `/` al final |
| Backend lento (primer request) | Normal en Free tier (se hiberna). Primera carga: 30-60s |
| Frontend muestra página en blanco | Verifica VITE_API_URL en Vercel Settings → Environment Variables |
| No aparecen grants | Verifica que las migraciones corrieron: Shell → `alembic current` |

**Logs**:
- Backend: Render dashboard → Logs tab
- Frontend: Vercel dashboard → Deployments → Runtime Logs

---

## 📚 Documentación Completa

- **Guía detallada**: `RENDER_DEPLOY_GUIDE.md`
- **Arquitectura**: `CLAUDE.md`
- **Features**: `README.md`
