import os
import requests
import pandas as pd
import numpy as np
from io import StringIO

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
    
    print("Berhasil mendownload. Membaca data dengan Pandas...")
    
    # Membaca file teks, mengabaikan baris yang diawali dengan '#' atau karakter non-data
    df = pd.read_csv(
        StringIO(response.text),
        comment='#',
        sep=r'\s+',
        header=None,
        engine='python'
    )
    
    # Ambil kolom pertama sebagai Tanggal dan kolom kedua sebagai Nilai Anomali
    df = df.iloc[:, [0, 1]]
    df.columns = ['Date', 'Relative_Nino34']
    
    # Bersihkan data: ubah ke datetime dan numerik, buang baris NaN/invalid
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Relative_Nino34'] = pd.to_numeric(df['Relative_Nino34'], errors='coerce')
    
    df = df.dropna(subset=['Date', 'Relative_Nino34'])
    df.set_index('Date', inplace=True)
    
    print(f"Total baris data valid setelah dibersihkan: {len(df)}")
    if len(df) == 0:
        raise Exception("DataFrame kosong setelah pembersihan!")

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
    print(f"[OK] Selesai! File CSV & Excel berhasil diperbarui dengan {len(monthly_df)} baris data.")

if __name__ == '__main__':
    main()
