# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import io
from datetime import datetime, time, date
import calendar
import os
import traceback

# ==============================================================================
# --- ค่าคงที่และข้อมูลอัตรา (CONFIGURATIONS) ---
# หมายเหตุ: เพื่อการบำรุงรักษาในระยะยาว ควรพิจารณาย้ายส่วนนี้ไปยังไฟล์แยก
# เช่น config.py หรือ rates.json เพื่อให้ง่ายต่อการอัปเดต
# ==============================================================================

# --- 1. อัตราค่าไฟฟ้า (Tariffs) ---
# อ้างอิงอัตราค่าไฟฟ้าฐานล่าสุด (ตรวจสอบกับ กฟน./กฟภ. เป็นระยะ)
TARIFFS = {
    "residential": {
        "normal_le_150": {'service_charge': 8.19, 'type': 'tiered', 'tiers': [{'limit': 15, 'rate': 2.3488}, {'limit': 25, 'rate': 2.9882}, {'limit': 35, 'rate': 3.2405}, {'limit': 100, 'rate': 3.6237}, {'limit': 150, 'rate': 3.7171}, {'limit': 400, 'rate': 4.2218}, {'limit': float('inf'), 'rate': 4.4217}]},
        "normal_gt_150": {'service_charge': 24.62, 'type': 'tiered', 'tiers': [{'limit': 150, 'rate': 3.2484}, {'limit': 400, 'rate': 4.2218}, {'limit': float('inf'), 'rate': 4.4217}]},
        "tou": {'service_charge': 24.62, 'type': 'tou', 'peak_rate': 5.7982, 'off_peak_rate': 2.6369}
    },
    "smb": { # กิจการขนาดเล็ก (Small General Service)
        "normal": {'service_charge': 312.24, 'type': 'tiered', 'tiers': [{'limit': 150, 'rate': 3.2484}, {'limit': 400, 'rate': 4.2218}, {'limit': float('inf'), 'rate': 4.4217}]},
        "tou": {'service_charge': 33.29, 'type': 'tou', 'peak_rate': 5.7982, 'off_peak_rate': 2.6369}
    }
}

# --- 2. อัตราค่า Ft (Fuel Adjustment Charge) ---
# ที่มา: ประกาศคณะกรรมการกำกับกิจการพลังงาน (กกพ.) - https://www.erc.or.th/
FT_RATES = {
    # (Year, Month) -> Rate per kWh (บาทต่อหน่วย)
    # ค่าในอดีต (ตัวอย่าง)
    (2023, 1): 0.9343, 
    (2023, 5): 0.9119, 
    (2023, 9): 0.2048,
    # ค่าปี 2024 (อัปเดตล่าสุด ณ มิ.ย. 67)
    (2024, 1): 0.3972, # ม.ค.-เม.ย. 67
    (2024, 5): 0.3972, # พ.ค.-ส.ค. 67 (ประกาศจริง)
    (2024, 9): 0.3972, # ก.ย.-ธ.ค. 67 (ใช้ค่าปัจจุบันไปก่อน รอประกาศจริง)
    # ค่าปี 2025 (ใช้ค่าปัจจุบันไปก่อน รอประกาศจริง)
    (2025, 1): 0.3972,
    (2025, 5): 0.3972,
    (2025, 9): 0.3972,
}


# --- 3. วันหยุดสำหรับอัตรา TOU ---
# ที่มา: ประกาศวันหยุดราชการประจำปีโดยคณะรัฐมนตรี
# **สำคัญ**: ควรตรวจสอบและอัปเดตทุกปี โดยเฉพาะวันหยุดชดเชยและวันหยุดพิเศษ

# วันหยุดปี 2024 (รวมวันหยุดสุดสัปดาห์และวันหยุดนักขัตฤกษ์)
HOLIDAYS_TOU_2024_STR = sorted(list(set([
    "2024-01-01", "2024-02-24", "2024-02-26", "2024-04-06", "2024-04-08",
    "2024-04-13", "2024-04-14", "2024-04-15", "2024-04-16", "2024-05-01",
    "2024-05-04", "2024-05-06", "2024-05-22", "2024-06-03", "2024-07-20",
    "2024-07-21", "2024-07-22", "2024-07-28", "2024-07-29", "2024-08-12",
    "2024-10-13", "2024-10-14", "2024-10-23", "2024-12-05", "2024-12-10",
    "2024-12-31"
])))

