import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib.lines as mlines
import os

# ===============================
# 1. Cargar datos
# ===============================
anomalia_temp = pd.read_csv('/media/duilio/8277-C610/OGGM/Thesis/tex/anomalias/anomalia_temperatura.csv')
anomalia_prec = pd.read_csv('/media/duilio/8277-C610/OGGM/Thesis/tex/anomalias/anomalia_precipitaciones.csv')

anomalia_temp['basin'] = anomalia_temp['basin'].astype(str)
anomalia_prec['basin'] = anomalia_prec['basin'].astype(str)

# ===============================
# 2. Definir estilo, colores y símbolos
# ===============================
sns.set(style="whitegrid")

# Directorio de salida
output_dir = '/media/duilio/8277-C610/OGGM/Thesis/tex/figuras_v2'
os.makedirs(output_dir, exist_ok=True)  # Crear carpeta si no existe

# Mapear cuenca a posición
basin_order_temp = {basin: idx for idx, basin in enumerate(anomalia_temp['basin'].unique())}
basin_order_prec = {basin: idx for idx, basin in enumerate(anomalia_prec['basin'].unique())}

# Colores por escenario
palette = {
    'SSP1-2.6': '#1f77b4',  # azul
    'SSP5-8.5': '#ff7f0e',  # naranjo
    'RCP8.5': '#2ca02c'     # verde
}

# Símbolos por modelo
markers = {
    'CHELSA': 'o',
    'CR2MET': 'X'
}

# Crear elementos de leyenda manual
legend_elements = [
    mlines.Line2D([], [], color=palette['SSP1-2.6'], marker='o', linestyle='None', markersize=8, label='SSP1-2.6'),
    mlines.Line2D([], [], color=palette['SSP5-8.5'], marker='o', linestyle='None', markersize=8, label='SSP5-8.5'),
    mlines.Line2D([], [], color=palette['RCP8.5'], marker='o', linestyle='None', markersize=8, label='RCP8.5'),
    mlines.Line2D([], [], color='black', marker='o', linestyle='None', markersize=8, label='CHELSA'),
    mlines.Line2D([], [], color='black', marker='X', linestyle='None', markersize=8, label='CR2MET')
]

# Offsets uniformemente distribuidos
offsets = [-0.25, -0.10, 0, 0.10, 0.25]

# ===============================
# 3. Gráfico de Anomalía de Temperatura
# ===============================

fig, ax = plt.subplots(figsize=(10, 6))

for basin in anomalia_temp['basin'].unique():
    data_cuenca = anomalia_temp[anomalia_temp['basin'] == basin]
    for idx, (_, row) in enumerate(data_cuenca.iterrows()):
        x = basin_order_temp[basin] + offsets[idx]
        ax.scatter(
            x,
            row['mean_temperature'],
            color=palette.get(row['ssp_list'], 'gray'),
            marker=markers.get(row['Modelo'], 'o'),
            s=100,
            edgecolor='black',
            linewidth=0.5,
            zorder=3
        )
        ax.errorbar(
            x,
            row['mean_temperature'],
            yerr=row['std_temperature'],
            fmt='none',
            ecolor=palette.get(row['ssp_list'], 'gray'),
            capsize=4,
            elinewidth=1,
            zorder=2
        )

ax.set_title('Anomalía de Temperatura 2030-2060', weight='bold', fontsize=16)
ax.set_xlabel('Cuenca', weight='bold', fontsize=14)
ax.set_ylabel('Anomalía de Temperatura [°C]', weight='bold', fontsize=14)
ax.set_xticks(list(basin_order_temp.values()))
ax.set_xticklabels(list(basin_order_temp.keys()), fontsize=12)
ax.tick_params(axis='y', labelsize=12)
ax.grid(True, linestyle='--', alpha=0.6)

# Leyenda afuera
ax.legend(handles=legend_elements, title='Escenario / Modelo', fontsize=10, title_fontsize=12,
          loc='center left', bbox_to_anchor=(1, 0.5))

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'anomalia_temperatura.png'), dpi=300, bbox_inches='tight')
plt.show()

# ===============================
# 4. Gráfico de Anomalía de Precipitación
# ===============================

fig, ax = plt.subplots(figsize=(10, 6))

for basin in anomalia_prec['basin'].unique():
    data_cuenca = anomalia_prec[anomalia_prec['basin'] == basin]
    for idx, (_, row) in enumerate(data_cuenca.iterrows()):
        x = basin_order_prec[basin] + offsets[idx]
        ax.scatter(
            x,
            row['mean_precipitation_perc'],
            color=palette.get(row['ssp_list'], 'gray'),
            marker=markers.get(row['Modelo'], 'o'),
            s=100,
            edgecolor='black',
            linewidth=0.5,
            zorder=3
        )
        ax.errorbar(
            x,
            row['mean_precipitation_perc'],
            yerr=row['std_precipitation_perc'],
            fmt='none',
            ecolor=palette.get(row['ssp_list'], 'gray'),
            capsize=4,
            elinewidth=1,
            zorder=2
        )

ax.set_title('Anomalía de Precipitación 2030-2060', weight='bold', fontsize=16)
ax.set_xlabel('Cuenca', weight='bold', fontsize=14)
ax.set_ylabel('Anomalía de Precipitación [%]', weight='bold', fontsize=14)
ax.set_xticks(list(basin_order_prec.values()))
ax.set_xticklabels(list(basin_order_prec.keys()), fontsize=12)
ax.tick_params(axis='y', labelsize=12)
ax.grid(True, linestyle='--', alpha=0.6)

# Leyenda afuera
ax.legend(handles=legend_elements, title='Escenario / Modelo', fontsize=10, title_fontsize=12,
          loc='center left', bbox_to_anchor=(1, 0.5))

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'anomalia_precipitacion.png'), dpi=300, bbox_inches='tight')
plt.show()
