# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import io
from datetime import datetime, time, date
import calendar
import os
import traceback

# --- ค่าคงที่และข้อมูลอัตรา ---
# (เหมือนเดิมจากโค้ด Tkinter)
TARIFFS = {
    "residential": {
        "normal_le_150": {'service_charge': 8.19, 'type': 'tiered', 'tiers': [{'limit': 15, 'rate': 2.3488}, {'limit': 25, 'rate': 2.9882}, {'limit': 35, 'rate': 3.2405}, {'limit': 100, 'rate': 3.6237}, {'limit': 150, 'rate': 3.7171}, {'limit': 400, 'rate': 4.2218}, {'limit': float('inf'), 'rate': 4.4217}]},
        "normal_gt_150": {'service_charge': 24.62, 'type': 'tiered', 'tiers': [{'limit': 150, 'rate': 3.2484}, {'limit': 400, 'rate': 4.2218}, {'limit': float('inf'), 'rate': 4.4217}]},
        "tou": {'service_charge': 24.62, 'type': 'tou', 'peak_rate': 5.7982, 'off_peak_rate': 2.6369}
    },
    "smb": {
        "normal": {'service_charge': 312.24, 'type': 'tiered', 'tiers': [{'limit': 150, 'rate': 3.2484}, {'limit': 400, 'rate': 4.2218}, {'limit': float('inf'), 'rate': 4.4217}]},
        "tou": {'service_charge': 33.29, 'type': 'tou', 'peak_rate': 5.7982, 'off_peak_rate': 2.6369}
    }
}
FT_RATES = {
    (1, 2023): 0.9343, (5, 2023): 0.9119, (9, 2023): 0.2048,
    (1, 2024): 0.3972, (5, 2024): 0.3972, (9, 2024): 0.3972,
    (1, 2025): 0.3672, (5, 2025): 0.3672, # อัปเดตข้อมูล Ft ปีปัจจุบันและอนาคตตามประกาศ
}
# --- วันหยุด TOU ---
# (เหมือนเดิม)
HOLIDAYS_TOU_2024_STR = ["2024-01-01", "2024-01-02", "2024-02-26", "2024-04-08", "2024-04-15", "2024-04-16",
                       "2024-05-01", "2024-05-06", "2024-05-22", "2024-06-03", "2024-07-22", "2024-07-29",
                       "2024-08-12", "2024-10-14", "2024-10-23", "2024-12-05", "2024-12-10", "2024-12-31"]
HOLIDAYS_TOU_2025_STR = ["2025-01-01", "2025-02-12", "2025-04-07", "2025-04-14", "2025-04-15", # วันหยุดปี 2025 (ตัวอย่าง)
                       "2025-05-01", "2025-05-05", "2025-05-09", "2025-06-03", "2025-07-10", "2025-07-11",
                       "2025-07-28", "2025-08-12", "2025-10-13", "2025-10-23", "2025-12-05", "2025-12-10",
                       "2025-12-31"] # *** ควรปรับปรุงรายการวันหยุดให้ถูกต้องตามประกาศจริง ***

HOLIDAYS_TOU_DATA = {}
try:
    HOLIDAYS_TOU_DATA[2024] = set(datetime.strptime(d, "%Y-%m-%d").date() for d in HOLIDAYS_TOU_2024_STR)
    HOLIDAYS_TOU_DATA[2025] = set(datetime.strptime(d, "%Y-%m-%d").date() for d in HOLIDAYS_TOU_2025_STR)
    # เพิ่มปีอื่นๆ ตามต้องการ
except ValueError as e:
    print(f"Error parsing HOLIDAY STR lists: {e}.")
    HOLIDAYS_TOU_DATA = {}

VAT_RATE = 0.07
PEAK_START = time(9, 0, 0)
PEAK_END = time(21, 59, 59)
MONTH_NAMES_TH = {1: "มกราคม", 2: "กุมภาพันธ์", 3: "มีนาคม", 4: "เมษายน",
                  5: "พฤษภาคม", 6: "มิถุนายน", 7: "กรกฎาคม", 8: "สิงหาคม",
                  9: "กันยายน", 10: "ตุลาคม", 11: "พฤศจิกายน", 12: "ธันวาคม"}
