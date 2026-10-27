# Método gráfico – Grupo 7 (IO1-82)

Software del Proyecto Final de Investigación de Operaciones 1.
Resuelve cualquier PL de **2 variables** (maximizar o minimizar, restricciones
≤, ≥ y =, hasta 8 restricciones) con el **método gráfico**, programado desde cero
(sin SciPy, PuLP ni OR-Tools dentro del software).

## Requisitos
- Python 3.10 o superior

## Instalación
```bash
python -m venv venv
# Windows:  venv\Scripts\activate        Linux/Mac:  source venv/bin/activate
pip install -r requirements.txt
```

## Ejecución
```bash
streamlit run app.py
```
Se abre el navegador en http://localhost:8501. Escoja un ejemplo precargado o
"Problema nuevo en blanco", escriba nombres, unidades, coeficientes y
restricciones, y pulse **Resolver con el método gráfico**.

## Pruebas automáticas
```bash
pytest -q
```

## Verificación externa (opcional)
```bash
python verificacion_externa.py
```
Compara los resultados con SciPy, usado solo para comprobar.

## Archivos
| Archivo | Qué hace |
|---|---|
| `app.py` | Interfaz (Streamlit): ingreso de datos, validación y resultados |
| `metodo_grafico.py` | Lógica del método gráfico y validación de datos |
| `grafico.py` | Dibuja rectas, región factible, vértices y óptimo |
| `ejemplos.json` | Ejemplos precargados (caso real + 5 pruebas) |
| `test_metodo_grafico.py` | Pruebas automáticas |
| `verificacion_externa.py` | Comprobación contra SciPy |