# วันหยุดปี 2025 (รวมวันหยุดตามปฏิทิน และ **วันหยุดชดเชยที่คาดการณ์**) - **ควรตรวจสอบความถูกต้องอีกครั้งปลายปี 24**
HOLIDAYS_TOU_2025_STR = sorted(list(set([
    "2025-01-01", "2025-02-12", "2025-02-26", "2025-04-06", "2025-04-07",
    "2025-04-13", "2025-04-14", "2025-04-15", "2025-05-01", "2025-05-04",
    "2025-05-05", "2025-05-12", "2025-06-03", "2025-07-10", "2025-07-11",
    "2025-07-28", "2025-07-29", "2025-08-12", "2025-10-13", "2025-10-23",
    "2025-12-05", "2025-12-08", "2025-12-10", "2025-12-31"
])))

# ฟังก์ชันสร้างรายการวันหยุดทั้งหมด (รวมเสาร์-อาทิตย์)
def get_all_offpeak_days(year, official_holidays_str):
    """สร้าง Set ของวัน Off-Peak ทั้งหมดสำหรับปีที่กำหนด (วันหยุดนักขัตฤกษ์ + ทุกวันเสาร์-อาทิตย์)"""
    offpeak_days = set()
    # 1. เพิ่มวันหยุดนักขัตฤกษ์
    for d_str in official_holidays_str:
        try:
            offpeak_days.add(datetime.strptime(d_str, "%Y-%m-%d").date())
        except ValueError:
            st.warning(f"รูปแบบวันที่ไม่ถูกต้องในรายการวันหยุด: {d_str}")
            continue
    # 2. เพิ่มทุกวันเสาร์-อาทิตย์ของปี
    for month in range(1, 13):
        cal = calendar.monthcalendar(year, month)
        for week in cal:
            saturday, sunday = week[calendar.SATURDAY], week[calendar.SUNDAY]
            if saturday != 0:
                offpeak_days.add(date(year, month, saturday))
            if sunday != 0:
                offpeak_days.add(date(year, month, sunday))
    return offpeak_days

HOLIDAYS_TOU_DATA = {
    2024: get_all_offpeak_days(2024, HOLIDAYS_TOU_2024_STR),
    2025: get_all_offpeak_days(2025, HOLIDAYS_TOU_2025_STR),
}

# --- 4. ค่าคงที่อื่นๆ ---
VAT_RATE = 0.07
PEAK_START = time(9, 0, 0)
PEAK_END = time(21, 59, 59) # 9:00:00 ถึง 21:59:59 คือ Peak
MONTH_NAMES_TH = {1: "มกราคม", 2: "กุมภาพันธ์", 3: "มีนาคม", 4: "เมษายน",
                  5: "พฤษภาคม", 6: "มิถุนายน", 7: "กรกฎาคม", 8: "สิงหาคม",
                  9: "กันยายน", 10: "ตุลาคม", 11: "พฤศจิกายน", 12: "ธันวาคม"}
HOURS = [f"{h:02d}" for h in range(24)]
MINUTES = ["00", "15", "30", "45"]

# ==============================================================================
# --- ฟังก์ชัน Helper ---
# ==============================================================================

