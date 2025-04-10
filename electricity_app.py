# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import io
from datetime import datetime, time, date
import calendar
import os
import traceback

# --- ค่าคงที่และข้อมูลอัตรา ---
# อัตราค่าไฟฟ้า (ควรตรวจสอบและอัปเดตตามประกาศล่าสุดของการไฟฟ้า)
TARIFFS = {
    "residential": {
        "normal_le_150": {'service_charge': 8.19, 'type': 'tiered', 'tiers': [{'limit': 15, 'rate': 2.3488}, {'limit': 25, 'rate': 2.9882}, {'limit': 35, 'rate': 3.2405}, {'limit': 100, 'rate': 3.6237}, {'limit': 150, 'rate': 3.7171}, {'limit': 400, 'rate': 4.2218}, {'limit': float('inf'), 'rate': 4.4217}]},
        "normal_gt_150": {'service_charge': 24.62, 'type': 'tiered', 'tiers': [{'limit': 150, 'rate': 3.2484}, {'limit': 400, 'rate': 4.2218}, {'limit': float('inf'), 'rate': 4.4217}]},
        "tou": {'service_charge': 24.62, 'type': 'tou', 'peak_rate': 5.7982, 'off_peak_rate': 2.6369} # อัปเดตอัตรา TOU หากมีการเปลี่ยนแปลง
    },
    "smb": {
        "normal": {'service_charge': 312.24, 'type': 'tiered', 'tiers': [{'limit': 150, 'rate': 3.2484}, {'limit': 400, 'rate': 4.2218}, {'limit': float('inf'), 'rate': 4.4217}]}, # อัปเดตอัตรา SMB หากมีการเปลี่ยนแปลง
        "tou": {'service_charge': 33.29, 'type': 'tou', 'peak_rate': 5.7982, 'off_peak_rate': 2.6369} # อัปเดตอัตรา TOU หากมีการเปลี่ยนแปลง
    }
}

# อัตราค่า Ft (ควรตรวจสอบและอัปเดตตามประกาศของ กกพ. ล่าสุด)
# ที่มา: https://www.erc.or.th/ (ตรวจสอบประกาศล่าสุด)
# ตัวอย่างนี้เป็นค่าสมมติและค่าในอดีต โปรดใช้ค่าที่ประกาศจริง
FT_RATES = {
    # (Year, Month) -> Rate per kWh
    # ค่าในอดีต (ตัวอย่าง)
    (2023, 1): 0.9343, (2023, 5): 0.9119, (2023, 9): 0.2048,
    # ค่าปี 2024 (ตัวอย่าง - อ้างอิงประกาศ ม.ค.-เม.ย. 67)
    # อาจมีเงื่อนไขเพิ่มเติมสำหรับบ้านอยู่อาศัยที่ใช้ไฟน้อยกว่า 300 หน่วย
    # โค้ดนี้ใช้ค่าทั่วไป โปรดตรวจสอบเงื่อนไขเฉพาะหากจำเป็น
    (2024, 1): 0.3972, # ม.ค.-เม.ย. 67
    (2024, 5): 0.3972, # พ.ค.-ส.ค. 67 (ตัวอย่าง, รอประกาศจริง) - ***ต้องอัปเดต***
    (2024, 9): 0.3972, # ก.ย.-ธ.ค. 67 (ตัวอย่าง, รอประกาศจริง) - ***ต้องอัปเดต***
    # ค่าปี 2025 (ตัวอย่าง, รอประกาศจริง) - ***ต้องอัปเดต***
    (2025, 1): 0.3672, # ม.ค.-เม.ย. 68 (ตัวอย่าง)
    (2025, 5): 0.3672, # พ.ค.-ส.ค. 68 (ตัวอย่าง)
    (2025, 9): 0.3672, # ก.ย.-ธ.ค. 68 (ตัวอย่าง)
}


# --- วันหยุด TOU ---
# ควรตรวจสอบและอัปเดตตามประกาศวันหยุดราชการประจำปี หรือวันหยุดพิเศษอื่นๆ
# ที่มา: ประกาศคณะรัฐมนตรี (ตรวจสอบปีล่าสุด)
HOLIDAYS_TOU_2024_STR = ["2024-01-01","2024-01-06","2024-01-07","2024-01-13","2024-01-14","2024-01-20","2024-01-21", 
                         "2024-01-27","2024-01-28","2024-02-03","2024-02-04","2024-02-10","2024-02-11","2024-02-17",
                         "2024-02-18","2024-02-24","2024-02-25","2024-03-02","2024-03-03","2024-03-09","2024-03-10",
                         "2024-03-16","2024-03-17","2024-03-23","2024-03-24","2024-03-30","2024-03-31","2024-04-06",
                         "2024-04-07","2024-04-13","2024-04-14","2024-04-15","2024-04-20","2024-04-21","2024-04-27",
                         "2024-04-28","2024-05-01","2024-05-04","2024-05-05","2024-05-11","2024-05-12","2024-05-18",
                         "2024-05-19","2024-05-22","2024-05-25","2024-05-26","2024-06-01","2024-06-02","2024-06-03",
                         "2024-06-08","2024-06-09","2024-06-15","2024-06-16","2024-06-22","2024-06-23","2024-06-29",
                         "2024-06-30","2024-07-06","2024-07-07","2024-07-13","2024-07-14","2024-07-20","2024-07-21",
                         "2024-07-27","2024-07-28","2024-08-03","2024-08-04","2024-08-10","2024-08-11","2024-08-12",
                         "2024-08-17","2024-08-18","2024-08-24","2024-08-25","2024-08-31","2024-09-01","2024-09-07",
                         "2024-09-08","2024-09-14","2024-09-15","2024-09-21","2024-09-22","2024-09-28","2024-09-29",
                         "2024-10-05","2024-10-06","2024-10-12","2024-10-05","2024-10-06","2024-10-12","2024-10-13",
                         "2024-10-19","2024-10-20","2024-10-23","2024-10-26","2024-10-27","2024-11-02","2024-11-03",
                         "2024-11-09","2024-11-10","2024-11-16","2024-11-17","2024-11-23","2024-11-24","2024-11-30",
                         "2024-12-01","2024-12-05","2024-12-07","2024-12-08","2024-12-10","2024-12-14","2024-12-15",
                         "2024-12-21","2024-12-22","2024-12-28","2024-12-29","2024-12-31"]
