import os
import requests
import pandas as pd
import numpy as np

def main():
    url = "https://www.bom.gov.au/clim_data/IDCK000072/rnino_3.4.txt"
    csv_output = 'nino34_bom_oni_format.csv'
    excel_output = 'nino34_bom_oni_format.xlsx'
    
    print(f"Mengunduh data dari: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Gagal mendownload data. Status code: {response.status_code}")
    
    print("Berhasil mendownload. Memproses baris teks...")
    
    # Parse baris teks secara manual untuk menghindari masalah format pandas separator
    rows = []
    for line in response.text.splitlines():
        line = line.strip()
        # Lewati baris kosong atau baris komentar '#'
        if not line or line.startswith('#'):
            continue
        
        parts = line.split()
        if len(parts) >= 2:
            rows.append({'Date': parts[0], 'Relative_Nino34': parts[1]})
            
    if not rows:
        raise Exception("Tidak ada data yang berhasil diekstrak dari file teks BOM!")
        
    df = pd.DataFrame(rows)
    
    # Konversi tipe data
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Relative_Nino34'] = pd.to_numeric(df['Relative_Nino34'], errors='coerce')
    
    df = df.dropna(subset=['Date', 'Relative_Nino34'])
    df.set_index('Date', inplace=True)
    
    print(f"Total baris valid ditemukan: {len(df)}")

    # Agregasi dari mingguan ke rata-rata bulanan (Monthly Mean)
    try:
        monthly_df = df.resample('ME')['Relative_Nino34'].mean().reset_index()
    except ValueError:
        monthly_df = df.resample('M')['Relative_Nino34'].mean().reset_index()
        
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
    print(f"[OK] Sukses! File CSV & Excel berhasil diperbarui dengan {len(monthly_df)} baris data.")

if __name__ == '__main__':
    main()