# @st.cache_data # Cache เพื่อเพิ่มความเร็วในการโหลดไฟล์เดิมซ้ำ
def parse_data_file(uploaded_file):
    """
    อ่านและประมวลผลไฟล์ข้อมูล Load Profile ที่อัปโหลดผ่าน Streamlit
    พยายามตรวจจับ Encoding, Delimiter, และรูปแบบวันที่โดยอัตโนมัติ
    """
    df_final = None
    file_content_string = ""
    detected_encoding = None
    detected_delimiter = None
    first_line = ""

    # 1. อ่านเนื้อหาไฟล์และตรวจจับ Encoding
    encodings_to_try = ['utf-8', 'cp874', 'tis-620']
    for enc in encodings_to_try:
        try:
            uploaded_file.seek(0)
            bytes_content = uploaded_file.getvalue()
            file_content_string = bytes_content.decode(enc)
            detected_encoding = enc
            first_line = file_content_string.splitlines()[0].strip() if file_content_string else ""
            break
        except (UnicodeDecodeError, IndexError):
            continue
    
    if not detected_encoding or not first_line:
        raise ValueError("ไม่สามารถอ่านไฟล์ได้ หรือไฟล์ว่างเปล่า")

    # 2. ตรวจจับตัวคั่น (Tab หรือ Comma)
    if '\t' in first_line:
        detected_delimiter = '\t'
    elif ',' in first_line:
        detected_delimiter = ','
    else:
        raise ValueError(f"ไม่พบตัวคั่นที่รองรับ (Tab หรือ Comma) ในบรรทัดแรก")

    data_io = io.StringIO(file_content_string)

    try:
        # 3. จัดการรูปแบบ Tab-Separated (ตามรูปแบบเฉพาะ)
        if detected_delimiter == '\t':
            if "DateTime\tTotal import kW demand" in first_line:
                df = pd.read_csv(data_io, sep='\t', header=0, skipinitialspace=True, low_memory=False)
                df.columns = df.columns.str.strip()
                required_cols = ['DateTime', 'Total import kW demand']
                if not all(col in df.columns for col in required_cols):
                    raise ValueError(f"ไฟล์ Tab ต้องมีคอลัมน์: {', '.join(required_cols)}")
                
                df['DateTime_parsed'] = pd.to_datetime(df['DateTime'], dayfirst=True, errors='coerce')
                df['Demand_parsed'] = pd.to_numeric(df['Total import kW demand'], errors='coerce')
                
                df_final = df.dropna(subset=['DateTime_parsed', 'Demand_parsed']) \
                             .rename(columns={'DateTime_parsed': 'DateTime', 'Demand_parsed': 'Total import kW demand'}) \
                             [['DateTime', 'Total import kW demand']].copy()
            else:
                raise ValueError("ไฟล์ Tab-separated แต่ Header ไม่ตรงกับรูปแบบที่คาดหวัง")

        # 4. จัดการรูปแบบ Comma-Separated
        elif detected_delimiter == ',':
            df_check = pd.read_csv(io.StringIO(file_content_string), sep=',', header=None, skipinitialspace=True, nrows=10, low_memory=False)
            num_cols = df_check.shape[1]
            
            datetime_col_idx = 1
            demand_col_idx = 3

            if num_cols <= max(datetime_col_idx, demand_col_idx):
                raise ValueError(f"ไฟล์ CSV มี {num_cols} คอลัมน์ ไม่เพียงพอสำหรับข้อมูล (ต้องการอย่างน้อย {max(datetime_col_idx, demand_col_idx)+1} คอลัมน์)")

            # อ่านไฟล์เต็มอีกครั้ง (พยายามเดาว่ามี header หรือไม่)
            try:
                first_row_values = df_check.iloc[0].astype(str).tolist()
                has_text = any(any(c.isalpha() for c in str(item)) for item in first_row_values[:4])
                header_setting = 0 if has_text else None
            except:
                header_setting = None

            data_io.seek(0)
            df = pd.read_csv(data_io, sep=',', header=header_setting, skipinitialspace=True, low_memory=False)

            # แปลง DateTime
            dt_str_series = df.iloc[:, datetime_col_idx].astype(str).str.strip()
            # เดา dayfirst
            dayfirst_guess = False
            potential_dates = dt_str_series[dt_str_series.str.contains(r'[\/\-:]', regex=True, na=False)].head(20)
            for s in potential_dates:
                if '/' in s:
                    try:
                        day_part = int(s.split(' ')[0].split('/')[0])
                        if day_part > 12:
                            dayfirst_guess = True
                            break
                    except: continue
            
            dt_series = pd.to_datetime(dt_str_series, dayfirst=dayfirst_guess, errors='coerce')
            if dt_series.isnull().sum() > len(df) * 0.9: # ถ้าล้มเหลวเยอะ ลองสลับ
                dt_series_alt = pd.to_datetime(dt_str_series, dayfirst=(not dayfirst_guess), errors='coerce')
                if dt_series_alt.isnull().sum() < dt_series.isnull().sum():
                    dt_series = dt_series_alt

            if dt_series.isnull().all():
                raise ValueError(f"ไม่สามารถแปลงค่าในคอลัมน์ที่ {datetime_col_idx+1} เป็น DateTime ได้เลย")
            
            # แปลง Demand และจัดการหน่วย
            demand_series_numeric = pd.to_numeric(df.iloc[:, demand_col_idx], errors='coerce')
            if demand_series_numeric.isnull().all():
                raise ValueError(f"ไม่สามารถแปลงค่าในคอลัมน์ที่ {demand_col_idx+1} เป็นตัวเลข (Demand) ได้เลย")

            # สันนิษฐานหน่วยจากจำนวนคอลัมน์
            if num_cols >= 8: # เช่น PRECISE, KY (หน่วยเป็น W)
                demand_series_kw = demand_series_numeric / 1000.0
                st.info("ℹ️ สันนิษฐานว่าหน่วย Demand เป็น Watt (W), จึงหารด้วย 1000 เพื่อแปลงเป็น kW")
            else: # กรณีอื่นๆ (สันนิษฐานว่าเป็น kW)
                demand_series_kw = demand_series_numeric
                st.info("ℹ️ สันนิษฐานว่าหน่วย Demand เป็น Kilowatt (kW)")

            df_temp = pd.DataFrame({'DateTime': dt_series, 'Total import kW demand': demand_series_kw})
            df_final = df_temp.dropna(subset=['DateTime', 'Total import kW demand']).copy()

        if df_final is None or df_final.empty:
            raise ValueError("ไม่พบข้อมูลที่ถูกต้องในไฟล์หลังการประมวลผล")

        df_final['DateTime'] = pd.to_datetime(df_final['DateTime'])
        df_final['Total import kW demand'] = pd.to_numeric(df_final['Total import kW demand'])
        df_final = df_final.sort_values(by='DateTime').reset_index(drop=True)

        st.success(f"ประมวลผลข้อมูลสำเร็จ: พบ {len(df_final)} รายการที่ถูกต้อง")
        return df_final

    except Exception as e:
        st.error(f"Traceback: {traceback.format_exc()}")
        raise ValueError(f"เกิดข้อผิดพลาดขณะประมวลผลข้อมูลด้วย Pandas: {e}")


