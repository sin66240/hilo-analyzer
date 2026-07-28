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
    .card-single { border-top: 4px solid #f59e0b; }
    .card-single-skip { border-top: 4px solid #64748b; background: #f1f5f9; }
    .card-pair { border-top: 4px solid #2563eb; }
    .card-pattern { border-top: 4px solid #7c3aed; }
    .card-eleven { border-top: 4px solid #dc2626; }
    .card-stoploss-wait { border-top: 4px solid #ef4444; background: #fef2f2; }
    .card-stoploss-bet { border-top: 4px solid #10b981; background: #f0fdf4; }
    .card-title { font-size: 0.85rem; font-weight: 700; text-transform: uppercase; color: #64748b; margin-bottom: 8px; }
    .card-main-val { font-size: 1.8rem; font-weight: 800; margin-bottom: 6px; }
    .card-winrate { font-size: 1rem; font-weight: 700; color: #10b981; background: #ecfdf5; padding: 4px 10px; border-radius: 20px; display: inline-block; margin-bottom: 10px; border: 1px solid #a7f3d0; }
    .card-status-skip { font-size: 0.95rem; font-weight: 700; color: #d97706; background: #fffbe2; padding: 4px 10px; border-radius: 20px; display: inline-block; margin-bottom: 10px; border: 1px solid #fde68a; }
    .card-status-wait { font-size: 0.95rem; font-weight: 700; color: #dc2626; background: #fee2e2; padding: 4px 10px; border-radius: 20px; display: inline-block; margin-bottom: 10px; border: 1px solid #fca5a5; }
    .card-desc { font-size: 0.85rem; color: #475569; line-height: 1.5; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="marquee-container">
    <div class="marquee-text">By น้องตูด</div>
</div>
""", unsafe_allow_html=True)

st.title("🎲 HI-LO SINGLE & PAIR ANALYZER")
st.caption("ระบบวิเคราะห์สถิติเน้น เต็งเลข + โต๊ดคู่ + จับรูปแบบชุดเลขนำโชค (Pattern Follower)")

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
recent_n = st.sidebar.slider("ช่วงตาสั้นเพื่อวิเคราะห์แนวโน้ม (Moving Avg):", 5, 30, 10)
confidence_threshold = st.sidebar.slider("เกณฑ์ความมั่นใจขั้นต่ำเพื่อสั่งแทง (%):", 40.0, 60.0, 48.0, 0.5) / 100.0

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

# --- 3. DATA PROCESSING & STOP-LOSS ENGINE ---
raw_df = load_data()

if not raw_df.empty:
    df = raw_df.copy()
    df["แต้มรวม (Sum)"] = df["ลูกที่ 1"] + df["ลูกที่ 2"] + df["ลูกที่ 3"]
    total_rounds = len(df)
    recent_df = df.tail(recent_n)
    
    # 1. นับสถิติโต๊ดคู่ทั้งหมด
    pair_counts = {}
    for _, row in df.iterrows():
        d = sorted([int(row["ลูกที่ 1"]), int(row["ลูกที่ 2"]), int(row["ลูกที่ 3"])])
        pairs = [(d[0], d[1]), (d[1], d[2]), (d[0], d[2])]
        for p in pairs:
            if p[0] != p[1]: # เน้นโต๊ดต่างหน้า
                pair_counts[p] = pair_counts.get(p, 0) + 1

    last_seen = {}
    for face in range(1, 7):
        indices = df[(df["ลูกที่ 1"] == face) | (df["ลูกที่ 2"] == face) | (df["ลูกที่ 3"] == face)].index
        last_seen[face] = (total_rounds - 1) - indices[-1] if len(indices) > 0 else total_rounds

    # 2. คำนวณ EMA สำหรับเต็งเลข
    n_recent = min(total_rounds, recent_n)
    weights = np.exp(np.linspace(-2.0, 0, n_recent))
    weights /= weights.sum()

    recent_rounds = df.tail(n_recent)
    weighted_counts = {num: 0.0 for num in range(1, 7)}
    for idx, (_, row) in enumerate(recent_rounds.iterrows()):
        for die in [row["ลูกที่ 1"], row["ลูกที่ 2"], row["ลูกที่ 3"]]:
            weighted_counts[die] += weights[idx]

    estimated_probs = {}
    counts_array = list(weighted_counts.values())
    mean_c = np.mean(counts_array)
    std_c = np.std(counts_array) if np.std(counts_array) > 0 else 1.0

    for num in range(1, 7):
        p_single = weighted_counts[num] / 3.0
        cold_bonus = 0.02 if last_seen[num] >= 6 else 0.0
        p_single_adjusted = max(0.05, min(0.35, p_single + cold_bonus))
        estimated_probs[num] = 1.0 - ((1.0 - p_single_adjusted) ** 3)

    top_short_face = max(estimated_probs, key=estimated_probs.get)
    best_confidence = estimated_probs[top_short_face]
    best_z = (weighted_counts[top_short_face] - mean_c) / std_c

    # ดึงคู่โต๊ดพ่วงเต็งเด่น
    pair_with_top = {p: count for p, count in pair_counts.items() if top_short_face in p}
    best_pair_combo = max(pair_with_top, key=pair_with_top.get) if pair_with_top else (top_short_face, 2 if top_short_face!=2 else 1)

    # 3. 🔍 PATTERN FOLLOWER ENGINE
    last_round_dice = sorted([int(df.iloc[-1]["ลูกที่ 1"]), int(df.iloc[-1]["ลูกที่ 2"]), int(df.iloc[-1]["ลูกที่ 3"])])
    pattern_matched_pairs = {}
    pattern_match_count = 0

    for i in range(len(df) - 1):
        hist_dice = sorted([int(df.iloc[i]["ลูกที่ 1"]), int(df.iloc[i]["ลูกที่ 2"]), int(df.iloc[i]["ลูกที่ 3"])])
        if hist_dice == last_round_dice:
            pattern_match_count += 1
            next_row = df.iloc[i+1]
            next_dice = [int(next_row["ลูกที่ 1"]), int(next_row["ลูกที่ 2"]), int(next_row["ลูกที่ 3"])]
            p1, p2, p3 = (min(next_dice[0], next_dice[1]), max(next_dice[0], next_dice[1])), \
                         (min(next_dice[1], next_dice[2]), max(next_dice[1], next_dice[2])), \
                         (min(next_dice[0], next_dice[2]), max(next_dice[0], next_dice[2]))
            for p in [p1, p2, p3]:
                if p[0] != p[1]:
                    pattern_matched_pairs[p] = pattern_matched_pairs.get(p, 0) + 1

    best_pattern_pair = max(pattern_matched_pairs, key=pattern_matched_pairs.get) if pattern_matched_pairs else None

    # สั่ง BET / SKIP เต็ง
    is_stat_significance = best_z >= 0.7 or last_seen[top_short_face] >= 6
    single_action = "BET" if (best_confidence >= confidence_threshold) and is_stat_significance else "SKIP"

    # --- 4. 🛑 STOP-LOSS & BACKTESTING ENGINE (ระบบคำนวณย้อนหลังตรวจผลผิด 2 ตาติด) ---
    results_history = []
    
    # วนลูปย้อนหลังเพื่อคำนวณสถานะ Win/Loss ของคู่โต๊ด
    for idx in range(1, len(df)):
        sub_df = df.iloc[:idx]
        actual_dice = [int(df.iloc[idx]["ลูกที่ 1"]), int(df.iloc[idx]["ลูกที่ 2"]), int(df.iloc[idx]["ลูกที่ 3"])]
        
        # คำนวณคู่โต๊ดสถิติ ณ ตานั้น
        sub_pair_counts = {}
        for _, r in sub_df.iterrows():
            d = sorted([int(r["ลูกที่ 1"]), int(r["ลูกที่ 2"]), int(r["ลูกที่ 3"])])
            for p in [(d[0], d[1]), (d[1], d[2]), (d[0], d[2])]:
                if p[0] != p[1]:
                    sub_pair_counts[p] = sub_pair_counts.get(p, 0) + 1
        
        pred_pair = max(sub_pair_counts, key=sub_pair_counts.get) if sub_pair_counts else (1, 2)
        
        # ตรวจผลว่าเต๋าจริงออกคู่โต๊ดที่ทำนายไหม
        is_win = (pred_pair[0] in actual_dice) and (pred_pair[1] in actual_dice)
        results_history.append("ถูก" if is_win else "ผิด")

    # ตรวจสอบสถานะการหยุดเล่น (Stop-Loss)
    stop_loss_status = "✅ BET"
    if len(results_history) >= 2:
        if results_history[-1] == "ผิด" and results_history[-2] == "ผิด":
            stop_loss_status = "🛑 WAIT"
        elif len(results_history) >= 3 and results_history[-2] == "ผิด" and results_history[-3] == "ผิด" and results_history[-1] == "ผิด":
            stop_loss_status = "🛑 WAIT"

    # --- 5. DASHBOARD DISPLAY ---
    st.markdown("### 🎯 สรุปตัวเลือกเดิมพันแนะนำ (เต็ง + โต๊ด)")
    
    # แสดงป้ายเตือนใหญ่ถ้าเข้าเงื่อนไข Stop-Loss
    if stop_loss_status == "🛑 WAIT":
        st.error("🛑 **ระบบตัดไฟทำงาน (Stop-Loss):** สูตรคำนวณผิดติดต่อกัน 2 ตาแล้ว! **แนะนำให้หยุดพักรอ 3-5 ตา** เพื่อให้กราฟกลับเข้าสู่รูปแบบเดิมก่อนลงเงิน")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if stop_loss_status == "🛑 WAIT":
            st.markdown(f"""
            <div class="glow-card card-stoploss-wait">
                <div class="card-title">🛡️ สถานะระบบ (System State)</div>
                <div class="card-main-val" style="color: #dc2626;">🛑 STOP / WAIT</div>
                <div class="card-status-wait">⚠️ ผิดติดกัน 2 ตาแล้ว</div>
                <div class="card-desc">• <b>คำแนะนำ:</b> ห้ามลงเดิมพันตานี้ ให้สังเกตการณ์ไปก่อน</div>
            </div>
            """, unsafe_allow_html=True)
        elif single_action == "BET":
            st.markdown(f"""
            <div class="glow-card card-single">
                <div class="card-title">🎲 เต็งเด่น (Single)</div>
                <div class="card-main-val">🎯 เต็งแต้ม {top_short_face}</div>
                <div class="card-winrate">Conf: {best_confidence*100:.1f}%</div>
                <div class="card-desc">
                    • <b>สถานะ:</b> สัญญาณเข้าเกณฑ์เด่นชัด<br>
                    • <b>แต้มรอง:</b> แต้ม {max(last_seen, key=last_seen.get)} อั้นนานสุด
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="glow-card card-single-skip">
                <div class="card-title">🎲 เต็งเด่น (Single)</div>
                <div class="card-main-val">⏸️ SKIP (ข้าม)</div>
                <div class="card-status-skip">⚠️ ความมั่นใจต่ำกว่าเกณฑ์</div>
                <div class="card-desc">• แนะนำข้ามตานี้ไปก่อนเพื่อรักษา Win Rate</div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="glow-card card-pair">
            <div class="card-title">👯 โต๊ดคู่หลัก (Stat Pair)</div>
            <div class="card-main-val">คู่ {best_pair_combo[0]} - {best_pair_combo[1]}</div>
            <div class="card-winrate">🎯 ออกบ่อยสุดในเกม</div>
            <div class="card-desc">• จับคู่พ่วงสถิติระหว่าง <b>เต็ง {top_short_face}</b> กับแต้มร่วม</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        if best_pattern_pair and pattern_match_count > 0:
            st.markdown(f"""
            <div class="glow-card card-pattern">
                <div class="card-title">🔄 โต๊ดตามเค้าชุดเลข (Pattern)</div>
                <div class="card-main-val">คู่ {best_pattern_pair[0]} - {best_pattern_pair[1]}</div>
                <div class="card-winrate">🔥 เคยเกิด {pattern_match_count} ครั้ง</div>
                <div class="card-desc">• ถัดจากชุด <b>{last_round_dice[0]}-{last_round_dice[1]}-{last_round_dice[2]}</b> ในอดีต คู่นี้ออกบ่อยสุด</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="glow-card card-pattern">
                <div class="card-title">🔄 โต๊ดตามเค้าชุดเลข (Pattern)</div>
                <div class="card-main-val">รอประวัติซ้ำ</div>
                <div class="card-status-skip">ℹ️ ยังไม่มีประวัติชุดเดิม</div>
                <div class="card-desc">• ระบบกำลังเก็บสถิติชุดเลข <b>{last_round_dice[0]}-{last_round_dice[1]}-{last_round_dice[2]}</b></div>
            </div>
            """, unsafe_allow_html=True)

    with col4:
        triple_count = (df["ลูกที่ 1"] == df["ลูกที่ 2"]) & (df["ลูกที่ 2"] == df["ลูกที่ 3"])
        st.markdown(f"""
        <div class="glow-card card-eleven">
            <div class="card-title">💥 สถิติตอง (Triple Alert)</div>
            <div class="card-main-val">{triple_count.sum()} ครั้ง</div>
            <div class="card-winrate">⚠️ ระวังการเสียเงินฟรี</div>
            <div class="card-desc">• แทงเต็งและโต๊ดช่วยกระจายความเสี่ยงตองได้ดีที่สุด</div>
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
        st.subheader("สถิติโต๊ดคู่ทั้งหมด")
        pair_df = pd.DataFrame([{"คู่โต๊ด": f"{k[0]} - {k[1]}", "จำนวนครั้งที่ออก": v} for k, v in pair_counts.items()]).sort_values(by="จำนวนครั้งที่ออก", ascending=False)
        st.dataframe(pair_df, use_container_width=True)

else:
    st.info("👈 เริ่มต้นกรอกชุดตัวเลขทางแถบซ้ายได้เลยครับ เช่น พิมพ์ `243 333 562 565` แล้วกดบันทึก")