# รายการ ชั่วโมง นาที สำหรับ Dropdown
HOURS = [f"{h:02d}" for h in range(24)]
MINUTES = ["00", "15", "30", "45"]


# --- ฟังก์ชัน Helper (ปรับปรุง parse_data_file เล็กน้อย) ---

# @st.cache_data # อาจใช้ cache เพื่อให้โหลดไฟล์เดิมเร็วขึ้นในการรันครั้งต่อไป
def parse_data_file(uploaded_file):
    """อ่านและประมวลผลไฟล์ข้อมูล Load Profile ที่อัปโหลดผ่าน Streamlit"""
    detected_format = None
    first_line = ""
    file_encoding = 'utf-8'
    file_content_string = ""
    df_final = None

    try:
        # ลองอ่านด้วย utf-8 ก่อน
        bytes_content = uploaded_file.getvalue()
        file_content_string = bytes_content.decode(file_encoding)
        first_line = file_content_string.split('\n', 1)[0].strip()
        st.write(f"✅ อ่านไฟล์ด้วย Encoding: {file_encoding}") # แสดงผลในแอป
    except UnicodeDecodeError:
        st.write(f"⚠️ อ่านด้วย {file_encoding} ไม่สำเร็จ, ลอง CP874/TIS-620...")
        file_encoding = 'cp874'
        try:
            uploaded_file.seek(0) # ย้อนกลับไปอ่านไฟล์ใหม่
            bytes_content = uploaded_file.getvalue()
            file_content_string = bytes_content.decode(file_encoding)
            first_line = file_content_string.split('\n', 1)[0].strip()
            st.write(f"✅ อ่านไฟล์ด้วย Encoding: {file_encoding}")
        except Exception as e:
            raise ValueError(f"ไม่สามารถอ่านไฟล์ด้วย UTF-8 หรือ CP874: {e}")
    except Exception as e:
        raise ValueError(f"เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")

    # --- ตรวจจับ Format ---
    if first_line.rstrip() == "DateTime\tTotal import kW demand":
        detected_format = "format1_tab"
        st.write("ตรวจพบรูปแบบไฟล์: Tab-separated (DateTime, Total import kW demand)")
    elif (first_line.startswith("PRECISE") or first_line.startswith("KY ")) and "," in first_line:
        detected_format = "format2_csv"
        st.write(f"ตรวจพบรูปแบบไฟล์: CSV LoadProfile ({first_line.split(' ')[0]}...)")
    elif first_line.count(',') >= 7: # ตรวจจับ CSV ทั่วไป
        detected_format = "format2_csv"
        st.write("ตรวจพบรูปแบบไฟล์: CSV (>= 8 คอลัมน์)")
    else:
        raise ValueError("ไม่รู้จักรูปแบบไฟล์ หรือ Header ไม่ถูกต้อง")

    # --- ประมวลผลข้อมูลด้วย Pandas ---
    try:
        data_io = io.StringIO(file_content_string) # ใช้ข้อมูล string ที่อ่านได้

        if detected_format == "format1_tab":
            df = pd.read_csv(data_io, sep='\t', header=0, engine='python', skipinitialspace=True)
            demand_col = 'Total import kW demand'
            datetime_col = 'DateTime'
            df.columns = df.columns.str.strip()
            if datetime_col not in df.columns or demand_col not in df.columns:
                raise ValueError(f"ไฟล์ Format 1 ต้องมีคอลัมน์ '{datetime_col}' และ '{demand_col}'")
            df['DateTime_parsed'] = pd.to_datetime(df[datetime_col], dayfirst=True, errors='coerce')
            df['Demand_parsed'] = pd.to_numeric(df[demand_col], errors='coerce')
            df_final = df.dropna(subset=['DateTime_parsed', 'Demand_parsed'])
            if not df_final.empty:
                 df_final = df_final.rename(columns={'DateTime_parsed': 'DateTime', 'Demand_parsed': 'Total import kW demand'}) \
                                     [['DateTime', 'Total import kW demand']].copy()

        elif detected_format == "format2_csv":
            column_names = ['MeterInfo', 'DateTimeStr', 'Val1', 'Demand_W', 'Val2', 'Val3', 'Val4', 'Val5']
            # อ่านโดยข้ามบรรทัดแรกถ้าเป็น header ที่ไม่ต้องการ (อาจจะต้องปรับปรุง)
            # header=None ถ้าไม่มี header เลย, header=0 ถ้ามี header แต่จะใช้ชื่อที่เรากำหนด
            df = pd.read_csv(data_io, sep=',', header=None, names=column_names, engine='python', skipinitialspace=True)
            datetime_col_idx = 1
            demand_col_idx = 3
            if df.shape[1] <= max(datetime_col_idx, demand_col_idx):
                raise ValueError(f"ไฟล์ CSV มีคอลัมน์ไม่พอ (ต้องการอย่างน้อย {max(datetime_col_idx, demand_col_idx)+1})")

            dt_series = pd.to_datetime(df.iloc[:, datetime_col_idx], errors='coerce')
            demand_series_numeric = pd.to_numeric(df.iloc[:, demand_col_idx], errors='coerce')
            demand_series_kw = demand_series_numeric / 1000.0

            df_temp = pd.DataFrame({'DateTime': dt_series, 'Total import kW demand': demand_series_kw})
            df_final = df_temp.dropna(subset=['DateTime', 'Total import kW demand'])
            if not df_final.empty:
                 df_final = df_final[['DateTime', 'Total import kW demand']].copy()


        if df_final is None or df_final.empty:
            raise ValueError("ไม่พบข้อมูลที่ถูกต้องในไฟล์หลังจากประมวลผล")

        st.write(f"ประมวลผลข้อมูลสำเร็จ: พบ {len(df_final)} รายการที่ถูกต้อง")
        return df_final

    except pd.errors.EmptyDataError:
        raise ValueError("ไฟล์ว่างเปล่า หรืออ่านข้อมูล Pandas ไม่ได้")
    except Exception as e:
        st.error(f"Traceback: {traceback.format_exc()}") # แสดง traceback ถ้ามีปัญหา
        raise type(e)(f"เกิดข้อผิดพลาดขณะประมวลผลข้อมูล: {e}")

