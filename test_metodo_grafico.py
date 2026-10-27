# -*- coding: utf-8 -*-
"""
Pruebas automáticas del método gráfico (ejecutar con:  pytest -q).
Cada prueba carga un ejemplo de ejemplos.json y comprueba el estado y el
óptimo esperado (los valores esperados se calcularon a mano).
"""
import json
import os

import pytest

from metodo_grafico import construir_problema, resolver

RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ejemplos.json")
with open(RUTA, encoding="utf-8") as f:
    EJEMPLOS = json.load(f)


def resolver_ejemplo(prefijo: str):
    clave = next(k for k in EJEMPLOS if k.startswith(prefijo))
    p, errores = construir_problema(EJEMPLOS[clave])
    assert errores == []
    return p, resolver(p)


def test_caso_real_optimo():
    # Óptimo: corte de proteína con maíz = 20 % de la mezcla
    _, res = resolver_ejemplo("Caso real")
    assert res.estado == "optimo"
    v = res.optimos[0]
    assert v.x1 == pytest.approx(0.48 / 0.765, rel=1e-6)          # 0.6275 kg maíz
    assert v.x2 == pytest.approx(4 * 0.48 / 0.765, rel=1e-6)      # 2.5098 kg Purina
    assert res.z_optimo == pytest.approx(6500.39, abs=0.01)


def test_maximizacion_unica():
    _, res = resolver_ejemplo("Prueba 1")
    assert res.estado == "optimo"
    assert (res.optimos[0].x1, res.optimos[0].x2) == pytest.approx((4, 8))
    assert res.z_optimo == pytest.approx(400)


def test_infactible():
    _, res = resolver_ejemplo("Prueba 2")
    assert res.estado == "infactible"
    assert res.vertices == []


def test_no_acotado():
    _, res = resolver_ejemplo("Prueba 3")
    assert res.estado == "no_acotado"
    assert res.z_optimo is None


def test_optimos_alternativos():
    _, res = resolver_ejemplo("Prueba 4")
    assert res.estado == "optimos_alternativos"
    assert len(res.optimos) == 2
    assert res.z_optimo == pytest.approx(16)


def test_restriccion_de_igualdad():
    # x1 + x2 = 10, x1 >= 2, x2 <= 7 -> mínimo de 3x1 + 2x2 en (3, 7): z = 23
    _, res = resolver_ejemplo("Prueba 5")
    assert res.estado == "optimo"
    assert (res.optimos[0].x1, res.optimos[0].x2) == pytest.approx((3, 7))
    assert res.z_optimo == pytest.approx(23)


def test_validacion_campos_vacios_y_texto():
    datos = {"objetivo": "min", "c1": "", "c2": "abc", "nombre_x1": "A", "nombre_x2": "B",
             "restricciones": [{"nombre": "R1", "a1": "1", "a2": "x", "signo": "<=", "b": ""}]}
    problema, errores = construir_problema(datos)
    assert problema is None
    assert len(errores) >= 4          # c1 vacío, c2 texto, a2 texto, b vacío


def test_validacion_demasiadas_restricciones():
    fila = {"nombre": "R", "a1": "1", "a2": "1", "signo": "<=", "b": "5"}
    datos = {"objetivo": "max", "c1": "1", "c2": "1", "nombre_x1": "A", "nombre_x2": "B",
             "restricciones": [fila] * 9}
    problema, errores = construir_problema(datos)
    assert problema is None
    assert any("máximo 8" in e for e in errores)


def test_coma_decimal():
    datos = {"objetivo": "min", "c1": "2,5", "c2": "1", "nombre_x1": "A", "nombre_x2": "B",
             "restricciones": [{"nombre": "R", "a1": "1", "a2": "1", "signo": ">=", "b": "3,5"}]}
    problema, errores = construir_problema(datos)
    assert errores == []
    assert problema.c1 == 2.5 and problema.restricciones[0].b == 3.5