def classify_tou_period(dt_obj):
    """จำแนกช่วงเวลา Peak/Off-Peak สำหรับอัตรา TOU"""
    if not isinstance(dt_obj, datetime): return 'Unknown'
    current_date = dt_obj.date()
    current_time = dt_obj.time()

    year_holidays = HOLIDAYS_TOU_DATA.get(current_date.year)
    if year_holidays is None:
        if current_date.year not in st.session_state.get('missing_holiday_years', set()):
            st.warning(f"ไม่พบข้อมูลวันหยุด TOU สำหรับปี {current_date.year} ในระบบ การคำนวณอาจไม่ถูกต้อง")
            if 'missing_holiday_years' not in st.session_state: st.session_state.missing_holiday_years = set()
            st.session_state.missing_holiday_years.add(current_date.year)
        # ถ้าไม่มีข้อมูลวันหยุด ให้ถือว่าวันนั้นเป็นวันทำงานปกติ
        if PEAK_START <= current_time <= PEAK_END:
            return 'Peak'
        else:
            return 'Off-Peak'

    # ถ้ามีข้อมูลวันหยุด ให้ตรวจสอบ
    if current_date in year_holidays:
        return 'Off-Peak'
    
    # วันทำงานปกติ
    if PEAK_START <= current_time <= PEAK_END:
        return 'Peak'
    else:
        return 'Off-Peak'


def get_ft_rate(date_in_period):
    """หาอัตรา Ft ที่เหมาะสมสำหรับวันที่ที่กำหนด"""
    if isinstance(date_in_period, datetime):
        date_in_period = date_in_period.date()
    elif not isinstance(date_in_period, date):
        date_in_period = datetime.now().date()

    sorted_ft_periods = sorted(FT_RATES.keys(), reverse=True)
    for start_year, start_month in sorted_ft_periods:
        ft_period_start_date = date(start_year, start_month, 1)
        if date_in_period >= ft_period_start_date:
            return FT_RATES[(start_year, start_month)]
    
    st.warning(f"ไม่พบอัตรา Ft สำหรับช่วงเวลา {date_in_period} หรือเก่ากว่า, ใช้ค่า Ft=0.0")
    return 0.0


