import pandas as pd
import numpy as np
import plotly.express as px
import re
import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Hi-Lo Smart Pattern Analyzer", layout="wide", page_icon="🎲")

# --- 1. CONNECT TO GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
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
    conn.update(data=df)

st.session_state['dice_data'] = load_data()

# --- 🎨 CUSTOM LIGHT THEME ---
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; color: #0f172a; font-family: sans-serif; }
    .marquee-container {
        width: 100%; overflow: hidden; white-space: nowrap;
        background: linear-gradient(90deg, rgba(37,99,235,0.05), rgba(124,58,237,0.08), rgba(37,99,235,0.05));
        border-radius: 12px; padding: 12px 0; margin-bottom: 20px; border: 1px solid #e2e8f0;
    }
    .marquee-text {
        display: inline-block; font-size: 2.2rem; font-weight: 900;
        background: linear-gradient(90deg, #2563eb, #7c3aed, #db2777);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        animation: marquee 12s linear infinite;
    }
    @keyframes marquee { 0% { transform: translateX(-100%); } 100% { transform: translateX(100vw); } }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    .glow-card { background: #ffffff; border-radius: 14px; padding: 20px; border: 1px solid #e2e8f0; box-shadow: 0 10px 25px -5px rgba(148, 163, 184, 0.15); }
    .card-recommend { border-top: 4px solid #2563eb; }
    .card-trend { border-top: 4px solid #7c3aed; }
    .card-stoploss-wait { border-top: 4px solid #ef4444; background: #fef2f2; }
    .card-stoploss-bet { border-top: 4px solid #10b981; background: #f0fdf4; }
    .card-title { font-size: 0.85rem; font-weight: 700; color: #64748b; margin-bottom: 8px; }
    .card-main-val { font-size: 1.8rem; font-weight: 800; margin-bottom: 6px; }
    .card-desc { font-size: 0.85rem; color: #475569; line-height: 1.5; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="marquee-container"><div class="marquee-text">By น้องตูด</div></div>', unsafe_allow_html=True)
st.title("🎲 HI-LO PATTERN LOOKBACK ANALYZER")
st.caption("ระบบแกะรอยประวัติเต๋า: ย้อนดูว่าเต๋าชุดล่าสุด เคยตามด้วยตัวเลือกไหนมากที่สุด")

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

# --- 3. PATTERN LOOKBACK ENGINE ---
def check_choice_win(choice, dice, total):
    """เช็กว่าตัวเลือกชนะหรือไม่"""
    if choice == "1ต่ำ": return (1 in dice) and (3 <= total <= 10)
    if choice == "3ต่ำ": return (3 in dice) and (3 <= total <= 10)
    if choice == "5ต่ำ": return (5 in dice) and (3 <= total <= 10)
    if choice == "6ต่ำ": return (6 in dice) and (3 <= total <= 10)
    if choice == "4สูง": return (4 in dice) and (12 <= total <= 18)
    if choice == "6สูง": return (6 in dice) and (12 <= total <= 18)
    if choice == "11ไฮโล": return total == 11
    return False

raw_df = load_data()

if not raw_df.empty and len(raw_df) >= 2:
    df = raw_df.copy()
    df["แต้มรวม (Sum)"] = df["ลูกที่ 1"] + df["ลูกที่ 2"] + df["ลูกที่ 3"]
    
    # ดึงผลตาล่าสุดมาดู
    last_dice = sorted([df.iloc[-1]["ลูกที่ 1"], df.iloc[-1]["ลูกที่ 2"], df.iloc[-1]["ลูกที่ 3"]])
    
    my_choices = ["1ต่ำ", "3ต่ำ", "5ต่ำ", "6ต่ำ", "4สูง", "6สูง", "11ไฮโล"]
    choice_stats = {c: 0 for c in my_choices}
    match_count = 0
    
    # ค้นหาในประวัติ (ข้ามตาล่าสุดไป)
    for i in range(len(df) - 1):
        hist_dice = sorted([df.iloc[i]["ลูกที่ 1"], df.iloc[i]["ลูกที่ 2"], df.iloc[i]["ลูกที่ 3"]])
        
        # ถ้าเจอชุดเต๋าที่ตรงกับตาล่าสุด
        if hist_dice == last_dice:
            match_count += 1
            next_row = df.iloc[i+1]
            next_dice = [next_row["ลูกที่ 1"], next_row["ลูกที่ 2"], next_row["ลูกที่ 3"]]
            next_sum = next_row["แต้มรวม (Sum)"]
            
            # ตรวจสอบว่าในตาถัดมา ตัวเลือกไหนชนะบ้าง
            for choice in my_choices:
                if check_choice_win(choice, next_dice, next_sum):
                    choice_stats[choice] += 1
                    
    # เรียงลำดับตัวเลือกที่ชนะบ่อยสุด
    sorted_choices = sorted(choice_stats.items(), key=lambda x: x[1], reverse=True)
    
    # กรณีมีประวัติซ้ำ
    if match_count > 0 and sorted_choices[0][1] > 0:
        recommended_pair = [sorted_choices[0][0], sorted_choices[1][0]]
        trend_name = f"พบเค้าซ้ำในอดีต {match_count} ครั้ง"
        trend_desc = f"เมื่อออกชุด {last_dice[0]}-{last_dice[1]}-{last_dice[2]} ตาถัดมามักจะตามด้วย {recommended_pair[0]} และ {recommended_pair[1]}"
    else:
        # กรณีไม่มีประวัติซ้ำ ให้ใช้ตัวเลือกพื้นฐานกระจายเสี่ยง
        recommended_pair = ["1ต่ำ", "5ต่ำ"]
        trend_name = "ยังไม่มีประวัติชุดเดิมซ้ำ"
        trend_desc = f"ยังไม่เคยพบชุดเต๋า {last_dice[0]}-{last_dice[1]}-{last_dice[2]} ในอดีต แนะนำเพลย์เซฟที่ 1ต่ำ + 5ต่ำ ไปก่อน"

    # --- 4. STOP-LOSS ENGINE (ผิด 2 ตาติด) ---
    consecutive_losses = 0
    for i in range(2, len(df)):
        sub_df = df.iloc[:i]
        curr_dice = sorted([sub_df.iloc[-1]["ลูกที่ 1"], sub_df.iloc[-1]["ลูกที่ 2"], sub_df.iloc[-1]["ลูกที่ 3"]])
        
        sub_stats = {c: 0 for c in my_choices}
        sub_matches = 0
        for j in range(len(sub_df) - 1):
            if sorted([sub_df.iloc[j]["ลูกที่ 1"], sub_df.iloc[j]["ลูกที่ 2"], sub_df.iloc[j]["ลูกที่ 3"]]) == curr_dice:
                sub_matches += 1
                n_dice = [sub_df.iloc[j+1]["ลูกที่ 1"], sub_df.iloc[j+1]["ลูกที่ 2"], sub_df.iloc[j+1]["ลูกที่ 3"]]
                n_sum = sub_df.iloc[j+1]["ลูกที่ 1"] + sub_df.iloc[j+1]["ลูกที่ 2"] + sub_df.iloc[j+1]["ลูกที่ 3"]
                for c in my_choices:
                    if check_choice_win(c, n_dice, n_sum):
                        sub_stats[c] += 1
        
        sorted_sub = sorted(sub_stats.items(), key=lambda x: x[1], reverse=True)
        pred = [sorted_sub[0][0], sorted_sub[1][0]] if (sub_matches > 0 and sorted_sub[0][1] > 0) else ["1ต่ำ", "5ต่ำ"]
        
        # ตรวจผลจริง
        act_dice = [df.iloc[i]["ลูกที่ 1"], df.iloc[i]["ลูกที่ 2"], df.iloc[i]["ลูกที่ 3"]]
        act_sum = df.iloc[i]["ลูกที่ 1"] + df.iloc[i]["ลูกที่ 2"] + df.iloc[i]["ลูกที่ 3"]
        
        w1 = check_choice_win(pred[0], act_dice, act_sum)
        w2 = check_choice_win(pred[1], act_dice, act_sum)
        
        if not w1 and not w2:
            consecutive_losses += 1
        else:
            consecutive_losses = 0

    stop_loss_active = consecutive_losses >= 2

    # --- 5. DASHBOARD DISPLAY ---
    st.markdown("### 🎯 ผลการวิเคราะห์จากประวัติ (Pattern Lookback)")
    
    if stop_loss_active:
        st.error("🛑 **ระบบตัดไฟทำงาน (Stop-Loss):** สูตรคำนวณพลาดติดต่อกัน 2 ตาแล้ว! **แนะนำให้หยุดพักรอ 3–5 ตา**")

    col1, col2, col3 = st.columns(3)

    with col1:
        if stop_loss_active:
            st.markdown(f"""
            <div class="glow-card card-stoploss-wait">
                <div class="card-title">🛡️ สถานะระบบ (System State)</div>
                <div class="card-main-val" style="color: #dc2626;">🛑 STOP / WAIT</div>
                <div class="card-desc">• แพ้ติดกัน 2 ตาแล้ว หยุดพักดูทรงเต๋าก่อน</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="glow-card card-stoploss-bet">
                <div class="card-title">🛡️ สถานะระบบ (System State)</div>
                <div class="card-main-val" style="color: #10b981;">✅ พร้อมลุย (BET)</div>
                <div class="card-desc">• สถานะปกติ สามารถแทงตามตัวเลือกแนะนำได้</div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="glow-card card-recommend">
            <div class="card-title">🎯 2 ตัวเลือกแนะนำ (จากประวัติ)</div>
            <div class="card-main-val" style="color: #2563eb;">{recommended_pair[0]} + {recommended_pair[1]}</div>
            <div class="card-desc">• แนะนำแบ่งทุนลงเท่าๆ กันทั้ง 2 ตัวเลือก</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="glow-card card-trend">
            <div class="card-title">🔍 สถิติลักษณะเค้าเต๋า</div>
            <div class="card-main-val" style="font-size: 1.3rem;">{trend_name}</div>
            <div class="card-desc">• {trend_desc}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📋 ตารางข้อมูลประวัติ", "🎲 ตารางความน่าจะเป็นของ 7 ตัวเลือก"])
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
        st.subheader(f"สถิติตัวเลือกถัดไป เมื่อก่อนหน้าออก {last_dice[0]}-{last_dice[1]}-{last_dice[2]}")
        stat_df = pd.DataFrame([{"ตัวเลือก": k, "จำนวนครั้งที่เคยชนะ": v} for k, v in choice_stats.items()]).sort_values(by="จำนวนครั้งที่เคยชนะ", ascending=False)
        st.dataframe(stat_df, use_container_width=True)

else:
    st.info("👈 เริ่มต้นกรอกชุดตัวเลขทางแถบซ้ายอย่างน้อย 2 ตาขึ้นไป เพื่อเริ่มย้อนดูประวัติ pattern ครับ")
