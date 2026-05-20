import matplotlib
# Forzar backend de escritorio para que la gráfica salga en ventana independiente
matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Configuración de estilo profesional
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.titlesize'] = 14

def plot_evolution(df_evolution, optimization="min", title=None):
    """
    Muestra la evolución del mejor valor de la función objetivo por iteración.
    La gráfica se abre en ventana independiente con estilo profesional.
    """
    if not isinstance(df_evolution, pd.DataFrame):
        raise TypeError("df_evolution debe ser un pandas.DataFrame.")
    if "Iteración" not in df_evolution.columns or "Mejor Obj" not in df_evolution.columns:
        raise ValueError("El DataFrame debe contener las columnas 'Iteración' y 'Mejor Obj'.")

    fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
    
    # Colores profesionales
    if optimization == "min":
        color_main = '#2E86AB'  # Azul profesional
        color_fill = '#A7C6DA'  # Azul claro para relleno
        default_title = "Evolución de la Función Objetivo (Minimización)"
    elif optimization == "max":
        color_main = '#06A77D'  # Verde profesional
        color_fill = '#90D9C0'  # Verde claro para relleno
        default_title = "Evolución de la Función Objetivo (Maximización)"
    else:
        raise ValueError("El parámetro 'optimization' debe ser 'min' o 'max'.")
    
    # Gráfica principal con línea más gruesa
    ax.plot(df_evolution["Iteración"], df_evolution["Mejor Obj"], 
            color=color_main, linewidth=2.5, label="Mejor valor encontrado",
            marker='o', markersize=5, markerfacecolor='white', 
            markeredgewidth=2, markeredgecolor=color_main)
    
    # Área sombreada bajo la curva para efecto visual
    ax.fill_between(df_evolution["Iteración"], df_evolution["Mejor Obj"], 
                     alpha=0.2, color=color_fill)
    
    # Etiquetas y título
    ax.set_xlabel("Iteración", fontweight='bold')
    ax.set_ylabel("Mejor Valor de la Función Objetivo", fontweight='bold')
    ax.set_title(title or default_title, fontweight='bold', pad=20)
    
    # Grid más sutil
    ax.grid(True, linestyle='--', alpha=0.3, linewidth=0.8)
    ax.set_axisbelow(True)
    
    # Leyenda con borde
    legend = ax.legend(loc='best', frameon=True, shadow=True, fancybox=True)
    legend.get_frame().set_alpha(0.9)
    
    # Marco más limpio
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.show(block=True)


def plot_multiple_evolutions(list_dfs, optimization="min", title=None, labels=None):
    """
    Dibuja varias curvas de evolución del ACO en una misma gráfica.
    La gráfica se abre en ventana independiente con estilo profesional.
    
    Args:
        list_dfs: Lista de DataFrames con evoluciones
        optimization: 'min' o 'max'
        title: Título personalizado
        labels: Lista de etiquetas personalizadas para cada curva
    """
    if not isinstance(list_dfs, list) or not all(isinstance(df, pd.DataFrame) for df in list_dfs):
        raise TypeError("list_dfs debe ser una lista de pandas.DataFrame.")

    fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
    
    # Paleta de colores profesional
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#06A77D', '#C73E1D', 
              '#6A4C93', '#1B998B', '#E71D36', '#2D3142', '#F77F00']
    
    # Calcular estadísticas si hay múltiples ejecuciones
    if len(list_dfs) > 1:
        # Crear matriz para calcular media y desviación
        max_iter = max(df["Iteración"].max() for df in list_dfs)
        all_values = []
        
        for df in list_dfs:
            all_values.append(df["Mejor Obj"].values)
        
        # Calcular media y desviación estándar
        mean_values = np.mean(all_values, axis=0)
        std_values = np.std(all_values, axis=0)
        iterations = list_dfs[0]["Iteración"].values
        
        # Plotear líneas individuales con transparencia
        for i, df in enumerate(list_dfs):
            if "Iteración" not in df.columns or "Mejor Obj" not in df.columns:
                raise ValueError(f"El DataFrame {i} no contiene las columnas requeridas.")
            
            label = labels[i] if labels and i < len(labels) else f"Ejecución {i+1}"
            ax.plot(df["Iteración"], df["Mejor Obj"], 
                   color=colors[i % len(colors)], linewidth=1.5, 
                   alpha=0.4, marker='o', markersize=3, label=label)
        
        # Plotear la media con línea destacada
        ax.plot(iterations, mean_values, color='black', linewidth=3, 
               label='Media', marker='s', markersize=6, markerfacecolor='white',
               markeredgewidth=2, markeredgecolor='black', zorder=10)
        
        # Área de confianza (±1 desviación estándar)
        ax.fill_between(iterations, mean_values - std_values, 
                       mean_values + std_values, alpha=0.2, color='gray',
                       label='±1 desv. estándar')
    else:
        # Si solo hay una ejecución
        df = list_dfs[0]
        if "Iteración" not in df.columns or "Mejor Obj" not in df.columns:
            raise ValueError("El DataFrame no contiene las columnas requeridas.")
        
        label = labels[0] if labels else "Evolución"
        ax.plot(df["Iteración"], df["Mejor Obj"], 
               color=colors[0], linewidth=2.5, marker='o', markersize=5,
               markerfacecolor='white', markeredgewidth=2, 
               markeredgecolor=colors[0], label=label)

    # Configuración de ejes y título
    ax.set_xlabel("Iteración", fontweight='bold')
    ax.set_ylabel("Mejor Valor de la Función Objetivo", fontweight='bold')
    
    default_title = f"Evolución Comparativa del Algoritmo ACO ({'Minimización' if optimization=='min' else 'Maximización'})"
    ax.set_title(title or default_title, fontweight='bold', pad=20)
    
    # Grid y estilo
    ax.grid(True, linestyle='--', alpha=0.3, linewidth=0.8)
    ax.set_axisbelow(True)
    
    # Leyenda optimizada
    legend = ax.legend(loc='best', frameon=True, shadow=True, 
                      fancybox=True, ncol=2 if len(list_dfs) > 4 else 1)
    legend.get_frame().set_alpha(0.9)
    
    # Marco limpio
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.show(block=True)