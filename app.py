import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import re
import os

DATA_FILE = "hilo_history.csv"

# ตั้งค่าหน้าเว็บแบบ Wide
st.set_page_config(page_title="Hi-Lo Smart Analyzer", layout="wide", page_icon="🎲")

# --- 🎨 CUSTOM LIGHT THEME WITH NEON GLOW TEXT ---
st.markdown("""
<style>
    /* พื้นหลังหลักสไตล์สว่าง สะอาดตา คลีนๆ */
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* ตกแต่ง Sidebar โทนสว่างนุ่มนวล */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    /* หัวข้อหลักแบบไล่เฉดสีเน้นความเด่น */
    h1 {
        background: linear-gradient(90deg, #2563eb, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }
    
    /* การ์ดสรุปคำแนะนำเดิมพันโทนขาว พร้อมเงาและขอบเรืองแสง (Glow) */
    .glow-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 10px 25px -5px rgba(148, 163, 184, 0.15);
        transition: all 0.3s ease;
        height: 100%;
    }
    .glow-card:hover {
        transform: translateY(-4px);
    }
    
    /* เอฟเฟกต์ตัวอักษรและขอบเรืองแสงแบ่งตามประเภท */
    .card-single { 
        border-top: 4px solid #f59e0b; 
        box-shadow: 0 8px 20px -4px rgba(245, 158, 11, 0.25);
    }
    .card-single .card-main-val {
        color: #d97706;
        text-shadow: 0 0 10px rgba(245, 158, 11, 0.3);
    }
    
    .card-pair { 
        border-top: 4px solid #2563eb; 
        box-shadow: 0 8px 20px -4px rgba(37, 99, 235, 0.25);
    }
    .card-pair .card-main-val {
        color: #2563eb;
        text-shadow: 0 0 10px rgba(37, 99, 235, 0.3);
    }
    
    .card-mix { 
        border-top: 4px solid #059669; 
        box-shadow: 0 8px 20px -4px rgba(5, 150, 105, 0.25);
    }
    .card-mix .card-main-val {
        color: #059669;
        text-shadow: 0 0 10px rgba(5, 150, 105, 0.3);
    }
    
    .card-eleven { 
        border-top: 4px solid #dc2626; 
        box-shadow: 0 8px 20px -4px rgba(220, 38, 38, 0.25);
    }
    .card-eleven .card-main-val {
        color: #dc2626;
        text-shadow: 0 0 10px rgba(220, 38, 38, 0.3);
    }
    
    .card-title {
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748b;
        margin-bottom: 8px;
    }
    .card-main-val {
        font-size: 1.8rem;
        font-weight: 800;
        margin-bottom: 10px;
    }
    .card-desc {
        font-size: 0.85rem;
        color: #475569;
        line-height: 1.5;
    }

    /* ตกแต่ง Tabs สไตล์สว่าง */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 8px;
        color: #64748b;
        border: 1px solid #e2e8f0;
        padding: 10px 18px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border-color: #2563eb !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }

    /* ตกแต่งปุ่มกด */
    .stButton>button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: #ffffff;
        border: none;
        border-radius: 8px;
        font-weight: 700;
        padding: 8px 16px;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. PERSISTENT DATA FUNCTIONS ---
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["ตาที่ (Round)", "ลูกที่ 1", "ลูกที่ 2", "ลูกที่ 3"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

if 'dice_data' not in st.session_state:
    st.session_state['dice_data'] = load_data()

st.title("🎲 HI-LO STATISTICAL ANALYZER")
st.caption("ระบบวิเคราะห์สถิติลูกเต๋าไฮโล | 4 ทฤษฎีประมวลผลเรียลไทม์ | สรุปช้อยส์เดิมพันเด่น")

# --- 2. SIDEBAR - FAST INPUT & SLIDER ---
st.sidebar.markdown("### ⚡ บันทึกข้อมูลรวดเร็ว")
st.sidebar.info("พิมพ์ชุดตัวเลข 3 หลัก เช่น `243 333 562 565`")

raw_input = st.sidebar.text_area("กรอกชุดตัวเลขผลทอย:", height=100, placeholder="243 333 562 565")

if st.sidebar.button("📥 บันทึกชุดตัวเลข"):
    if raw_input.strip():
        matches = re.findall(r'[1-6]{3}', raw_input)
        if matches:
            current_df = st.session_state['dice_data']
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
            st.session_state['dice_data'] = updated_df
            save_data(updated_df)
            st.sidebar.success(f"บันทึกสำเร็จ {len(matches)} ตา!")
            st.rerun()

st.sidebar.markdown("---")
recent_n = st.sidebar.slider("ช่วงตาสั้นเพื่อวิเคราะห์แนวโน้ม (Moving Avg):", 5, 30, 10)

if st.sidebar.button("⚠️ ล้างประวัติข้อมูลทั้งหมด"):
    empty_df = pd.DataFrame(columns=["ตาที่ (Round)", "ลูกที่ 1", "ลูกที่ 2", "ลูกที่ 3"])
    st.session_state['dice_data'] = empty_df
    save_data(empty_df)
    st.rerun()

# --- 3. DATA PROCESSING ---
raw_df = st.session_state['dice_data']

if not raw_df.empty:
    df = raw_df.copy()
    df["แต้มรวม (Sum)"] = df["ลูกที่ 1"] + df["ลูกที่ 2"] + df["ลูกที่ 3"]
    
    def check_result(row):
        d1, d2, d3 = row["ลูกที่ 1"], row["ลูกที่ 2"], row["ลูกที่ 3"]
        if d1 == d2 == d3:
            return "ตอง (Triple)"
        elif row["แต้มรวม (Sum)"] >= 11:
            return "สูง (High)"
        else:
            return "ต่ำ (Low)"

    df["ผลลัพธ์ (Result)"] = df.apply(check_result, axis=1)
    
    total_rounds = len(df)
    recent_df = df.tail(recent_n)
    
    all_dice_long = pd.concat([df["ลูกที่ 1"], df["ลูกที่ 2"], df["ลูกที่ 3"]])
    long_counts = all_dice_long.value_counts().reindex(range(1, 7), fill_value=0)
    
    all_dice_short = pd.concat([recent_df["ลูกที่ 1"], recent_df["ลูกที่ 2"], recent_df["ลูกที่ 3"]])
    short_counts = all_dice_short.value_counts().reindex(range(1, 7), fill_value=0)
    
    last_seen = {}
    for face in range(1, 7):
        indices = df[(df["ลูกที่ 1"] == face) | (df["ลูกที่ 2"] == face) | (df["ลูกที่ 3"] == face)].index
        if len(indices) > 0:
            last_seen[face] = (total_rounds - 1) - indices[-1]
        else:
            last_seen[face] = total_rounds

    pair_counts = {}
    combo_mix = {}
    for _, row in df.iterrows():
        d = sorted([row["ลูกที่ 1"], row["ลูกที่ 2"], row["ลูกที่ 3"]])
        res = row["ผลลัพธ์ (Result)"]
        pairs = [(d[0], d[1]), (d[1], d[2]), (d[0], d[2])]
        for p in pairs:
            pair_counts[p] = pair_counts.get(p, 0) + 1
        for face in set(d):
            if res in ["สูง (High)", "ต่ำ (Low)"]:
                label = f"{face}-{res.split()[0]}"
                combo_mix[label] = combo_mix.get(label, 0) + 1

    sorted_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)
    best_pair = sorted_pairs[0][0] if sorted_pairs else (1, 2)
    sorted_combos = sorted(combo_mix.items(), key=lambda x: x[1], reverse=True)
    best_combo = sorted_combos[0][0] if sorted_combos else "3-ต่ำ"

    eleven_count = (df["แต้มรวม (Sum)"] == 11).sum()
    eleven_pct = (eleven_count / total_rounds) * 100
    low_faces = long_counts[1] + long_counts[2] + long_counts[3]
    high_faces = long_counts[4] + long_counts[5] + long_counts[6]

    top_short_face = short_counts.sort_values(ascending=False).index[0]
    top_cold_face = max(last_seen, key=last_seen.get)

    # --- 4. LIGHT NEON SUMMARY RECOMMENDATIONS DASHBOARD ---
    st.markdown("### 🎯 สรุปตัวเลือกเดิมพันแนะนำ")
    
    rec_col1, rec_col2, rec_col3, rec_col4 = st.columns(4)
    
    with rec_col1:
        st.markdown(f"""
        <div class="glow-card card-single">
            <div class="card-title">🎲 เต็งเด่น (Single)</div>
            <div class="card-main-val">เต็งแต้ม {top_short_face}</div>
            <div class="card-desc">
                • <b>ตามกระแส:</b> หน้า {top_short_face} ฮอตสุดใน {recent_n} ตา<br>
                • <b>สายดึงกลับ:</b> แต้ม {top_cold_face} เงียบมา {last_seen[top_cold_face]} ตา
            </div>
        </div>
        """, unsafe_allow_html=True)

    with rec_col2:
        st.markdown(f"""
        <div class="glow-card card-pair">
            <div class="card-title">👯 โต๊ดคู่ (Pair)</div>
            <div class="card-main-val">คู่ {best_pair[0]} - {best_pair[1]}</div>
            <div class="card-desc">
                • <b>สถิติดีที่สุด:</b> ออกคู่กัน {pair_counts.get(best_pair, 0)} ตา<br>
                • <b>คิดเป็น:</b> {(pair_counts.get(best_pair, 0)/total_rounds)*100:.1f}% ของเกมทั้งหมด
            </div>
        </div>
        """, unsafe_allow_html=True)

    with rec_col3:
        st.markdown(f"""
        <div class="glow-card card-mix">
            <div class="card-title">🎰 โต๊ดผสม (Mix)</div>
            <div class="card-main-val">{best_combo}</div>
            <div class="card-desc">
                • <b>คู่หน้า-ผลรวม:</b> ออกถี่สุด {combo_mix.get(best_combo, 0)} ครั้ง<br>
                • <b>แนะนำ:</b> เดิมพันควบหน้าเต๋ากับสูง/ต่ำ
            </div>
        </div>
        """, unsafe_allow_html=True)

    with rec_col4:
        eleven_status = "🔥 ออกถี่พิเศษ" if eleven_pct > 12.5 else "⚖️ ออกตามเกณฑ์ปกติ"
        st.markdown(f"""
        <div class="glow-card card-eleven">
            <div class="card-title">💥 11 ไฮโล (Total 11)</div>
            <div class="card-main-val">{eleven_pct:.1f}%</div>
            <div class="card-desc">
                • <b>จำนวนครั้ง:</b> ออกไปแล้ว {eleven_count} ครั้ง<br>
                • <b>สถานะ:</b> {eleven_status}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 5. DETAILED THEORY TABS ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 วิเคราะห์ 4 ทฤษฎีสถิติ", 
        "📈 กราฟเปรียบเทียบสั้น-ยาว", 
        "📋 ตารางข้อมูลเรียลไทม์",
        "🎲 สถิติคู่ออกผสม"
    ])

    with tab1:
        st.subheader("เจาะลึก 4 ทฤษฎีการวิเคราะห์ไฮโล")
        t_col1, t_col2 = st.columns(2)
        
        with t_col1:
            st.markdown("#### 1️⃣ Moving Average (แนวโน้มช่วงสั้น)")
            st.dataframe(pd.DataFrame({
                "หน้าเต๋า": [f"แต้ม {i}" for i in range(1, 7)],
                "ออกช่วงสั้น": [short_counts[i] for i in range(1, 7)],
                "ออกภาพรวม": [long_counts[i] for i in range(1, 7)]
            }), use_container_width=True)

            st.markdown("#### 2️⃣ Law of Large Numbers (ดึงเข้าสู่ค่าเฉลี่ย)")
            cold_df = pd.DataFrame({
                "หน้าเต๋า": [f"แต้ม {i}" for i in range(1, 7)],
                "ไม่ได้ออกนาน (ตา)": [last_seen[i] for i in range(1, 7)]
            }).sort_values(by="ไม่ได้ออกนาน (ตา)", ascending=False)
            st.dataframe(cold_df, use_container_width=True)

        with t_col2:
            st.markdown("#### 3️⃣ Cluster Analysis (กลุ่มแต้ม ต่ำ vs สูง)")
            c_ratio = (low_faces / (low_faces + high_faces)) * 100 if (low_faces + high_faces) > 0 else 50
            st.write(f"* สัดส่วนหน้าเต๋าเล็ก (1-2-3): **{c_ratio:.1f}%**")
            st.write(f"* สัดส่วนหน้าเต๋าใหญ่ (4-5-6): **{100 - c_ratio:.1f}%**")
            if c_ratio > 55:
                st.info("💡 กระดานเอียงไปทาง **กลุ่มหน้าเล็ก (1-2-3)**")
            elif c_ratio < 45:
                st.info("💡 กระดานเอียงไปทาง **กลุ่มหน้าใหญ่ (4-5-6)**")
            else:
                st.info("⚖️ กระดานมีความสมดุล")

            st.markdown("#### 4️⃣ Markov Chain (การเปลี่ยนสถานะ)")
            df["ผลลัพธ์_ก่อนหน้า"] = df["ผลลัพธ์ (Result)"].shift(1)
            same_trend = (df["ผลลัพธ์ (Result)"] == df["ผลลัพธ์_ก่อนหน้า"]).sum()
            total_transitions = total_rounds - 1
            streak_pct = (same_trend / total_transitions * 100) if total_transitions > 0 else 0
            st.write(f"* โอกาสออกผลซ้ำติดกัน (มังกร): **{streak_pct:.1f}%**")
            st.write(f"* โอกาสออกสลับฝั่ง (ปิงปอง): **{100 - streak_pct:.1f}%**")

    with tab2:
        g_col1, g_col2 = st.columns(2)
        with g_col1:
            fig_comp = px.bar(
                x=[f"แต้ม {i}" for i in range(1, 7)],
                y=[short_counts[i] for i in range(1, 7)],
                title=f"ความถี่หน้าเต๋า ({recent_n} ตาล่าสุด)",
                template="plotly_white",
                color_discrete_sequence=['#2563eb']
            )
            st.plotly_chart(fig_comp, use_container_width=True)

        with g_col2:
            fig_sum = px.histogram(
                df, x="แต้มรวม (Sum)", nbins=16, 
                title="การกระจายตัวของแต้มรวม (3 - 18)",
                range_x=[2.5, 18.5], template="plotly_white",
                color_discrete_sequence=['#059669']
            )
            st.plotly_chart(fig_sum, use_container_width=True)

    with tab3:
        st.subheader("ตารางประวัติผลลัพธ์ทั้งหมด")
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="hilo_editor")
        save_cols = ["ตาที่ (Round)", "ลูกที่ 1", "ลูกที่ 2", "ลูกที่ 3"]
        clean_edited_df = edited_df[save_cols].dropna(how='all')
        if not clean_edited_df.equals(st.session_state['dice_data']):
            st.session_state['dice_data'] = clean_edited_df
            save_data(clean_edited_df)
            st.rerun()

    with tab4:
        st.subheader("สถิติโต๊ดผสม (หน้าเต๋า + ผลลัพธ์ สูง/ต่ำ)")
        mix_df = pd.DataFrame(list(combo_mix.items()), columns=["รูปแบบการโต๊ด", "จำนวนครั้งที่ออก"]).sort_values(by="จำนวนครั้งที่ออก", ascending=False)
        st.dataframe(mix_df, use_container_width=True)

