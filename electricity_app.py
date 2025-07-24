# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import io
from datetime import datetime, time, date
import calendar
import traceback

# ==============================================================================
# --- ค่าคงที่และข้อมูลอัตรา (CONFIGURATIONS) ---
# ==============================================================================

# 1. อัตราค่าไฟฟ้า (Tariffs)
TARIFFS = {
    "residential": {
        "normal": {'service_charge': 24.62, 'type': 'tiered', 'tiers': [{'limit': 150, 'rate': 3.2484}, {'limit': 400, 'rate': 4.2218}, {'limit': float('inf'), 'rate': 4.4217}]},
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
    if uploaded_file is None:
        return None
    
    df_final = None
    try:
        if file_type in ['BLE-iMeter', 'IPG']:
            file_content_string = ""
            encodings_to_try = ['utf-8', 'cp874', 'tis-620']
            for enc in encodings_to_try:
                try:
                    uploaded_file.seek(0)
                    file_content_string = uploaded_file.getvalue().decode(enc)
                    break
                except (UnicodeDecodeError, IndexError):
                    continue
            if not file_content_string: raise ValueError("ไม่สามารถอ่านไฟล์ได้ หรือไฟล์ว่างเปล่า")
            data_io = io.StringIO(file_content_string)

            if file_type == 'BLE-iMeter':
                df = pd.read_csv(data_io, sep=',', header=None, low_memory=False)
                if df.shape[1] < 4: raise ValueError(f"ไฟล์ BLE-iMeter CSV มี {df.shape[1]} คอลัมน์ ไม่เพียงพอ")
                df['DateTime'] = pd.to_datetime(df.iloc[:, 1], errors='coerce')
                df['Total import kW demand'] = pd.to_numeric(df.iloc[:, 3], errors='coerce') / 1000.0
                st.info("ℹ️ หน่วย Demand ในไฟล์ BLE-iMeter เป็น Watt (W), แปลงเป็น kW โดยการหาร 1000")
            
            elif file_type == 'IPG':
                df = pd.read_csv(data_io, sep='\t', header=0, skipinitialspace=True, low_memory=False)
                df.columns = df.columns.str.strip()
                if not all(col in df.columns for col in ['DateTime', 'Total import kW demand']):
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
                df['DateTime_Corrected'] = df['DateTime'].apply(correct_buddhist_year)
                df['DateTime'] = pd.to_datetime(df['DateTime_Corrected'], errors='coerce')
                df['Total import kW demand'] = pd.to_numeric(df['Total import kW demand'], errors='coerce')
                st.info("ℹ️ หน่วย Demand ในไฟล์ IPG เป็น Kilowatt (kW)")

        elif file_type == 'Excel':
            # หมายเหตุ: หากไฟล์ Excel ของคุณมีชื่อคอลัมน์ต่างไป ให้แก้ไขที่นี่
            datetime_col_name = 'DateTime'
            demand_col_name = 'Total import kW demand'
            
            # ใช้ openpyxl engine สำหรับ .xlsx
            df = pd.read_excel(uploaded_file, engine='openpyxl')

            if datetime_col_name not in df.columns or demand_col_name not in df.columns:
                raise ValueError(f"ไฟล์ Excel ต้องมีคอลัมน์ชื่อ '{datetime_col_name}' และ '{demand_col_name}'")

            df['DateTime'] = pd.to_datetime(df[datetime_col_name], errors='coerce')
            df['Total import kW demand'] = pd.to_numeric(df[demand_col_name], errors='coerce')
            st.info("ℹ️ สันนิษฐานว่าหน่วย Demand ในไฟล์ Excel เป็น Kilowatt (kW)")

        df_final = df.dropna(subset=['DateTime', 'Total import kW demand'])[['DateTime', 'Total import kW demand']].copy()
        if df_final.empty: raise ValueError("ไม่พบข้อมูลที่ถูกต้องในไฟล์หลังการประมวลผล")
        return df_final.sort_values(by='DateTime').reset_index(drop=True)

    except Exception as e:
        raise ValueError(f"เกิดข้อผิดพลาดขณะประมวลผลข้อมูล: {e}")

def calculate_bill(df_processed, customer_type_key, tariff_type_key):
    # ... (โค้ดส่วนนี้ไม่เปลี่ยนแปลง)
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
    service_charge = rate_structure['service_charge']; applicable_ft_rate = get_ft_rate(data_period_end_dt); ft_cost = total_kwh * applicable_ft_rate
    total_before_vat = base_energy_cost + service_charge + ft_cost; vat_amount = total_before_vat * VAT_RATE; final_bill = total_before_vat + vat_amount
    return {"total_kwh": total_kwh, "final_bill": final_bill, "base_energy_cost": base_energy_cost, "service_charge": service_charge, "ft_cost": ft_cost, "total_before_vat": total_before_vat, "vat_amount": vat_amount, "applicable_ft_rate": applicable_ft_rate, "kwh_peak": kwh_peak if tariff_type_key == 'tou' else None, "kwh_off_peak": kwh_off_peak if tariff_type_key == 'tou' else None, "data_period_start": df_processed['DateTime'].iloc[0].strftime('%Y-%m-%d %H:%M'), "data_period_end": data_period_end_dt.strftime('%Y-%m-%d %H:%M'), "error": None}

def get_ft_rate(date_in_period):
    # ... (โค้ดส่วนนี้ไม่เปลี่ยนแปลง)
    d = date_in_period.date() if isinstance(date_in_period, datetime) else date_in_period
    sorted_ft_periods = sorted(FT_RATES.keys(), reverse=True)
    for start_year, start_month in sorted_ft_periods:
        if d >= date(start_year, start_month, 1): return FT_RATES[(start_year, start_month)]
    st.warning(f"ไม่พบอัตรา Ft สำหรับ {d}, ใช้ค่า Ft=0.0"); return 0.0

def classify_tou_period(dt_obj):
    # ... (โค้ดส่วนนี้ไม่เปลี่ยนแปลง)
    if not isinstance(dt_obj, datetime): return 'Unknown'
    current_date = dt_obj.date(); current_time = dt_obj.time()
    year_holidays = HOLIDAYS_TOU_DATA.get(current_date.year)
    if year_holidays is None:
        if current_date.year not in st.session_state.get('missing_holiday_years', set()):
            st.warning(f"ไม่พบข้อมูลวันหยุด TOU ปี {current_date.year}"); st.session_state.setdefault('missing_holiday_years', set()).add(current_date.year)
        return 'Peak' if PEAK_START <= current_time <= PEAK_END else 'Off-Peak'
    if current_date in year_holidays: return 'Off-Peak'
    return 'Peak' if PEAK_START <= current_time <= PEAK_END else 'Off-Peak'

# ==============================================================================
# --- Streamlit App ---
# ==============================================================================
st.set_page_config(page_title="คำนวณค่าไฟฟ้า", layout="wide")
st.title("📊 โปรแกรมคำนวณและจำลองค่าไฟฟ้า")

for key in ['full_dataframe', 'last_uploaded_filename', 'calculation_result', 'ev_cost', 'base_kwh', 'ev_kwh']:
    if key not in st.session_state: st.session_state[key] = None

st.header("1. เลือกประเภทและอัปโหลดไฟล์ข้อมูล")
selected_file_type = st.radio(
    "เลือกประเภทไฟล์ข้อมูล (Load Profile):",
    ("BLE-iMeter", "IPG", "Excel"),
    horizontal=True, key="data_file_type"
)

file_types = ['txt'] if selected_file_type != 'Excel' else ['xlsx']
uploaded_file = st.file_uploader(f"เลือกไฟล์ ({', '.join(file_types)})", type=file_types, key="file_uploader")

if uploaded_file and (uploaded_file.name != st.session_state.get('last_uploaded_filename') or selected_file_type != st.session_state.get('last_file_type')):
    with st.spinner('กำลังประมวลผลไฟล์...'):
        try:
            st.session_state.full_dataframe = parse_data_file(uploaded_file, selected_file_type)
            st.session_state.last_uploaded_filename = uploaded_file.name
            st.session_state.last_file_type = selected_file_type
            st.success(f"ประมวลผลไฟล์ '{uploaded_file.name}' สำเร็จ")
        except ValueError as ve:
            st.error(f"ข้อผิดพลาด: {ve}"); st.session_state.full_dataframe = None

if st.session_state.get('full_dataframe') is not None:
    st.divider(); st.header("2. ตั้งค่าการคำนวณ")
    df_full = st.session_state.full_dataframe
    min_date = df_full['DateTime'].min().date(); max_date = df_full['DateTime'].max().date()
    
    col1, col2 = st.columns([1, 2])
    with col1:
        customer_label = st.selectbox("ประเภทผู้ใช้:", ["บ้านอยู่อาศัย", "กิจการขนาดเล็ก"], key="customer_type_label")
        customer_key = "residential"
        if customer_label == "กิจการขนาดเล็ก":
            voltage_label = st.radio("ระดับแรงดันไฟฟ้า:", ("แรงดันต่ำกว่า 22 kV", "แรงดัน 22-33 kV"), key="voltage_level", horizontal=True)
            customer_key = "smb_lv" if voltage_label == "แรงดันต่ำกว่า 22 kV" else "smb_mv"
        tariff_type = st.selectbox("ประเภทอัตรา:", ["อัตราปกติ", "อัตรา TOU"], key="tariff_type")
        
    with col2:
        main_date_range = st.date_input("เลือกช่วงวันที่สำหรับคำนวณ", value=(min_date, max_date), min_value=min_date, max_value=max_date, key="main_date_range")

    with st.expander("🔌 จำลอง EV Charger (ตัวเลือกเพิ่มเติม)"):
        ev_enabled = st.checkbox("เปิดใช้งานการจำลอง EV", key="ev_enabled")
        if len(main_date_range) == 2:
            ev_start_range, ev_end_range = main_date_range
            ev_date_range = st.date_input("เลือกช่วงวันที่สำหรับชาร์จ EV", value=(ev_start_range, ev_end_range), min_value=ev_start_range, max_value=ev_end_range, key="ev_date_range", disabled=not ev_enabled)
        ev_col1, ev_col2, ev_col3 = st.columns(3)
        ev_power_kw = ev_col1.number_input("กำลังไฟ Charger (kW):", min_value=0.1, value=7.0, step=0.1, key="ev_power", disabled=not ev_enabled)
        ev_start_time = ev_col2.time_input("เวลาเริ่มชาร์จ", time(22, 0), key="ev_start_time", disabled=not ev_enabled)
        ev_end_time = ev_col3.time_input("เวลาสิ้นสุดชาร์จ", time(5, 0), key="ev_end_time", disabled=not ev_enabled)
    st.divider()

    if st.button("คำนวณค่าไฟ", type="primary"):
        st.session_state.calculation_result = None; st.session_state.ev_cost = None; st.session_state.base_kwh = None; st.session_state.ev_kwh = None
        if len(main_date_range) != 2: st.error("กรุณาเลือกวันเริ่มต้นและวันสิ้นสุด")
        else:
            main_start_date, main_end_date = main_date_range
            with st.spinner("กำลังคำนวณ..."):
                try:
                    mask = (df_full['DateTime'].dt.date >= main_start_date) & (df_full['DateTime'].dt.date <= main_end_date)
                    df_filtered = df_full[mask].copy()
                    if df_filtered.empty: st.warning("ไม่พบข้อมูลในช่วงวันที่ที่เลือก")
                    else:
                        tariff_key_str = "tou" if tariff_type == "อัตรา TOU" else "normal"
                        interval_hours = (df_filtered['DateTime'].iloc[1] - df_filtered['DateTime'].iloc[0]).total_seconds() / 3600.0 if len(df_filtered) > 1 else 0.25
                        if not (0 < interval_hours <= 24): interval_hours = 0.25
                        
                        df_base = df_filtered.copy(); df_base['kWh'] = df_base['Total import kW demand'] * interval_hours
                        base_bill_details = calculate_bill(df_base, customer_key, tariff_key_str)
                        st.session_state.base_kwh = base_bill_details['total_kwh']
                        
                        total_bill_details = base_bill_details
                        
                        if ev_enabled:
                            df_with_ev = df_filtered.copy()
                            time_series = df_with_ev['DateTime'].dt.time; date_series = df_with_ev['DateTime'].dt.date
                            ev_start_date_select, ev_end_date_select = st.session_state.ev_date_range
                            time_mask = (time_series >= ev_start_time) | (time_series < ev_end_time) if ev_start_time > ev_end_time else (time_series >= ev_start_time) & (time_series < ev_end_time)
                            date_mask = (date_series >= ev_start_date_select) & (date_series <= ev_end_date_select)
                            df_with_ev.loc[time_mask & date_mask, 'Total import kW demand'] += ev_power_kw
                            
                            df_with_ev['kWh'] = df_with_ev['Total import kW demand'] * interval_hours
                            total_bill_details = calculate_bill(df_with_ev, customer_key, tariff_key_str)
                            
                            st.session_state.ev_cost = total_bill_details['final_bill'] - base_bill_details['final_bill']
                            st.session_state.ev_kwh = total_bill_details['total_kwh'] - base_bill_details['total_kwh']
                            st.session_state.df_for_plotting = df_with_ev
                        else: st.session_state.df_for_plotting = df_base
                        st.session_state.calculation_result = total_bill_details
                except Exception as e: st.error(f"เกิดข้อผิดพลาด: {e}"); st.error(traceback.format_exc())

if st.session_state.calculation_result:
    # ... (โค้ดส่วนแสดงผลไม่เปลี่ยนแปลง)
    st.divider(); st.header("3. ผลการคำนวณ")
    bill = st.session_state.calculation_result; ev_cost = st.session_state.ev_cost; base_kwh = st.session_state.base_kwh; ev_kwh = st.session_state.ev_kwh
    if bill.get("error"): st.error(f"เกิดข้อผิดพลาด: {bill['error']}")
    else:
        is_ev_calculated = st.session_state.get('ev_enabled') and ev_cost is not None
        if is_ev_calculated:
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("💰 ยอดค่าไฟรวม", f"{bill['final_bill']:,.2f} บาท")
            m_col2.metric("🚗 ค่าไฟส่วน EV", f"{ev_cost:,.2f} บาท")
            m_col3.metric("🏠 หน่วยไฟบ้าน", f"{base_kwh:,.2f} kWh")
            m_col4.metric("🚗 หน่วยไฟ EV", f"{ev_kwh:,.2f} kWh")
        else:
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("💰 ยอดค่าไฟฟ้าสุทธิ", f"{bill['final_bill']:,.2f} บาท")
            m_col2.metric("⚡️ ยอดใช้ไฟรวม", f"{bill['total_kwh']:,.2f} kWh")
            m_col3.metric("🔥 อัตรา Ft ที่ใช้", f"{bill['applicable_ft_rate']:.4f}")

        with st.expander("📄 ดูรายละเอียดการคำนวณและดาวน์โหลด"):
            display_customer_label = st.session_state.customer_type_label
            if st.session_state.customer_type_label == "กิจการขนาดเล็ก":
                display_customer_label += f" ({st.session_state.voltage_level})"
            output = [
                "--- ผลการคำนวณค่าไฟฟ้า ---",
                f"ช่วงข้อมูล: {bill['data_period_start']} ถึง {bill['data_period_end']}",
                f"ประเภทผู้ใช้: {display_customer_label}, อัตรา: {st.session_state.tariff_type}",]
            if is_ev_calculated:
                ev_start_date_str = st.session_state.ev_date_range[0].strftime('%d/%m/%Y')
                ev_end_date_str = st.session_state.ev_date_range[1].strftime('%d/%m/%Y')
                output.append(f"จำลอง EV: {st.session_state.ev_power:.2f} kW ({st.session_state.ev_start_time.strftime('%H:%M')} - {st.session_state.ev_end_time.strftime('%H:%M')})")
                output.append(f"          (ช่วงวันที่ชาร์จ: {ev_start_date_str} - {ev_end_date_str})")
            
            output.extend(["-"*40, f"ยอดใช้ไฟรวม: {bill['total_kwh']:,.2f} kWh"])
            if is_ev_calculated: output.extend([f"  - หน่วยไฟบ้าน: {base_kwh:,.2f} kWh", f"  - หน่วยไฟ EV: {ev_kwh:,.2f} kWh"])
            if st.session_state.tariff_type == 'อัตรา TOU': output.extend([f"  - Peak: {bill['kwh_peak']:,.2f} kWh", f"  - Off-Peak: {bill['kwh_off_peak']:,.2f} kWh"])
            output.extend(["-"*40, f"{'ค่าพลังงานไฟฟ้า':<25}: {bill['base_energy_cost']:>12,.2f} บาท", f"{'ค่าบริการรายเดือน':<25}: {bill['service_charge']:>12,.2f} บาท", f"{f'ค่า Ft (@{bill['applicable_ft_rate']:.4f})':<25}: {bill['ft_cost']:>12,.2f} บาท", "-"*40, f"{'ยอดรวมก่อน VAT':<25}: {bill['total_before_vat']:>12,.2f} บาท", f"{f'ภาษีมูลค่าเพิ่ม ({VAT_RATE*100:.0f}%)':<25}: {bill['vat_amount']:>12,.2f} บาท", "="*40])
            if is_ev_calculated: output.extend([f"{'ค่าไฟบ้าน (ไม่รวม EV)':<25}: {bill['final_bill'] - ev_cost:>12,.2f} บาท", f"{'ค่าไฟส่วน EV':<25}: {ev_cost:>12,.2f} บาท", "="*40])
            output.append(f"{'**ยอดค่าไฟฟ้าสุทธิ**':<25}: {bill['final_bill']:>12,.2f} บาท")
            details_text = "\n".join(output)
            st.code(
