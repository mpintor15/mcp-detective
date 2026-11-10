import pytest

import server


@pytest.fixture(autouse=True)
def limpiar_alertas():
    server._alertas.clear()
    yield
    server._alertas.clear()


def test_listar_casos_devuelve_los_tres():
    casos = server.logica_listar_casos()
    assert [c["caso_id"] for c in casos] == ["INC-001", "INC-002", "INC-003"]
    assert [c["cantidad_eventos"] for c in casos] == [2, 6, 5]
    assert all(set(c) == {"caso_id", "sistema", "cantidad_eventos"} for c in casos)


def test_consultar_eventos_inc002_seis_fallos():
    eventos = server.logica_consultar_eventos("INC-002")
    assert len(eventos) == 6
    assert all(e["evento"] == "LOGIN_FAILED" and e["usuario"] == "admin" for e in eventos)


def test_consultar_eventos_desconocido_lanza_error():
    with pytest.raises(ValueError, match="INC-999"):
        server.logica_consultar_eventos("INC-999")


def test_registrar_alerta_valida():
    r = server.logica_registrar_alerta("INC-003", "alto", "Cuatro fallos y un acceso exitoso")
    assert r == {
        "caso_id": "INC-003",
        "nivel": "alto",
        "motivo": "Cuatro fallos y un acceso exitoso",
        "estado": "registrada",
    }


def test_alerta_duplicada_rechazada():
    server.logica_registrar_alerta("INC-003", "alto", "motivo")
    with pytest.raises(ValueError, match="Ya existe"):
        server.logica_registrar_alerta("INC-003", "alto", "motivo")


def test_nivel_invalido():
    with pytest.raises(ValueError, match="bajo, medio, alto"):
        server.logica_registrar_alerta("INC-002", "critico", "Intentos repetidos")


def test_motivo_en_blanco():
    with pytest.raises(ValueError, match="motivo"):
        server.logica_registrar_alerta("INC-002", "medio", "   ")


def test_alerta_caso_inexistente():
    with pytest.raises(ValueError, match="no existe"):
        server.logica_registrar_alerta("INC-999", "bajo", "x")