# (ฟังก์ชัน classify_tou_period, get_ft_rate, calculate_bill เหมือนเดิม)
def classify_tou_period(dt_obj):
    # (โค้ดเหมือนเดิม)
    if not isinstance(dt_obj, datetime): return 'Unknown'
    current_date = dt_obj.date()
    current_time = dt_obj.time()
    day_of_week = dt_obj.weekday()
    year_holidays = HOLIDAYS_TOU_DATA.get(current_date.year)
    if year_holidays and current_date in year_holidays: return 'Off-Peak'
    if day_of_week >= 5: return 'Off-Peak' # Saturday (5), Sunday (6)
    if PEAK_START <= current_time <= PEAK_END: return 'Peak'
    return 'Off-Peak'

def get_ft_rate(date_in_period):
    # (โค้ดเหมือนเดิม)
    if not isinstance(date_in_period, (datetime, date)):
        print(f"Warning: Invalid date type ({type(date_in_period)}) passed to get_ft_rate. Using current date.")
        date_in_period = datetime.now().date()
    if isinstance(date_in_period, datetime):
        date_in_period = date_in_period.date()

    sorted_ft_periods = sorted(FT_RATES.keys())
    applicable_rate = None
    for start_month, start_year in reversed(sorted_ft_periods):
        if (date_in_period.year > start_year) or \
           (date_in_period.year == start_year and date_in_period.month >= start_month):
            applicable_rate = FT_RATES[(start_month, start_year)]
            break
    if applicable_rate is None:
        print(f"Warning: Ft rate not found for period including {date_in_period}. Using Ft=0.0")
        applicable_rate = 0.0
    return applicable_rate

