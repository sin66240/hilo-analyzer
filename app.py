import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="HiLo Analyzer", page_icon="🎲", layout="wide")

st.title("🎲 HiLo Analyzer (Google Sheets Real-time)")

# 1. สร้างการเชื่อมต่อกับ Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ฟังก์ชันจัดการข้อมูล ---
def load_data():
    """ดึงข้อมูลล่าสุดจาก Google Sheets"""
    try:
        # ttl=0 เพื่อให้อ่านข้อมูลใหม่สดเสมอ ไม่ติดแคช
        df = conn.read(ttl=0)
        return df
    except Exception as e:
        # กรณี Sheet ว่างเปล่า ให้สร้าง DataFrame โครงสร้างเริ่มต้น
        return pd.DataFrame(columns=["Timestamp", "Dice1", "Dice2", "Dice3", "Total", "Result"])

def save_data(df):
    """บันทึก DataFrame กลับลง Google Sheets"""
    conn.update(data=df)

# --- โหลดข้อมูลปัจจุบัน ---
df_history = load_data()

# --- ส่วนรับข้อมูล/บันทึกสถิติใหม่ (ตัวอย่างส่วนฟอร์ม) ---
st.subheader("➕ บันทึกผลลูกเต๋า")
with st.form("hilo_input_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        d1 = st.number_input("ลูกที่ 1", min_value=1, max_value=6, value=1)
    with col2:
        d2 = st.number_input("ลูกที่ 2", min_value=1, max_value=6, value=1)
    with col3:
        d3 = st.number_input("ลูกที่ 3", min_value=1, max_value=6, value=1)
    
    submitted = st.form_submit_button("💾 บันทึกผล")
    
    if submitted:
        total = d1 + d2 + d3
        # เงื่อนไขไฮโลทั่วไป (ตัวอย่าง)
        result = "สูง" if total >= 11 else "ต่ำ"
        timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        
        new_entry = pd.DataFrame([{
            "Timestamp": timestamp,
            "Dice1": d1,
            "Dice2": d2,
            "Dice3": d3,
            "Total": total,
            "Result": result
        }])
        
        # รวมข้อมูลใหม่เข้ากับข้อมูลเดิมแล้วเซฟลง Google Sheets
        updated_df = pd.concat([df_history, new_entry], ignore_index=True)
        save_data(updated_df)
        st.success("บันทึกข้อมูลลง Google Sheets เรียบร้อยแล้ว!")
        st.rerun()

st.divider()

# --- ส่วนแสดงประวัติการบันทึก ---
st.subheader("📜 ประวัติการบันทึกข้อมูล")

if not df_history.empty:
    col_btn1, col_btn2 = st.columns([1, 1])
    
    # ปุ่มลบรายการล่าสุด
    with col_btn1:
        if st.button("🗑️ ลบรายการล่าสุด"):
            updated_df = df_history.iloc[:-1] # ตัดบรรทัดสุดท้ายออก
            save_data(updated_df)
            st.success("ลบรายการล่าสุดเรียบร้อย!")
            st.rerun()
            
    # ปุ่มล้างประวัติทั้งหมด
    with col_btn2:
        if st.button("⚠️ ล้างประวัติทั้งหมด"):
            empty_df = pd.DataFrame(columns=["Timestamp", "Dice1", "Dice2", "Dice3", "Total", "Result"])
            save_data(empty_df)
            st.warning("ล้างประวัติข้อมูลทั้งหมดแล้ว!")
            st.rerun()

    # แสดงตารางสถิติล่าสุดขึ้นก่อน (เรียงย้อนกลับ)
    st.dataframe(df_history.iloc[::-1], use_container_width=True)
else:
    st.info("ยังไม่มีประวัติการบันทึกข้อมูลใน Google Sheets")
