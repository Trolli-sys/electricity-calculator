# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import io
from datetime import datetime, time, date
import calendar
import traceback
import numpy as np
from datetime import datetime, time, date
import base64

# ==============================================================================
# --- Custom CSS Styling ---
# ==============================================================================
def load_custom_css():
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .main {
        font-family: 'Inter', sans-serif;
    }
    
    /* Header Styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        color: rgba(255,255,255,0.9);
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
        font-weight: 300;
    }
    
    /* Section Cards */
    .section-card {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        border: 1px solid rgba(0,0,0,0.05);
        margin-bottom: 2rem;
    }
    
    .section-header {
        display: flex;
        align-items: center;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #f0f2f6;
    }
    
    .section-header h2 {
        color: #2c3e50;
        font-size: 1.8rem;
        font-weight: 600;
        margin: 0;
        margin-left: 0.5rem;
    }
    
    .section-icon {
        font-size: 2rem;
        color: #667eea;
    }
    
    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
        border-radius: 12px;
        padding: 1.5rem;
        border-left: 4px solid #667eea;
        box-shadow: 0 3px 15px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #2c3e50;
        line-height: 1;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
        font-weight: 500;
        margin-top: 0.5rem;
    }
    
    /* Comparison Cards */
    .comparison-card {
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 3px 15px rgba(0,0,0,0.05);
    }
    
    .comparison-normal {
        background: linear-gradient(135deg, #e3f2fd 0%, #ffffff 100%);
        border-left: 4px solid #2196f3;
    }
    
    .comparison-tou {
        background: linear-gradient(135deg, #f3e5f5 0%, #ffffff 100%);
        border-left: 4px solid #9c27b0;
    }
    
    .comparison-diff {
        background: linear-gradient(135deg, #e8f5e8 0%, #ffffff 100%);
        border-left: 4px solid #4caf50;
    }
    
    .comparison-diff.negative {
        background: linear-gradient(135deg, #ffebee 0%, #ffffff 100%);
        border-left: 4px solid #f44336;
    }
    
    /* File Upload Area */
    .upload-area {
        border: 2px dashed #667eea;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
        margin: 1rem 0;
    }
    
    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.2rem;
    }
    
    .status-success {
        background: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .status-warning {
        background: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }
    
    .status-info {
        background: #d1ecf1;
        color: #0c5460;
        border: 1px solid #bee5eb;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 10px;
        border: none;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(0,0,0,0.15);
    }
    
    /* Charts */
    .chart-container {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 3px 15px rgba(0,0,0,0.05);
        border: 1px solid rgba(0,0,0,0.05);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #5a6fd8;
    }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# --- ค่าคงที่และข้อมูลอัตรา (CONFIGURATIONS) ---
# ==============================================================================

# 1. อัตราค่าไฟฟ้า (Tariffs)
TARIFFS = {
    "residential": {
        "normal": {
            'service_charge_tiers': [
                {'limit': 150, 'rate': 8.19},
                {'limit': float('inf'), 'rate': 24.62}
            ],
            'type': 'tiered', 
            'tiers': [
                {'limit': 150, 'rate': 3.2484}, 
                {'limit': 400, 'rate': 4.2218}, 
                {'limit': float('inf'), 'rate': 4.4217}
            ]
        },
        "tou": {'service_charge': 24.62, 'type': 'tou', 'peak_rate': 5.7982, 'off_peak_rate': 2.6369}
    },
    "smb_lv": { # กิจการขนาดเล็ก, แรงดันต่ำกว่า 22 kV
        "normal": {'service_charge': 46.16, 'type': 'tiered', 'tiers': [{'limit': 150, 'rate': 3.2484}, {'limit': 400, 'rate': 4.2218}, {'limit': float('inf'), 'rate': 4.4217}]},
        "tou": {'service_charge': 46.16, 'type': 'tou', 'peak_rate': 5.7982, 'off_peak_rate': 2.6369}
    },
    "smb_mv": { # กิจการขนาดเล็ก, แรงดัน 22-33 kV
        "normal": {'service_charge': 312.24, 'type': 'flat', 'rate': 4.3168},
        "tou": {'service_charge': 312.24, 'type': 'tou', 'peak_rate': 4.8773, 'off_peak_rate': 2.6549}
    }
}

# 2. อัตราค่า Ft (Fuel Adjustment Charge)
FT_RATES = {
    (2023, 1): 0.9343, (2023, 5): 0.9119, (2023, 9): 0.2048,
    (2024, 1): 0.3972, (2024, 5): 0.3972, (2024, 9): 0.3972,
    (2025, 1): 0.3972, (2025, 5): 0.1972, (2025, 9): 0.1972,
}

# 3. วันหยุดสำหรับอัตรา TOU
def get_all_offpeak_days(year, official_holidays_str):
    offpeak_days = set()
    for d_str in official_holidays_str:
        try: offpeak_days.add(datetime.strptime(d_str, "%Y-%m-%d").date())
        except ValueError: st.warning(f"รูปแบบวันที่ไม่ถูกต้องในรายการวันหยุด: {d_str}")
    for month in range(1, 13):
        cal = calendar.monthcalendar(year, month)
        for week in cal:
            saturday, sunday = week[calendar.SATURDAY], week[calendar.SUNDAY]
            if saturday != 0: offpeak_days.add(date(year, month, saturday))
            if sunday != 0: offpeak_days.add(date(year, month, sunday))
    return offpeak_days

HOLIDAYS_TOU_2024_STR = ["2024-01-01", "2024-02-12", "2024-02-24", "2024-02-26", "2024-04-06", "2024-04-08", "2024-04-13", "2024-04-14", "2024-04-15", "2024-04-16", "2024-05-01", "2024-05-04", "2024-05-06", "2024-05-22", "2024-06-03", "2024-07-20", "2024-07-21", "2024-07-22", "2024-07-28", "2024-07-29", "2024-08-12", "2024-10-13", "2024-10-14", "2024-10-23", "2024-12-05", "2024-12-10", "2024-12-31"]
HOLIDAYS_TOU_2025_STR = ["2025-01-01", "2025-02-12", "2025-02-26", "2025-04-07", "2025-04-14", "2025-04-15", "2025-05-01", "2025-05-05", "2025-06-03", "2025-07-10", "2025-07-11", "2025-07-28", "2025-08-12", "2025-10-13", "2025-10-23", "2025-12-05", "2025-12-08", "2025-12-10", "2025-12-29", "2025-12-31"]
HOLIDAYS_TOU_DATA = {2024: get_all_offpeak_days(2024, HOLIDAYS_TOU_2024_STR), 2025: get_all_offpeak_days(2025, HOLIDAYS_TOU_2025_STR)}

# 4. ค่าคงที่อื่นๆ
VAT_RATE = 0.07; PEAK_START = time(9, 0, 0); PEAK_END = time(21, 59, 59)

# ==============================================================================
# --- ฟังก์ชัน Helper ---
# ==============================================================================
@st.cache_data(show_spinner=False)
def parse_data_file(uploaded_file, file_type):
    if uploaded_file is None: return None
    
    df = None

    try:
        if file_type in ['BLE-iMeter', 'IPG']:
            file_content_string = ""
            encodings_to_try = ['utf-8', 'cp874', 'tis-620']
            for enc in encodings_to_try:
                try:
                    uploaded_file.seek(0)
                    file_content_string = uploaded_file.getvalue().decode(enc)
                    break
                except (UnicodeDecodeError, IndexError): continue
            if not file_content_string: raise ValueError("ไม่สามารถอ่านไฟล์ได้ หรือไฟล์ว่างเปล่า")
            data_io = io.StringIO(file_content_string)

            if file_type == 'BLE-iMeter':
                df_raw = pd.read_csv(data_io, sep=',', header=None, low_memory=False)
                if df_raw.shape[1] < 4: raise ValueError(f"ไฟล์ BLE-iMeter CSV มี {df_raw.shape[1]} คอลัมน์ ไม่เพียงพอ")
                df = pd.DataFrame({
                    'DateTime': pd.to_datetime(df_raw.iloc[:, 1], errors='coerce'),
                    'Total import kW demand': pd.to_numeric(df_raw.iloc[:, 3], errors='coerce') / 1000.0
                })
                st.success("✅ หน่วย Demand ในไฟล์ BLE-iMeter เป็น Watt (W), แปลงเป็น kW โดยการหาร 1000")
            
            elif file_type == 'IPG':
                df_raw = pd.read_csv(data_io, sep='\t', header=0, skipinitialspace=True, low_memory=False)
                df_raw.columns = df_raw.columns.str.strip()
                if not all(col in df_raw.columns for col in ['DateTime', 'Total import kW demand']):
                    raise ValueError("ไฟล์ IPG ต้องมีคอลัมน์: 'DateTime' และ 'Total import kW demand'")
                def correct_buddhist_year(dt_str):
                    try:
                        parts = dt_str.split(' '); date_part = parts[0]; date_components = date_part.split('/')
                        if len(date_components) == 3:
                            day, month, year_be = map(int, date_components)
                            year_ce = datetime.now().year if year_be < 1000 else year_be - 543
                            return datetime(year_ce, month, day).strftime('%Y-%m-%d') + ' ' + parts[1]
                    except Exception: return None
                    return dt_str
                df_raw['DateTime_Corrected'] = df_raw['DateTime'].apply(correct_buddhist_year)
                df = pd.DataFrame({
                    'DateTime': pd.to_datetime(df_raw['DateTime_Corrected'], errors='coerce'),
                    'Total import kW demand': pd.to_numeric(df_raw['Total import kW demand'], errors='coerce')
                })
                st.success("✅ หน่วย Demand ในไฟล์ IPG เป็น Kilowatt (kW)")

        elif file_type == 'มิเตอร์ PEA (CSV)':
            uploaded_file.seek(0)
            df_raw = pd.read_csv(uploaded_file, header=0, low_memory=False)
            required_cols = ['DateTime', 'Total import kW demand']
            if not all(col in df_raw.columns for col in required_cols):
                raise ValueError(f"ไฟล์ CSV ต้องมีคอลัมน์ชื่อ '{required_cols[0]}' และ '{required_cols[1]}'")
            df = pd.DataFrame({
                'DateTime': pd.to_datetime(df_raw['DateTime'], dayfirst=True, errors='coerce'),
                'Total import kW demand': pd.to_numeric(df_raw['Total import kW demand'], errors='coerce')
            })
            st.success("✅ สันนิษฐานว่าหน่วย Demand ในไฟล์ CSV เป็น Kilowatt (kW)")

        if df is None:
            raise ValueError(f"ประเภทไฟล์ '{file_type}' ไม่รองรับหรือไม่สามารถประมวลผลได้")

        df_final = df.dropna(subset=['DateTime', 'Total import kW demand']).copy()
        if df_final.empty: raise ValueError("ไม่พบข้อมูลที่ถูกต้องในไฟล์หลังการประมวลผล")
        return df_final.sort_values(by='DateTime').reset_index(drop=True)

    except Exception as e:
        raise ValueError(f"เกิดข้อผิดพลาดขณะประมวลผลข้อมูล: {e}")

def calculate_service_charge(total_kwh, rate_structure):
    """คำนวณค่าบริการรายเดือนตาม tier ของหน่วยไฟที่ใช้"""
    if 'service_charge_tiers' in rate_structure:
        for tier in rate_structure['service_charge_tiers']:
            if total_kwh <= tier['limit']:
                return tier['rate']
        return rate_structure['service_charge_tiers'][-1]['rate']
    else:
        return rate_structure['service_charge']

def calculate_bill(df_processed, customer_type_key, tariff_type_key):
    if df_processed is None or df_processed.empty: return {"error": "ไม่มีข้อมูลสำหรับคำนวณ"}
    total_kwh = df_processed['kWh'].sum(); data_period_end_dt = df_processed['DateTime'].iloc[-1]; kwh_peak, kwh_off_peak = 0.0, 0.0
    if tariff_type_key == 'tou':
        df_processed['TOU_Period'] = df_processed['DateTime'].apply(classify_tou_period); kwh_summary = df_processed.groupby('TOU_Period')['kWh'].sum()
        kwh_peak = kwh_summary.get('Peak', 0.0); kwh_off_peak = kwh_summary.get('Off-Peak', 0.0) + kwh_summary.get('Unknown', 0.0)
    try:
        rate_structure = TARIFFS[customer_type_key][tariff_type_key]
    except KeyError as e: return {"error": f"ไม่พบโครงสร้างอัตราค่าไฟฟ้าสำหรับ '{customer_type_key}'/'{tariff_type_key}': {e}"}
    
    base_energy_cost = 0.0
    if rate_structure['type'] == 'flat': base_energy_cost = total_kwh * rate_structure['rate']
    elif rate_structure['type'] == 'tiered':
        last_limit = 0
        for tier in rate_structure['tiers']:
            units_in_tier = max(0, min(total_kwh, tier['limit']) - last_limit); base_energy_cost += units_in_tier * tier['rate']; last_limit = tier['limit'];
            if total_kwh <= tier['limit']: break
    elif rate_structure['type'] == 'tou': base_energy_cost = (kwh_peak * rate_structure['peak_rate']) + (kwh_off_peak * rate_structure['off_peak_rate'])
    
    service_charge = calculate_service_charge(total_kwh, rate_structure)
    applicable_ft_rate = get_ft_rate(data_period_end_dt); ft_cost = total_kwh * applicable_ft_rate
    total_before_vat = base_energy_cost + service_charge + ft_cost; vat_amount = total_before_vat * VAT_RATE; final_bill = total_before_vat + vat_amount
    
    return {
        "total_kwh": total_kwh, "final_bill": final_bill, "base_energy_cost": base_energy_cost,
        "service_charge": service_charge, "ft_cost": ft_cost, "total_before_vat": total_before_vat,
        "vat_amount": vat_amount, "applicable_ft_rate": applicable_ft_rate,
        "kwh_peak": kwh_peak if tariff_type_key == 'tou' else None,
        "kwh_off_peak": kwh_off_peak if tariff_type_key == 'tou' else None,
        "data_period_start": df_processed['DateTime'].iloc[0].strftime('%Y-%m-%d %H:%M'),
        "data_period_end": data_period_end_dt.strftime('%Y-%m-%d %H:%M'), "error": None
    }

def get_ft_rate(date_in_period):
    d = date_in_period.date() if isinstance(date_in_period, datetime) else date_in_period
    sorted_ft_periods = sorted(FT_RATES.keys(), reverse=True)
    for start_year, start_month in sorted_ft_periods:
        if d >= date(start_year, start_month, 1): return FT_RATES[(start_year, start_month)]
    st.warning(f"ไม่พบอัตรา Ft สำหรับ {d}, ใช้ค่า Ft=0.0"); return 0.0

def classify_tou_period(dt_obj):
    if not isinstance(dt_obj, datetime): return 'Unknown'
    current_date = dt_obj.date(); current_time = dt_obj.time()
    year_holidays = HOLIDAYS_TOU_DATA.get(current_date.year)
    if year_holidays is None:
        if current_date.year not in st.session_state.get('missing_holiday_years', set()):
            st.warning(f"ไม่พบข้อมูลวันหยุด TOU ปี {current_date.year}"); st.session_state.setdefault('missing_holiday_years', set()).add(current_date.year)
        return 'Peak' if PEAK_START <= current_time <= PEAK_END else 'Off-Peak'
    if current_date in year_holidays: return 'Off-Peak'
    return 'Peak' if PEAK_START <= current_time <= PEAK_END else 'Off-Peak'

def create_enhanced_chart_data(df_plot):
    """เตรียมข้อมูลสำหรับกราฟ Streamlit"""
    if df_plot is None or df_plot.empty:
        return None
    
    # เตรียมข้อมูลสำหรับ line chart
    chart_data = df_plot.set_index('DateTime')['Total import kW demand']
    return chart_data

def create_daily_consumption_data(df_plot):
    """สร้างข้อมูลการใช้ไฟรายวัน"""
    if df_plot is None or df_plot.empty:
        return None
    
    daily_data = df_plot.groupby(df_plot['DateTime'].dt.date)['Total import kW demand'].mean()
    return daily_data

def create_hourly_pattern_data(df_plot):
    """สร้างข้อมูลรูปแบบการใช้ไฟตามชั่วโมง"""
    if df_plot is None or df_plot.empty:
        return None
    
    df_plot['Hour'] = df_plot['DateTime'].dt.hour
    hourly_data = df_plot.groupby('Hour')['Total import kW demand'].mean()
    return hourly_data

def generate_print_report(bill_data, ev_data, df_plot, settings):
    """สร้างรายงานสำหรับพิมพ์ในรูปแบบ HTML"""
    
    # คำนวณสถิติเพิ่มเติม
    if df_plot is not None and not df_plot.empty:
        stats = {
            'max_demand': df_plot['Total import kW demand'].max(),
            'min_demand': df_plot['Total import kW demand'].min(),
            'avg_demand': df_plot['Total import kW demand'].mean(),
            'median_demand': df_plot['Total import kW demand'].median(),
            'std_demand': df_plot['Total import kW demand'].std(),
            'load_factor': (df_plot['Total import kW demand'].mean() / df_plot['Total import kW demand'].max()) * 100,
            'total_records': len(df_plot)
        }
    else:
        stats = {}
    
    # สร้าง HTML รายงาน
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>รายงานการคำนวณค่าไฟฟ้า</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700&display=swap');
            
            body {{
                font-family: 'Sarabun', sans-serif;
                margin: 0;
                padding: 20px;
                background: white;
                color: #2c3e50;
                line-height: 1.6;
            }}
            
            .report-header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 15px;
                text-align: center;
                margin-bottom: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }}
            
            .report-header h1 {{
                margin: 0;
                font-size: 2.5rem;
                font-weight: 700;
            }}
            
            .report-header p {{
                margin: 10px 0 0 0;
                font-size: 1.2rem;
                opacity: 0.9;
            }}
            
            .section {{
                background: white;
                border-radius: 12px;
                padding: 25px;
                margin-bottom: 25px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.08);
                border: 1px solid rgba(0,0,0,0.05);
                page-break-inside: avoid;
            }}
            
            .section-title {{
                color: #667eea;
                font-size: 1.5rem;
                font-weight: 600;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid #f0f2f6;
            }}
            
            .info-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }}
            
            .info-item {{
                background: #f8f9ff;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }}
            
            .info-label {{
                font-weight: 600;
                color: #2c3e50;
                margin-bottom: 5px;
            }}
            
            .info-value {{
                font-size: 1.1rem;
                color: #667eea;
                font-weight: 500;
            }}
            
            .metric-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }}
            
            .metric-card {{
                background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                border-left: 4px solid #667eea;
                box-shadow: 0 3px 15px rgba(0,0,0,0.05);
            }}
            
            .metric-value {{
                font-size: 2rem;
                font-weight: 700;
                color: #2c3e50;
                margin-bottom: 5px;
            }}
            
            .metric-label {{
                color: #6c757d;
                font-weight: 500;
            }}
            
            .calculation-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 3px 15px rgba(0,0,0,0.05);
            }}
            
            .calculation-table th {{
                background: #667eea;
                color: white;
                padding: 15px;
                text-align: left;
                font-weight: 600;
            }}
            
            .calculation-table td {{
                padding: 12px 15px;
                border-bottom: 1px solid #f0f2f6;
            }}
            
            .calculation-table tr:nth-child(even) {{
                background: #f8f9ff;
            }}
            
            .total-row {{
                background: #667eea !important;
                color: white !important;
                font-weight: 700;
            }}
            
            .total-row td {{
                border-bottom: none !important;
            }}
            
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }}
            
            .stat-item {{
                background: #f8f9ff;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                border: 1px solid #e3f2fd;
            }}
            
            .stat-value {{
                font-size: 1.3rem;
                font-weight: 600;
                color: #667eea;
                margin-bottom: 5px;
            }}
            
            .stat-label {{
                font-size: 0.9rem;
                color: #6c757d;
            }}
            
            .recommendations {{
                background: linear-gradient(135deg, #e8f5e8 0%, #ffffff 100%);
                border-left: 4px solid #4caf50;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            
            .recommendations h4 {{
                color: #2e7d32;
                margin-top: 0;
            }}
            
            .recommendations ul {{
                margin: 0;
                padding-left: 20px;
            }}
            
            .recommendations li {{
                margin-bottom: 8px;
                color: #2c3e50;
            }}
            
            .footer {{
                text-align: center;
                margin-top: 40px;
                padding: 20px;
                background: #f8f9ff;
                border-radius: 12px;
                color: #6c757d;
            }}
            
            @media print {{
                body {{ margin: 0; padding: 15px; font-size: 12pt; }}
                .report-header {{ margin-bottom: 20px; }}
                .section {{ margin-bottom: 15px; page-break-inside: avoid; }}
                .metric-grid {{ grid-template-columns: repeat(2, 1fr); }}
                .info-grid {{ grid-template-columns: 1fr; }}
            }}
        </style>
    </head>
    <body>
        <div class="report-header">
            <h1>⚡ รายงานการคำนวณค่าไฟฟ้า</h1>
            <p>Electric Bill Calculation Report</p>
            <p>สร้างเมื่อ: {datetime.now().strftime('%d/%m/%Y %H:%M น.')}</p>
        </div>
        
        <div class="section">
            <h2 class="section-title">📋 ข้อมูลทั่วไป</h2>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">ช่วงข้อมูล</div>
                    <div class="info-value">{bill_data['data_period_start']} ถึง {bill_data['data_period_end']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">ประเภทผู้ใช้</div>
                    <div class="info-value">{settings['customer_type']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">ประเภทอัตรา</div>
                    <div class="info-value">{settings['tariff_type']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">อัตรา Ft</div>
                    <div class="info-value">{bill_data['applicable_ft_rate']:.4f} บาท/kWh</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">💰 สรุปค่าไฟฟ้า</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{bill_data['final_bill']:,.2f}</div>
                    <div class="metric-label">ยอดค่าไฟสุทธิ (บาท)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{bill_data['total_kwh']:,.2f}</div>
                    <div class="metric-label">ยอดใช้ไฟรวม (kWh)</div>
                </div>"""
    
    # เพิ่มข้อมูล EV หากมี
    if ev_data['is_enabled']:
        html_content += f"""
                <div class="metric-card">
                    <div class="metric-value">{ev_data['cost']:,.2f}</div>
                    <div class="metric-label">ค่าไฟส่วน EV (บาท)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{ev_data['kwh']:,.2f}</div>
                    <div class="metric-label">หน่วยไฟ EV (kWh)</div>
                </div>"""
    
    html_content += """
            </div>
            
            <table class="calculation-table">
                <thead>
                    <tr>
                        <th>รายการ</th>
                        <th style="text-align: right;">จำนวน (บาท)</th>
                    </tr>
                </thead>
                <tbody>"""
    
    # เพิ่มรายการคำนวณ
    calculation_items = [
        ("ค่าพลังงานไฟฟ้า", bill_data['base_energy_cost']),
        ("ค่าบริการรายเดือน", bill_data['service_charge']),
        (f"ค่า Ft (@{bill_data['applicable_ft_rate']:.4f})", bill_data['ft_cost']),
        ("รวมก่อน VAT", bill_data['total_before_vat']),
        ("ภาษีมูลค่าเพิ่ม (7%)", bill_data['vat_amount'])
    ]
    
    for item, value in calculation_items:
        html_content += f"""
                    <tr>
                        <td>{item}</td>
                        <td style="text-align: right;">{value:,.2f}</td>
                    </tr>"""
    
    html_content += f"""
                    <tr class="total-row">
                        <td><strong>ยอดค่าไฟฟ้าสุทธิ</strong></td>
                        <td style="text-align: right;"><strong>{bill_data['final_bill']:,.2f}</strong></td>
                    </tr>
                </tbody>
            </table>
        </div>"""
    
    # เพิ่มข้อมูล TOU หากใช้
    if bill_data.get('kwh_peak') is not None:
        html_content += f"""
        <div class="section">
            <h2 class="section-title">⏰ วิเคราะห์ Peak/Off-Peak</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{bill_data['kwh_peak']:,.2f}</div>
                    <div class="metric-label">Peak Period (kWh)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{bill_data['kwh_off_peak']:,.2f}</div>
                    <div class="metric-label">Off-Peak Period (kWh)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{(bill_data['kwh_peak']/(bill_data['kwh_peak']+bill_data['kwh_off_peak'])*100):,.1f}%</div>
                    <div class="metric-label">สัดส่วน Peak</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{(bill_data['kwh_off_peak']/(bill_data['kwh_peak']+bill_data['kwh_off_peak'])*100):,.1f}%</div>
                    <div class="metric-label">สัดส่วน Off-Peak</div>
                </div>
            </div>
        </div>"""
    
    # เพิ่มสถิติการใช้ไฟ
    if stats:
        html_content += f"""
        <div class="section">
            <h2 class="section-title">📊 สถิติการใช้ไฟ</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">{stats['max_demand']:,.2f}</div>
                    <div class="stat-label">ค่าสูงสุด (kW)</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{stats['min_demand']:,.2f}</div>
                    <div class="stat-label">ค่าต่ำสุด (kW)</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{stats['avg_demand']:,.2f}</div>
                    <div class="stat-label">ค่าเฉลี่ย (kW)</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{stats['median_demand']:,.2f}</div>
                    <div class="stat-label">ค่ามัธยฐาน (kW)</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{stats['std_demand']:,.2f}</div>
                    <div class="stat-label">ส่วนเบียงเบนมาตรฐาน</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{stats['load_factor']:,.1f}%</div>
                    <div class="stat-label">Load Factor</div>
                </div>
            </div>
        </div>"""
    
    # เพิ่มคำแนะนำ
    html_content += """
        <div class="section">
            <h2 class="section-title">💡 คำแนะนำประหยัดพลังงาน</h2>
            
            <div class="recommendations">
                <h4>🏠 สำหรับบ้านอยู่อาศัย</h4>
                <ul>
                    <li>🌡️ ตั้งเครื่องปรับอากาศที่ 25-26°C เพื่อประหยัดได้ 6-8%</li>
                    <li>💡 เปลี่ยนเป็นหลอด LED ประหยัดได้ถึง 80%</li>
                    <li>🔌 ถอดปลั๊กเครื่องใช้ไฟฟ้าที่ไม่ได้ใช้งาน</li>
                    <li>⏰ ใช้ไฟในช่วง Off-Peak (22:00-09:00 น.)</li>
                </ul>
            </div>
            
            <div class="recommendations">
                <h4>🚗 สำหรับ EV Charging</h4>
                <ul>
                    <li>🌙 ชาร์จในช่วงกลางคืน (22:00-05:00) เพื่อประหยัดสุด</li>
                    <li>📱 ใช้ระบบ Smart Charging เพื่อจัดการการชาร์จอัตโนมัติ</li>
                    <li>🔋 ชาร์จแบตเตอรี่ในช่วง 20-80% เพื่อยืดอายุการใช้งาน</li>
                    <li>☀️ พิจารณาติดตั้งโซลาร์เซลล์ร่วมกับ EV</li>
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>⚡ Electric Bill Calculator Pro</strong></p>
            <p>เครื่องมือคำนวณค่าไฟฟ้าระดับมืออาชีพ | สร้างด้วย ❤️</p>
            <p>รายงานนี้สร้างขึ้นเพื่อการวิเคราะห์และวางแผนการใช้พลังงานเท่านั้น</p>
        </div>
    </body>
    </html>
    """
    
    return html_content

# ==============================================================================
# --- Streamlit App ---
# ==============================================================================
st.set_page_config(
    page_title="Electric Bill Calculator Pro", 
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="⚡"
)

# Load custom CSS
load_custom_css()

# Initialize session state
for key in ['full_dataframe', 'last_uploaded_filename', 'calculation_result', 'ev_cost', 'base_kwh', 'ev_kwh']:
    if key not in st.session_state: st.session_state[key] = None

# Header
st.markdown("""
<div class="main-header">
    <h1>⚡ Electric Bill Calculator Pro</h1>
    <p>โปรแกรมคำนวณและจำลองค่าไฟฟ้าระดับมืออาชีพ</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🔧 เครื่องมือและข้อมูล")
    
    # Quick Stats
    if st.session_state.get('full_dataframe') is not None:
        df_info = st.session_state.full_dataframe
        st.markdown("### 📈 ข้อมูลไฟล์")
        st.metric("จำนวนข้อมูล", f"{len(df_info):,} รายการ")
        st.metric("ช่วงเวลา", f"{(df_info['DateTime'].max() - df_info['DateTime'].min()).days} วัน")
        st.metric("Demand เฉลี่ย", f"{df_info['Total import kW demand'].mean():.2f} kW")
        st.metric("Demand สูงสุด", f"{df_info['Total import kW demand'].max():.2f} kW")
    
    st.markdown("---")
    st.markdown("### 💡 คำแนะนำ")
    st.info("💡 **เคล็ดลับ**: ใช้อัตรา TOU หากใช้ไฟใน Off-Peak มาก")
    st.info("🔋 **EV Charging**: ควรชาร์จในช่วง 22:00-05:00 เพื่อประหยัด")

# Section 1: File Upload
st.markdown("""
<div class="section-card">
    <div class="section-header">
        <span class="section-icon">📁</span>
        <h2>อัปโหลดข้อมูลมิเตอร์</h2>
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 3])
with col1:
    selected_file_type_label = st.radio(
        "เลือกประเภทไฟล์ข้อมูล:",
        ("📱 BLE-iMeter (.txt)", "🖥️ IPG (.txt)", "📊 มิเตอร์ PEA (CSV)"),
        key="data_file_type_label"
    )

file_type_mapping = {
    "📱 BLE-iMeter (.txt)": "BLE-iMeter",
    "🖥️ IPG (.txt)": "IPG", 
    "📊 มิเตอร์ PEA (CSV)": "มิเตอร์ PEA (CSV)"
}
internal_file_type = file_type_mapping[selected_file_type_label]

with col2:
    file_extension = 'csv' if internal_file_type == 'มิเตอร์ PEA (CSV)' else 'txt'
    if internal_file_type == 'มิเตอร์ PEA (CSV)':
        st.markdown('<div class="status-badge status-info">💡 สำหรับไฟล์ Excel (.xlsx) กรุณาบันทึกเป็น CSV ก่อน</div>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        f"เลือกไฟล์ (.{file_extension})",
        type=[file_extension],
        key="file_uploader",
        help=f"อัปโหลดไฟล์ {internal_file_type} ของคุณ"
    )

if uploaded_file and (uploaded_file.name != st.session_state.get('last_uploaded_filename') or internal_file_type != st.session_state.get('last_file_type')):
    with st.spinner('🔄 กำลังประมวลผลไฟล์...'):
        try:
            st.session_state.full_dataframe = parse_data_file(uploaded_file, internal_file_type)
            st.session_state.last_uploaded_filename = uploaded_file.name
            st.session_state.last_file_type = internal_file_type
            st.balloons()
            st.success(f"✅ ประมวลผลไฟล์ '{uploaded_file.name}' สำเร็จ!")
        except ValueError as ve:
            st.error(f"❌ ข้อผิดพลาด: {ve}")
            st.session_state.full_dataframe = None

if st.session_state.get('full_dataframe') is not None:
    # Section 2: Configuration
    st.markdown("""
    <div class="section-card">
        <div class="section-header">
            <span class="section-icon">⚙️</span>
            <h2>ตั้งค่าการคำนวณ</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    df_full = st.session_state.full_dataframe
    min_date = df_full['DateTime'].min().date()
    max_date = df_full['DateTime'].max().date()
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("#### 👤 ประเภทผู้ใช้")
        customer_label = st.selectbox(
            "เลือกประเภท:",
            ["🏠 บ้านอยู่อาศัย", "🏢 กิจการขนาดเล็ก"],
            key="customer_type_label"
        )
        
        customer_key = "residential"
        if customer_label == "🏢 กิจการขนาดเล็ก":
            voltage_label = st.radio(
                "ระดับแรงดันไฟฟ้า:",
                ("⚡ แรงดันต่ำกว่า 22 kV", "⚡⚡ แรงดัน 22-33 kV"),
                key="voltage_level"
            )
            customer_key = "smb_lv" if voltage_label == "⚡ แรงดันต่ำกว่า 22 kV" else "smb_mv"
        
        st.markdown("#### 💰 ประเภทอัตรา")
        tariff_type = st.selectbox(
            "เลือกอัตรา:",
            ["📊 อัตราปกติ", "⏰ อัตรา TOU"],
            key="tariff_type"
        )
        
    with col2:
        st.markdown("#### 📅 ช่วงวันที่คำนวณ")
        main_date_range = st.date_input(
            "เลือกช่วงเวลา:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="main_date_range",
            help="เลือกช่วงวันที่ที่ต้องการคำนวณค่าไฟ"
        )

    # EV Simulation Section
    with st.expander("🚗 จำลอง EV Charger (Advanced)", expanded=False):
        st.markdown("### ⚡ การตั้งค่า Electric Vehicle Charging")
        
        ev_enabled = st.checkbox("🔌 เปิดใช้งานการจำลอง EV Charger", key="ev_enabled")
        
        col_ev1, col_ev2 = st.columns(2)
        with col_ev1:
            if len(main_date_range) == 2:
                ev_start_range, ev_end_range = main_date_range
                ev_date_range = st.date_input(
                    "📅 ช่วงวันที่ชาร์จ EV:",
                    value=(ev_start_range, ev_end_range),
                    min_value=ev_start_range,
                    max_value=ev_end_range,
                    key="ev_date_range",
                    disabled=not ev_enabled
                )
            
            ev_power_kw = st.number_input(
                "⚡ กำลังไฟ Charger (kW):",
                min_value=0.1,
                value=7.0,
                step=0.1,
                key="ev_power",
                disabled=not ev_enabled,
                help="กำลังไฟของเครื่องชาร์จ EV"
            )
        
        with col_ev2:
            ev_start_time = st.time_input(
                "🌙 เวลาเริ่มชาร์จ:",
                time(22, 0),
                key="ev_start_time",
                disabled=not ev_enabled,
                help="เวลาที่เริ่มชาร์จ EV"
            )
            
            ev_end_time = st.time_input(
                "🌅 เวลาสิ้นสุดชาร์จ:",
                time(5, 0),
                key="ev_end_time",
                disabled=not ev_enabled,
                help="เวลาที่สิ้นสุดการชาร์จ EV"
            )
        
        if ev_enabled:
            # Show EV preview
            st.markdown("### 📋 สรุปการตั้งค่า EV")
            ev_hours = (datetime.combine(date.today(), ev_end_time) - datetime.combine(date.today(), ev_start_time)).total_seconds() / 3600
            if ev_hours < 0:
                ev_hours += 24  # Handle overnight charging
            
            col_preview1, col_preview2, col_preview3 = st.columns(3)
            col_preview1.metric("🔋 กำลังชาร์จ", f"{ev_power_kw} kW")
            col_preview2.metric("⏱️ ชั่วโมงต่อวัน", f"{ev_hours:.1f} ชม.")
            col_preview3.metric("📊 พลังงานต่อวัน", f"{ev_power_kw * ev_hours:.1f} kWh")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Calculation Buttons
    col_calc1, col_calc2 = st.columns(2)
    with col_calc1:
        calc_button = st.button("🧮 คำนวณค่าไฟ", type="primary", use_container_width=True)
        if calc_button:
            st.session_state.do_calculation = True
    
    with col_calc2:
        compare_button = st.button("🔄 เปรียบเทียบอัตราปกติ vs TOU", type="secondary", use_container_width=True)
        if compare_button:
            st.session_state.do_comparison = True

    # Calculation Logic
    if st.session_state.get('do_calculation', False):
        st.session_state.calculation_result = None
        st.session_state.ev_cost = None
        st.session_state.base_kwh = None
        st.session_state.ev_kwh = None
        
        if len(main_date_range) != 2:
            st.error("❌ กรุณาเลือกวันเริ่มต้นและวันสิ้นสุด")
        else:
            main_start_date, main_end_date = main_date_range
            with st.spinner("🔄 กำลังคำนวณ..."):
                try:
                    mask = (df_full['DateTime'].dt.date >= main_start_date) & (df_full['DateTime'].dt.date <= main_end_date)
                    df_filtered = df_full[mask].copy()
                    if df_filtered.empty:
                        st.warning("⚠️ ไม่พบข้อมูลในช่วงวันที่ที่เลือก")
                    else:
                        tariff_key_str = "tou" if tariff_type == "⏰ อัตรา TOU" else "normal"
                        interval_hours = (df_filtered['DateTime'].iloc[1] - df_filtered['DateTime'].iloc[0]).total_seconds() / 3600.0 if len(df_filtered) > 1 else 0.25
                        if not (0 < interval_hours <= 24): interval_hours = 0.25
                        
                        df_base = df_filtered.copy()
                        df_base['kWh'] = df_base['Total import kW demand'] * interval_hours
                        base_bill_details = calculate_bill(df_base, customer_key, tariff_key_str)
                        st.session_state.base_kwh = base_bill_details['total_kwh']
                        
                        total_bill_details = base_bill_details
                        
                        if ev_enabled:
                            df_with_ev = df_filtered.copy()
                            time_series = df_with_ev['DateTime'].dt.time
                            date_series = df_with_ev['DateTime'].dt.date
                            ev_start_date_select, ev_end_date_select = st.session_state.ev_date_range
                            time_mask = (time_series >= ev_start_time) | (time_series < ev_end_time) if ev_start_time > ev_end_time else (time_series >= ev_start_time) & (time_series < ev_end_time)
                            date_mask = (date_series >= ev_start_date_select) & (date_series <= ev_end_date_select)
                            df_with_ev.loc[time_mask & date_mask, 'Total import kW demand'] += ev_power_kw
                            
                            df_with_ev['kWh'] = df_with_ev['Total import kW demand'] * interval_hours
                            total_bill_details = calculate_bill(df_with_ev, customer_key, tariff_key_str)
                            
                            st.session_state.ev_cost = total_bill_details['final_bill'] - base_bill_details['final_bill']
                            st.session_state.ev_kwh = total_bill_details['total_kwh'] - base_bill_details['total_kwh']
                            st.session_state.df_for_plotting = df_with_ev
                        else:
                            st.session_state.df_for_plotting = df_base
                        
                        st.session_state.calculation_result = total_bill_details
                        st.session_state.do_calculation = False
                        st.success("✅ คำนวณเสร็จสิ้น!")
                        
                except Exception as e:
                    st.error(f"❌ เกิดข้อผิดพลาด: {e}")
                    st.error(traceback.format_exc())

    # Comparison Logic
    if st.session_state.get('do_comparison', False):
        st.session_state.calculation_result = None
        st.session_state.ev_cost = None
        st.session_state.base_kwh = None
        st.session_state.ev_kwh = None
        
        if len(main_date_range) != 2:
            st.error("❌ กรุณาเลือกวันเริ่มต้นและวันสิ้นสุด")
        else:
            main_start_date, main_end_date = main_date_range
            with st.spinner("🔄 กำลังเปรียบเทียบอัตราค่าไฟ..."):
                try:
                    mask = (df_full['DateTime'].dt.date >= main_start_date) & (df_full['DateTime'].dt.date <= main_end_date)
                    df_filtered = df_full[mask].copy()
                    if df_filtered.empty:
                        st.warning("⚠️ ไม่พบข้อมูลในช่วงวันที่ที่เลือก")
                    else:
                        interval_hours = (df_filtered['DateTime'].iloc[1] - df_filtered['DateTime'].iloc[0]).total_seconds() / 3600.0 if len(df_filtered) > 1 else 0.25
                        if not (0 < interval_hours <= 24): interval_hours = 0.25
                        
                        df_base = df_filtered.copy()
                        df_base['kWh'] = df_base['Total import kW demand'] * interval_hours
                        
                        if ev_enabled:
                            time_series = df_base['DateTime'].dt.time
                            date_series = df_base['DateTime'].dt.date
                            ev_start_date_select, ev_end_date_select = st.session_state.ev_date_range
                            time_mask = (time_series >= ev_start_time) | (time_series < ev_end_time) if ev_start_time > ev_end_time else (time_series >= ev_start_time) & (time_series < ev_end_time)
                            date_mask = (date_series >= ev_start_date_select) & (date_series <= ev_end_date_select)
                            df_base.loc[time_mask & date_mask, 'Total import kW demand'] += ev_power_kw
                            df_base['kWh'] = df_base['Total import kW demand'] * interval_hours
                        
                        normal_bill = calculate_bill(df_base, customer_key, "normal")
                        tou_bill = calculate_bill(df_base, customer_key, "tou")
                        
                        # Display Comparison Results
                        st.markdown("""
                        <div class="section-card">
                            <div class="section-header">
                                <span class="section-icon">🔄</span>
                                <h2>เปรียบเทียบอัตราค่าไฟ</h2>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        comp_col1, comp_col2, comp_col3 = st.columns(3)
                        
                        with comp_col1:
                            st.markdown("""
                            <div class="comparison-card comparison-normal">
                                <h3>📊 อัตราปกติ</h3>
                            </div>
                            """, unsafe_allow_html=True)
                            st.metric("💰 ยอดค่าไฟสุทธิ", f"{normal_bill['final_bill']:,.2f} บาท")
                            st.metric("⚡ หน่วยไฟรวม", f"{normal_bill['total_kwh']:,.2f} kWh")
                        
                        with comp_col2:
                            st.markdown("""
                            <div class="comparison-card comparison-tou">
                                <h3>⏰ อัตรา TOU</h3>
                            </div>
                            """, unsafe_allow_html=True)
                            st.metric("💰 ยอดค่าไฟสุทธิ", f"{tou_bill['final_bill']:,.2f} บาท")
                            st.metric("⚡ หน่วยไฟรวม", f"{tou_bill['total_kwh']:,.2f} kWh")
                            st.metric("🌅 Peak", f"{tou_bill['kwh_peak']:,.2f} kWh")
                            st.metric("🌙 Off-Peak", f"{tou_bill['kwh_off_peak']:,.2f} kWh")
                        
                        with comp_col3:
                            difference = tou_bill['final_bill'] - normal_bill['final_bill']
                            percentage = (difference / normal_bill['final_bill']) * 100 if normal_bill['final_bill'] > 0 else 0
                            
                            card_class = "comparison-diff" if difference <= 0 else "comparison-diff negative"
                            st.markdown(f"""
                            <div class="comparison-card {card_class}">
                                <h3>💡 ผลต่าง</h3>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if difference < 0:
                                st.success(f"✅ TOU ประหยัดกว่า\n{abs(difference):,.2f} บาท")
                                st.success(f"📉 ประหยัด {abs(percentage):.1f}%")
                            elif difference > 0:
                                st.error(f"❌ TOU แพงกว่า\n{difference:,.2f} บาท")
                                st.error(f"📈 แพงขึ้น {percentage:.1f}%")
                            else:
                                st.info("⚖️ ค่าไฟเท่ากัน")
                        
                        # Detailed Comparison Table
                        with st.expander("📋 รายละเอียดการเปรียบเทียบ", expanded=True):
                            comparison_data = {
                                "รายการ": [
                                    "ค่าพลังงานไฟฟ้า (บาท)",
                                    "ค่าบริการรายเดือน (บาท)", 
                                    "ค่า Ft (บาท)",
                                    "รวมก่อน VAT (บาท)",
                                    "VAT 7% (บาท)",
                                    "ยอดสุทธิ (บาท)"
                                ],
                                "📊 อัตราปกติ": [
                                    f"{normal_bill['base_energy_cost']:,.2f}",
                                    f"{normal_bill['service_charge']:,.2f}",
                                    f"{normal_bill['ft_cost']:,.2f}",
                                    f"{normal_bill['total_before_vat']:,.2f}",
                                    f"{normal_bill['vat_amount']:,.2f}",
                                    f"{normal_bill['final_bill']:,.2f}"
                                ],
                                "⏰ อัตรา TOU": [
                                    f"{tou_bill['base_energy_cost']:,.2f}",
                                    f"{tou_bill['service_charge']:,.2f}",
                                    f"{tou_bill['ft_cost']:,.2f}",
                                    f"{tou_bill['total_before_vat']:,.2f}",
                                    f"{tou_bill['vat_amount']:,.2f}",
                                    f"{tou_bill['final_bill']:,.2f}"
                                ],
                                "💡 ผลต่าง": [
                                    f"{tou_bill['base_energy_cost'] - normal_bill['base_energy_cost']:+,.2f}",
                                    f"{tou_bill['service_charge'] - normal_bill['service_charge']:+,.2f}",
                                    f"{tou_bill['ft_cost'] - normal_bill['ft_cost']:+,.2f}",
                                    f"{tou_bill['total_before_vat'] - normal_bill['total_before_vat']:+,.2f}",
                                    f"{tou_bill['vat_amount'] - normal_bill['vat_amount']:+,.2f}",
                                    f"{tou_bill['final_bill'] - normal_bill['final_bill']:+,.2f}"
                                ]
                            }
                            comparison_df = pd.DataFrame(comparison_data)
                            st.dataframe(comparison_df, use_container_width=True, hide_index=True)
                            
                            # Recommendations
                            st.markdown("### 💡 คำแนะนำ")
                            if difference < -50:
                                st.success("🎯 **แนะนำให้เปลี่ยนเป็นอัตรา TOU** - ประหยัดค่าไฟได้มาก เนื่องจากใช้ไฟใน Off-Peak มากกว่า Peak")
                            elif difference < 0:
                                st.info("✅ **อัตรา TOU ประหยัดกว่าเล็กน้อย** - ควรพิจารณาเปลี่ยนหากต้องการประหยัด")
                            elif difference <= 50:
                                st.warning("⚖️ **ค่าไฟใกล้เคียงกัน** - เลือกอัตราที่สะดวกต่อการใช้งาน")
                            else:
                                st.error("❌ **อัตราปกติประหยัดกว่า** - ไม่แนะนำให้เปลี่ยนเป็น TOU เนื่องจากใช้ไฟใน Peak มาก")
                        
                        st.session_state.do_comparison = False
                        
                except Exception as e:
                    st.error(f"❌ เกิดข้อผิดพลาด: {e}")
                    st.error(traceback.format_exc())

# Results Display
if st.session_state.calculation_result:
    st.markdown("""
    <div class="section-card">
        <div class="section-header">
            <span class="section-icon">📊</span>
            <h2>ผลการคำนวณ</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    bill = st.session_state.calculation_result
    ev_cost = st.session_state.ev_cost
    base_kwh = st.session_state.base_kwh
    ev_kwh = st.session_state.ev_kwh
    
    if bill.get("error"):
        st.error(f"❌ เกิดข้อผิดพลาด: {bill['error']}")
    else:
        is_ev_calculated = st.session_state.get('ev_enabled') and ev_cost is not None
        
        # Main Metrics
        if is_ev_calculated:
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            with m_col1:
                st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">💰 {:.2f}</div>
                    <div class="metric-label">ยอดค่าไฟรวม (บาท)</div>
                </div>
                """.format(bill['final_bill']), unsafe_allow_html=True)
            
            with m_col2:
                st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">🚗 {:.2f}</div>
                    <div class="metric-label">ค่าไฟส่วน EV (บาท)</div>
                </div>
                """.format(ev_cost), unsafe_allow_html=True)
            
            with m_col3:
                st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">🏠 {:.2f}</div>
                    <div class="metric-label">หน่วยไฟบ้าน (kWh)</div>
                </div>
                """.format(base_kwh), unsafe_allow_html=True)
            
            with m_col4:
                st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">🔋 {:.2f}</div>
                    <div class="metric-label">หน่วยไฟ EV (kWh)</div>
                </div>
                """.format(ev_kwh), unsafe_allow_html=True)
        else:
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">💰 {:.2f}</div>
                    <div class="metric-label">ยอดค่าไฟฟ้าสุทธิ (บาท)</div>
                </div>
                """.format(bill['final_bill']), unsafe_allow_html=True)
            
            with m_col2:
                st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">⚡ {:.2f}</div>
                    <div class="metric-label">ยอดใช้ไฟรวม (kWh)</div>
                </div>
                """.format(bill['total_kwh']), unsafe_allow_html=True)
            
            with m_col3:
                st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">🔥 {:.4f}</div>
                    <div class="metric-label">อัตรา Ft ที่ใช้</div>
                </div>
                """.format(bill['applicable_ft_rate']), unsafe_allow_html=True)

        # Detailed Results
        with st.expander("📄 รายละเอียดการคำนวณและดาวน์โหลด", expanded=False):
            display_customer_label = st.session_state.customer_type_label
            if st.session_state.customer_type_label == "🏢 กิจการขนาดเล็ก":
                display_customer_label += f" ({st.session_state.voltage_level})"
            
            output = [
                "=== ผลการคำนวณค่าไฟฟ้า ===",
                f"ช่วงข้อมูล: {bill['data_period_start']} ถึง {bill['data_period_end']}",
                f"ประเภทผู้ใช้: {display_customer_label}, อัตรา: {st.session_state.tariff_type}",
            ]
            
            if is_ev_calculated:
                ev_start_date_str = st.session_state.ev_date_range[0].strftime('%d/%m/%Y')
                ev_end_date_str = st.session_state.ev_date_range[1].strftime('%d/%m/%Y')
                output.append(f"จำลอง EV: {st.session_state.ev_power:.2f} kW ({st.session_state.ev_start_time.strftime('%H:%M')} - {st.session_state.ev_end_time.strftime('%H:%M')})")
                output.append(f"          (ช่วงวันที่ชาร์จ: {ev_start_date_str} - {ev_end_date_str})")
            
            output.extend(["-"*50, f"ยอดใช้ไฟรวม: {bill['total_kwh']:,.2f} kWh"])
            
            if is_ev_calculated: 
                output.extend([f"  - หน่วยไฟบ้าน: {base_kwh:,.2f} kWh", f"  - หน่วยไฟ EV: {ev_kwh:,.2f} kWh"])
            
            if st.session_state.tariff_type == '⏰ อัตรา TOU': 
                output.extend([f"  - Peak: {bill['kwh_peak']:,.2f} kWh", f"  - Off-Peak: {bill['kwh_off_peak']:,.2f} kWh"])
            
            output.extend([
                "-"*50,
                f"{'ค่าพลังงานไฟฟ้า':<30}: {bill['base_energy_cost']:>15,.2f} บาท",
                f"{'ค่าบริการรายเดือน':<30}: {bill['service_charge']:>15,.2f} บาท",
                f"{f'ค่า Ft (@{bill['applicable_ft_rate']:.4f})':<30}: {bill['ft_cost']:>15,.2f} บาท",
                "-"*50,
                f"{'ยอดรวมก่อน VAT':<30}: {bill['total_before_vat']:>15,.2f} บาท",
                f"{f'ภาษีมูลค่าเพิ่ม ({VAT_RATE*100:.0f}%)':<30}: {bill['vat_amount']:>15,.2f} บาท",
                "="*50
            ])
            
            if is_ev_calculated: 
                output.extend([
                    f"{'ค่าไฟบ้าน (ไม่รวม EV)':<30}: {bill['final_bill'] - ev_cost:>15,.2f} บาท",
                    f"{'ค่าไฟส่วน EV':<30}: {ev_cost:>15,.2f} บาท",
                    "="*50
                ])
            
            output.append(f"{'**ยอดค่าไฟฟ้าสุทธิ**':<30}: {bill['final_bill']:>15,.2f} บาท")
            
            details_text = "\n".join(output)
            st.code(details_text, language=None)
            st.download_button(
                "📥 ดาวน์โหลดผลลัพธ์ (.txt)",
                details_text.encode('utf-8'),
                f"bill_result_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                'text/plain'
            )
        
        # Enhanced Chart Section
        st.markdown("""
        <div class="section-card">
            <div class="section-header">
                <span class="section-icon">📈</span>
                <h2>กราฟวิเคราะห์การใช้ไฟ</h2>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        df_plot = st.session_state.get('df_for_plotting')
        if df_plot is not None and not df_plot.empty:
            # Main load profile chart
            st.markdown("### 📊 Load Profile Analysis")
            chart_data = create_enhanced_chart_data(df_plot)
            if chart_data is not None:
                st.line_chart(chart_data, height=400)
            
            # Additional analysis charts
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("### 📊 การใช้ไฟเฉลี่ยรายวัน")
                daily_data = create_daily_consumption_data(df_plot)
                if daily_data is not None:
                    st.bar_chart(daily_data, height=300)
            
            with col_chart2:
                st.markdown("### ⏰ รูปแบบการใช้ไฟตามชั่วโมง")
                hourly_data = create_hourly_pattern_data(df_plot)
                if hourly_data is not None:
                    st.line_chart(hourly_data, height=300)
            
            # TOU Analysis (if applicable)
            if st.session_state.tariff_type == '⏰ อัตรา TOU':
                st.markdown("### ⏰ วิเคราะห์ Peak/Off-Peak")
                
                # Add TOU classification
                df_plot['TOU_Period'] = df_plot['DateTime'].apply(classify_tou_period)
                tou_summary = df_plot.groupby('TOU_Period')['Total import kW demand'].agg(['mean', 'sum', 'count'])
                
                col_tou1, col_tou2 = st.columns(2)
                
                with col_tou1:
                    st.markdown("#### 🥧 สัดส่วนการใช้ไฟ Peak vs Off-Peak")
                    # Create pie chart data for Streamlit
                    tou_pie_data = tou_summary['sum']
                    
                    # Display as metrics instead of pie chart
                    total_consumption = tou_pie_data.sum()
                    for period, consumption in tou_pie_data.items():
                        percentage = (consumption / total_consumption) * 100
                        if period == 'Peak':
                            st.error(f"🔥 {period}: {consumption:.2f} kWh ({percentage:.1f}%)")
                        else:
                            st.success(f"🌙 {period}: {consumption:.2f} kWh ({percentage:.1f}%)")
                
                with col_tou2:
                    st.markdown("#### 📊 ค่าเฉลี่ย Peak vs Off-Peak")
                    tou_avg_data = tou_summary['mean']
                    st.bar_chart(tou_avg_data, height=300)
            
            # Summary Statistics
            with st.expander("📊 สถิติการใช้ไฟ", expanded=False):
                stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                
                with stats_col1:
                    st.metric("📈 ค่าสูงสุด", f"{df_plot['Total import kW demand'].max():.2f} kW")
                    st.metric("📉 ค่าต่ำสุด", f"{df_plot['Total import kW demand'].min():.2f} kW")
                
                with stats_col2:
                    st.metric("📊 ค่าเฉลี่ย", f"{df_plot['Total import kW demand'].mean():.2f} kW")
                    st.metric("📐 ค่ามัธยฐาน", f"{df_plot['Total import kW demand'].median():.2f} kW")
                
                with stats_col3:
                    st.metric("📏 ส่วนเบียงเบนมาตรฐาน", f"{df_plot['Total import kW demand'].std():.2f} kW")
                    st.metric("🎯 Load Factor", f"{(df_plot['Total import kW demand'].mean() / df_plot['Total import kW demand'].max() * 100):.1f}%")
                
                with stats_col4:
                    peak_hours = len(df_plot[df_plot['Total import kW demand'] > df_plot['Total import kW demand'].quantile(0.9)])
                    st.metric("⚡ จำนวนข้อมูล", f"{len(df_plot):,} รายการ")
                    st.metric("🔥 ช่วง Peak (>90%)", f"{peak_hours:,} รายการ")
        else:
            st.warning("⚠️ ไม่มีข้อมูลสำหรับสร้างกราฟ")
        
        # Energy Efficiency Tips
        st.markdown("""
        <div class="section-card">
            <div class="section-header">
                <span class="section-icon">💡</span>
                <h2>คำแนะนำประหยัดพลังงาน</h2>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        tips_col1, tips_col2 = st.columns(2)
        
        with tips_col1:
            st.markdown("""
            ### 🏠 สำหรับบ้านอยู่อาศัย
            - 🌡️ **เครื่องปรับอากาศ**: ตั้งที่ 25-26°C ประหยัดได้ 6-8%
            - 💡 **หลัดไฟ LED**: ประหยัดได้ถึง 80% เมื่อเทียบกับหลอดไส้
            - 🔌 **ถอดปลั๊ก**: เครื่องใช้ไฟฟ้าที่ไม่ได้ใช้งาน
            - ⏰ **ใช้ไฟในช่วง Off-Peak**: 22:00-09:00 น.
            """)
        
        with tips_col2:
            st.markdown("""
            ### 🚗 สำหรับ EV Charging
            - 🌙 **ชาร์จกลางคืน**: ช่วง 22:00-05:00 ประหยัดสุด
            - 📱 **Smart Charging**: ใช้ระบบจัดการการชาร์จอัตโนมัติ
            - 🔋 **Battery Management**: ชาร์จ 20-80% เพื่อยืดอายุแบตเตอรี่
            - ☀️ **Solar + EV**: พิจารณาติดตั้งโซลาร์เซลล์
            """)

# Footer
st.markdown("""
<div style="margin-top: 3rem; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; text-align: center;">
    <p style="color: white; margin: 0; font-size: 1.1rem; font-weight: 500;">
        ⚡ Electric Bill Calculator Pro | Made with ❤️ using Streamlit
    </p>
    <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 0.9rem;">
        เครื่องมือคำนวณค่าไฟฟ้าระดับมืออาชีพสำหรับทุกคน
    </p>
</div>
""", unsafe_allow_html=True)
