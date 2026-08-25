# 📐 Modelo de Observación del Sensor (Basado en el TFG de Yago Brotón)

> 📌 **UBICACIÓN EN LA MEMORIA DEL TFM:**
> - **Capítulo:** Capítulo 3 (*Modelado del Problema* / `Capitulo3_Modelado.tex`)
> - **Sección:** Sección 3.3 (*Observaciones y Modelo de Sensor del Dron*)

---

```bibtex
% =============================================================================
% RECORDATORIO: Añadir esta entrada al archivo bibliografia.bib de la memoria
% =============================================================================
@mastersthesis{broton2025revision,
  title={Revisión de estrategias de búsqueda en espacios con incertidumbre},
  author={Brotón Gutiérrez, Yago},
  school={Universidad Carlos III de Madrid (UC3M)},
  year={2025},
  month={Febrero},
  type={Trabajo de Fin de Grado}
}
```

---

## 1. Contexto Teórico

En las misiones de búsqueda probabilística en tiempo mínimo (MTS), los vehículos aéreos no tripulados (UAVs) están equipados con sensores de visión a bordo (cámaras ópticas/térmicas) encargados de realizar observaciones sobre el espacio de búsqueda discretizado $\Omega$.

Sea $s_t^u$ la posición geográfica del dron $u$ en el instante de tiempo $t$, y sea $\nu^t$ la posición real de la víctima desaparecida. La función de verosimilitud de la observación $P(z_t^u \mid \nu^t, s_t^u)$ determina la probabilidad de detectar el objetivo dada la distancia $d = \|s_t^u - \nu^t\|$.

---

## 2. Formulación General (Función de Verosimilitud Exponencial)

De acuerdo con el modelo probabilístico estándar descrito en la literatura (Lanillos et al., Stone):

$$P(z_t^u \mid \nu^t, s_t^u) = P_{\max} \cdot \exp\left(-\sigma \left(\frac{d}{d_{\max}}\right)^2\right)$$

Donde:
- $P_{\max} \in [0.0, 1.0]$: Probabilidad máxima de detección del sensor cuando el objetivo se encuentra en el centro de la huella.
- $d_{\max}$: Distancia/radio máximo de detección del sensor (apotema de la huella sobre el terreno).
- $\sigma$: Sensibilidad a la distancia (factor de caída exponencial).

---

## 3. Modelo de Sensor Ideal *Level 1* (Adoptado en este TFM)

Siguiendo el enfoque simplificado y robusto propuesto por Brotón Gutiérrez \cite{broton2025revision}, asumimos un **Sensor Ideal de Barrido Geométrico (Level 1)**.

Bajo este modelo, la probabilidad de detección dentro del Campo de Visión (*Field of View* / FoV) proyectado sobre el terreno es perfecta ($P_d = 1.0$) y nula fuera del mismo:

$$P_d(x, y) = \begin{cases} 
1.0 & \text{si } (x, y) \in \text{FoV (Huella geométrica del cono de la cámara)} \\ 
0.0 & \text{si } (x, y) \notin \text{FoV} 
\end{cases}$$

---

## 4. Discretización y Huella de Barrido en Casa de Campo

En nuestras simulaciones sobre la Casa de Campo:
- La malla espacial está discretizada en celdas de $10\text{ m} \times 10\text{ m}$ ($100\text{ m}^2$).
- El cono de la cámara del dron proyecta una huella circular de radio $R_d = 50\text{ m}$ (cobertura de 5 celdas de radio / $100\text{ m}$ de ancho de barrido total).
- En cada instante $t$, toda celda $(i, j)$ dentro de la huella es inspeccionada:
  - Si la víctima no se encuentra en esa celda, su creencia Bayesiana se actualiza a $b(v_{i,j}^t) = 0.0$.
  - La probabilidad restante del terreno no explorado se renormaliza dividiendo por $\sum b(v^t)$ para mantener la densidad total sumando $1.0$ ($100\%$).
