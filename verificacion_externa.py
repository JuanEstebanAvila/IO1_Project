"""
Comprueba los resultados del método gráfico contra SciPy 
"""
import json
import os

from scipy.optimize import linprog

from metodo_grafico import construir_problema, resolver

RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ejemplos.json")

with open(RUTA, encoding="utf-8") as f:
    ejemplos = json.load(f)

print(f"{'Ejemplo':45s} {'Método gráfico':>16s} {'SciPy':>12s}  Coincide")
for nombre, datos in ejemplos.items():
    p, _ = construir_problema(datos)
    res = resolver(p)

    # Se arma el problema para linprog: min c·x, A_ub x <= b_ub, A_eq x = b_eq
    c = [p.c1, p.c2] if p.objetivo == "min" else [-p.c1, -p.c2]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for r in p.restricciones:
        if r.signo == "=":
            A_eq.append([r.a1, r.a2]); b_eq.append(r.b)
        else:
            s = 1 if r.signo == "<=" else -1
            A_ub.append([s * r.a1, s * r.a2]); b_ub.append(s * r.b)
    sol = linprog(c, A_ub=A_ub or None, b_ub=b_ub or None,
                  A_eq=A_eq or None, b_eq=b_eq or None, bounds=[(0, None)] * 2)

    if sol.status == 0:
        z_ref = sol.fun if p.objetivo == "min" else -sol.fun
        propio = f"{res.z_optimo:.4f}" if res.z_optimo is not None else res.estado
        ok = res.z_optimo is not None and abs(res.z_optimo - z_ref) < 1e-6
        print(f"{nombre[:45]:45s} {propio:>16s} {z_ref:12.4f}  {'sí' if ok else 'NO'}")
    else:
        estado_ref = {2: "infactible", 3: "no_acotado"}.get(sol.status, "otro")
        print(f"{nombre[:45]:45s} {res.estado:>16s} {estado_ref:>12s}  "
              f"{'sí' if res.estado == estado_ref else 'NO'}")