# วันหยุดปี 2025 (ตัวอย่างตามประกาศ ณ ปลายปี 2024 - ควรตรวจสอบความถูกต้องอีกครั้ง)
HOLIDAYS_TOU_2025_STR = ["2025-01-01","2025-01-04","2025-01-05","2025-01-11","2025-01-12","2025-01-18","2025-01-19",
                         "2025-01-25","2025-01-26","2025-02-01","2025-02-02","2025-02-08","2025-02-09","2025-02-12",
                         "2025-02-15","2025-02-16","2025-02-22","2025-02-23","2025-03-01","2025-03-02","2025-03-08",
                         "2025-03-09","2025-03-15","2025-03-16","2025-03-22","2025-03-23","2025-03-29","2025-03-30",
                         "2025-04-05","2025-04-06","2025-04-12","2025-04-13","2025-04-14","2025-04-15","2025-04-19",
                         "2025-04-20","2025-04-26","2025-04-27","2025-05-01","2025-05-03","2025-05-04","2025-05-10",
                         "2025-05-11","2025-05-17","2025-05-18","2025-05-24","2025-05-25","2025-05-31","2025-06-01",
                         "2025-06-03","2025-06-07","2025-06-08","2025-06-14","2025-06-15","2025-06-21","2025-06-22",
                         "2025-06-28","2025-06-29","2025-07-05","2025-07-06","2025-07-10","2025-07-11","2025-07-12",
                         "2025-07-13","2025-07-19","2025-07-20","2025-07-26","2025-07-27","2025-07-28","2025-08-02",
                         "2025-08-09","2025-08-10","2025-08-12","2025-08-16","2025-08-17","2025-08-23","2025-08-24",
                         "2025-08-30","2025-08-31","2025-09-06","2025-09-07","2025-09-13","2025-09-14","2025-09-20",
                         "2025-09-21","2025-09-27","2025-09-28","2025-10-04","2025-10-05","2025-10-11","2025-10-12",
                         "2025-10-13","2025-10-18","2025-10-19","2025-10-23","2025-10-25","2025-10-26","2025-11-01",
                         "2025-11-02","2025-11-08","2025-11-09","2025-11-15","2025-11-16","2025-11-22","2025-11-23",
                         "2025-11-29","2025-11-30","2025-12-05","2025-12-06","2025-12-07","2025-12-10","2025-12-13",
                         "2025-12-14","2025-12-20","2025-12-21","2025-12-27","2025-12-28","2025-12-31"]
# ทำความสะอาดรายการวันหยุด (ลบรายการซ้ำและเรียงลำดับ)
HOLIDAYS_TOU_2025_STR = sorted(list(set(HOLIDAYS_TOU_2025_STR)))

HOLIDAYS_TOU_DATA = {}
try:
    HOLIDAYS_TOU_DATA[2024] = set(datetime.strptime(d, "%Y-%m-%d").date() for d in HOLIDAYS_TOU_2024_STR)
    HOLIDAYS_TOU_DATA[2025] = set(datetime.strptime(d, "%Y-%m-%d").date() for d in HOLIDAYS_TOU_2025_STR)
    # เพิ่มข้อมูลวันหยุดสำหรับปีอื่นๆ ตามต้องการ
except ValueError as e:
    error_message = f"เกิดข้อผิดพลาดในการแปลงข้อมูลวันหยุด: {e}. โปรดตรวจสอบรูปแบบวันที่ใน HOLIDAYS_TOU_xxx_STR."
    print(error_message)
    st.error(error_message) # แสดงข้อผิดพลาดในแอปด้วย
    HOLIDAYS_TOU_DATA = {} # ใช้ข้อมูลว่างถ้ามีปัญหา

VAT_RATE = 0.07
PEAK_START = time(9, 0, 0)
PEAK_END = time(21, 59, 59) # 9:00:00 ถึง 21:59:59 คือ Peak
MONTH_NAMES_TH = {1: "มกราคม", 2: "กุมภาพันธ์", 3: "มีนาคม", 4: "เมษายน",
                  5: "พฤษภาคม", 6: "มิถุนายน", 7: "กรกฎาคม", 8: "สิงหาคม",
                  9: "กันยายน", 10: "ตุลาคม", 11: "พฤศจิกายน", 12: "ธันวาคม"}
HOURS = [f"{h:02d}" for h in range(24)]
MINUTES = ["00", "15", "30", "45"]


# --- ฟังก์ชัน Helper (ปรับปรุง parse_data_file) ---

