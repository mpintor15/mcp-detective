# Deber 5 — MCP Detective

**Agente usado:** Claude Code (app de escritorio de Claude, pestaña Code).

**Cómo comprobé que estaba conectado:** 
El agente listó sus herramientas y aparecieron listar_casos, consultar_eventos y registrar_alerta. Ver evidencias/agente_tools.png

## Instalación y uso

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install "mcp[cli]>=2,<3" pytest
pytest mcp-detective -q
mcp dev mcp-detective/server.py
```

Conexión al agente (stdio, con rutas absolutas; ajusta las rutas a tu equipo):

```bash
claude mcp add detective -- /RUTA/ABSOLUTA/.venv/bin/python /RUTA/ABSOLUTA/mcp-detective/server.py
```

## 1. Arquitectura

- **LLM:** interpreta mi petición y *propone* qué tool llamar y con qué argumentos; después redacta la respuesta usando lo que devolvió la tool. No ejecuta nada.
- **Harness/host (el agente):** es la aplicación que corre el ciclo: envía al LLM las tools disponibles, recibe su propuesta de llamada, pide permiso si hace falta y devuelve el resultado al LLM.
- **Cliente MCP:** vive dentro del host. Lanza el servidor por stdio, descubre las tools y transmite cada llamada y su resultado con el protocolo MCP.
- **Servidor MCP (mi `server.py`):** expone `listar_casos`, `consultar_eventos` y `registrar_alerta`, valida los argumentos y mantiene el estado en memoria.

**Quien ejecutó realmente Python fue el servidor MCP.** El LLM solo produjo texto con la llamada propuesta.

## 2. Evidencia

`INC-003` merece investigación: cuatro fallos de login seguidos (03:00 a 03:03) del usuario `admin` desde la misma IP, y un acceso exitoso a las 03:04 en el panel de administración. Es un patrón compatible con adivinar una contraseña.

Pero los logs no permiten afirmar con certeza que hubo una intrusión. Cuatro fallos y un éxito también pueden ser un administrador que olvidó su contraseña y la acertó al quinto intento. Los registros no muestran quién estaba detrás de la IP, si el acceso fue legítimo ni qué hizo la sesión después. Un patrón sospechoso justifica revisar; no demuestra por sí solo un compromiso. Por eso el nivel de alerta y el motivo hablan de "requiere investigación" y no de "intrusión confirmada".

## 3. Validación y seguridad

El servidor rechaza `INC-999`, los niveles inválidos (`critico`), los motivos en blanco y las alertas duplicadas, con un mensaje de error explícito. No es seguro confiar solo en que el modelo genere argumentos correctos: el LLM puede inventar un id, equivocarse de nivel o repetir una llamada, y una acción que cambia estado, como `registrar_alerta`, no debe aceptar cualquier cosa. El servidor es el único punto que puede **garantizar** esas reglas siempre, de forma determinista, pase lo que pase con el modelo. El LLM no puede garantizar eso por sí solo.

(Detalle de implementación: en el SDK 2.3 solo los `ToolError` llegan con su mensaje al agente, así que las tools convierten el `ValueError` de la lógica en `ToolError`; si no, el agente solo vería "Error executing tool".)
