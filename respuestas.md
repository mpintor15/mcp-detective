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

Conexión al agente (stdio, con rutas absolutas; ejecutar desde la raíz del repositorio):

```bash
claude mcp add detective -- "$PWD/.venv/bin/python" "$PWD/mcp-detective/server.py"
```

## 1. Arquitectura

- **LLM:** entiende lo que le pido y decide qué herramienta usar y con qué datos. Después escribe la respuesta con lo que le devolvió la herramienta. No ejecuta nada por sí mismo.
- **Harness/host (el agente):** es la aplicación donde hablo con el modelo. Le pasa las herramientas disponibles, recibe la llamada que propone y le devuelve el resultado.
- **Cliente MCP:** está dentro del host. Arranca mi servidor por stdio, descubre las tres herramientas y envía cada llamada y su respuesta.
- **Servidor MCP (mi `server.py`):** tiene las tres tools, valida lo que recibe y guarda las alertas en memoria.

Quien ejecutó realmente Python fue **el servidor MCP**. El LLM solo generó texto pidiendo la llamada.

## 2. Evidencia

`INC-003` merece investigación porque `admin` falló 4 veces seguidas (03:00 a 03:03) desde la misma IP, y a las 03:04 entró con éxito al panel de administración, de madrugada. Ese patrón se parece a alguien adivinando una contraseña.

Aun así, los logs no prueban que hubo una intrusión. Pudo ser el propio administrador que se equivocó de contraseña tres veces y acertó a la cuarta. Los registros no dicen quién estaba detrás de la IP ni qué hizo después de entrar. Un patrón sospechoso es una razón para revisar, no una prueba de compromiso. Por eso el agente puso nivel `alto` pero con un motivo que dice "patrón compatible" y "posible compromiso", sin afirmar que pasó.

## 3. Validación y seguridad

El **servidor MCP** rechaza `INC-999`, los niveles inválidos como `critico`, los motivos vacíos y las alertas repetidas, y devuelve un error claro en cada caso. No es seguro confiar solo en que el modelo mande bien los argumentos: puede inventar un id, equivocarse de nivel o repetir una llamada. `registrar_alerta` cambia estado, así que no debe aceptar cualquier cosa. El servidor siempre aplica las mismas reglas, y el LLM no puede garantizar eso por sí solo.

Detalle técnico: en el SDK 2.3 solo los `ToolError` muestran su mensaje al agente. Por eso las tools convierten el `ValueError` de mi lógica en `ToolError`; si no, el agente solo vería "Error executing tool".