def calculate_bill(df_processed, customer_type, tariff_type):
    """คำนวณค่าไฟฟ้าจาก DataFrame ที่ประมวลผลแล้ว"""
    if df_processed is None or df_processed.empty:
        return {"error": "ไม่มีข้อมูลสำหรับคำนวณ"}

    total_kwh = df_processed['kWh'].sum()
    data_period_end_dt = df_processed['DateTime'].iloc[-1]
    
    # --- คำนวณ Peak/Off-peak (ถ้าเป็น TOU) ---
    kwh_peak, kwh_off_peak = 0.0, 0.0
    if tariff_type == 'tou':
        df_processed['TOU_Period'] = df_processed['DateTime'].apply(classify_tou_period)
        kwh_summary = df_processed.groupby('TOU_Period')['kWh'].sum()
        kwh_peak = kwh_summary.get('Peak', 0.0)
        kwh_off_peak = kwh_summary.get('Off-Peak', 0.0) + kwh_summary.get('Unknown', 0.0)

    # --- เลือกโครงสร้างอัตรา ---
    try:
        if customer_type == "residential":
            tariff_key = "tou" if tariff_type == "tou" else ("normal_le_150" if total_kwh <= 150 else "normal_gt_150")
            rate_structure = TARIFFS["residential"][tariff_key]
        elif customer_type == "smb":
            rate_structure = TARIFFS["smb"][tariff_type]
        else: raise ValueError("ประเภทผู้ใช้ไม่ถูกต้อง")
    except KeyError as e:
        return {"error": f"ไม่พบโครงสร้างอัตราค่าไฟฟ้าสำหรับ: {e}"}

    # --- คำนวณค่าพลังงานไฟฟ้าฐาน ---
    base_energy_cost = 0.0
    if rate_structure['type'] == 'tiered':
        last_limit = 0
        for tier in rate_structure['tiers']:
            limit, rate = tier['limit'], tier['rate']
            units_in_tier = max(0, min(total_kwh, limit) - last_limit)
            base_energy_cost += units_in_tier * rate
            last_limit = limit
            if total_kwh <= limit: break
    elif rate_structure['type'] == 'tou':
        base_energy_cost = (kwh_peak * rate_structure['peak_rate']) + (kwh_off_peak * rate_structure['off_peak_rate'])

    # --- คำนวณส่วนที่เหลือ ---
    service_charge = rate_structure['service_charge']
    applicable_ft_rate = get_ft_rate(data_period_end_dt)
    ft_cost = total_kwh * applicable_ft_rate
    total_before_vat = base_energy_cost + service_charge + ft_cost
    vat_amount = total_before_vat * VAT_RATE
    final_bill = total_before_vat + vat_amount

    # --- จัดเตรียมผลลัพธ์ ---
    result = {
        "data_period_start": df_processed['DateTime'].iloc[0].strftime('%Y-%m-%d %H:%M'),
        "data_period_end": data_period_end_dt.strftime('%Y-%m-%d %H:%M'),
        "data_year": data_period_end_dt.year,
        "total_kwh": total_kwh,
        "kwh_peak": kwh_peak if tariff_type == 'tou' else None,
        "kwh_off_peak": kwh_off_peak if tariff_type == 'tou' else None,
        "base_energy_cost": base_energy_cost,
        "service_charge": service_charge,
        "applicable_ft_rate": applicable_ft_rate,
        "ft_cost": ft_cost,
        "total_before_vat": total_before_vat,
        "vat_amount": vat_amount,
        "final_bill": final_bill,
        "error": None
    }
    return result

# ==============================================================================
# --- Streamlit App ---
# ==============================================================================
st.set_page_config(page_title="คำนวณค่าไฟฟ้า", layout="wide")
st.title("📊 โปรแกรมคำนวณและจำลองค่าไฟฟ้า")
st.markdown("อัปโหลดไฟล์ Load Profile (.txt, .csv) เพื่อคำนวณค่าไฟโดยประมาณ และจำลองการใช้งาน EV Charger")

# --- Session State Initialization ---
if 'full_dataframe' not in st.session_state: st.session_state.full_dataframe = None
if 'last_uploaded_filename' not in st.session_state: st.session_state.last_uploaded_filename = None
if 'calculation_result' not in st.session_state: st.session_state.calculation_result = None
if 'calculation_details_text' not in st.session_state: st.session_state.calculation_details_text = ""

