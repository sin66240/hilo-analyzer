import streamlit as st
import numpy as np
import pandas as pd

# ==========================================
# 1. PAGE SETUP & TITLE
# ==========================================
st.set_page_config(page_title="Hi-Lo Hit & Run System", page_icon="🎲", layout="wide")

st.title("🎲 ระบบวิเคราะห์ไฮโล (Hit & Run Strategy)")
st.caption("กลยุทธ์สแกน 25 ตาตั้งต้น + ทำกำไรระยะสั้น 20-30% แล้วเลิก")

# Initialize Session State
if "history" not in st.session_state:
    st.session_state.history = []

# ==========================================
# 2. SIDEBAR: MONEY MANAGEMENT & TARGETS
# ==========================================
st.sidebar.header("💰 ระบบบริหารเงินทุน")

capital = st.sidebar.number_input(
    "กรอกเงินทุนเริ่มต้น (บาท):", 
    min_value=100, 
    value=1000, 
    step=100
)

# คำนวณเป้าหมาย Hit & Run (+30%) และ Base Unit (3-4% ของทุน)
target_profit = capital * 0.30
base_unit = max(20, round((capital * 0.035) / 10) * 10)

st.sidebar.markdown("---")
st.sidebar.metric("🎯 เป้าหมายกำไร (+30%)", f"{target_profit:,.0f} บาท")
st.sidebar.metric("💵 Unit เดินเงินพื้นฐาน", f"{base_unit:,.0f} บาท/ตา")
st.sidebar.markdown("---")

# ปุ่ม Reset ข้อมูลเมื่อย้ายห้อง
if st.sidebar.button("⚠️ ล้างประวัติข้อมูล (เมื่อย้ายห้อง)", type="primary"):
    st.session_state.history = []
    st.rerun()

# ==========================================
# 3. INPUT SECTION: กรอกผลทีละตา
# ==========================================
st.subheader("📥 ป้อนผลทอยลูกเต๋า (3 ลูก)")
st.info("💡 **ข้อแนะนำ:** นั่งดูและกรอกผลย้อนหลังให้ครบ **25 ตา** โดยยังไม่ต้องวางเงิน เพื่อให้ระบบสร้าง Pattern ที่แม่นยำก่อนครับ")

col_i1, col_i2, col_i3, col_btn = st.columns([2, 2, 2, 2])

with col_i1:
    d1 = st.number_input("ลูกที่ 1", min_value=1, max_value=6, value=1, key="d1")
with col_i2:
    d2 = st.number_input("ลูกที่ 2", min_value=1, max_value=6, value=1, key="d2")
with col_i3:
    d3 = st.number_input("ลูกที่ 3", min_value=1, max_value=6, value=1, key="d3")

with col_btn:
    st.markdown("###")
    if st.button("บันทึกผล ➕", use_container_width=True):
        total_sum = d1 + d2 + d3
        # ไฮโลไทย: 3-10 คือ ต่ำ (Low), 12-18 คือ สูง (High), 11 คือ ไฮโล
        if total_sum == 11:
            result_type = "11-HiLo"
        elif total_sum <= 10:
            result_type = "Low"
        else:
            result_type = "High"
            
        st.session_state.history.append({
            "d1": d1, "d2": d2, "d3": d3,
            "sum": total_sum,
            "type": result_type
        })
        st.rerun()

# ==========================================
# 4. ANALYSIS & DECISION ENGINE
# ==========================================
st.markdown("---")
count_history = len(st.session_state.history)

st.subheader(f"📊 ผลการวิเคราะห์ (สถิติปัจจุบัน: {count_history} ตา)")

if count_history < 5:
    st.warning(f"⏳ **ระบบกำลังสะสมข้อมูล:** กรอกสถิติต่ออีกอย่างน้อย {5 - count_history} ตา เพื่อเริ่มประมวลผล (แนะนำให้ครบ 25 ตา)")
else:
    df = pd.DataFrame(st.session_state.history)
    
    # คำนวณความถี่หน้าเต๋า (Digit Scan)
    all_dice = df[['d1', 'd2', 'd3']].values.flatten()
    dice_counts = pd.Series(all_dice).value_counts().reindex(range(1, 7), fill_value=0)
    
    # คำนวณสัดส่วน สูง/ต่ำ
    type_counts = df['type'].value_counts()
    low_count = type_counts.get('Low', 0)
    high_count = type_counts.get('High', 0)
    hilo_count = type_counts.get('11-HiLo', 0)
    
    # คำนวณค่า Entropy (วัดความมั่ว/ผันผวนของเค้าเต๋า)
    probs = [low_count/count_history, high_count/count_history, hilo_count/count_history]
    probs = [p for p in probs if p > 0]
    entropy = -sum(p * np.log2(p) for p in probs) if probs else 0

    # --------------------------------------
    # DISPLAY METRICS & SIGNAL
    # --------------------------------------
    c1, c2, c3 = st.columns(3)
    c1.metric("อัตราส่วน ต่ำ (Low)", f"{(low_count/count_history)*100:.1f}% ({low_count} ครั้ง)")
    c2.metric("อัตราส่วน สูง (High)", f"{(high_count/count_history)*100:.1f}% ({high_count} ครั้ง)")
    c3.metric("ดัชนีความผันผวน (Entropy)", f"{entropy:.2f}")

    # คำสั่งแทงตามอัลกอริทึม Hit & Run
    st.markdown("### 🎯 คำแนะนำการลงเดิมพันตาถัดไป")
    
    # กรณีที่ 1: entropy สูงเกินไป (เต๋าสลับมั่ว) -> สั่ง WAIT
    if entropy > 1.35:
        st.error("🛑 **STOP / WAIT (อย่าเพิ่งแทง):** เค้าเต๋ากำลังผันผวนสลับมั่วสูง หากเป็นช่วงย้อนหลัง 25 ตา แนะนำให้พิจารณาเปลี่ยนห้องครับ")
    
    # กรณีที่ 2: เค้าเต๋าเริ่มชัดเจน
    else:
        # ดูน้ำหนัก 5 ตาล่าสุด (Recency Decay)
        recent_df = df.tail(5)
        recent_low = (recent_df['type'] == 'Low').sum()
        recent_high = (recent_df['type'] == 'High').sum()
        
        # ค้นหาเลขเต๋าที่ไหลแรงที่สุด
        top_digit = dice_counts.idxmax()
        
        if recent_low >= 3:
            st.success(f"✅ **BET: แทง 'ต่ำ (Low)'** | **ขนาดเงิน:** {base_unit} บาท")
            st.caption(f"💡 **เสริมตัวเลข:** เต๋าเลข **{top_digit}** ออกบ่อยที่สุดในสแกน สามารถติดเต็ง {top_digit} กันไว้ได้")
        elif recent_high >= 3:
            st.success(f"✅ **BET: แทง 'สูง (High)'** | **ขนาดเงิน:** {base_unit} บาท")
            st.caption(f"💡 **เสริมตัวเลข:** เต๋าเลข **{top_digit}** ออกบ่อยที่สุดในสแกน สามารถติดเต็ง {top_digit} กันไว้ได้")
        else:
            st.warning("⏳ **WAIT:** กราฟกำลังเปลี่ยนทรง รอจังหวะไหลชัดๆ อีก 1-2 ตา")

    # --------------------------------------
    # SHOW HISTORY TABLE
    # --------------------------------------
    with st.expander("📜 ดูประวัติสถิติทั้งหมดที่กรอกไว้"):
        st.dataframe(df.style.highlight_max(subset=['sum'], color='lightgreen'), use_container_width=True)
