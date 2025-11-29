# Guía para Instalar Claude Code CLI

## Problema Actual

Estás intentando instalar `@anthropic-ai/claude-code` vía npm, pero hay una instalación corrupta que está bloqueando la instalación.

## Solución: Limpiar e Instalar Correctamente

### Paso 1: Limpiar la Instalación Corrupta

Ejecuta estos comandos en tu terminal (te pedirá tu contraseña):

```bash
# Eliminar directorios corruptos
sudo rm -rf /opt/homebrew/lib/node_modules/@anthropic-ai/claude-code
sudo rm -rf /opt/homebrew/lib/node_modules/@anthropic-ai/.claude-code-*

# Verificar que se eliminaron
ls -la /opt/homebrew/lib/node_modules/@anthropic-ai/
```

Si el directorio `@anthropic-ai` queda vacío, también puedes eliminarlo:

```bash
sudo rm -rf /opt/homebrew/lib/node_modules/@anthropic-ai
```

### Paso 2: Instalar Claude Code (Método Correcto)

**⚠️ IMPORTANTE**: Según la documentación oficial, Claude Code NO se instala vía npm. Se instala usando un script oficial.

#### Opción A: Instalación Oficial (Recomendada)

Ejecuta este comando en tu terminal:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Este script:
- Descargará e instalará Claude Code correctamente
- Configurará el PATH automáticamente
- Te pedirá autenticarte con tu cuenta de Claude

#### Opción B: Si Prefieres npm (No Oficial)

Si realmente quieres usar el paquete npm (aunque no es el método oficial):

```bash
# Después de limpiar (Paso 1)
npm install -g @anthropic-ai/claude-code
```

**Nota**: Este paquete npm puede no ser el método oficial de instalación.

### Paso 3: Verificar la Instalación

Después de instalar, verifica que funciona:

```bash
# Recargar configuración de shell
source ~/.zshrc

# Verificar que el comando existe
which claude

# Ver la versión
claude --version
```

### Paso 4: Autenticación

La primera vez que ejecutes `claude`, te pedirá que inicies sesión:

```bash
claude
```

Usa las mismas credenciales que usas en claude.ai

## ¿Por Qué Falló la Instalación Original?

El error `ENOTEMPTY` ocurre cuando:
1. Una instalación anterior falló y dejó archivos temporales
2. npm intenta renombrar un directorio pero encuentra archivos bloqueados
3. Hay permisos incorrectos en los directorios

## ✅ Instalación Completada

**Estado actual**: Claude Code CLI está instalado y funcionando correctamente.

- **Versión**: 2.0.55
- **Ubicación**: `~/.local/bin/claude`
- **Comando**: `claude` disponible en PATH

## Cómo Usar Claude Code CLI

### Uso Básico

```bash
# Iniciar sesión interactiva (modo por defecto)
claude

# Hacer una pregunta rápida y obtener respuesta
claude "explica este código"

# Modo no interactivo (útil para scripts)
claude -p "revisa este archivo"

# Continuar la conversación anterior
claude --continue

# Reanudar una conversación específica
claude --resume
```

### Ejemplos Prácticos

```bash
# Analizar un archivo específico
claude "revisa backend/app/main.py y sugiere mejoras"

# Generar código
claude -p "crea una función Python que valide emails"

# Formato JSON para integración
claude -p --output-format json "lista los endpoints de la API"

# Con herramientas específicas
claude --tools "Bash,Edit" "refactoriza esta función"
```

### Comandos Útiles

```bash
# Ver ayuda completa
claude --help

# Verificar actualizaciones
claude update

# Configurar token de autenticación
claude setup-token

# Diagnosticar problemas
claude doctor
```

## Comparación: Cursor vs Claude Code CLI

### Cursor (Donde Estás Ahora)
- ✅ **Mejor para desarrollo**: Integrado con el editor
- ✅ **Acceso directo al código**: Ve y edita archivos directamente
- ✅ **Interfaz visual**: Más fácil de usar
- ✅ **Sin terminal**: Todo desde la UI

### Claude Code CLI
- ✅ **Mejor para automatización**: Scripts y pipelines
- ✅ **Integración con otros tools**: Fácil de usar en scripts
- ✅ **Modo no interactivo**: Perfecto para CI/CD
- ✅ **Desde terminal**: Útil si prefieres la línea de comandos

**Recomendación**: Usa **Cursor** para desarrollo diario y **Claude CLI** para tareas automatizadas o cuando trabajes desde terminal.

## Referencias

- [Documentación Oficial de Claude Code](https://docs.claude.com/es/docs/claude-code/overview)
- [Guía de Inicio Rápido](https://docs.claude.com/es/docs/claude-code/quickstart)
- Ver todas las opciones: `claude --help`