# --- 1. ส่วนอัปโหลดไฟล์ ---
st.header("1. อัปโหลดไฟล์ข้อมูล Load Profile")
uploaded_file = st.file_uploader("เลือกไฟล์ (.txt หรือ .csv)", type=['txt', 'csv'], key="file_uploader")

if uploaded_file is not None:
    if uploaded_file.name != st.session_state.last_uploaded_filename:
        st.info(f"กำลังประมวลผลไฟล์ใหม่: {uploaded_file.name}...")
        try:
            with st.spinner('กำลังอ่านและประมวลผลข้อมูล...'):
                # Reset states
                for key in ['full_dataframe', 'calculation_result', 'missing_holiday_years']:
                    if key in st.session_state: del st.session_state[key]
                
                df_parsed = parse_data_file(uploaded_file)
                st.session_state.full_dataframe = df_parsed
                st.session_state.last_uploaded_filename = uploaded_file.name
        except ValueError as ve:
            st.error(f"ข้อผิดพลาดในการประมวลผลไฟล์: {ve}")
            st.session_state.full_dataframe = None
            st.session_state.last_uploaded_filename = None

# --- 2. ส่วนตั้งค่าการคำนวณ ---
if st.session_state.get('full_dataframe') is not None:
    st.markdown("---")
    st.header("2. ตั้งค่าการคำนวณ")

    df_full = st.session_state.full_dataframe
    available_years = sorted(df_full['DateTime'].dt.year.unique())
    available_months_num = sorted(df_full['DateTime'].dt.month.unique())
    available_months_th = [MONTH_NAMES_TH.get(m, str(m)) for m in available_months_num]

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_customer = st.selectbox("ประเภทผู้ใช้:", ["บ้านอยู่อาศัย", "กิจการขนาดเล็ก"], key="customer_type")
        selected_tariff = st.selectbox("ประเภทอัตรา:", ["อัตราปกติ", "อัตรา TOU"], key="tariff_type")
    with col2:
        selected_year = st.selectbox("เลือกปี:", ["ทั้งหมด"] + available_years, key="year")
        selected_month = st.selectbox("เลือกเดือน:", ["ทั้งหมด"] + available_months_th, key="month")
    with col3:
        st.write("จำลอง EV Charger")
        ev_enabled = st.checkbox("เปิดใช้งาน", key="ev_enabled")
        ev_power_kw = st.number_input("กำลังไฟ (kW):", min_value=0.1, max_value=50.0, value=7.0, step=0.1, key="ev_power", disabled=not ev_enabled)

    # EV Time settings
    with st.expander("ตั้งเวลาชาร์จ EV", expanded=ev_enabled):
        ev_col1, ev_col2, _ = st.columns([1,1,2])
        with ev_col1:
            ev_start_time = st.time_input("เวลาเริ่มชาร์จ", time(22, 0), key="ev_start_time", disabled=not ev_enabled)
        with ev_col2:
            ev_end_time = st.time_input("เวลาสิ้นสุดชาร์จ", time(5, 0), key="ev_end_time", disabled=not ev_enabled)

    st.markdown("---")

    # --- ปุ่มคำนวณ ---
    if st.button("คำนวณค่าไฟ", type="primary", key="calculate_button"):
        st.session_state.calculation_result = None
        st.session_state.calculation_details_text = ""
        with st.spinner("กำลังคำนวณ..."):
            try:
                # --- 1. กรองข้อมูลตามปีและเดือน ---
                df_filtered = df_full.copy()
                if selected_year != "ทั้งหมด":
                    df_filtered = df_filtered[df_filtered['DateTime'].dt.year == selected_year]
                if selected_month != "ทั้งหมด":
                    month_num = next((num for num, name in MONTH_NAMES_TH.items() if name == selected_month), None)
                    if month_num:
                        df_filtered = df_filtered[df_filtered['DateTime'].dt.month == month_num]
                
                if df_filtered.empty:
                    st.warning(f"ไม่พบข้อมูลสำหรับช่วงเวลาที่เลือก")
                else:
                    # --- 2. จัดการการจำลอง EV Charger ---
                    if ev_enabled:
                        time_series = df_filtered['DateTime'].dt.time
                        if ev_start_time <= ev_end_time: # ไม่ข้ามคืน
                            charging_mask = (time_series >= ev_start_time) & (time_series < ev_end_time)
                        else: # ข้ามคืน
                            charging_mask = (time_series >= ev_start_time) | (time_series < ev_end_time)
                        df_filtered.loc[charging_mask, 'Total import kW demand'] += ev_power_kw

                    # --- 3. คำนวณ kWh (พร้อมตรวจจับ Interval อัตโนมัติ) ---
                    if len(df_filtered) > 1:
                        time_diff = df_filtered['DateTime'].iloc[1] - df_filtered['DateTime'].iloc[0]
                        interval_hours = time_diff.total_seconds() / 3600.0
                        if not (0 < interval_hours <= 24): interval_hours = 0.25 # Fallback
                    else:
                        interval_hours = 0.25 # Fallback
                    
                    df_filtered['kWh'] = df_filtered['Total import kW demand'] * interval_hours

                    # --- 4. เรียกฟังก์ชันคำนวณค่าไฟ ---
                    customer_key = "residential" if selected_customer == "บ้านอยู่อาศัย" else "smb"
                    tariff_key = "normal" if selected_tariff == "อัตราปกติ" else "tou"
                    bill_details = calculate_bill(df_filtered, customer_key, tariff_key)

                    # --- 5. เก็บผลลัพธ์ ---
                    st.session_state.calculation_result = bill_details
                    
                    # สร้างข้อความสำหรับแสดงรายละเอียด
                    period_str = f"{selected_month} {selected_year}" if selected_year != "ทั้งหมด" and selected_month != "ทั้งหมด" else "ช่วงเวลาที่เลือก"
                    output = [f"--- ผลการคำนวณค่าไฟฟ้า ({period_str}) ---"]
                    output.append(f"ประเภทผู้ใช้: {selected_customer}, อัตรา: {selected_tariff}")
                    if ev_enabled:
                         output.append(f"จำลอง EV Charger: {ev_power_kw:.2f} kW ({ev_start_time.strftime('%H:%M')} - {ev_end_time.strftime('%H:%M')})")
                    output.append(f"ช่วงข้อมูล: {bill_details['data_period_start']} ถึง {bill_details['data_period_end']}")
                    output.append("-" * 40)
                    output.append(f"ยอดใช้ไฟรวม: {bill_details['total_kwh']:,.2f} kWh")
                    if tariff_key == 'tou':
                        output.append(f"  - Peak: {bill_details['kwh_peak']:,.2f} kWh")
                        output.append(f"  - Off-Peak: {bill_details['kwh_off_peak']:,.2f} kWh")
                    output.append("-" * 40)
                    output.append(f"{'ค่าพลังงานไฟฟ้า':<25}: {bill_details['base_energy_cost']:>12,.2f} บาท")
                    output.append(f"{'ค่าบริการรายเดือน':<25}: {bill_details['service_charge']:>12,.2f} บาท")
                    output.append(f"{f'ค่า Ft (@{bill_details['applicable_ft_rate']:.4f})':<25}: {bill_details['ft_cost']:>12,.2f} บาท")
                    output.append("-" * 40)
                    output.append(f"{'ยอดรวมก่อน VAT':<25}: {bill_details['total_before_vat']:>12,.2f} บาท")
                    output.append(f"{f'ภาษีมูลค่าเพิ่ม ({VAT_RATE*100:.0f}%)':<25}: {bill_details['vat_amount']:>12,.2f} บาท")
                    output.append("=" * 40)
                    output.append(f"{'**ยอดค่าไฟฟ้าสุทธิ**':<25}: {bill_details['final_bill']:>12,.2f} บาท")
                    output.append("=" * 40)
                    output.append(f"\nหมายเหตุ:")
                    output.append(f"- คำนวณจากข้อมูล {len(df_filtered)} รายการ (ตรวจพบช่วงห่าง ~{interval_hours*60:.0f} นาที/รายการ)")
                    output.append(f"- ใช้ค่า Ft และวันหยุด TOU ตามปีของข้อมูล ({bill_details['data_year']})")
                    
                    st.session_state.calculation_details_text = "\n".join(output)

            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดระหว่างการคำนวณ: {e}")
                st.error(f"Traceback: {traceback.format_exc()}")