else:
    st.info("👈 เริ่มต้นกรอกชุดตัวเลขทางแถบซ้ายได้เลยครับ เช่น พิมพ์ `243 333 562 565` แล้วกดบันทึก")

    import pandas as pd
import streamlit as st

# --- ปุ่มลบรายการล่าสุด ---
if st.sidebar.button("🗑️ ลบข้อมูลรายการล่าสุด"):
    try:
        # อ่านไฟล์ข้อมูลที่มีอยู่
        df = pd.read_csv("hilo_history.csv")

        if not df.empty:
            # ลบบรรทัดสุดท้ายออก
            df = df.iloc[:-1]
            # บันทึกกลับลงไฟล์เดิม
            df.to_csv("hilo_history.csv", index=False)
            st.sidebar.success("ลบข้อมูลรายการล่าสุดเรียบร้อยแล้ว!")
            st.rerun()  # รีเฟรชหน้าเว็บเพื่ออัปเดตตารางทันที
        else:
            st.sidebar.warning("ไม่มีข้อมูลให้ลบครับ")
    except FileNotFoundError:
        st.sidebar.error("ยังไม่มีไฟล์ประวัติข้อมูล")

        import os
import pandas as pd
import streamlit as st

CSV_FILE = "hilo_history.csv"

# --- ส่วนแสดงผลประวัติการบันทึก ---
st.subheader("📜 ประวัติการบันทึกข้อมูล")

if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)

    if not df.empty:
        col1, col2 = st.columns([1, 1])

        # 1. ปุ่มลบรายการล่าสุด
        with col1:
            if st.button("🗑️ ลบรายการล่าสุด"):
                df = df.iloc[:-1]  # ลบบรรทัดสุดท้าย
                df.to_csv(CSV_FILE, index=False)
                st.success("ลบรายการล่าสุดเรียบร้อย!")
                st.rerun()

        # 2. ปุ่มล้างประวัติทั้งหมด
        with col2:
            if st.button("⚠️ ล้างประวัติทั้งหมด"):
                # สร้างไฟล์ว่างเปล่าทับไฟล์เดิม
                pd.DataFrame().to_csv(CSV_FILE, index=False)
                st.warning("ล้างประวัติข้อมูลทั้งหมดแล้ว!")
                st.rerun()

        # แสดงตารางประวัติ (ย้อนหลังล่าสุดขึ้นก่อน)
        st.dataframe(df.iloc[::-1], use_container_width=True)

    else:
        st.info("ยังไม่มีประวัติการบันทึกข้อมูล")
else:
        st.info("ยังไม่มีประวัติการบันทึกข้อมูล")