def calculate_bill(df_processed, customer_type, tariff_type):
    # (โค้ดเหมือนเดิม - รับ df ที่มีคอลัมน์ kWh แล้ว)
    if df_processed is None or df_processed.empty: return {"error": "No valid data to process."}
    if 'kWh' not in df_processed.columns or 'DateTime' not in df_processed.columns: return {"error": "Internal error: Missing required columns (kWh or DateTime)."}
    if not pd.api.types.is_datetime64_any_dtype(df_processed['DateTime']): return {"error": "Internal error: DateTime column is not the correct type."}

    total_kwh = df_processed['kWh'].sum()
    kwh_peak, kwh_off_peak = 0, 0
    df_temp = df_processed.copy() # Work on a copy

    data_year = None
    last_valid_date_index = df_temp['DateTime'].last_valid_index()
    if last_valid_date_index is not None:
        data_year = df_temp.loc[last_valid_date_index, 'DateTime'].year

    if tariff_type == 'tou':
        df_temp['TOU_Period'] = df_temp['DateTime'].apply(classify_tou_period)
        kwh_summary = df_temp.groupby('TOU_Period')['kWh'].sum()
        kwh_peak = kwh_summary.get('Peak', 0)
        kwh_off_peak = kwh_summary.get('Off-Peak', 0) + kwh_summary.get('Unknown', 0)
        if abs((kwh_peak + kwh_off_peak) - total_kwh) > 0.01:
            print(f"Warning: Peak/Off-peak sum ({kwh_peak + kwh_off_peak:.4f}) doesn't match total kWh ({total_kwh:.4f}). Check TOU classification.")

    try:
        if customer_type == "residential":
            if tariff_type == "normal":
                tariff_key = "normal_le_150" if total_kwh <= 150 else "normal_gt_150"
                rate_structure = TARIFFS["residential"][tariff_key]
            elif tariff_type == "tou":
                rate_structure = TARIFFS["residential"]["tou"]
            else: raise ValueError("Invalid residential tariff type specified.")
        elif customer_type == "smb":
            if tariff_type == "normal":
                rate_structure = TARIFFS["smb"]["normal"]
            elif tariff_type == "tou":
                rate_structure = TARIFFS["smb"]["tou"]
            else: raise ValueError("Invalid small business tariff type specified.")
        else: raise ValueError("Invalid customer type specified.")
    except KeyError as e: return {"error": f"Tariff structure not found in TARIFFS data: {e}"}
    except ValueError as e: return {"error": str(e)}

    base_energy_cost = 0
    if rate_structure['type'] == 'tiered':
        last_limit = 0
        for tier in rate_structure['tiers']:
            limit, rate = tier['limit'], tier['rate']
            units_in_tier = max(0, min(total_kwh, limit) - last_limit)
            if units_in_tier > 0:
                base_energy_cost += units_in_tier * rate
            last_limit = limit
            if total_kwh <= limit and limit != float('inf'):
                break
    elif rate_structure['type'] == 'tou':
        base_energy_cost = (kwh_peak * rate_structure['peak_rate']) + (kwh_off_peak * rate_structure['off_peak_rate'])

    service_charge = rate_structure['service_charge']

    applicable_ft_rate = 0.0
    if last_valid_date_index is not None:
        last_date_obj = df_processed.loc[last_valid_date_index, 'DateTime']
        if pd.notnull(last_date_obj):
            applicable_ft_rate = get_ft_rate(last_date_obj.date())
        else:
            print("Warning: Last date object is null, using current date for Ft rate.")
            applicable_ft_rate = get_ft_rate(datetime.now().date())
    else:
         print("Warning: Could not determine last date, using current date for Ft rate.")
         applicable_ft_rate = get_ft_rate(datetime.now().date())

    ft_cost = total_kwh * applicable_ft_rate
    total_before_vat = base_energy_cost + service_charge + ft_cost
    vat_amount = total_before_vat * VAT_RATE
    final_bill = total_before_vat + vat_amount

    result = {
        "customer_type": customer_type, "tariff_type": tariff_type,
        "data_period_start": df_temp['DateTime'].iloc[0].strftime('%Y-%m-%d %H:%M:%S') if not df_temp.empty else "N/A",
        "data_period_end": df_temp['DateTime'].iloc[-1].strftime('%Y-%m-%d %H:%M:%S') if not df_temp.empty else "N/A",
        "data_year": data_year,
        "total_kwh": round(total_kwh, 4),
        "kwh_peak": round(kwh_peak, 4) if tariff_type == 'tou' else None,
        "kwh_off_peak": round(kwh_off_peak, 4) if tariff_type == 'tou' else None,
        "base_energy_cost": round(base_energy_cost, 2),
        "service_charge": round(service_charge, 2),
        "applicable_ft_rate": round(applicable_ft_rate, 4),
        "ft_cost": round(ft_cost, 2),
        "total_before_vat": round(total_before_vat, 2),
        "vat_amount": round(vat_amount, 2),
        "final_bill": round(final_bill, 2),
        "error": None
    }
    return result
