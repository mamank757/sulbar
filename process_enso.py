import os
import requests
import pandas as pd
import numpy as np

def main():
    url = "https://www.bom.gov.au/clim_data/IDCK000072/rnino_3.4.txt"
    csv_output = 'nino34_bom_oni_format.csv'
    excel_output = 'nino34_bom_oni_format.xlsx'
    
    print(f"Mengunduh data dari: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Gagal mendownload data. Status code: {response.status_code}")
    
    # Simpan sementara atau baca langsung dari string buffer
    from io import StringIO
    f = StringIO(response.text)
    
    # Membaca data teks BOM (mengabaikan baris komentar '#')
    df = pd.read_csv(
        f, 
        comment='#', 
        sep=r'\s+', 
        header=None, 
        names=['Date', 'Relative_Nino34']
    )
    
    # Konversi format tanggal dan pembersihan data invalid
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date', 'Relative_Nino34'])
    df.set_index('Date', inplace=True)
    
    # Agregasi dari mingguan ke rata-rata bulanan (Monthly Mean)
    monthly_df = df.resample('ME')['Relative_Nino34'].mean().reset_index()
    monthly_df.rename(columns={'Relative_Nino34': 'Monthly_Anomaly'}, inplace=True)
    
    # Hitung 3-Month Running Mean (Centered Moving Average ala ONI NOAA)
    monthly_df['ONI_Equivalent_3Mo'] = (
        monthly_df['Monthly_Anomaly']
        .rolling(window=3, center=True, min_periods=3)
        .mean()
    )
    
    # Ekstrak Tahun dan Bulan
    monthly_df['Year'] = monthly_df['Date'].dt.year
    monthly_df['Month'] = monthly_df['Date'].dt.month
    
    # Export ke CSV & Excel
    monthly_df.to_csv(csv_output, index=False)
    monthly_df.to_excel(excel_output, index=False, engine='openpyxl')
    print("[OK] Data berhasil diproses dan file berhasil diperbarui.")

if __name__ == '__main__':
    main()
