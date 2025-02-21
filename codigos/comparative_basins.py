import pandas as pd
import numpy as np
from pymannkendall import mk_test
import os

# Directorio donde están los archivos
data_dir = "/mnt/data/"
output_dir = "/mnt/data/results/"

os.makedirs(output_dir, exist_ok=True)

# Lista de archivos por cuenca
cuenca_files = {
    "Aconcagua": "054_runoff_std.csv",
    "Maipo": "057_runoff_std.csv",
    "Rapel": "060_runoff_std.csv",
    "Maule": "071_runoff_std.csv",
    "Mataquito": "073_runoff_std.csv"
}

# Columnas de modelos a analizar
models = [
    "SSP126_CR2MET_Runoff",
    "SSP585_CR2MET_Runoff",
    "CMIP5_CR2MET_Runoff",
    "SSP126_CHELSA_Runoff",
    "SSP585_CHELSA_Runoff",
    "BH5_All_Models_Sum"
]

# Períodos de comparación
start_year_initial = 1980
end_year_initial = 1989
start_year_final = 2051
end_year_final = 2060

# Función para calcular diferencias porcentuales
def calculate_percentage_difference(initial_mean, final_mean):
    return ((final_mean - initial_mean) / initial_mean) * 100

# Función para aplicar el test de Mann-Kendall
def apply_mann_kendall_test(data):
    result = mk_test(data, alpha=0.05)
    return {
        "tau": result.Tau,
        "p_value": result.p,
        "trend": result.trend,
        "classification": "Significativa" if result.p < 0.05 else "No significativa"
    }

# DataFrame para almacenar los resultados
results_list = []

for cuenca, filename in cuenca_files.items():
    file_path = os.path.join(data_dir, filename)
    df = pd.read_csv(file_path, index_col=0)

    # Convertir índice a enteros (años)
    df.index = df.index.astype(int)

    # Extraer datos de los períodos inicial y final
    df_initial = df.loc[start_year_initial:end_year_initial]
    df_final = df.loc[start_year_final:end_year_final]

    for model in models:
        if model in df.columns:
            # Cálculo de promedios y desviaciones estándar
            initial_mean = df_initial[model].mean()
            initial_std = df_initial[model].std()
            final_mean = df_final[model].mean()
            final_std = df_final[model].std()

            # Diferencia porcentual
            percentage_diff = calculate_percentage_difference(initial_mean, final_mean)

            # Aplicación del test de Mann-Kendall
            kendall_results = apply_mann_kendall_test(df[model].dropna())

            # Guardar resultados
            results_list.append({
                "Cuenca": cuenca,
                "Modelo": model,
                "Inicial (m³/s)": f"{initial_mean:.2f} ± {initial_std:.2f}",
                "Final (m³/s)": f"{final_mean:.2f} ± {final_std:.2f}",
                "Diferencia (%)": f"{percentage_diff:.2f}%",
                "Mann-Kendall Tau": f"{kendall_results['tau']:.2f}",
                "p-valor": f"{kendall_results['p_value']:.4f}",
                "Tendencia": kendall_results["trend"],
                "Significancia": kendall_results["classification"]
            })

# Convertir a DataFrame y guardar resultados
results_df = pd.DataFrame(results_list)
results_csv_path = os.path.join(output_dir, "runoff_analysis_results.csv")
results_df.to_csv(results_csv_path, index=False)

print(f"Análisis completado. Resultados guardados en {results_csv_path}")