# --- สิ้นสุดส่วนฟังก์ชัน Helper ---


# --- Streamlit App ---
st.set_page_config(page_title="คำนวณค่าไฟฟ้า", layout="wide") # ตั้งค่าหน้าจอให้กว้างขึ้น
st.title("📊 โปรแกรมคำนวณค่าไฟฟ้า (มีจำลอง EV)")

# --- Session State Initialization ---
# ใช้ st.session_state เพื่อเก็บค่าระหว่างการรัน
if 'full_dataframe' not in st.session_state:
    st.session_state.full_dataframe = None
if 'available_years' not in st.session_state:
    st.session_state.available_years = []
if 'available_months_th' not in st.session_state:
    st.session_state.available_months_th = []
if 'calculation_result' not in st.session_state:
    st.session_state.calculation_result = ""


# --- ส่วนอัปโหลดไฟล์ ---
uploaded_file = st.file_uploader("1. เลือกไฟล์ข้อมูล Load Profile (.txt หรือ .csv)", type=['txt', 'csv'])

if uploaded_file is not None:
    # ตรวจสอบว่าไฟล์เปลี่ยนไปหรือไม่ หรือยังไม่มี df ใน state
    # (Streamlit จะเก็บ uploaded_file object เดิมถ้าผู้ใช้ไม่ได้เลือกไฟล์ใหม่)
    # อาจจะต้องเพิ่มการเช็คชื่อไฟล์หรือ hash ถ้าต้องการบังคับให้โหลดใหม่เสมอ
    if st.session_state.full_dataframe is None or getattr(uploaded_file, "name", "") != getattr(st.session_state.get('last_uploaded_file'), "name", ""):
        st.info(f"กำลังประมวลผลไฟล์: {uploaded_file.name}...")
        try:
            with st.spinner('กำลังอ่านและประมวลผลข้อมูล...'):
                st.session_state.full_dataframe = parse_data_file(uploaded_file)
                st.session_state.last_uploaded_file = uploaded_file # เก็บข้อมูลไฟล์ล่าสุดที่โหลด

                # ดึงปีและเดือนจาก DataFrame ที่โหลดได้
                if st.session_state.full_dataframe is not None and not st.session_state.full_dataframe.empty:
                    st.session_state.available_years = sorted(st.session_state.full_dataframe['DateTime'].dt.year.unique())
                    available_months_num = sorted(st.session_state.full_dataframe['DateTime'].dt.month.unique())
                    st.session_state.available_months_th = [MONTH_NAMES_TH.get(m, str(m)) for m in available_months_num]
                    st.success(f"โหลดและประมวลผลไฟล์ '{uploaded_file.name}' สำเร็จ!")
                else:
                    st.session_state.full_dataframe = None # ตั้งค่ากลับถ้า df ว่าง
                    st.error("ไม่พบข้อมูลที่ถูกต้องในไฟล์")

        except ValueError as ve:
            st.session_state.full_dataframe = None
            st.error(f"ข้อผิดพลาดในการประมวลผลไฟล์: {ve}")
            # st.error(f"Traceback: {traceback.format_exc()}")
        except Exception as ex:
            st.session_state.full_dataframe = None
            st.error(f"เกิดข้อผิดพลาดไม่คาดคิด: {ex}")
            # st.error(f"Traceback: {traceback.format_exc()}")

