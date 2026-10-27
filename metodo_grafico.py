# -*- coding: utf-8 -*-
"""
metodo_grafico.py  --  Grupo 7 (IO1-82)

Lógica del MÉTODO GRÁFICO para programación lineal de 2 variables
(max o min, restricciones <=, >= y =, hasta 8 restricciones).

IMPORTANTE: este módulo NO usa ninguna librería que resuelva programación
lineal (SciPy, PuLP, OR-Tools, etc.). Todo el método está programado aquí:
rectas frontera -> intersecciones -> vértices factibles -> evaluar z -> óptimo.

El módulo no depende de la interfaz: recibe datos (texto o números) y devuelve
objetos Python. La interfaz (app.py) y la gráfica (grafico.py) lo usan.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from itertools import combinations
from typing import List, Optional, Tuple

TOL = 1e-9                 # tolerancia numérica general
MAX_RESTRICCIONES = 8      # tamaño máximo exigido por el enunciado
SIGNOS = ("<=", ">=", "=")


class ErrorDeDatos(ValueError):
    """Error de validación de los datos que escribe el usuario."""


# ---------------------------------------------------------------------------
# Estructuras de datos
# ---------------------------------------------------------------------------
@dataclass
class Restriccion:
    """a1*x1 + a2*x2  (<=, >=, =)  b"""
    nombre: str
    a1: float
    a2: float
    signo: str
    b: float

    def valor(self, x1: float, x2: float) -> float:
        return self.a1 * x1 + self.a2 * x2

    def _tol(self) -> float:
        return 1e-7 * (1.0 + abs(self.b))

    def cumple(self, x1: float, x2: float) -> bool:
        """¿El punto (x1, x2) satisface la restricción?"""
        v, tol = self.valor(x1, x2), self._tol()
        if self.signo == "<=":
            return v <= self.b + tol
        if self.signo == ">=":
            return v >= self.b - tol
        return abs(v - self.b) <= tol

    def esta_activa(self, x1: float, x2: float) -> bool:
        """¿El punto está sobre la recta frontera de la restricción?"""
        return abs(self.valor(x1, x2) - self.b) <= self._tol()


@dataclass
class Problema:
    objetivo: str                      # "min" o "max"
    c1: float
    c2: float
    nombre_x1: str = "x1"
    nombre_x2: str = "x2"
    unidad_x1: str = ""
    unidad_x2: str = ""
    unidad_z: str = ""
    restricciones: List[Restriccion] = field(default_factory=list)


@dataclass
class Vertice:
    x1: float
    x2: float
    z: float
    activas: List[str] = field(default_factory=list)   # restricciones que se cortan aquí
    es_optimo: bool = False


@dataclass
class Resultado:
    # "optimo" | "optimos_alternativos" | "infactible" | "no_acotado"
    estado: str = ""
    vertices: List[Vertice] = field(default_factory=list)
    optimos: List[Vertice] = field(default_factory=list)
    z_optimo: Optional[float] = None
    n_intersecciones: int = 0
    pasos: List[str] = field(default_factory=list)
    mensajes: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Validación de datos escritos por el usuario
# ---------------------------------------------------------------------------
def _a_numero(texto, campo: str, errores: List[str]) -> Optional[float]:
    """Convierte texto a número. Acepta coma o punto decimal.
    Si el campo está vacío o no es un número, agrega un mensaje claro."""
    if texto is None or str(texto).strip() == "":
        errores.append(f"El campo «{campo}» está vacío.")
        return None
    limpio = str(texto).strip().replace(" ", "").replace(",", ".")
    try:
        valor = float(limpio)
    except ValueError:
        errores.append(f"El campo «{campo}» debe ser un número, pero se escribió «{texto}».")
        return None
    if math.isnan(valor) or math.isinf(valor):
        errores.append(f"El campo «{campo}» no es un número válido.")
        return None
    return valor


def construir_problema(datos: dict) -> Tuple[Optional[Problema], List[str]]:
    """Valida los datos de la interfaz y arma el Problema.

    datos = {"objetivo": "min"|"max", "c1": str, "c2": str,
             "nombre_x1": str, "nombre_x2": str, "unidad_x1": str,
             "unidad_x2": str, "unidad_z": str,
             "restricciones": [{"nombre","a1","a2","signo","b"}, ...]}

    Devuelve (problema, errores). Si hay errores, problema es None.
    El programa nunca se cierra: todos los errores se devuelven como texto.
    """
    errores: List[str] = []

    objetivo = str(datos.get("objetivo", "")).strip().lower()
    if objetivo not in ("min", "max"):
        errores.append("Debe escoger si el objetivo es minimizar o maximizar.")

    n1 = str(datos.get("nombre_x1", "")).strip()
    n2 = str(datos.get("nombre_x2", "")).strip()
    if not n1 or not n2:
        errores.append("Escriba el nombre de las dos variables de decisión.")

    c1 = _a_numero(datos.get("c1"), "coeficiente de la función objetivo (variable 1)", errores)
    c2 = _a_numero(datos.get("c2"), "coeficiente de la función objetivo (variable 2)", errores)
    if c1 is not None and c2 is not None and c1 == 0 and c2 == 0:
        errores.append("La función objetivo no puede tener los dos coeficientes en 0.")

    filas = datos.get("restricciones", [])
    if len(filas) < 1:
        errores.append("Debe haber al menos una restricción.")
    if len(filas) > MAX_RESTRICCIONES:
        errores.append(f"El método gráfico admite máximo {MAX_RESTRICCIONES} restricciones.")

    restricciones: List[Restriccion] = []
    for i, f in enumerate(filas[:MAX_RESTRICCIONES], start=1):
        nombre = str(f.get("nombre", "")).strip() or f"Restricción {i}"
        a1 = _a_numero(f.get("a1"), f"restricción {i}: coeficiente de {n1 or 'variable 1'}", errores)
        a2 = _a_numero(f.get("a2"), f"restricción {i}: coeficiente de {n2 or 'variable 2'}", errores)
        b = _a_numero(f.get("b"), f"restricción {i}: lado derecho", errores)
        signo = str(f.get("signo", "")).strip()
        if signo not in SIGNOS:
            errores.append(f"Restricción {i}: el signo debe ser <=, >= o =.")
        if a1 is not None and a2 is not None and a1 == 0 and a2 == 0:
            errores.append(f"Restricción {i}: los dos coeficientes son 0; no limita nada.")
        if None not in (a1, a2, b) and signo in SIGNOS and not (a1 == 0 and a2 == 0):
            restricciones.append(Restriccion(nombre, a1, a2, signo, b))

    if errores:
        return None, errores

    return Problema(objetivo, c1, c2, n1, n2,
                    str(datos.get("unidad_x1", "")).strip(),
                    str(datos.get("unidad_x2", "")).strip(),
                    str(datos.get("unidad_z", "")).strip(),
                    restricciones), []


# ---------------------------------------------------------------------------
# Núcleo del método gráfico
# ---------------------------------------------------------------------------
def _interseccion(r1: Restriccion, r2: Restriccion) -> Optional[Tuple[float, float]]:
    """Punto donde se cortan las rectas frontera de dos restricciones
    (regla de Cramer). Devuelve None si son paralelas."""
    det = r1.a1 * r2.a2 - r1.a2 * r2.a1
    if abs(det) < 1e-12:
        return None
    x1 = (r1.b * r2.a2 - r1.a2 * r2.b) / det
    x2 = (r1.a1 * r2.b - r1.b * r2.a1) / det
    return x1, x2


def _direcciones_de_recesion(todas: List[Restriccion]) -> List[Tuple[float, float]]:
    """Direcciones en las que la región factible se extiende al infinito.

    Una dirección d es de recesión si, partiendo de cualquier punto factible,
    el punto x + t*d sigue siendo factible para todo t >= 0. Basta probar las
    direcciones paralelas a cada recta frontera (y a los ejes)."""
    candidatas = [(1.0, 0.0), (0.0, 1.0)]
    for r in todas:
        n = math.hypot(r.a1, r.a2)
        if n < TOL:
            continue
        d = (-r.a2 / n, r.a1 / n)
        candidatas += [d, (-d[0], -d[1])]

    validas = []
    for d in candidatas:
        if d[0] < -TOL or d[1] < -TOL:          # x1 >= 0, x2 >= 0
            continue
        ok = True
        for r in todas:
            v = r.a1 * d[0] + r.a2 * d[1]
            tol = 1e-9 * (1.0 + math.hypot(r.a1, r.a2))
            if r.signo == "<=" and v > tol:
                ok = False
            elif r.signo == ">=" and v < -tol:
                ok = False
            elif r.signo == "=" and abs(v) > tol:
                ok = False
        if ok:
            validas.append(d)
    return validas


def resolver(p: Problema) -> Resultado:
    """Resuelve el problema con el método gráfico y documenta cada paso."""
    res = Resultado()
    sentido = "minimizar" if p.objetivo == "min" else "maximizar"

    # Se agregan x1 >= 0 y x2 >= 0 como restricciones más (rectas de los ejes)
    no_negativas = [Restriccion(f"{p.nombre_x1} ≥ 0", 1, 0, ">=", 0),
                    Restriccion(f"{p.nombre_x2} ≥ 0", 0, 1, ">=", 0)]
    todas = list(p.restricciones) + no_negativas

    # PASO 1 -- cada restricción define una recta frontera
    res.pasos.append("Paso 1. Cada restricción se convierte en una recta frontera:")
    for r in todas:
        res.pasos.append(f"   • {r.nombre}: {r.a1:g}·x1 + {r.a2:g}·x2 {r.signo} {r.b:g}")

    # PASO 2 -- puntos de corte entre todos los pares de rectas
    candidatos: List[Tuple[float, float]] = []
    for r1, r2 in combinations(todas, 2):
        punto = _interseccion(r1, r2)
        if punto is not None:
            candidatos.append(punto)
    res.n_intersecciones = len(candidatos)
    res.pasos.append(f"Paso 2. Se calculan las intersecciones de cada par de rectas: "
                     f"{len(candidatos)} puntos candidatos.")

    # PASO 3 -- se conservan solo los puntos que cumplen TODAS las restricciones
    unicos = {}
    for x1, x2 in candidatos:
        if all(r.cumple(x1, x2) for r in todas):
            clave = (round(x1, 7) + 0.0, round(x2, 7) + 0.0)
            unicos.setdefault(clave, (x1 + 0.0, x2 + 0.0))
    res.pasos.append(f"Paso 3. Se descartan los puntos que violan alguna restricción: "
                     f"quedan {len(unicos)} vértices de la región factible.")

    # Sin vértices factibles la región es vacía (con x >= 0 toda región no
    # vacía tiene al menos un vértice)
    if not unicos:
        res.estado = "infactible"
        res.mensajes.append("Problema INFACTIBLE: ningún punto cumple todas las restricciones "
                            "a la vez (la región factible está vacía). Revise los datos.")
        return res

    # PASO 4 -- evaluar la función objetivo z en cada vértice
    for (x1, x2) in unicos.values():
        z = p.c1 * x1 + p.c2 * x2
        activas = [r.nombre for r in todas if r.esta_activa(x1, x2)]
        res.vertices.append(Vertice(x1, x2, z, activas))
    res.vertices.sort(key=lambda v: (v.x1, v.x2))
    res.pasos.append(f"Paso 4. Se evalúa z = {p.c1:g}·x1 + {p.c2:g}·x2 en cada vértice.")

    # ¿La región es no acotada en la dirección en que mejora z?
    tol_c = 1e-9 * (1.0 + math.hypot(p.c1, p.c2))
    mejora = False
    paralela = False
    for d in _direcciones_de_recesion(todas):
        dz = p.c1 * d[0] + p.c2 * d[1]
        if (p.objetivo == "max" and dz > tol_c) or (p.objetivo == "min" and dz < -tol_c):
            mejora = True
        elif abs(dz) <= tol_c:
            paralela = True

    if mejora:
        res.estado = "no_acotado"
        res.pasos.append("Paso 5. La región factible se extiende al infinito en una dirección "
                         "donde z sigue mejorando: no hay óptimo finito.")
        res.mensajes.append("Problema NO ACOTADO: z puede mejorar sin límite, por lo que no existe "
                            "un óptimo finito. Probablemente falta una restricción en el modelo.")
        return res

    # PASO 5 -- escoger el mejor vértice
    if p.objetivo == "min":
        mejor = min(v.z for v in res.vertices)
    else:
        mejor = max(v.z for v in res.vertices)
    tol_z = 1e-7 * (1.0 + abs(mejor))
    res.optimos = [v for v in res.vertices if abs(v.z - mejor) <= tol_z]
    for v in res.optimos:
        v.es_optimo = True
    res.z_optimo = mejor
    res.pasos.append(f"Paso 5. Como se desea {sentido}, el mejor valor es z* = {mejor:.4f}.")

    if len(res.optimos) >= 2 or paralela:
        res.estado = "optimos_alternativos"
        res.mensajes.append("ÓPTIMOS ALTERNATIVOS: la recta de z es paralela a un borde de la "
                            "región, por lo que hay infinitas soluciones con el mismo z*.")
    else:
        res.estado = "optimo"
    return res


# ---------------------------------------------------------------------------
# Texto de interpretación con los nombres y unidades del problema
# ---------------------------------------------------------------------------
def interpretar(p: Problema, res: Resultado) -> str:
    """Resultado final escrito con los nombres y unidades del problema."""
    if res.estado in ("infactible", "no_acotado"):
        return " ".join(res.mensajes)
    v = res.optimos[0]
    u1 = f" {p.unidad_x1}" if p.unidad_x1 else ""
    u2 = f" {p.unidad_x2}" if p.unidad_x2 else ""
    uz = f" {p.unidad_z}" if p.unidad_z else ""
    sentido = "mínimo" if p.objetivo == "min" else "máximo"
    texto = (f"La mejor decisión es usar {v.x1:.4f}{u1} de {p.nombre_x1} y "
             f"{v.x2:.4f}{u2} de {p.nombre_x2}, con un valor {sentido} de "
             f"z = {res.z_optimo:.2f}{uz}.")
    if res.estado == "optimos_alternativos":
        texto += (" Atención: existen óptimos alternativos con el mismo valor de z "
                  "(ver la tabla de vértices).")
    return texto
