#Clase principal de recolecta y validación de los datos 
import json
import os

import streamlit as st

from grafico import dibujar
from metodo_grafico import MAX_RESTRICCIONES, construir_problema, interpretar, resolver

RUTA_EJEMPLOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ejemplos.json")
EN_BLANCO = "— Problema nuevo en blanco —"
ESTADOS = {
    "optimo": ("success", "Solución óptima única encontrada."),
    "optimos_alternativos": ("warning", "Óptimos alternativos."),
    "infactible": ("error", "Problema infactible."),
    "no_acotado": ("error", "Problema no acotado."),
}


@st.cache_data
def cargar_ejemplos() -> dict:
    with open(RUTA_EJEMPLOS, encoding="utf-8") as f:
        return json.load(f)


def poner_datos(e: dict) -> None:
    s = st.session_state
    s["obj"] = e.get("objetivo", "min")
    for clave in ("c1", "c2", "nombre_x1", "unidad_x1", "nombre_x2", "unidad_x2", "unidad_z"):
        s[clave] = e.get(clave, "")
    filas = e.get("restricciones", [])
    s["nrest"] = max(1, len(filas)) if filas else 3
    for i in range(MAX_RESTRICCIONES):
        f = filas[i] if i < len(filas) else {}
        s[f"rn{i}"] = f.get("nombre", "")
        s[f"ra{i}"] = f.get("a1", "")
        s[f"rb{i}"] = f.get("a2", "")
        s[f"rs{i}"] = f.get("signo", "<=")
        s[f"rr{i}"] = f.get("b", "")


def al_cambiar_ejemplo() -> None:
    nombre = st.session_state["ejemplo"]
    poner_datos({} if nombre == EN_BLANCO else cargar_ejemplos()[nombre])



ejemplos = cargar_ejemplos()
if "iniciado" not in st.session_state:
    st.session_state["iniciado"] = True
    st.session_state["ejemplo"] = list(ejemplos)[0]
    poner_datos(ejemplos[st.session_state["ejemplo"]])

#Ingreso de datos 
st.selectbox("Ejemplo precargado", [EN_BLANCO] + list(ejemplos), key="ejemplo",
             on_change=al_cambiar_ejemplo)
st.caption("Escriba los números con punto o coma decimal y sin separador de miles "
           "(por ejemplo 2560 y 0.085).")

col_a, col_b = st.columns(2)
with col_a:
    st.radio("Objetivo", ["min", "max"], key="obj", horizontal=True,
             format_func=lambda v: "Minimizar" if v == "min" else "Maximizar")
    st.text_input("Unidad de z (ej. $/día)", key="unidad_z")
with col_b:
    st.number_input("Número de restricciones (1 a 8)", min_value=1,
                    max_value=MAX_RESTRICCIONES, step=1, key="nrest")

st.markdown("**Variables de decisión y función objetivo**")
v1, v2 = st.columns(2)
with v1:
    st.text_input("Nombre de la variable 1 (x1)", key="nombre_x1")
    st.text_input("Unidad de x1", key="unidad_x1")
    st.text_input("Coeficiente de x1 en z", key="c1")
with v2:
    st.text_input("Nombre de la variable 2 (x2)", key="nombre_x2")
    st.text_input("Unidad de x2", key="unidad_x2")
    st.text_input("Coeficiente de x2 en z", key="c2")

st.markdown("**Restricciones**  (coeficiente de x1, coeficiente de x2, signo, lado derecho)")
filas = []
for i in range(int(st.session_state["nrest"])):
    c0, c1, c2, c3, c4 = st.columns([3, 1.3, 1.3, 1, 1.5])
    c0.text_input(f"Nombre restricción {i + 1}", key=f"rn{i}")
    c1.text_input("x1", key=f"ra{i}")
    c2.text_input("x2", key=f"rb{i}")
    c3.selectbox("Signo", ["<=", ">=", "="], key=f"rs{i}",
                 format_func=lambda s: {"<=": "≤", ">=": "≥", "=": "="}[s])
    c4.text_input("Lado derecho", key=f"rr{i}")
    filas.append({"nombre": st.session_state[f"rn{i}"], "a1": st.session_state[f"ra{i}"],
                  "a2": st.session_state[f"rb{i}"], "signo": st.session_state[f"rs{i}"],
                  "b": st.session_state[f"rr{i}"]})

#Resolver
if st.button("Resolver con el método gráfico", type="primary"):
    datos = {k: st.session_state[k] for k in
             ("c1", "c2", "nombre_x1", "unidad_x1", "nombre_x2", "unidad_x2", "unidad_z")}
    datos["objetivo"] = st.session_state["obj"]
    datos["restricciones"] = filas

    # Validación: si hay errores se muestran y el programa NO se cierra
    problema, errores = construir_problema(datos)
    if errores:
        st.error("Revise los datos antes de resolver:")
        for e in errores:
            st.markdown(f"- {e}")
    else:
        try:
            res = resolver(problema)
        except Exception as exc:  # protección: la app nunca debe cerrarse
            st.error(f"Ocurrió un error inesperado al resolver: {exc}")
        else:
            tipo, titulo = ESTADOS[res.estado]
            getattr(st, tipo)(f"**{titulo}**  {interpretar(problema, res)}")
            if res.estado == "optimos_alternativos":
                st.info("Los vértices óptimos están marcados con ★ en la tabla.")

            t1, t2, t3 = st.tabs(["Gráfica", "Vértices y z", "Paso a paso"])
            with t1:
                st.pyplot(dibujar(problema, res))
            with t2:
                u1 = f" ({problema.unidad_x1})" if problema.unidad_x1 else ""
                u2 = f" ({problema.unidad_x2})" if problema.unidad_x2 else ""
                st.dataframe([{
                    "Vértice": f"V{i + 1}",
                    f"{problema.nombre_x1}{u1}": round(v.x1, 4),
                    f"{problema.nombre_x2}{u2}": round(v.x2, 4),
                    f"z ({problema.unidad_z})" if problema.unidad_z else "z": round(v.z, 4),
                    "Restricciones activas": ", ".join(v.activas),
                    "Óptimo": "★" if v.es_optimo else "",
                } for i, v in enumerate(res.vertices)])
            with t3:
                for linea in res.pasos:
                    st.text(linea)
