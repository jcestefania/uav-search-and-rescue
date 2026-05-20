# Trabajo de Fin de Grado: Revisión de estrategias de búsqueda en tiempo mínimo en espacios con incertidumbre
## Requisitos
Este proyecto utiliza las librerías [numpy](https://numpy.org/doc/stable/), [pandas](https://pandas.pydata.org/docs) y [plotly](https://plotly.com/python/).
Estas librerías se pueden instalar con `pip`
```bash
$ pip install numpy pandas plotly==5.23.0
```
## Pruebas
Como cada algoritmo de búsqueda necesita ejecutarse de con unos parámetros específicos
y para mejorar la legibilidad, cada algoritmo se configura en un archivo distinto.  
Los algoritmos de fuerza bruta tienen el prefijo `bf-` (brute force)
y los que usan heurística `ldfs-` (limited depth first search).  

```bash
$ python3 <algoritmo de búsqueda> <archivo de prueba>
```
Para hacer las pruebas se ejecuta cada archivo de prueba con cada archivo de algoritmo.  

También se puede usar el cuaderno de python `lanzar-pruebas.ipynb`,
que organiza las pruebas de la misma forma que en la memoria.

### Casos de prueba
En el archivo pruebas.zip, se encuentran todos los archivos de prueba usados en este trabajo.
Se puede encontrar más información sobre cada archivo archivo de prueba en esta
[tabla publicada en Google Sheets](https://docs.google.com/spreadsheets/d/e/2PACX-1vRLJnhT5WI1-autzNrDDxAIw6PKOBSrm1mNe09J6y_rBDWasL869ojAjvPsbAo7jzR3MfNMmwHn6iZH/pubhtml)

## Análisis de resultados
Las gráficas usadas para el análisis de los casos de prueba, se han creado en los cuadernos
`analisis-resultados.ipynb`, `analisis-resultados-multiagente.ipynb` y `analisis-resultados-multiindicio.ipynb`.

