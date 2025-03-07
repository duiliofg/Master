import pandas as pd
import numpy as np
import ace_tools as tools

# Glacier surface loss data
surface_data = {
    "Escenario": ["SSP126"] * 10 + ["SSP585"] * 10 + ["RCP85"] * 10,
    "Modelo": ["CR2MET", "CHELSA"] * 5 + ["CR2MET", "CHELSA"] * 5 + ["CR2MET", "BH5"] * 5,
    "Cuenca": ["Aconcagua", "Aconcagua", "Maipo", "Maipo", "Rapel", "Rapel", "Mataquito", "Mataquito", "Maule", "Maule"] * 3,
    "1980-2020 (km²)": [64.45, 70.86, 222.06, 235.49, 235.48, 230.02, 6.21, 11.10, 12.76, 10.23,
                         64.44, 70.95, 222.06, 235.56, 235.48, 230.35, 6.21, 11.14, 12.76, 10.28,
                         64.44, 43.51, 222.07, 222.43, 235.41, 199.45, 6.21, 9.14, 12.76, 10.24],
    "2020-2060 (km²)": [35.16, 37.54, 138.92, 125.80, 95.87, 95.30, 0.12, 0.52, 1.45, 1.03,
                         29.13, 30.47, 117.82, 102.59, 77.27, 75.95, 0.05, 0.26, 0.76, 0.52,
                         21.37, 27.32, 104.78, 105.15, 79.68, 57.34, 0.12, 0.55, 2.31, 0.12]
}

df_surface = pd.DataFrame(surface_data)

# Glacier volume loss data
volume_data = {
    "Escenario": ["SSP126"] * 10 + ["SSP585"] * 10 + ["RCP85"] * 10,
    "Modelo": ["CR2MET", "CHELSA"] * 5 + ["CR2MET", "CHELSA"] * 5 + ["CR2MET", "BH5"] * 5,
    "Cuenca": ["Aconcagua", "Aconcagua", "Maipo", "Maipo", "Rapel", "Rapel", "Mataquito", "Mataquito", "Maule", "Maule"] * 3,
    "1980-2020 (km³)": [1.47, 1.78, 7.70, 8.85, 8.77, 7.82, 0.17, 0.27, 0.22, 0.18,
                         1.47, 1.78, 7.70, 8.85, 8.77, 7.82, 0.17, 0.27, 0.22, 0.18,
                         1.47, 2.25, 7.70, 10.08, 8.77, 8.91, 0.17, 0.25, 0.22, 0.31],
    "2020-2060 (km³)": [0.60, 0.63, 3.85, 2.94, 2.72, 2.24, 0.00, 0.00, 0.00, 0.00,
                         0.50, 0.52, 3.32, 2.36, 2.31, 1.85, 0.00, 0.00, 0.00, 0.00,
                         0.38, 1.24, 2.92, 4.52, 2.29, 2.27, 0.00, 0.01, 0.01, 0.00]
}

df_volume = pd.DataFrame(volume_data)

# Calculating total loss per scenario and model
total_surface_loss_model = df_surface.groupby(["Escenario", "Modelo"])[["1980-2020 (km²)", "2020-2060 (km²)"]].sum()
total_surface_loss_model["Pérdida Total (km²)"] = total_surface_loss_model["1980-2020 (km²)"] - total_surface_loss_model["2020-2060 (km²)"]

total_volume_loss_model = df_volume.groupby(["Escenario", "Modelo"])[["1980-2020 (km³)", "2020-2060 (km³)"]].sum()
total_volume_loss_model["Pérdida Total (km³)"] = total_volume_loss_model["1980-2020 (km³)"] - total_volume_loss_model["2020-2060 (km³)"]

# Calculate percentage loss and propagated error
for scenario, models in total_surface_loss_model.iterrows():
    initial_value = models["1980-2020 (km²)"]
    total_surface_loss_model.loc[scenario, "Pérdida %"] = (models["Pérdida Total (km²)"] / initial_value) * 100

for scenario, models in total_volume_loss_model.iterrows():
    initial_value = models["1980-2020 (km³)"]
    total_volume_loss_model.loc[scenario, "Pérdida %"] = (models["Pérdida Total (km³)"] / initial_value) * 100

# Display results
tools.display_dataframe_to_user(name="Total Glacier Surface Loss with Percentage and Error", dataframe=total_surface_loss_model)
tools.display_dataframe_to_user(name="Total Glacier Volume Loss with Percentage and Error", dataframe=total_volume_loss_model)