# @st.cache_data # พิจารณาใช้ cache หากต้องการเพิ่มความเร็วในการโหลดไฟล์เดิมซ้ำ
def parse_data_file(uploaded_file):
    """
    อ่านและประมวลผลไฟล์ข้อมูล Load Profile ที่อัปโหลดผ่าน Streamlit
    รองรับไฟล์ Tab-separated (รูปแบบเฉพาะ) และ CSV หลายรูปแบบ:
    - CSV 7 คอลัมน์: คาดว่า DateTime อยู่ที่ index 1, Demand (kW) อยู่ที่ index 3
    - CSV >=8 คอลัมน์: คาดว่า DateTime อยู่ที่ index 1, Demand (W) อยู่ที่ index 3
    พยายามตรวจจับ Encoding (UTF-8, CP874/TIS-620) และรูปแบบวันที่ (YYYY-MM-DD หรือ DD/MM/YYYY)
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
            uploaded_file.seek(0) # รีเซ็ตตำแหน่งการอ่านไฟล์
            bytes_content = uploaded_file.getvalue()
            file_content_string = bytes_content.decode(enc)
            detected_encoding = enc
            st.write(f"✅ อ่านไฟล์ด้วย Encoding: {detected_encoding}")
            # อ่านบรรทัดแรกเพื่อตรวจจับตัวคั่น
            # ใช้ splitlines() เพื่อจัดการกับ \r\n หรือ \n
            first_line = file_content_string.splitlines()[0].strip() if file_content_string else ""
            break # อ่านสำเร็จ ออกจาก loop
        except UnicodeDecodeError:
            st.write(f"⚠️ อ่านด้วย {enc} ไม่สำเร็จ...")
            continue # ลอง encoding ถัดไป
        except IndexError: # กรณีไฟล์ว่างเปล่าหลัง decode
             raise ValueError("ไฟล์ว่างเปล่า หรือไม่สามารถอ่านบรรทัดแรกได้")
        except Exception as e:
            raise ValueError(f"เกิดข้อผิดพลาดไม่คาดคิดขณะอ่านไฟล์ด้วย {enc}: {e}")

    if not detected_encoding:
        raise ValueError(f"ไม่สามารถอ่านไฟล์ด้วย Encoding ที่รองรับ ({', '.join(encodings_to_try)})")
    if not first_line:
         raise ValueError("ไฟล์ว่างเปล่า หรือไม่สามารถอ่านบรรทัดแรกได้")

    # 2. ตรวจจับตัวคั่น (Tab หรือ Comma)
    if '\t' in first_line:
        detected_delimiter = '\t'
        st.write("ตรวจพบตัวคั่น: Tab (\\t)")
    elif ',' in first_line:
        detected_delimiter = ','
        st.write("ตรวจพบตัวคั่น: Comma (,)")
    else:
        # หากไม่พบตัวคั่นที่รู้จัก อาจลองอ่านทั้งบรรทัดเป็นข้อมูลเดียว? (ตอนนี้แจ้ง error)
        raise ValueError(f"ไม่พบตัวคั่นที่รองรับ (Tab หรือ Comma) ในบรรทัดแรก: '{first_line}'")

    # --- ประมวลผลตามตัวคั่น ---
    data_io = io.StringIO(file_content_string) # ใช้ string ที่ถอดรหัสแล้ว

    try:
        # 3. จัดการรูปแบบ Tab-Separated
        if detected_delimiter == '\t':
            # ตรวจสอบ Header เฉพาะของรูปแบบ Tab ที่รู้จัก
            if first_line.strip() == "DateTime\tTotal import kW demand":
                st.write("ตรวจพบรูปแบบ: Tab-separated (Header มาตรฐาน)")
                # header=0 คือใช้บรรทัดแรกเป็น Header
                df = pd.read_csv(data_io, sep='\t', header=0, skipinitialspace=True, low_memory=False)
                df.columns = df.columns.str.strip() # ทำความสะอาดชื่อคอลัมน์

                required_cols = ['DateTime', 'Total import kW demand']
                if not all(col in df.columns for col in required_cols):
                    raise ValueError(f"ไฟล์ Tab ต้องมีคอลัมน์: {', '.join(required_cols)}")

                # แปลง DateTime (ใช้ dayfirst=True ตามโค้ดเดิมสำหรับ format นี้)
                df['DateTime_parsed'] = pd.to_datetime(df['DateTime'], dayfirst=True, errors='coerce')
                # แปลง Demand (หน่วยเป็น kW อยู่แล้ว)
                df['Demand_parsed'] = pd.to_numeric(df['Total import kW demand'], errors='coerce')

                # สร้าง DataFrame สุดท้าย
                df_final = df.dropna(subset=['DateTime_parsed', 'Demand_parsed']) \
                             .rename(columns={'DateTime_parsed': 'DateTime',
                                              'Demand_parsed': 'Total import kW demand'}) \
                             [['DateTime', 'Total import kW demand']].copy()
            else:
                raise ValueError("ไฟล์เป็น Tab-separated แต่ Header ไม่ตรงกับรูปแบบที่คาดหวัง ('DateTime\\tTotal import kW demand')")

        # 4. จัดการรูปแบบ Comma-Separated
        elif detected_delimiter == ',':
            # อ่านข้อมูลตัวอย่างเพื่อตรวจสอบจำนวนคอลัมน์ก่อน
            # ใช้ low_memory=False เพื่อลดคำเตือนเกี่ยวกับ dtype ตอนอ่าน
            try:
                df_check = pd.read_csv(io.StringIO(file_content_string), sep=',', header=None, skipinitialspace=True, nrows=10, low_memory=False)
                num_cols = df_check.shape[1]
                st.write(f"ตรวจพบรูปแบบ: CSV จำนวน {num_cols} คอลัมน์")
            except pd.errors.EmptyDataError:
                 raise ValueError("ไฟล์ CSV ว่างเปล่า")
            except Exception as read_err:
                 raise ValueError(f"เกิดปัญหาในการอ่านตัวอย่างไฟล์ CSV: {read_err}")


            # กำหนด index คอลัมน์ที่คาดหวัง (นับจาก 0)
            datetime_col_idx = 1
            demand_col_idx = 3

            # ตรวจสอบว่ามีคอลัมน์เพียงพอหรือไม่
            if num_cols <= max(datetime_col_idx, demand_col_idx):
                 raise ValueError(f"ไฟล์ CSV มี {num_cols} คอลัมน์ ไม่เพียงพอสำหรับข้อมูลที่ต้องการ (ต้องการ DateTime ที่ index {datetime_col_idx}, Demand ที่ index {demand_col_idx})")

            # อ่านไฟล์เต็มอีกครั้ง
            # พยายามเดาว่ามี header หรือไม่ (ถ้าบรรทัดแรกดูเหมือน header ให้ใช้ header=0)
            header_setting = None # Default to no header
            try:
                 first_row_values = df_check.iloc[0].astype(str).tolist()
                 # เกณฑ์ง่ายๆ: ถ้ามีตัวอักษรใน 4 คอลัมน์แรก ถือว่าอาจเป็น header
                 if any(any(c.isalpha() for c in str(item)) for item in first_row_values[:4]):
                     header_setting = 0
                 st.write(f"การอ่าน CSV: ใช้ header={header_setting}")
                 df = pd.read_csv(data_io, sep=',', header=header_setting, skipinitialspace=True, low_memory=False)
            except Exception as read_err:
                 st.warning(f"เกิดปัญหาในการอ่าน CSV เต็มรูปแบบ ({read_err}), ลองอ่านแบบไม่มี Header...")
                 data_io.seek(0) # รีเซ็ต buffer
                 df = pd.read_csv(data_io, sep=',', header=None, skipinitialspace=True, low_memory=False)

            # --- แปลง DateTime (คอลัมน์ index 1) ---
            if datetime_col_idx >= df.shape[1]:
                 raise ValueError(f"Index คอลัมน์ DateTime ({datetime_col_idx}) อยู่นอกช่วงของข้อมูล ({df.shape[1]} คอลัมน์)")

            dt_str_series = df.iloc[:, datetime_col_idx].astype(str).str.strip()

            # เดา dayfirst โดยดูจากข้อมูลตัวอย่าง
            dayfirst_guess = False
            # มองหาข้อมูลที่มีรูปแบบคล้ายวันที่/เวลา และมี '/' หรือ '-'
            potential_dates = dt_str_series[dt_str_series.str.contains(r'[\/\-:]', regex=True) & dt_str_series.notna()].head(20) # เอาตัวอย่างมากขึ้น
            guessed = False
            for s in potential_dates:
                if '/' in s: # อาจเป็น DD/MM/YYYY
                    try:
                        # แยกส่วนวันที่ (ก่อน space แรก) และแยกด้วย '/' เอาส่วนแรก (day)
                        day_part_str = s.split(' ')[0].split('/')[0]
                        if day_part_str.isdigit():
                             day_part = int(day_part_str)
                             if day_part > 12:
                                 dayfirst_guess = True
                                 st.write("✔️ ตรวจพบรูปแบบวันที่อาจเป็น DD/MM/YYYY (day > 12)")
                                 guessed = True
                                 break
                    except Exception:
                         pass # ไม่สามารถแยกส่วนได้, ข้ามไป
                elif '-' in s: # มักจะเป็น YYYY-MM-DD
                    st.write("✔️ ตรวจพบรูปแบบวันที่อาจเป็น YYYY-MM-DD ('-' separator)")
                    dayfirst_guess = False # YYYY-MM-DD ไม่ใช่ dayfirst
                    guessed = True
                    break
            if not guessed and not potential_dates.empty:
                 st.write("⚠️ ไม่สามารถเดารูปแบบวันที่ (DD/MM หรือ YYYY-MM) ได้ชัดเจน, ใช้ค่าเริ่มต้น dayfirst=False")


            st.write(f"กำลังแปลง DateTime จากคอลัมน์ {datetime_col_idx+1} โดยใช้ dayfirst={dayfirst_guess}")
            dt_series = pd.to_datetime(dt_str_series, dayfirst=dayfirst_guess, errors='coerce')

            # ตรวจสอบผลการแปลง
            null_dates = dt_series.isnull().sum()
            total_rows = len(df)
            if null_dates > total_rows * 0.9: # ถ้าผิดพลาด > 90% น่าจะมีปัญหา
                # ลองสลับ dayfirst ดู ถ้ายังไม่ได้เดา
                if not guessed:
                     st.write(f"ลองแปลง DateTime อีกครั้งโดยใช้ dayfirst={not dayfirst_guess}")
                     dt_series_alt = pd.to_datetime(dt_str_series, dayfirst=(not dayfirst_guess), errors='coerce')
                     if dt_series_alt.isnull().sum() < null_dates: # ถ้าผลดีขึ้น ให้ใช้ค่าใหม่
                          st.write("✔️ การสลับ dayfirst ให้ผลดีขึ้น")
                          dt_series = dt_series_alt
                          null_dates = dt_series.isnull().sum()

            if null_dates == total_rows:
                 raise ValueError(f"ไม่สามารถแปลงค่าในคอลัมน์ที่ {datetime_col_idx+1} เป็น DateTime ได้เลย กรุณาตรวจสอบรูปแบบข้อมูล")
            elif null_dates > 0:
                 st.warning(f"คำเตือน: ไม่สามารถแปลงค่าในคอลัมน์ที่ {datetime_col_idx+1} เป็น DateTime ได้จำนวน {null_dates}/{total_rows} รายการ")


            # --- แปลง Demand (คอลัมน์ index 3) และจัดการหน่วย ---
            if demand_col_idx >= df.shape[1]:
                 raise ValueError(f"Index คอลัมน์ Demand ({demand_col_idx}) อยู่นอกช่วงของข้อมูล ({df.shape[1]} คอลัมน์)")

            # พยายามแปลงเป็นตัวเลข, บังคับ error ให้เป็น NaN
            demand_series_numeric = pd.to_numeric(df.iloc[:, demand_col_idx], errors='coerce')
            null_demand = demand_series_numeric.isnull().sum()

            if null_demand == total_rows:
                 raise ValueError(f"ไม่สามารถแปลงค่าในคอลัมน์ที่ {demand_col_idx+1} เป็นตัวเลข (Demand) ได้เลย")
            elif null_demand > 0:
                 st.warning(f"คำเตือน: ไม่สามารถแปลงค่าในคอลัมน์ที่ {demand_col_idx+1} เป็นตัวเลขได้จำนวน {null_demand}/{total_rows} รายการ (ถูกแทนที่ด้วยค่าว่าง)")


            # จัดการหน่วยตามจำนวนคอลัมน์ (ตามข้อสันนิษฐานจากไฟล์ตัวอย่าง)
            if num_cols >= 8:
                # สันนิษฐานว่าเป็น Watts สำหรับไฟล์ >= 8 คอลัมน์ (เช่น PRECISE, KY)
                demand_series_kw = demand_series_numeric / 1000.0
                unit_assumption = "W (นำไปหาร 1000 เพื่อให้เป็น kW)"
            elif num_cols == 7:
                # สันนิษฐานว่าเป็น kW สำหรับไฟล์ 7 คอลัมน์ (เช่น 0062*)
                demand_series_kw = demand_series_numeric
                unit_assumption = "kW (ใช้ค่าเดิม)"
            else:
                # กรณีนี้ไม่ควรเกิดขึ้นแล้ว เพราะมีการตรวจสอบก่อนหน้า
                raise ValueError(f"จำนวนคอลัมน์ ({num_cols}) ในไฟล์ CSV ไม่รองรับ")

            st.write(f"✔️ สันนิษฐานว่าหน่วย Demand ในคอลัมน์ {demand_col_idx+1} เป็น: {unit_assumption}")

            # --- สร้าง DataFrame สุดท้าย ---
            df_temp = pd.DataFrame({'DateTime': dt_series, 'Total import kW demand': demand_series_kw})
            # ลบแถวที่ DateTime หรือ Demand เป็นค่าว่าง (NaN/NaT)
            df_final = df_temp.dropna(subset=['DateTime', 'Total import kW demand']).copy()

        # สิ้นสุดการจัดการ CSV
        else:
             raise ValueError("Internal Error: ไม่สามารถระบุตัวคั่นไฟล์ได้") # ไม่ควรเกิดขึ้น

        # ตรวจสอบผลลัพธ์สุดท้าย
        if df_final is None or df_final.empty:
            raise ValueError("ไม่พบข้อมูลที่ถูกต้องในไฟล์หลังจากประมวลผล หรือข้อมูลทั้งหมดถูกกรองออก (อาจเกิดจากปัญหาการแปลงค่า)")

        # ทำให้แน่ใจว่า dtype ถูกต้องก่อนส่งคืน
        df_final['DateTime'] = pd.to_datetime(df_final['DateTime'])
        df_final['Total import kW demand'] = pd.to_numeric(df_final['Total import kW demand'])

        st.success(f"ประมวลผลข้อมูลสำเร็จ: พบ {len(df_final)} รายการที่ถูกต้อง")
        st.write("ตัวอย่างข้อมูลหลังการประมวลผล:")
        st.dataframe(df_final.head()) # แสดงตัวอย่างข้อมูลที่ได้
        return df_final

    except pd.errors.EmptyDataError:
        raise ValueError("ไฟล์ข้อมูลว่างเปล่า")
    except ValueError as ve: # ส่งต่อ ValueError ที่เราสร้างขึ้นเอง
        raise ve
    except Exception as e:
        st.error(f"Traceback: {traceback.format_exc()}") # แสดง traceback สำหรับ debugging
        raise ValueError(f"เกิดข้อผิดพลาดขณะประมวลผลข้อมูลด้วย Pandas: {e}")


# --- ฟังก์ชันอื่นๆ (classify_tou_period, get_ft_rate, calculate_bill) ---
# (ใช้เวอร์ชันล่าสุดจากความคิดเห็นก่อนหน้า ไม่มีการเปลี่ยนแปลง)

def classify_tou_period(dt_obj):
    """จำแนกช่วงเวลา Peak/Off-Peak สำหรับอัตรา TOU"""
    if not isinstance(dt_obj, datetime): return 'Unknown'
    current_date = dt_obj.date()
    current_time = dt_obj.time()
    day_of_week = dt_obj.weekday() # Monday is 0 and Sunday is 6

    # ตรวจสอบปีของข้อมูลเทียบกับข้อมูลวันหยุดที่มี
    year_holidays = HOLIDAYS_TOU_DATA.get(current_date.year)
    if year_holidays is None:
        if current_date.year not in st.session_state.get('missing_holiday_years', set()):
             st.warning(f"ไม่พบข้อมูลวันหยุด TOU สำหรับปี {current_date.year}. การคำนวณ TOU อาจไม่ถูกต้องสำหรับวันหยุดในปีนั้น")
             if 'missing_holiday_years' not in st.session_state: st.session_state.missing_holiday_years = set()
             st.session_state.missing_holiday_years.add(current_date.year)

    # 1. วันหยุดนักขัตฤกษ์ (ตามประกาศ ไม่รวมวันหยุดชดเชย) -> Off-Peak ทั้งวัน
    if year_holidays and current_date in year_holidays:
        return 'Off-Peak'

    # 2. วันเสาร์-อาทิตย์ -> Off-Peak ทั้งวัน
    if day_of_week >= 5: # Saturday (5), Sunday (6)
        return 'Off-Peak'

    # 3. วันธรรมดา (จันทร์-ศุกร์)
    # ช่วงเวลา 9:00:00 - 21:59:59 คือ Peak
    if PEAK_START <= current_time <= PEAK_END:
        return 'Peak'
    else: # นอกเหนือจากนั้นคือ Off-Peak
        return 'Off-Peak'

def get_ft_rate(date_in_period):
    """หาอัตรา Ft ที่เหมาะสมสำหรับวันที่ที่กำหนด"""
    # ตรวจสอบและแปลง input ให้เป็น date object
    if isinstance(date_in_period, datetime):
        date_in_period = date_in_period.date()
    elif not isinstance(date_in_period, date):
         # ใช้ fallback เป็นวันที่ปัจจุบันถ้า input ไม่ถูกต้อง
         fallback_date = datetime.now().date()
         if 'invalid_date_ft_warn' not in st.session_state:
             st.warning(f"ข้อมูลวันที่ ('{date_in_period}') ไม่ถูกต้องสำหรับหาค่า Ft, ใช้ข้อมูลปัจจุบัน ({fallback_date}) แทน")
             print(f"Warning: Invalid date type ({type(date_in_period)}) passed to get_ft_rate. Using current date.")
             st.session_state.invalid_date_ft_warn = True # แสดงคำเตือนครั้งเดียว
         date_in_period = fallback_date

    applicable_rate = None
    # เรียงลำดับช่วงเวลา Ft จากใหม่สุดไปเก่าสุด
    sorted_ft_periods = sorted(FT_RATES.keys(), reverse=True)

    # หาช่วง Ft แรกที่วันที่ของเราอยู่หลังจากหรือตรงกับวันเริ่มต้นของช่วงนั้น
    for start_year, start_month in sorted_ft_periods:
        # สร้างวันที่เริ่มต้นของช่วง Ft (วันที่ 1 ของเดือน)
        ft_period_start_date = date(start_year, start_month, 1)
        if date_in_period >= ft_period_start_date:
            applicable_rate = FT_RATES[(start_year, start_month)]
            # st.write(f"DEBUG Ft: Found rate {applicable_rate} for period starting {start_year}-{start_month} for date {date_in_period}")
            break # เจออัตราล่าสุดที่ใช้ได้แล้ว หยุดค้นหา

    if applicable_rate is None:
        # ถ้าไม่เจอเลย (อาจเป็นวันที่เก่ากว่าข้อมูล Ft ที่มี)
        if 'ft_not_found_warn' not in st.session_state:
            st.warning(f"ไม่พบอัตรา Ft ที่กำหนดไว้สำหรับช่วงเวลาที่มีวันที่ {date_in_period} หรือเก่ากว่า. ใช้ค่า Ft=0.0")
            print(f"Warning: Ft rate not found for period including {date_in_period}. Using Ft=0.0")
            st.session_state.ft_not_found_warn = True # แสดงคำเตือนครั้งเดียว
        applicable_rate = 0.0

    return applicable_rate


def calculate_bill(df_processed, customer_type, tariff_type):
    """คำนวณค่าไฟฟ้าจาก DataFrame ที่ประมวลผลแล้ว"""
    # ตรวจสอบข้อมูลนำเข้า
    if df_processed is None or df_processed.empty:
        return {"error": "ไม่มีข้อมูลที่ถูกต้องสำหรับคำนวณ"}
    required_cols = ['DateTime', 'kWh']
    if not all(col in df_processed.columns for col in required_cols):
        return {"error": f"Internal error: ขาดคอลัมน์ที่จำเป็น ({', '.join(required_cols)})"}
    if not pd.api.types.is_datetime64_any_dtype(df_processed['DateTime']):
         return {"error": "Internal error: คอลัมน์ DateTime ไม่ใช่ประเภทข้อมูลวันที่"}
    if not pd.api.types.is_numeric_dtype(df_processed['kWh']):
         # ลองแปลงเป็น numeric อีกครั้ง เผื่อมีปัญหาตอนส่งค่า
         df_processed['kWh'] = pd.to_numeric(df_processed['kWh'], errors='coerce')
         if df_processed['kWh'].isnull().any():
              return {"error": "Internal error: คอลัมน์ kWh มีค่าที่ไม่ใช่ตัวเลข"}
         st.warning("มีการแปลง dtype ของ kWh ใน calculate_bill")

    # --- เริ่มการคำนวณ ---
    total_kwh = df_processed['kWh'].sum()
    kwh_peak, kwh_off_peak = 0.0, 0.0 # กำหนดเป็น float
    df_temp = df_processed.copy() # ทำงานกับ copy ป้องกันแก้ไขข้อมูลเดิม

    # หาปีของข้อมูลเพื่อใช้กับวันหยุดและ Ft (ใช้วันที่สุดท้ายในข้อมูล)
    data_period_end_dt = df_temp['DateTime'].iloc[-1] if not df_temp.empty else datetime.now()
    data_year = data_period_end_dt.year
    relevant_date_for_ft = data_period_end_dt.date() # ใช้วันที่นี้ในการหา Ft

    # คำนวณ Peak/Off-peak หากเป็นอัตรา TOU
    if tariff_type == 'tou':
        df_temp['TOU_Period'] = df_temp['DateTime'].apply(classify_tou_period)
        # st.write("DEBUG: ตัวอย่างการแบ่งประเภท TOU:") # Debugging statement
        # st.dataframe(df_temp[['DateTime', 'kWh', 'TOU_Period']].head(10)) # Debugging statement

        kwh_summary = df_temp.groupby('TOU_Period')['kWh'].sum()
        kwh_peak = kwh_summary.get('Peak', 0.0)
        # รวมหน่วยที่ไม่ทราบประเภท (Unknown) เข้ากับ Off-Peak
        kwh_off_peak = kwh_summary.get('Off-Peak', 0.0) + kwh_summary.get('Unknown', 0.0)

        # ตรวจสอบความถูกต้องของการรวมหน่วย
        if abs((kwh_peak + kwh_off_peak) - total_kwh) > 0.01: # อนุญาตความคลาดเคลื่อนเล็กน้อย
             st.warning(f"ผลรวม Peak ({kwh_peak:.4f}) + Off-peak ({kwh_off_peak:.4f}) ไม่เท่ากับยอดรวม kWh ({total_kwh:.4f}) เล็กน้อย. อาจมีปัญหาการปัดเศษหรือการแบ่งประเภท TOU.")
             print(f"Warning: Peak/Off-peak sum ({kwh_peak + kwh_off_peak:.4f}) differs slightly from total kWh ({total_kwh:.4f}).")

    # --- เลือกโครงสร้างอัตราค่าไฟฟ้า ---
    try:
        if customer_type == "residential":
            if tariff_type == "normal":
                # ตรวจสอบการใช้ไฟสำหรับบ้านอัตราปกติ (<=150 หรือ >150)
                tariff_key = "normal_le_150" if total_kwh <= 150 else "normal_gt_150"
                rate_structure = TARIFFS["residential"][tariff_key]
            elif tariff_type == "tou":
                rate_structure = TARIFFS["residential"]["tou"]
            else: raise ValueError("ประเภทอัตราสำหรับบ้านอยู่อาศัยไม่ถูกต้อง")
        elif customer_type == "smb":
            if tariff_type == "normal":
                rate_structure = TARIFFS["smb"]["normal"]
            elif tariff_type == "tou":
                rate_structure = TARIFFS["smb"]["tou"]
            else: raise ValueError("ประเภทอัตราสำหรับกิจการขนาดเล็กไม่ถูกต้อง")
        else: raise ValueError("ประเภทผู้ใช้ไม่ถูกต้อง")
    except KeyError as e:
        return {"error": f"ไม่พบโครงสร้างอัตราค่าไฟฟ้าในระบบสำหรับ: {e}. กรุณาตรวจสอบค่าคงที่ TARIFFS."}
    except ValueError as e:
        return {"error": str(e)}

    # --- คำนวณค่าพลังงานไฟฟ้าฐาน ---
    base_energy_cost = 0.0
    if rate_structure['type'] == 'tiered':
        last_limit = 0
        for tier in rate_structure['tiers']:
            limit, rate = tier['limit'], tier['rate']
            # คำนวณหน่วยที่ใช้ในขั้นนี้
            units_in_tier = max(0, min(total_kwh, limit) - last_limit)
            if units_in_tier > 0:
                base_energy_cost += units_in_tier * rate
            last_limit = limit
            # หยุดเมื่อคำนวณครบหน่วยแล้ว (ยกเว้นขั้นสุดท้ายที่เป็น inf)
            if total_kwh <= limit and limit != float('inf'):
                break
    elif rate_structure['type'] == 'tou':
        base_energy_cost = (kwh_peak * rate_structure['peak_rate']) + \
                           (kwh_off_peak * rate_structure['off_peak_rate'])

    # --- ดึงค่าบริการ ---
    service_charge = rate_structure['service_charge']

    # --- คำนวณค่า Ft ---
    applicable_ft_rate = get_ft_rate(relevant_date_for_ft) # ใช้วันที่ที่หาไว้
    ft_cost = total_kwh * applicable_ft_rate

    # --- คำนวณยอดรวม ---
    total_before_vat = base_energy_cost + service_charge + ft_cost
    vat_amount = total_before_vat * VAT_RATE
    final_bill = total_before_vat + vat_amount

    # --- จัดเตรียมผลลัพธ์ ---
    result = {
        "customer_type": customer_type, "tariff_type": tariff_type,
        "data_period_start": df_temp['DateTime'].iloc[0].strftime('%Y-%m-%d %H:%M:%S') if not df_temp.empty else "N/A",
        "data_period_end": data_period_end_dt.strftime('%Y-%m-%d %H:%M:%S'),
        "data_year": data_year, # ปีที่ใช้สำหรับวันหยุด/Ft
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
        "error": None # ไม่มี error
    }
    return result
# --- สิ้นสุดส่วนฟังก์ชัน Helper ---


# --- Streamlit App ---
st.set_page_config(page_title="คำนวณค่าไฟฟ้า", layout="wide")
st.title("📊 โปรแกรมคำนวณค่าไฟฟ้า (จำลอง EV)")

# --- Session State Initialization ---
# ใช้สำหรับเก็บข้อมูลระหว่างการทำงานของแอป
if 'full_dataframe' not in st.session_state:
    st.session_state.full_dataframe = None # DataFrame ที่อ่านจากไฟล์
if 'available_years' not in st.session_state:
    st.session_state.available_years = [] # ปีที่มีข้อมูลในไฟล์
if 'available_months_th' not in st.session_state:
    st.session_state.available_months_th = [] # เดือนที่มีข้อมูลในไฟล์ (ชื่อไทย)
if 'calculation_result' not in st.session_state:
    st.session_state.calculation_result = "" # ผลการคำนวณ (ข้อความ)
if 'last_uploaded_filename' not in st.session_state:
    st.session_state.last_uploaded_filename = None # ชื่อไฟล์ล่าสุดที่อัปโหลดสำเร็จ


# --- ส่วนอัปโหลดไฟล์ ---
st.header("1. อัปโหลดไฟล์ข้อมูล Load Profile")
uploaded_file = st.file_uploader("เลือกไฟล์ (.txt หรือ .csv)", type=['txt', 'csv'], key="file_uploader")

# ตรวจสอบว่ามีการอัปโหลดไฟล์ใหม่หรือไม่
if uploaded_file is not None:
    # ถ้ายังไม่มีข้อมูลในระบบ หรือไฟล์ที่อัปโหลดเป็นไฟล์ใหม่
    if st.session_state.full_dataframe is None or uploaded_file.name != st.session_state.get('last_uploaded_filename'):
        st.info(f"กำลังประมวลผลไฟล์ใหม่: {uploaded_file.name}...")
        try:
            with st.spinner('กำลังอ่านและประมวลผลข้อมูล... กรุณารอสักครู่'):
                # ล้างข้อมูลเก่าก่อนประมวลผลไฟล์ใหม่
                st.session_state.full_dataframe = None
                st.session_state.available_years = []
                st.session_state.available_months_th = []
                st.session_state.calculation_result = ""
                # ล้างคำเตือนเก่าๆ
                st.session_state.missing_holiday_years = set()
                if 'invalid_date_ft_warn' in st.session_state: del st.session_state.invalid_date_ft_warn
                if 'ft_not_found_warn' in st.session_state: del st.session_state.ft_not_found_warn

                # เรียกใช้ฟังก์ชัน parse_data_file ที่ปรับปรุงแล้ว
                df_parsed = parse_data_file(uploaded_file)

                # เก็บ DataFrame และข้อมูลปี/เดือน ถ้าสำเร็จ
                if df_parsed is not None and not df_parsed.empty:
                    st.session_state.full_dataframe = df_parsed
                    st.session_state.last_uploaded_filename = uploaded_file.name # เก็บชื่อไฟล์ที่สำเร็จ

                    # ดึงปีและเดือนจาก DataFrame (ตรวจสอบ dtype ก่อน)
                    if not pd.api.types.is_datetime64_any_dtype(st.session_state.full_dataframe['DateTime']):
                         st.session_state.full_dataframe['DateTime'] = pd.to_datetime(st.session_state.full_dataframe['DateTime'], errors='coerce')
                         st.session_state.full_dataframe.dropna(subset=['DateTime'], inplace=True) # ลบแถวที่แปลงไม่ได้

                    if not st.session_state.full_dataframe.empty:
                        st.session_state.available_years = sorted(st.session_state.full_dataframe['DateTime'].dt.year.unique())
                        available_months_num = sorted(st.session_state.full_dataframe['DateTime'].dt.month.unique())
                        st.session_state.available_months_th = [MONTH_NAMES_TH.get(m, str(m)) for m in available_months_num]
                        #สำเร็จแล้ว ไม่ต้องแสดง st.success ซ้ำซ้อนกับใน parse_data_file
                    else:
                         st.error("ไม่พบข้อมูลที่ถูกต้องหลังจากการแปลง DateTime เพิ่มเติม")
                         st.session_state.full_dataframe = None # รีเซ็ตถ้าว่างเปล่า

                # กรณี parse_data_file คืนค่า None หรือ Empty (ซึ่งไม่ควรเกิดถ้ามีการ raise error)
                # else:
                #     st.session_state.full_dataframe = None
                #     st.error("การประมวลผลไฟล์ไม่สำเร็จ หรือไม่พบข้อมูลที่ใช้งานได้")

        except ValueError as ve:
            st.session_state.full_dataframe = None # รีเซ็ตเมื่อเกิดข้อผิดพลาด
            st.session_state.last_uploaded_filename = None
            st.error(f"ข้อผิดพลาดในการประมวลผลไฟล์: {ve}")
        except Exception as ex:
            st.session_state.full_dataframe = None # รีเซ็ตเมื่อเกิดข้อผิดพลาด
            st.session_state.last_uploaded_filename = None
            st.error(f"เกิดข้อผิดพลาดไม่คาดคิด: {ex}")
            st.error(f"Traceback: {traceback.format_exc()}") # แสดง traceback สำหรับข้อผิดพลาดที่ไม่คาดคิด

# --- ส่วนตั้งค่าการคำนวณ (แสดงเมื่อโหลดไฟล์สำเร็จและมีข้อมูล) ---
if st.session_state.full_dataframe is not None and not st.session_state.full_dataframe.empty:
    st.markdown("---")
    st.header("2. ตั้งค่าการคำนวณ")

    col1, col2 = st.columns(2) # แบ่งเป็น 2 คอลัมน์

    with col1:
        # ประเภทผู้ใช้
        customer_options = ["บ้านอยู่อาศัย", "กิจการขนาดเล็ก"]
        selected_customer = st.selectbox("ประเภทผู้ใช้:", customer_options, key="customer_type")

        # เลือกปี
        # เพิ่มตรวจสอบว่า available_years มีค่าหรือไม่
        year_options = ["ทั้งปี"] + st.session_state.get('available_years', [])
        selected_year = st.selectbox("เลือกปี:", year_options, key="year")

    with col2:
        # ประเภทอัตรา
        tariff_options = ["อัตราปกติ", "อัตรา TOU"]
        selected_tariff = st.selectbox("ประเภทอัตรา:", tariff_options, key="tariff_type")

        # เลือกเดือน
        # เพิ่มตรวจสอบว่า available_months_th มีค่าหรือไม่
        month_options = ["ทั้งเดือน"] + st.session_state.get('available_months_th', [])
        selected_month = st.selectbox("เลือกเดือน:", month_options, key="month")

    # --- ส่วนจำลอง EV Charger ---
    with st.expander("🔌 จำลอง EV Charger (ตัวเลือกเพิ่มเติม)"):
        ev_enabled = st.checkbox("เปิดใช้งานการจำลอง EV", key="ev_enabled")

        ev_col1, ev_col2, ev_col3 = st.columns(3)
        with ev_col1:
             # กำหนดค่า min/max/default ที่เหมาะสม
             ev_power_kw = st.number_input("กำลังไฟ Charger (kW):", min_value=0.1, max_value=50.0, value=7.0, step=0.1, format="%.1f", key="ev_power", disabled=not ev_enabled)
        with ev_col2:
             # กำหนดค่าเริ่มต้นที่เหมาะสม (เช่น 22:00)
             ev_start_hour = st.selectbox("เวลาเริ่มชาร์จ (ชม.):", HOURS, index=22, key="ev_start_h", disabled=not ev_enabled)
             ev_start_min = st.selectbox("นาทีเริ่ม:", MINUTES, index=0, key="ev_start_m", disabled=not ev_enabled)
        with ev_col3:
             # กำหนดค่าเริ่มต้นที่เหมาะสม (เช่น 05:00)
             ev_end_hour = st.selectbox("เวลาสิ้นสุด (ชม.):", HOURS, index=5, key="ev_end_h", disabled=not ev_enabled)
             ev_end_min = st.selectbox("นาทีสิ้นสุด:", MINUTES, index=0, key="ev_end_m", disabled=not ev_enabled)

    st.markdown("---")

    # --- ปุ่มคำนวณ ---
    if st.button("คำนวณค่าไฟ", type="primary", key="calculate_button"):
        st.session_state.calculation_result = "" # เคลียร์ผลลัพธ์เก่า
        with st.spinner("กำลังคำนวณค่าไฟฟ้า..."):
            try:
                # --- 1. กรองข้อมูลตามปีและเดือนที่เลือก ---
                df_filtered = st.session_state.full_dataframe.copy() # ทำงานกับ copy

                # กรองตามปี
                if selected_year != "ทั้งปี":
                    try:
                         year_int = int(selected_year)
                         df_filtered = df_filtered[df_filtered['DateTime'].dt.year == year_int]
                    except ValueError:
                         st.error(f"ปีที่เลือกไม่ถูกต้อง: {selected_year}")
                         raise # หยุดการทำงานถ้าปีผิดพลาด

                # กรองตามเดือน
                if selected_month != "ทั้งเดือน":
                    month_num = None
                    for num, name in MONTH_NAMES_TH.items():
                        if name == selected_month:
                            month_num = num
                            break
                    if month_num:
                        df_filtered = df_filtered[df_filtered['DateTime'].dt.month == month_num]
                    else:
                        # กรณีไม่เจอชื่อเดือน (ไม่ควรเกิดกับ selectbox แต่ป้องกันไว้)
                        st.warning(f"ไม่พบเลขเดือนสำหรับ '{selected_month}'. ไม่สามารถกรองข้อมูลตามเดือนได้")

                # ตรวจสอบว่ามีข้อมูลหลังจากการกรองหรือไม่
                if df_filtered.empty:
                    st.warning(f"ไม่พบข้อมูลสำหรับ '{selected_month} ปี {selected_year}' ในไฟล์นี้")
                    st.session_state.calculation_result = f"ไม่พบข้อมูลสำหรับ '{selected_month} ปี {selected_year}'"
                else:
                    st.write(f"พบข้อมูล {len(df_filtered)} รายการสำหรับช่วงเวลาที่เลือก")

                    # --- 2. จัดการการจำลอง EV Charger ---
                    ev_charging_intervals = 0
                    ev_kwh_added = 0.0
                    ev_details_for_output = ""
                    charge_start_time = None
                    charge_end_time = None
                    original_total_demand = df_filtered['Total import kW demand'].sum() # เก็บค่าเดิมไว้เปรียบเทียบ

                    if ev_enabled:
                        try:
                            # ดึงค่าจาก session_state ตาม key ที่กำหนด
                            start_h = int(st.session_state.ev_start_h)
                            start_m = int(st.session_state.ev_start_m)
                            end_h = int(st.session_state.ev_end_h)
                            end_m = int(st.session_state.ev_end_m)
                            ev_power = float(st.session_state.ev_power) # ใช้ ev_power ไม่ใช่ ev_power_kw
                            if ev_power <= 0: raise ValueError("กำลังไฟ EV ต้องมากกว่า 0")

                            charge_start_time = time(start_h, start_m)
                            charge_end_time = time(end_h, end_m)

                            ev_details_for_output = f"จำลอง EV Charger: {ev_power:.2f} kW ({start_h:02d}:{start_m:02d} - {end_h:02d}:{end_m:02d})\n"

                            # สร้าง mask สำหรับช่วงเวลาชาร์จ
                            time_series = df_filtered['DateTime'].dt.time
                            if charge_start_time <= charge_end_time: # ชาร์จไม่ข้ามคืน
                                charging_mask = (time_series >= charge_start_time) & (time_series < charge_end_time) # ใช้ < end time เพื่อไม่รวม interval สุดท้าย
                            else: # ชาร์จข้ามคืน (เช่น 22:00 - 05:00)
                                charging_mask = (time_series >= charge_start_time) | (time_series < charge_end_time)

                            # เพิ่ม demand ในช่วงเวลาชาร์จ
                            df_filtered.loc[charging_mask, 'Total import kW demand'] += ev_power
                            ev_charging_intervals = charging_mask.sum()

                            # คำนวณ kWh ที่เพิ่ม (สมมติฐาน: ข้อมูลเป็นราย 15 นาที = 0.25 ชั่วโมง)
                            # ควรตรวจสอบ interval ของข้อมูลจริงถ้าเป็นไปได้
                            interval_hours = 0.25 # สมมติฐาน 15 นาที
                            ev_kwh_added = ev_charging_intervals * ev_power * interval_hours
                            st.write(f"✔️ เพิ่มโหลด EV สำเร็จ ({ev_charging_intervals} ช่วงเวลา, {ev_kwh_added:.2f} kWh)")

                        except ValueError as ve:
                            st.error(f"ข้อมูล EV ไม่ถูกต้อง: {ve}")
                            ev_details_for_output = f"⚠️ ข้อมูล EV ไม่ถูกต้อง: {ve}\n"
                            # ไม่รวมโหลด EV ถ้าข้อมูลผิดพลาด แต่คำนวณต่อไป
                        except Exception as ex_ev:
                            st.error(f"เกิดปัญหาในการประมวลผล EV Charger: {ex_ev}")
                            ev_details_for_output = f"⚠️ เกิดปัญหาในการประมวลผล EV: {ex_ev}\n"


                    # --- 3. คำนวณ kWh จาก kW Demand ---
                    # สมมติฐาน: ข้อมูลเป็นราย 15 นาที (0.25 ชั่วโมง)
                    # หากข้อมูลมี interval อื่น ต้องปรับตัวคูณนี้
                    interval_hours = 0.25
                    df_filtered['kWh'] = df_filtered['Total import kW demand'] * interval_hours

                    # --- 4. เรียกฟังก์ชันคำนวณค่าไฟ ---
                    # แปลงชื่อที่แสดงผลเป็น key ที่ใช้ในโค้ด
                    customer_key = "residential" if selected_customer == "บ้านอยู่อาศัย" else "smb"
                    tariff_key = "normal" if selected_tariff == "อัตราปกติ" else "tou"

                    bill_details = calculate_bill(df_filtered, customer_key, tariff_key)

                    # --- 5. สร้างข้อความผลลัพธ์ ---
                    if bill_details.get("error"):
                        st.error(f"เกิดข้อผิดพลาดในการคำนวณ: {bill_details['error']}")
                        st.session_state.calculation_result = f"เกิดข้อผิดพลาดในการคำนวณ:\n{bill_details['error']}"
                    else:
                        # สร้างส่วนหัวของผลลัพธ์
                        calculation_period = ""
                        if selected_year == "ทั้งปี" and selected_month == "ทั้งเดือน": calculation_period = "ข้อมูลทั้งหมดในไฟล์"
                        elif selected_year == "ทั้งปี": calculation_period = f"เดือน{selected_month} (ทุกปีในไฟล์)"
                        elif selected_month == "ทั้งเดือน": calculation_period = f"ทั้งปี {selected_year}"
                        else: calculation_period = f"{selected_month} {selected_year}"

                        output = f"--- ผลการคำนวณค่าไฟฟ้า ({calculation_period}) ---\n"
                        if ev_enabled: output += ev_details_for_output # เพิ่มรายละเอียด EV ถ้าเปิดใช้งาน
                        output += f"ไฟล์ข้อมูล: {st.session_state.last_uploaded_filename}\n"
                        output += f"ประเภทผู้ใช้: {selected_customer}\n"
                        output += f"ประเภทอัตรา: {selected_tariff}\n"
                        output += f"ช่วงเวลาข้อมูลที่ใช้คำนวณ: {bill_details['data_period_start']} ถึง {bill_details['data_period_end']}\n"
                        output += f"ยอดใช้ไฟรวม: {bill_details['total_kwh']:.2f} kWh\n"

                        # แสดงหน่วยที่เพิ่มจาก EV ถ้ามีการจำลองและเพิ่มจริง
                        if ev_enabled and ev_kwh_added > 0:
                            output += f"  - หน่วยที่เพิ่มจาก EV: {ev_kwh_added:.2f} kWh ({ev_charging_intervals} ช่วงเวลา x {interval_hours} ชม.)\n"

                        # แสดงหน่วย Peak/Off-peak ถ้าเป็น TOU
                        if bill_details['tariff_type'] == 'tou':
                            output += f"  - Peak: {bill_details['kwh_peak']:.2f} kWh\n"
                            output += f"  - Off-Peak: {bill_details['kwh_off_peak']:.2f} kWh\n"

                        # รายละเอียดค่าใช้จ่าย
                        output += "----------------------------------------\n"
                        output += f"ค่าพลังงานไฟฟ้า: {bill_details['base_energy_cost']:>18,.2f} บาท\n"
                        output += f"ค่าบริการรายเดือน: {bill_details['service_charge']:>19,.2f} บาท\n"

                        # ค่า Ft พร้อมอัตราที่ใช้
                        ft_rate_for_period = bill_details['applicable_ft_rate']
                        ft_year_used = bill_details['data_year'] # ปีที่ใช้หา Ft
                        output += f"ค่า Ft (@{ft_rate_for_period:.4f} บาท/หน่วย, ปี {ft_year_used}): {bill_details['ft_cost']:>6,.2f} บาท\n"

                        # ยอดรวมและ VAT
                        output += "----------------------------------------\n"
                        output += f"ยอดรวมก่อน VAT: {bill_details['total_before_vat']:>20,.2f} บาท\n"
                        output += f"ภาษีมูลค่าเพิ่ม ({VAT_RATE*100:.0f}%): {bill_details['vat_amount']:>13,.2f} บาท\n"
                        output += "========================================\n"
                        output += f"**ยอดค่าไฟฟ้าสุทธิ:** {bill_details['final_bill']:>18,.2f} **บาท**\n"
                        output += "========================================\n"

                        # หมายเหตุเพิ่มเติม
                        output += f"\nหมายเหตุ:\n"
                        output += f"- คำนวณจากข้อมูล {len(df_filtered)} รายการ (ช่วงเวลา {interval_hours*60:.0f} นาทีต่อรายการ)\n"
                        output += f"- ใช้ค่า Ft และวันหยุด TOU ตามปีของข้อมูล ณ วันสุดท้าย ({bill_details['data_period_end'].split(' ')[0]})\n"
                        if bill_details['tariff_type'] == 'tou' and st.session_state.get('missing_holiday_years'):
                             missing_years_str = ', '.join(map(str, sorted(list(st.session_state.missing_holiday_years))))
                             output += f"- **คำเตือน:** ไม่พบข้อมูลวันหยุด TOU สำหรับปี: {missing_years_str}. การคำนวณ Off-Peak ในวันหยุดของปีนั้นๆ อาจไม่ถูกต้อง\n"
                        if ev_enabled and charge_start_time is not None and charge_end_time is not None and charge_start_time > charge_end_time:
                             output += "- การจำลอง EV เป็นแบบข้ามคืน\n"
                        output += "- อัตราค่าไฟฟ้าและ Ft อ้างอิงจากค่าที่กำหนดในโค้ด ควรตรวจสอบกับประกาศล่าสุด\n"

                        st.session_state.calculation_result = output # เก็บผลลัพธ์ใน state เพื่อแสดงผล

            except Exception as calc_ex:
                 st.error(f"เกิดข้อผิดพลาดระหว่างการคำนวณ: {calc_ex}")
                 st.error(f"Traceback: {traceback.format_exc()}")
                 st.session_state.calculation_result = f"เกิดข้อผิดพลาดระหว่างการคำนวณ:\n{calc_ex}"

# --- ส่วนแสดงผลลัพธ์ ---
if st.session_state.calculation_result:
    st.markdown("---")
    st.header("3. ผลการคำนวณ")
    st.code("รายละเอียดค่าไฟฟ้าโดยประมาณ:", st.session_state.calculation_result, language=None, height=450, key="result_text_area", disabled=True)

    # เพิ่มปุ่มสำหรับดาวน์โหลดผลลัพธ์เป็นไฟล์ txt
    try:
         result_bytes = st.session_state.calculation_result.encode('utf-8')
         st.download_button(
             label="📥 ดาวน์โหลดผลลัพธ์ (.txt)",
             data=result_bytes,
             file_name=f"electricity_bill_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
             mime='text/plain'
         )
    except Exception as e:
         st.error(f"ไม่สามารถสร้างปุ่มดาวน์โหลดได้: {e}")


# --- (Optional) ส่วนแสดงข้อมูลดิบหรือกราฟ ---
if st.session_state.full_dataframe is not None and not st.session_state.full_dataframe.empty:
    st.markdown("---")
    if st.checkbox("แสดงตัวอย่างข้อมูลที่ประมวลผลแล้ว (5 บรรทัดแรก)", key="show_parsed_data"):
        st.dataframe(st.session_state.full_dataframe.head())

    # if st.checkbox("แสดงกราฟ Load Profile เบื้องต้น (จากข้อมูลที่อัปโหลด)", key="show_graph"):
    #     try:
    #         # สร้างกราฟจาก DataFrame เต็ม ก่อนการกรองหรือเพิ่ม EV
    #         df_display = st.session_state.full_dataframe.set_index('DateTime')
    #         st.line_chart(df_display['Total import kW demand'])
    #         st.caption("กราฟแสดงค่า kW demand ตลอดช่วงเวลาในไฟล์ข้อมูลที่อัปโหลด")
    #     except Exception as plot_ex:
    #         st.warning(f"ไม่สามารถสร้างกราฟได้: {plot_ex}")