# --- ส่วนตั้งค่าการคำนวณ (จะแสดงเมื่อโหลดไฟล์สำเร็จ) ---
if st.session_state.full_dataframe is not None:
    st.markdown("---")
    st.header("2. ตั้งค่าการคำนวณ")

    col1, col2 = st.columns(2) # แบ่งเป็น 2 คอลัมน์

    with col1:
        customer_options = ["บ้านอยู่อาศัย", "กิจการขนาดเล็ก"]
        selected_customer = st.selectbox("ประเภทผู้ใช้:", customer_options, key="customer_type")

        year_options = ["ทั้งปี"] + st.session_state.available_years
        selected_year = st.selectbox("เลือกปี:", year_options, key="year")

    with col2:
        tariff_options = ["อัตราปกติ", "อัตรา TOU"]
        selected_tariff = st.selectbox("ประเภทอัตรา:", tariff_options, key="tariff_type")

        month_options = ["ทั้งเดือน"] + st.session_state.available_months_th
        selected_month = st.selectbox("เลือกเดือน:", month_options, key="month")

    # --- ส่วนจำลอง EV Charger ---
    with st.expander("🔌 จำลอง EV Charger (Optional)"):
        ev_enabled = st.checkbox("เปิดใช้งานการจำลอง EV", key="ev_enabled")

        ev_col1, ev_col2, ev_col3 = st.columns(3)
        with ev_col1:
             ev_power_kw = st.number_input("กำลังไฟ Charger (kW):", min_value=0.1, value=7.0, step=0.1, format="%.1f", key="ev_power", disabled=not ev_enabled)
        with ev_col2:
             ev_start_hour = st.selectbox("เวลาเริ่มชาร์จ (ชม.):", HOURS, index=22, key="ev_start_h", disabled=not ev_enabled) # Default 22
             ev_start_min = st.selectbox("นาทีเริ่ม:", MINUTES, index=0, key="ev_start_m", disabled=not ev_enabled) # Default 00
        with ev_col3:
             ev_end_hour = st.selectbox("เวลาสิ้นสุด (ชม.):", HOURS, index=5, key="ev_end_h", disabled=not ev_enabled) # Default 05
             ev_end_min = st.selectbox("นาทีสิ้นสุด:", MINUTES, index=0, key="ev_end_m", disabled=not ev_enabled) # Default 00

    st.markdown("---")

    # --- ปุ่มคำนวณ ---
    if st.button("คำนวณค่าไฟ", type="primary"):
        st.session_state.calculation_result = "" # เคลียร์ผลลัพธ์เก่า
        with st.spinner("กำลังคำนวณ..."):
            try:
                # --- กรองข้อมูล ---
                df_filtered = st.session_state.full_dataframe.copy()
                if selected_year != "ทั้งปี":
                    df_filtered = df_filtered[df_filtered['DateTime'].dt.year == int(selected_year)]
                if selected_month != "ทั้งเดือน":
                    month_num = None
                    for num, name in MONTH_NAMES_TH.items():
                        if name == selected_month: month_num = num; break
                    if month_num:
                        df_filtered = df_filtered[df_filtered['DateTime'].dt.month == month_num]
                    else: # กรณีไม่เจอชื่อเดือน (ไม่ควรเกิดกับ selectbox)
                         st.warning(f"ไม่พบเลขเดือนสำหรับ '{selected_month}'")


                if df_filtered.empty:
                    st.warning(f"ไม่พบข้อมูลสำหรับ '{selected_month} ปี {selected_year}' ในไฟล์นี้")
                    st.session_state.calculation_result = f"ไม่พบข้อมูลสำหรับ '{selected_month} ปี {selected_year}'"
                else:
                    # --- จัดการ EV ---
                    ev_charging_intervals = 0
                    ev_kwh_added = 0.0
                    ev_details_for_output = ""
                    charge_start_time = None
                    charge_end_time = None

                    if ev_enabled:
                        try:
                            start_h = int(st.session_state.ev_start_h)
                            start_m = int(st.session_state.ev_start_m)
                            end_h = int(st.session_state.ev_end_h)
                            end_m = int(st.session_state.ev_end_m)
                            ev_power = float(st.session_state.ev_power) # ใช้ key ที่กำหนด
                            if ev_power <= 0: raise ValueError("กำลังไฟ EV ต้องมากกว่า 0")

                            charge_start_time = time(start_h, start_m)
                            charge_end_time = time(end_h, end_m)

                            ev_details_for_output = f"จำลอง EV Charger: {ev_power:.2f} kW ({start_h:02d}:{start_m:02d} - {end_h:02d}:{end_m:02d})\n"

                            time_series = df_filtered['DateTime'].dt.time
                            if charge_start_time <= charge_end_time:
                                charging_mask = (time_series >= charge_start_time) & (time_series <= charge_end_time)
                            else: # ข้ามคืน
                                charging_mask = (time_series >= charge_start_time) | (time_series <= charge_end_time)

                            df_filtered.loc[charging_mask, 'Total import kW demand'] += ev_power
                            ev_charging_intervals = charging_mask.sum()
                            ev_kwh_added = ev_charging_intervals * ev_power * 0.25

                        except ValueError as ve:
                            st.error(f"ข้อมูล EV ไม่ถูกต้อง: {ve}")
                            ev_details_for_output = f"⚠️ ข้อมูล EV ไม่ถูกต้อง: {ve}\n" # แสดง error ในผลลัพธ์ด้วย
                            # ไม่หยุดคำนวณ แต่ไม่รวมโหลด EV
                        except Exception as ex_ev:
                            st.error(f"เกิดปัญหาในการประมวลผล EV Charger: {ex_ev}")
                            ev_details_for_output = f"⚠️ เกิดปัญหาในการประมวลผล EV: {ex_ev}\n"


                    # --- คำนวณ kWh ---
                    df_filtered['kWh'] = df_filtered['Total import kW demand'] * 0.25

                    # --- คำนวณค่าไฟ ---
                    customer_key = "residential" if selected_customer == "บ้านอยู่อาศัย" else "smb"
                    tariff_key = "normal" if selected_tariff == "อัตราปกติ" else "tou"
                    bill_details = calculate_bill(df_filtered, customer_key, tariff_key)

                    # --- สร้าง Output String ---
                    if bill_details.get("error"):
                         st.error(f"เกิดข้อผิดพลาดในการคำนวณ: {bill_details['error']}")
                         st.session_state.calculation_result = f"เกิดข้อผิดพลาดในการคำนวณ:\n{bill_details['error']}"
                    else:
                        # (โค้ดสร้าง output string เหมือนเดิม แต่ใช้ bill_details และเพิ่มข้อมูล EV)
                        calculation_period = ""
                        if selected_year == "ทั้งปี" and selected_month == "ทั้งเดือน": calculation_period = "ข้อมูลทั้งหมดในไฟล์"
                        elif selected_year == "ทั้งปี": calculation_period = f"เดือน{selected_month} (ทุกปีในไฟล์)"
                        elif selected_month == "ทั้งเดือน": calculation_period = f"ทั้งปี {selected_year}"
                        else: calculation_period = f"{selected_month} {selected_year}"

                        output = f"--- ผลการคำนวณค่าไฟฟ้า ({calculation_period}) ---\n"
                        if ev_enabled: output += ev_details_for_output # ใส่รายละเอียด EV ถ้าเปิดใช้งาน
                        output += f"ประเภทผู้ใช้: {selected_customer}\n"
                        output += f"ประเภทอัตรา: {selected_tariff}\n"
                        output += f"ไฟล์ข้อมูล: {uploaded_file.name}\n" # แสดงชื่อไฟล์ที่ใช้
                        output += f"ช่วงเวลาข้อมูลที่ใช้คำนวณ: {bill_details['data_period_start']} ถึง {bill_details['data_period_end']}\n"
                        output += f"ยอดใช้ไฟรวม: {bill_details['total_kwh']:.2f} kWh\n"
                        if ev_enabled and ev_kwh_added > 0: # แสดงเฉพาะเมื่อมีการเพิ่มจริง
                            output += f"  - หน่วยที่เพิ่มจาก EV: {ev_kwh_added:.2f} kWh ({ev_charging_intervals} ช่วงเวลา)\n"
                        if bill_details['tariff_type'] == 'tou':
                            output += f"  - Peak: {bill_details['kwh_peak']:.2f} kWh\n"
                            output += f"  - Off-Peak: {bill_details['kwh_off_peak']:.2f} kWh\n"
                        output += "----------------------------------------\n"
                        output += f"ค่าพลังงานไฟฟ้า: {bill_details['base_energy_cost']:>18,.2f} บาท\n"
                        output += f"ค่าบริการ: {bill_details['service_charge']:>25,.2f} บาท\n"
                        ft_warning = ""
                        ft_rate_for_year = bill_details['applicable_ft_rate']
                        # (โค้ด Ft warning เหมือนเดิม)
                        output += f"ค่า Ft (@{ft_rate_for_year:.4f}/หน่วย): {bill_details['ft_cost']:>12,.2f} บาท{ft_warning}\n"
                        output += "----------------------------------------\n"
                        output += f"ยอดรวมก่อน VAT: {bill_details['total_before_vat']:>20,.2f} บาท\n"
                        output += f"ภาษีมูลค่าเพิ่ม (VAT 7%): {bill_details['vat_amount']:>13,.2f} บาท\n"
                        output += "========================================\n"
                        output += f"ยอดค่าไฟฟ้าสุทธิ: {bill_details['final_bill']:>19,.2f} บาท\n"
                        output += "========================================\n"
                        output += f"\nหมายเหตุ:\n"
                        output += f"- คำนวณจากข้อมูล {len(df_filtered)} รายการ\n"
                        output += f"- ใช้ค่า Ft และวันหยุดตามปีของข้อมูล ณ วันสุดท้ายในชุดข้อมูล ({bill_details['data_period_end'].split(' ')[0]})\n"
                        if ev_enabled and charge_start_time is not None and charge_end_time is not None and charge_start_time > charge_end_time:
                             output += "- การจำลอง EV เป็นแบบข้ามคืน\n"

                        st.session_state.calculation_result = output # เก็บผลลัพธ์ใน state

            except Exception as calc_ex:
                 st.error(f"เกิดข้อผิดพลาดระหว่างการคำนวณ: {calc_ex}")
                 st.error(f"Traceback: {traceback.format_exc()}")
                 st.session_state.calculation_result = f"เกิดข้อผิดพลาดระหว่างการคำนวณ:\n{calc_ex}"

# --- ส่วนแสดงผลลัพธ์ ---
if st.session_state.calculation_result:
    st.markdown("---")
    st.header("3. ผลการคำนวณ")
    st.text_area("รายละเอียด:", st.session_state.calculation_result, height=450) # แสดงผลจาก state


# --- อาจจะเพิ่มส่วนแสดงข้อมูลดิบหรือกราฟเบื้องต้น ---
# if st.session_state.full_dataframe is not None:
#     st.markdown("---")
#     if st.checkbox("แสดงตัวอย่างข้อมูลที่โหลด"):
#         st.dataframe(st.session_state.full_dataframe.head())
#     if st.checkbox("แสดงกราฟ Load Profile เบื้องต้น"):
#         try:
#              # กรองข้อมูลตามที่เลือก (อาจจะต้องทำซ้ำส่วนกรอง หรือเก็บ df_filtered ไว้ใน state)
#              # df_display = ... กรองข้อมูล ...
#              st.line_chart(st.session_state.full_dataframe.set_index('DateTime')['Total import kW demand']) # แสดงกราฟจากข้อมูลเต็มก่อนกรอง
#         except Exception as plot_ex:
#              st.warning(f"ไม่สามารถสร้างกราฟได้: {plot_ex}")