# --- 3. ส่วนแสดงผลลัพธ์ ---
if st.session_state.get('calculation_result'):
    bill_details = st.session_state.calculation_result
    if bill_details.get("error"):
        st.error(f"เกิดข้อผิดพลาดในการคำนวณ: {bill_details['error']}")
    else:
        st.markdown("---")
        st.header("3. ผลการคำนวณ")
        
        # แสดงผลแบบ Metric
        res_col1, res_col2, res_col3 = st.columns(3)
        res_col1.metric("💰 ยอดค่าไฟฟ้าสุทธิ", f"{bill_details['final_bill']:,.2f} บาท")
        res_col2.metric("⚡️ ยอดใช้ไฟรวม", f"{bill_details['total_kwh']:,.2f} kWh")
        res_col3.metric("🔥 อัตรา Ft ที่ใช้", f"{bill_details['applicable_ft_rate']:.4f}")

        # แสดงรายละเอียดใน Expander
        with st.expander("📄 ดูรายละเอียดการคำนวณและดาวน์โหลด"):
            st.code(st.session_state.calculation_details_text, language=None)
            st.download_button(
                label="📥 ดาวน์โหลดผลลัพธ์ (.txt)",
                data=st.session_state.calculation_details_text.encode('utf-8'),
                file_name=f"bill_result_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime='text/plain'
            )

        # --- ส่วนแสดงกราฟ ---
        st.subheader("กราฟ Load Profile (kW Demand)")
        try:
            # ดึงข้อมูลที่ผ่านการกรองและอาจมีการเพิ่มโหลด EV แล้ว
            df_to_plot = st.session_state.get('df_for_plotting', pd.DataFrame()) # จะต้องส่ง df_filtered มาเก็บใน state
            
            # --- แก้ไข: ต้องกรองข้อมูลอีกครั้งสำหรับพล็อตกราฟ ---
            df_filtered_plot = df_full.copy()
            if selected_year != "ทั้งหมด":
                df_filtered_plot = df_filtered_plot[df_filtered_plot['DateTime'].dt.year == selected_year]
            if selected_month != "ทั้งหมด":
                month_num = next((num for num, name in MONTH_NAMES_TH.items() if name == selected_month), None)
                if month_num:
                    df_filtered_plot = df_filtered_plot[df_filtered_plot['DateTime'].dt.month == month_num]
            
            if not df_filtered_plot.empty:
                df_original_plot = df_filtered_plot.set_index('DateTime')
                
                # ถ้าเปิด EV ให้สร้างกราฟเปรียบเทียบ
                if ev_enabled:
                    df_with_ev_plot = df_filtered_plot.copy()
                    time_series = df_with_ev_plot['DateTime'].dt.time
                    if ev_start_time <= ev_end_time: # ไม่ข้ามคืน
                        charging_mask = (time_series >= ev_start_time) & (time_series < ev_end_time)
                    else: # ข้ามคืน
                        charging_mask = (time_series >= ev_start_time) | (time_series < ev_end_time)
                    df_with_ev_plot.loc[charging_mask, 'Total import kW demand'] += ev_power_kw
                    
                    df_with_ev_plot = df_with_ev_plot.set_index('DateTime')
                    
                    # รวม DataFrame เพื่อพล็อต
                    df_plot_combined = pd.DataFrame({
                        'Original Demand': df_original_plot['Total import kW demand'],
                        'Demand with EV': df_with_ev_plot['Total import kW demand']
                    })
                    st.line_chart(df_plot_combined)
                    st.caption("กราฟเปรียบเทียบการใช้พลังงาน (kW) ก่อนและหลังจำลอง EV")
                else:
                    st.line_chart(df_original_plot['Total import kW demand'])
                    st.caption("กราฟแสดงการใช้พลังงาน (kW) ตามช่วงเวลาที่เลือก")
            else:
                 st.warning("ไม่พบข้อมูลสำหรับสร้างกราฟในช่วงเวลาที่เลือก")

        except Exception as plot_ex:
            st.error(f"ไม่สามารถสร้างกราฟได้: {plot_ex}")
