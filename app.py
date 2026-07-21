import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# --------------------------------------------------
# Page Config
# --------------------------------------------------
st.set_page_config(
    page_title="HiLo Statistical Analyzer",
    page_icon="🎲",
    layout="wide"
)

# --------------------------------------------------
# Google Sheets Connection Setup
# --------------------------------------------------
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    """โหลดข้อมูลจาก Google Sheets"""
    try:
        df = conn.read(ttl=0)
        # ตรวจสอบว่ามีคอลัมน์หลักครบถ้วนไหม
        required_cols = ["Timestamp", "Dice1", "Dice2", "Dice3", "Total", "HiLo", "OddEven"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        return df
    except Exception:
        return pd.DataFrame(columns=["Timestamp", "Dice1", "Dice2", "Dice3", "Total", "HiLo", "OddEven"])

def save_data(df):
    """บันทึกข้อมูลกลับลง Google Sheets"""
    conn.update(data=df)

# โหลดข้อมูล
df_history = load_data()

# --------------------------------------------------
# Helper Functions
# --------------------------------------------------
def calculate_hilo(total):
    if total == 11:
        return "11 ไฮโล"
    elif total >= 12:
        return "สูง"
    else:
        return "ต่ำ"

def calculate_odd_even(total):
    return "คี่" if total % 2 != 0 else "คู่"

# --------------------------------------------------
# Header
# --------------------------------------------------
st.title("🎲 HiLo Statistical Analyzer")
st.caption("ระบบวิเคราะห์สถิติไฮโลและประเมินความน่าจะเป็น (เชื่อมต่อ Google Sheets Real-time)")

st.markdown("---")

# --------------------------------------------------
# Section 1: Input & Data Entry
# --------------------------------------------------
st.subheader("📌 1. บันทึกผลลูกเต๋า")

col_in1, col_in2, col_in3, col_btn = st.columns([2, 2, 2, 2])

with col_in1:
    d1 = st.selectbox("ลูกที่ 1", options=[1, 2, 3, 4, 5, 6], index=0)
with col_in2:
    d2 = st.selectbox("ลูกที่ 2", options=[1, 2, 3, 4, 5, 6], index=0)
with col_in3:
    d3 = st.selectbox("ลูกที่ 3", options=[1, 2, 3, 4, 5, 6], index=0)

with col_btn:
    st.write("") # Spacing
    st.write("")
    if st.button("💾 บันทึกผล", type="primary", use_container_width=True):
        total = d1 + d2 + d3
        hilo_res = calculate_hilo(total)
        odd_even_res = calculate_odd_even(total)
        timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

        new_row = pd.DataFrame([{
            "Timestamp": timestamp,
            "Dice1": d1,
            "Dice2": d2,
            "Dice3": d3,
            "Total": total,
            "HiLo": hilo_res,
            "OddEven": odd_even_res
        }])

        df_updated = pd.concat([df_history, new_row], ignore_index=True)
        save_data(df_updated)
        st.success(f"บันทึกผล: {d1}-{d2}-{d3} (รวม {total} | {hilo_res} | {odd_even_res})")
        st.rerun()

st.markdown("---")

# --------------------------------------------------
# Section 2: Summary Dashboard & Analytics
# --------------------------------------------------
st.subheader("📊 2. สรุปสถิติและแนวโน้ม")

if not df_history.empty and len(df_history) > 0:
    total_rounds = len(df_history)
    high_count = len(df_history[df_history["HiLo"] == "สูง"])
    low_count = len(df_history[df_history["HiLo"] == "ต่ำ"])
    hilo11_count = len(df_history[df_history["HiLo"] == "11 ไฮโล"])

    odd_count = len(df_history[df_history["OddEven"] == "คี่"])
    even_count = len(df_history[df_history["OddEven"] == "คู่"])

    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("จำนวนรอบทั้งหมด", f"{total_rounds} รอบ")
    m2.metric("สูง (High)", f"{high_count} ({high_count/total_rounds*100:.1f}%)")
    m3.metric("ต่ำ (Low)", f"{low_count} ({low_count/total_rounds*100:.1f}%)")
    m4.metric("11 ไฮโล", f"{hilo11_count} ({hilo11_count/total_rounds*100:.1f}%)")

    st.write("")

    # Visualizations
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        # HiLo Distribution Chart
        hilo_df = df_history["HiLo"].value_counts().reset_index()
        hilo_df.columns = ["ผลลัพธ์", "จำนวน"]
        fig_hilo = px.pie(
            hilo_df, 
            values="จำนวน", 
            names="ผลลัพธ์", 
            title="สัดส่วน สูง / ต่ำ / 11 ไฮโล",
            color="ผลลัพธ์",
            color_discrete_map={"สูง": "#EF553B", "ต่ำ": "#636EFA", "11 ไฮโล": "#00CC96"}
        )
        st.plotly_chart(fig_hilo, use_container_width=True)

    with col_chart2:
        # Total Sum Distribution Chart
        total_counts = df_history["Total"].value_counts().reset_index()
        total_counts.columns = ["แต้มรวม", "จำนวนครั้ง"]
        fig_total = px.bar(
            total_counts, 
            x="แต้มรวม", 
            y="จำนวนครั้ง", 
            title="ความถี่ของแต้มรวม (3-18)",
            text_auto=True
        )
        fig_total.update_layout(xaxis=dict(tickmode='linear', tick0=3, dtick=1))
        st.plotly_chart(fig_total, use_container_width=True)

    st.markdown("---")

    # --------------------------------------------------
    # Section 3: History Table & Management
    # --------------------------------------------------
    st.subheader("📜 3. ประวัติการบันทึกข้อมูล")

    col_btn1, col_btn2, _ = st.columns([2, 2, 6])
    
    with col_btn1:
        if st.button("🗑️ ลบรายการล่าสุด", use_container_width=True):
            df_updated = df_history.iloc[:-1]
            save_data(df_updated)
            st.success("ลบรายการล่าสุดเรียบร้อย!")
            st.rerun()

    with col_btn2:
        if st.button("⚠️ ล้างประวัติทั้งหมด", type="secondary", use_container_width=True):
            empty_df = pd.DataFrame(columns=["Timestamp", "Dice1", "Dice2", "Dice3", "Total", "HiLo", "OddEven"])
            save_data(empty_df)
            st.warning("ล้างประวัติข้อมูลเรียบร้อย!")
            st.rerun()

    # Display DataFrame (Reversed order to show latest first)
    st.dataframe(df_history.iloc[::-1], use_container_width=True)

else:
    st.info("ยังไม่มีข้อมูลสถิติ กรุณาบันทึกผลลูกเต๋าด้านบนเพื่อเริ่มการวิเคราะห์")
