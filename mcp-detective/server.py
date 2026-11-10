"""Servidor MCP "MCP Detective": consulta casos y registra alertas (entorno simulado)."""

import json
from pathlib import Path

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

mcp = MCPServer("MCP Detective")

RUTA_CASOS = Path(__file__).resolve().parent / "casos.json"
NIVELES_VALIDOS = ("bajo", "medio", "alto")

# Almacenamiento en memoria: se pierde al reiniciar el servidor.
_alertas: dict[str, dict] = {}


def _cargar_casos() -> dict:
    with open(RUTA_CASOS, encoding="utf-8") as f:
        return json.load(f)


def logica_listar_casos() -> list[dict]:
    casos = _cargar_casos()
    return [
        {"caso_id": cid, "sistema": c["sistema"], "cantidad_eventos": len(c["eventos"])}
        for cid, c in casos.items()
    ]


def logica_consultar_eventos(caso_id: str) -> list[dict]:
    casos = _cargar_casos()
    if not isinstance(caso_id, str) or caso_id not in casos:
        raise ValueError(
            f"El caso '{caso_id}' no existe. Casos disponibles: {', '.join(casos)}."
        )
    return [dict(e) for e in casos[caso_id]["eventos"]]


def logica_registrar_alerta(caso_id: str, nivel: str, motivo: str) -> dict:
    casos = _cargar_casos()
    if not isinstance(caso_id, str) or caso_id not in casos:
        raise ValueError(
            f"El caso '{caso_id}' no existe. Casos disponibles: {', '.join(casos)}."
        )
    if not isinstance(nivel, str) or nivel not in NIVELES_VALIDOS:
        raise ValueError(
            f"Nivel inválido '{nivel}'. Solo se permite: {', '.join(NIVELES_VALIDOS)}."
        )
    if not isinstance(motivo, str) or not motivo.strip():
        raise ValueError("El motivo no puede estar vacío ni contener solo espacios.")
    if caso_id in _alertas:
        raise ValueError(f"Ya existe una alerta registrada para el caso '{caso_id}'.")
    alerta = {
        "caso_id": caso_id,
        "nivel": nivel,
        "motivo": motivo,
        "estado": "registrada",
    }
    _alertas[caso_id] = alerta
    return dict(alerta)


def _como_error_mcp(funcion, *args) -> object:
    """Convierte ValueError de la lógica en ToolError: así el mensaje llega al agente."""
    try:
        return funcion(*args)
    except ValueError as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool()
def listar_casos() -> list[dict]:
    """Lista los casos disponibles (id, sistema y cantidad de eventos). Solo lectura; no incluye conclusiones."""
    return logica_listar_casos()


@mcp.tool()
def consultar_eventos(caso_id: str) -> list[dict]:
    """Devuelve los eventos exactos de un caso (por ejemplo "INC-002"). Solo lectura. Error si el caso no existe."""
    return _como_error_mcp(logica_consultar_eventos, caso_id)


@mcp.tool()
def registrar_alerta(caso_id: str, nivel: str, motivo: str) -> dict:
    """Registra en memoria una alerta para un caso. Modifica estado.

    nivel debe ser "bajo", "medio" o "alto"; motivo no puede estar vacío.
    Solo se permite una alerta por caso; un duplicado produce error.
    """
    return _como_error_mcp(logica_registrar_alerta, caso_id, nivel, motivo)


if __name__ == "__main__":
    mcp.run(transport="stdio")
