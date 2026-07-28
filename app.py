import pandas as pd
import numpy as np
import plotly.express as px
import re
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# ตั้งค่าหน้าเว็บแบบ Wide
st.set_page_config(page_title="Hi-Lo Smart Analyzer", layout="wide", page_icon="🎲")

# --- 1. CONNECT TO GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    """โหลดข้อมูลประวัติจาก Google Sheets"""
    try:
        df = conn.read(ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=["ตาที่ (Round)", "ลูกที่ 1", "ลูกที่ 2", "ลูกที่ 3"])
        
        required_cols = ["ตาที่ (Round)", "ลูกที่ 1", "ลูกที่ 2", "ลูกที่ 3"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
                
        df["ตาที่ (Round)"] = pd.to_numeric(df["ตาที่ (Round)"], errors='coerce')
        df["ลูกที่ 1"] = pd.to_numeric(df["ลูกที่ 1"], errors='coerce')
        df["ลูกที่ 2"] = pd.to_numeric(df["ลูกที่ 2"], errors='coerce')
        df["ลูกที่ 3"] = pd.to_numeric(df["ลูกที่ 3"], errors='coerce')
        
        df = df.dropna(subset=["ตาที่ (Round)", "ลูกที่ 1", "ลูกที่ 2", "ลูกที่ 3"])
        df = df.astype({"ตาที่ (Round)": int, "ลูกที่ 1": int, "ลูกที่ 2": int, "ลูกที่ 3": int})
        return df
    except Exception:
        return pd.DataFrame(columns=["ตาที่ (Round)", "ลูกที่ 1", "ลูกที่ 2", "ลูกที่ 3"])

def save_data(df):
    """บันทึกข้อมูลทั้งหมดกลับลง Google Sheets"""
    conn.update(data=df)

# ดึงข้อมูลเข้า Session State จาก Google Sheets
st.session_state['dice_data'] = load_data()

# --- 🎨 CUSTOM LIGHT THEME ---
st.markdown("""
<style>
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .marquee-container {
        width: 100%;
        overflow: hidden;
        white-space: nowrap;
        background: linear-gradient(90deg, rgba(37,99,235,0.05), rgba(124,58,237,0.08), rgba(37,99,235,0.05));
        border-radius: 12px;
        padding: 12px 0;
        margin-bottom: 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(148, 163, 184, 0.1);
    }
    .marquee-text {
        display: inline-block;
        font-size: 2.2rem;
        font-weight: 900;
        background: linear-gradient(90deg, #2563eb, #7c3aed, #db2777);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 15px rgba(124, 58, 237, 0.2);
        animation: marquee 12s linear infinite;
    }
    @keyframes marquee {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100vw); }
    }
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    h1 {
        background: linear-gradient(90deg, #2563eb, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }
    .glow-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 10px 25px -5px rgba(148, 163, 184, 0.15);
        transition: all 0.3s ease;
        height: 100%;
    }
    .card-recommend { border-top: 4px solid #2563eb; }
    .card-trend { border-top: 4px solid #7c3aed; }
    .card-stoploss-wait { border-top: 4px solid #ef4444; background: #fef2f2; }
    .card-stoploss-bet { border-top: 4px solid #10b981; background: #f0fdf4; }
    .card-title { font-size: 0.85rem; font-weight: 700; text-transform: uppercase; color: #64748b; margin-bottom: 8px; }
    .card-main-val { font-size: 1.8rem; font-weight: 800; margin-bottom: 6px; }
    .card-winrate { font-size: 1rem; font-weight: 700; color: #10b981; background: #ecfdf5; padding: 4px 10px; border-radius: 20px; display: inline-block; margin-bottom: 10px; border: 1px solid #a7f3d0; }
    .card-status-wait { font-size: 0.95rem; font-weight: 700; color: #dc2626; background: #fee2e2; padding: 4px 10px; border-radius: 20px; display: inline-block; margin-bottom: 10px; border: 1px solid #fca5a5; }
    .card-desc { font-size: 0.85rem; color: #475569; line-height: 1.5; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="marquee-container">
    <div class="marquee-text">By น้องตูด</div>
</div>
""", unsafe_allow_html=True)

st.title("🎲 HI-LO CUSTOM PAIR ANALYZER")
st.caption("ระบบวิเคราะห์เลือก 2 ตัวเลือกจากสูตรส่วนตัว (1ต่ำ, 3ต่ำ, 5ต่ำ, 6ต่ำ, 4สูง, 6สูง, 11ไฮโล)")

# --- 2. SIDEBAR ---
st.sidebar.markdown("### ⚡ บันทึกข้อมูลรวดเร็ว")
raw_input = st.sidebar.text_area("กรอกชุดตัวเลขผลทอย:", height=100, placeholder="243 333 562 565")

if st.sidebar.button("📥 บันทึกชุดตัวเลข"):
    if raw_input.strip():
        matches = re.findall(r'[1-6]{3}', raw_input)
        if matches:
            current_df = load_data()
            new_rows = []
            start_round = len(current_df) + 1
            for idx, match in enumerate(matches):
                new_rows.append({
                    "ตาที่ (Round)": start_round + idx,
                    "ลูกที่ 1": int(match[0]),
                    "ลูกที่ 2": int(match[1]),
                    "ลูกที่ 3": int(match[2])
                })
            updated_df = pd.concat([current_df, pd.DataFrame(new_rows)], ignore_index=True)
            save_data(updated_df)
            st.session_state['dice_data'] = updated_df
            st.sidebar.success(f"บันทึกสำเร็จ {len(matches)} ตา!")
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 ตั้งค่าการคัดกรอง (Filter)")
recent_n = st.sidebar.slider("ช่วงตาสั้นเพื่อวิเคราะห์เค้าเต๋า (Moving Avg):", 3, 15, 3)

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ ลบรายการล่าสุด"):
    current_df = load_data()
    if not current_df.empty:
        updated_df = current_df.iloc[:-1]
        save_data(updated_df)
        st.session_state['dice_data'] = updated_df
        st.sidebar.success("ลบข้อมูลรายการล่าสุดเรียบร้อยแล้ว!")
        st.rerun()

if st.sidebar.button("⚠️ ล้างประวัติข้อมูลทั้งหมด"):
    empty_df = pd.DataFrame(columns=["ตาที่ (Round)", "ลูกที่ 1", "ลูกที่ 2", "ลูกที่ 3"])
    save_data(empty_df)
    st.session_state['dice_data'] = empty_df
    st.sidebar.warning("ล้างประวัติข้อมูลเรียบร้อยแล้ว!")
    st.rerun()

# --- 3. DATA PROCESSING & CUSTOM PAIR ENGINE ---
raw_df = load_data()

if not raw_df.empty:
    df = raw_df.copy()
    df["แต้มรวม (Sum)"] = df["ลูกที่ 1"] + df["ลูกที่ 2"] + df["ลูกที่ 3"]
    df["is_11"] = df["แต้มรวม (Sum)"] == 11
    df["is_low"] = (df["แต้มรวม (Sum)"] >= 3) & (df["แต้มรวม (Sum)"] <= 10) & (~df["is_11"])
    df["is_high"] = (df["แต้มรวม (Sum)"] >= 12) & (df["แต้มรวม (Sum)"] <= 18) & (~df["is_11"])

    total_rounds = len(df)
    
    # 🔍 วิเคราะห์เค้าเต๋าล่าสุด 3 ตา
    n_lookback = min(total_rounds, recent_n)
    recent_rounds = df.tail(n_lookback)
    
    low_count = recent_rounds["is_low"].sum()
    high_count = recent_rounds["is_high"].sum()

    # เลือก 2 ตัวเลือกตามชุดสูตรของคุณ
    if low_count >= 2:
        recommended_pair = ["1ต่ำ", "5ต่ำ"]
        trend_name = "เต๋าไหลต่ำ (เน้นกินกว้าง)"
        trend_desc = "3 ตาล่าสุดเน้นออกต่ำ แนะนำจับคู่เซฟหน้าต่ำกว้างๆ"
    elif high_count >= 2:
        recommended_pair = ["6สูง", "11ไฮโล"]
        trend_name = "เต๋าไหลสูง (ดักสูง + ลุ้นแจ็คพอต)"
        trend_desc = "3 ตาล่าสุดเน้นออกสูง แนะนำดักหน้า 6สูง พร้อมลุ้น 11 ไฮโล"
    else:
        recommended_pair = ["1ต่ำ", "4สูง"]
        trend_name = "เต๋าสลับ / สวิง (ดัก 2 ฝั่ง)"
        trend_desc = "เต๋าออกสลับสูง-ต่ำ แนะนำแทงดักทั้งสองฝั่ง"

    # --- 4. 🛑 STOP-LOSS ENGINE (ตรวจผลย้อนหลังว่าแพ้ 2 ตาติดไหม) ---
    consecutive_losses = 0
    
    # คำนวณตรวจผลย้อนหลังง่ายๆ เพื่อคุมความเสี่ยง
    for i in range(1, len(df)):
        sub_recent = df.iloc[max(0, i-3):i]
        sub_low = sub_recent["is_low"].sum()
        sub_high = sub_recent["is_high"].sum()
        
        # คู่ที่ทำนายไว้ในตานั้น
        if sub_low >= 2:
            pred = ["1ต่ำ", "5ต่ำ"]
        elif sub_high >= 2:
            pred = ["6สูง", "11ไฮโล"]
        else:
            pred = ["1ต่ำ", "4สูง"]

        # ตรวจผลตาจริง (df.iloc[i])
        act_dice = [df.iloc[i]["ลูกที่ 1"], df.iloc[i]["ลูกที่ 2"], df.iloc[i]["ลูกที่ 3"]]
        act_sum = df.iloc[i]["แต้มรวม (Sum)"]
        
        # ฟังก์ชันเช็กว่าชนะหรือไม่
        def check_win(choice, dice, total):
            if choice == "1ต่ำ": return (1 in dice) and (3 <= total <= 10)
            if choice == "3ต่ำ": return (3 in dice) and (3 <= total <= 10)
            if choice == "5ต่ำ": return (5 in dice) and (3 <= total <= 10)
            if choice == "6ต่ำ": return (6 in dice) and (3 <= total <= 10)
            if choice == "4สูง": return (4 in dice) and (12 <= total <= 18)
            if choice == "6สูง": return (6 in dice) and (12 <= total <= 18)
            if choice == "11ไฮโล": return total == 11
            return False

        win1 = check_win(pred[0], act_dice, act_sum)
        win2 = check_win(pred[1], act_dice, act_sum)
        
        # ถ้าไม่ถูกเลยสักตัวถือว่าแพ้
        if not win1 and not win2:
            consecutive_losses += 1
        else:
            consecutive_losses = 0

    stop_loss_active = consecutive_losses >= 2

    # --- 5. DASHBOARD DISPLAY ---
    st.markdown("### 🎯 สรุปผลการวิเคราะห์สูตร (แทง 2 ตัวเลือก)")
    
    if stop_loss_active:
        st.error("🛑 **ระบบตัดไฟทำงาน (Stop-Loss):** สูตรแพ้ติดต่อกัน 2 ตาแล้ว! **แนะนำให้หยุดพักสังเกตการณ์ 3–5 ตา** ก่อนเริ่มวางเงินใหม่")

    col1, col2, col3 = st.columns(3)

    with col1:
        if stop_loss_active:
            st.markdown(f"""
            <div class="glow-card card-stoploss-wait">
                <div class="card-title">🛡️ สถานะระบบ (System State)</div>
                <div class="card-main-val" style="color: #dc2626;">🛑 STOP / WAIT</div>
                <div class="card-status-wait">⚠️ แพ้ติดกัน {consecutive_losses} ตา</div>
                <div class="card-desc">• <b>คำแนะนำ:</b> หยุดพักทันทีเพื่อเซฟทุน</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="glow-card card-stoploss-bet">
                <div class="card-title">🛡️ สถานะระบบ (System State)</div>
                <div class="card-main-val" style="color: #10b981;">✅ พร้อมลุย (BET)</div>
                <div class="card-winrate">ความเสี่ยงปกติ</div>
                <div class="card-desc">• กราฟอยู่ในเกณฑ์ สามารถแทงตามชุดแนะนำได้</div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="glow-card card-recommend">
            <div class="card-title">🎯 ตัวเลือกแนะนำ (2 ตัวเลือก)</div>
            <div class="card-main-val" style="color: #2563eb;">{recommended_pair[0]} + {recommended_pair[1]}</div>
            <div class="card-desc">• ลงเงินเดิมพันเท่าๆ กันทั้ง 2 หน้า</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="glow-card card-trend">
            <div class="card-title">📈 แนวโน้มเค้าเต๋า</div>
            <div class="card-main-val" style="font-size: 1.3rem;">{trend_name}</div>
            <div class="card-desc">• {trend_desc}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📋 ตารางข้อมูลประวัติ", "🎲 สถิติคู่ออกผสม"])
    with tab1:
        st.subheader("ตารางประวัติผลลัพธ์ทั้งหมด")
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="hilo_editor")
        save_cols = ["ตาที่ (Round)", "ลูกที่ 1", "ลูกที่ 2", "ลูกที่ 3"]
        clean_edited_df = edited_df[save_cols].dropna(how='all')
        if not clean_edited_df.equals(raw_df):
            save_data(clean_edited_df)
            st.session_state['dice_data'] = clean_edited_df
            st.rerun()
    with tab2:
        st.subheader("สถิติต่ำ / สูง / 11 ไฮโล")
        summary_data = {
            "ฝั่ง": ["ต่ำ (Low)", "สูง (High)", "11 ไฮโล"],
            "จำนวนครั้ง": [df["is_low"].sum(), df["is_high"].sum(), df["is_11"].sum()]
        }
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)

else:
    st.info("👈 เริ่มต้นกรอกชุดตัวเลขทางแถบซ้ายได้เลยครับ เช่น พิมพ์ `243 333 562 565` แล้วกดบันทึก")
