import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- 1. CONFIGURACIÓN ---
# Usamos exactamente el path relativo.
# EJECUTAR ESTO PARADO EN LA CARPETA 'python'
input_path = '../data/ncr_ride_bookings.csv'
output_path = '../data/ncr_rides_cleaned.csv'

# Configuración visual
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = [12, 6]

print(f"🔄 Buscando archivo original en: {input_path}")

try:
    # --- 2. CARGA Y LIMPIEZA (ETL) ---
    df = pd.read_csv(input_path)
    print("✅ Archivo cargado.")

    # A. Limpieza de Comillas
    cols_text = ['Booking ID', 'Booking Status', 'Vehicle Type', 'Customer ID',
                 'Pickup Location', 'Drop Location', 'Payment Method']
    
    for col in cols_text:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('"', '').str.replace("'", "").str.strip()

    # B. Conversión de Números
    numeric_cols = ['Booking Value', 'Ride Distance', 'Driver Ratings', 'Customer Rating']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # C. Limpieza de Fechas
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    print("✅ Datos limpios: Comillas eliminadas y tipos corregidos.")

    # --- 3. INGENIERÍA DE CARACTERÍSTICAS ---
    
    # A. Franja Horaria
    if 'Time' in df.columns:
        df['Hour_Num'] = pd.to_datetime(df['Time'], format='%H:%M:%S', errors='coerce').dt.hour
        
        def get_time_of_day(h):
            if pd.isna(h): return 'Unknown'
            if 6 <= h < 12: return 'Mañana'
            elif 12 <= h < 18: return 'Tarde'
            elif 18 <= h < 24: return 'Noche'
            else: return 'Madrugada'

        df['Time_of_Day'] = df['Hour_Num'].apply(get_time_of_day)

    # B. Ingresos Perdidos
    avg_ticket = df[df['Booking Status'] == 'Completed']['Booking Value'].mean()
    
    df['Potential_Revenue_Loss'] = df.apply(
        lambda x: x['Booking Value'] if x['Booking Value'] > 0 
        else (avg_ticket if x['Booking Status'] != 'Completed' else 0), 
        axis=1
    )

    print("✅ Nuevas métricas creadas: Franja Horaria y Pérdida Estimada.")

    # --- 4. EXPORTACIÓN PARA POWER BI ---
    df.to_csv(output_path, index=False)
    print(f"💾 Archivo limpio GENERADO en: {output_path}")

    # --- 5. VISUALIZACIÓN (EDA) ---
    
    # Gráfico 1: Tasa de Éxito por Vehículo
    if 'Vehicle Type' in df.columns:
        vehicle_kpi = df.groupby('Vehicle Type').agg(
            Total=('Booking ID', 'count'),
            Completed=('Booking Status', lambda x: (x == 'Completed').sum())
        ).reset_index()
        vehicle_kpi['Success_Rate'] = (vehicle_kpi['Completed'] / vehicle_kpi['Total']) * 100
        vehicle_kpi = vehicle_kpi.sort_values('Success_Rate')

        plt.figure()
        # AQUÍ ESTÁ EL CAMBIO PARA QUITAR EL WARNING: hue='Vehicle Type' y legend=False
        sns.barplot(data=vehicle_kpi, x='Success_Rate', y='Vehicle Type', hue='Vehicle Type', legend=False, palette='RdYlGn')
        
        plt.title('Tasa de Éxito por Tipo de Vehículo')
        plt.xlabel('% Viajes Completados')
        plt.axvline(x=50, color='red', linestyle='--', label='Punto Crítico (50%)')
        plt.legend()
        plt.tight_layout()
        plt.savefig('chart_vehicle_success.png')
        print("📊 Gráfico 1 generado: chart_vehicle_success.png")

    # Gráfico 2: Dinero Perdido por Motivo
    if 'Booking Status' in df.columns:
        loss_kpi = df[df['Booking Status'] != 'Completed'].groupby('Booking Status')['Potential_Revenue_Loss'].sum().sort_values(ascending=False)
        
        plt.figure()
        loss_kpi.plot(kind='bar', color='salmon')
        plt.title('Dinero Estimado Perdido por Estado del Viaje')
        plt.ylabel('Monto Total')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('chart_revenue_loss.png')
        print("📊 Gráfico 2 generado: chart_revenue_loss.png")

    print("\n--- PROCESO TERMINADO ---")

except FileNotFoundError:
    print("\n❌ ERROR DE RUTA:")
    print(f"No se encuentra el archivo en '{input_path}'")
except Exception as e:
    print(f"\n❌ Ocurrió un error: {e}")