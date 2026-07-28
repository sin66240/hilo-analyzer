import streamlit as st
import numpy as np
import pandas as pd
import re

# ==========================================
# 1. PAGE SETUP & TITLE
# ==========================================
st.set_page_config(page_title="Hi-Lo Specific Bet System", page_icon="🎲", layout="wide")

st.title("🎲 ระบบวิเคราะห์ไฮโล (แทงเต็ง / โต๊ด / 11 ไฮโล)")
st.caption("สแกน 25 ตาตั้งต้น + วิเคราะห์จับคู่โต๊ด/เต็งเต๋า + แผน Hit & Run ทำกำไร +30%")

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

# คำนวณเป้าหมาย Hit & Run (+30%) และ Base Unit
target_profit = capital * 0.30
base_unit = max(20, round((capital * 0.035) / 10) * 10)

st.sidebar.markdown("---")
st.sidebar.metric("🎯 เป้าหมายกำไร (+30%)", f"{target_profit:,.0f} บาท")
st.sidebar.metric("💵 Unit เดินเงินพื้นฐาน/หน้า", f"{base_unit:,.0f} บาท")
st.sidebar.markdown("---")

# ปุ่ม Reset ข้อมูลเมื่อย้ายห้อง
if st.sidebar.button("⚠️ ล้างประวัติข้อมูล (เมื่อย้ายห้อง)", type="primary"):
    st.session_state.history = []
    st.rerun()

# ==========================================
# 3. INPUT SECTION: กรอกสถิติตัวเลขรวดเร็ว
# ==========================================
st.subheader("📥 ป้อนผลทอยลูกเต๋ารวดเร็ว")
st.info("💡 **รูปแบบการกรอก:** พิมพ์ตัวเลข 3 หลัก เว้นวรรคได้ เช่น `223 123 453 456 665` (แนะนำกรอกย้อนหลังให้ครบ 25 ตาก่อนเริ่มวางเงิน)")

input_text = st.text_area("กรอกชุดตัวเลขผลทอย:", placeholder="เช่น 223 123 453 456 665", height=100)

if st.button("📥 บันทึกชุดตัวเลข", type="primary"):
    if input_text.strip():
        # ดึงเฉพาะกลุ่มตัวเลข 3 หลัก (เลข 1-6 เท่านั้น)
        matches = re.findall(r'[1-6]{3}', input_text)
        if matches:
            for m in matches:
                d1, d2, d3 = int(m[0]), int(m[1]), int(m[2])
                total_sum = d1 + d2 + d3
                
                if total_sum == 11:
                    result_type = "11-HiLo"
                elif total_sum <= 10:
                    result_type = "Low"
                else:
                    result_type = "High"
                    
                st.session_state.history.append({
                    "d1": d1, "d2": d2, "d3": d3,
                    "sum": total_sum,
                    "type": result_type,
                    "raw": f"{d1}{d2}{d3}"
                })
            st.success(f"เพิ่มสถิติสำเร็จ {len(matches)} ตา!")
            st.rerun()
        else:
            st.error("กรุณากรอกตัวเลข 1-6 ให้ครบ 3 หลักต่อตา เช่น 123 หรือ 456")

# ==========================================
# 4. ANALYSIS ENGINE (เต็ง / โต๊ด / 11 ไฮโล)
# ==========================================
st.markdown("---")
count_history = len(st.session_state.history)

st.subheader(f"📊 ผลการวิเคราะห์ (สถิติปัจจุบัน: {count_history} ตา)")

if count_history < 5:
    st.warning(f"⏳ **ระบบกำลังสะสมข้อมูล:** กรอกสถิติต่ออีกอย่างน้อย {5 - count_history} ตา เพื่อเริ่มวิเคราะห์ (แนะนำเก็บให้ครบ 25 ตา)")
else:
    df = pd.DataFrame(st.session_state.history)
    
    # 1. ความถี่หน้าเต๋าเดี่ยว (สำหรับเลือกแทงเต็ง)
    all_dice = df[['d1', 'd2', 'd3']].values.flatten()
    dice_counts = pd.Series(all_dice).value_counts().reindex(range(1, 7), fill_value=0)
    
    # 2. ความถี่คู่โต๊ด (สำหรับเลือกแทงโต๊ด)
    pairs = []
    for _, row in df.iterrows():
        d = sorted([row['d1'], row['d2'], row['d3']])
        pairs.append(f"{d[0]}-{d[1]}")
        pairs.append(f"{d[0]}-{d[2]}")
        pairs.append(f"{d[1]}-{d[2]}")
    pair_counts = pd.Series(pairs).value_counts()
    
    # 3. อัตราเกิด 11 ไฮโล
    hilo_count = (df['sum'] == 11).sum()
    hilo_rate = (hilo_count / count_history) * 100
    
    # 4. คำนวณ Entropy (วัดความมั่ว)
    type_counts = df['type'].value_counts()
    probs = [type_counts.get('Low', 0)/count_history, type_counts.get('High', 0)/count_history, hilo_count/count_history]
    probs = [p for p in probs if p > 0]
    entropy = -sum(p * np.log2(p) for p in probs) if probs else 0

    # --------------------------------------
    # DISPLAY METRICS
    # --------------------------------------
    c1, c2, c3 = st.columns(3)
    top_single = dice_counts.idxmax()
    top_pair = pair_counts.index[0] if not pair_counts.empty else "N/A"
    
    c1.metric("เต๋าเดี่ยวที่มาแรงสุด (เต็ง)", f"เลข {top_single}", f"ออก {dice_counts[top_single]} ครั้ง")
    c2.metric("คู่โต๊ดที่ออกบ่อยสุด (โต๊ด)", f"คู่ {top_pair}", f"ออก {pair_counts.iloc[0] if not pair_counts.empty else 0} ครั้ง")
    c3.metric("อัตราออก 11 ไฮโล", f"{hilo_rate:.1f}%", f"{hilo_count} ครั้ง")

    st.markdown("### 🎯 คำแนะนำการแทง (เต็ง / โต๊ด / 11 ไฮโล)")
    
    if entropy > 1.38:
        st.error("🛑 **STOP / WAIT (อย่าเพิ่งแทง):** เต๋ากำลังผันผวนสลับมั่วสูง หากเป็นช่วงย้อนหลัง 25 ตา แนะนำให้พิจารณาเปลี่ยนห้องครับ")
    else:
        col_rec1, col_rec2, col_rec3 = st.columns(3)
        
        # ตัวเลือกที่ 1: แทงเต็งเต๋า (Singles)
        with col_rec1:
            st.markdown("#### 1. ตัวเลือกแทงเต็ง")
            st.success(f"✅ **เต็งเลข: {top_single}**")
            st.write(f"• วางเงิน: **{base_unit} บาท**")
            st.caption(f"เลข {top_single} มีสถิติความถี่สูงสุดในช่วง {count_history} ตาที่ผ่านมา")
            
        # ตัวเลือกที่ 2: แทงโต๊ด (Pairs)
        with col_rec2:
            st.markdown("#### 2. ตัวเลือกแทงโต๊ด")
            st.success(f"✅ **โต๊ดคู่: {top_pair}**")
            st.write(f"• วางเงิน: **{base_unit} บาท**")
            st.caption(f"คู่ {top_pair} จับคู่กันออกบ่อยที่สุดในสแกน")

        # ตัวเลือกที่ 3: แทง 11 ไฮโล (HiLo)
        with col_rec3:
            st.markdown("#### 3. สัญญาณ 11 ไฮโล")
            recent_11_gap = 0
            for idx, r in enumerate(reversed(st.session_state.history)):
                if r['sum'] == 11:
                    recent_11_gap = idx
                    break
                recent_11_gap = len(st.session_state.history)
                
            if recent_11_gap >= 7 and hilo_rate >= 10:
                st.warning(f"⚠️ **ดัก 11 ไฮโล!** (เว้นมา {recent_11_gap} ตาแล้ว)")
                st.write(f"• ติดไว้เบาๆ: **{max(10, round(base_unit * 0.5))} บาท**")
            else:
                st.info("ℹ️ **ยังไม่ต้องดัก 11 ไฮโล** (จังหวะยังไม่สุกงอม)")

    # --------------------------------------
    # SHOW HISTORY TABLE
    # --------------------------------------
    with st.expander("📜 ดูประวัติสถิติทั้งหมดที่กรอกไว้"):
        st.dataframe(df[['raw', 'd1', 'd2', 'd3', 'sum', 'type']], use_container_width=True)st.sidebar.markdown("---")

# ปุ่ม Reset ข้อมูลเมื่อย้ายห้อง
if st.sidebar.button("⚠️ ล้างประวัติข้อมูล (เมื่อย้ายห้อง)", type="primary"):
    st.session_state.history = []
    st.rerun()

# ==========================================
# 3. INPUT SECTION: กรอกสถิติตัวเลขรวดเร็ว
# ==========================================
st.subheader("📥 ป้อนผลทอยลูกเต๋ารวดเร็ว")
st.info("💡 **รูปแบบการกรอก:** พิมพ์ตัวเลข 3 หลัก เว้นวรรคได้ เช่น `223 123 453 456 665` (แนะนำกรอกย้อนหลังให้ครบ 25 ตาก่อนเริ่มวางเงิน)")

input_text = st.text_area("กรอกชุดตัวเลขผลทอย:", placeholder="เช่น 223 123 453 456 665", height=100)

if st.button("📥 บันทึกชุดตัวเลข", type="primary"):
    if input_text.strip():
        # ดึงเฉพาะกลุ่มตัวเลข 3 หลัก (เลข 1-6 เท่านั้น)
        matches = re.findall(r'[1-6]{3}', input_text)
        if matches:
            for m in matches:
                d1, d2, d3 = int(m[0]), int(m[1]), int(m[2])
                total_sum = d1 + d2 + d3
                
                if total_sum == 11:
                    result_type = "11-HiLo"
                elif total_sum <= 10:
                    result_type = "Low"
                else:
                    result_type = "High"
                    
                st.session_state.history.append({
                    "d1": d1, "d2": d2, "d3": d3,
                    "sum": total_sum,
                    "type": result_type,
                    "raw": f"{d1}{d2}{d3}"
                })
            st.success(f"เพิ่มสถิติสำเร็จ {len(matches)} ตา!")
            st.rerun()
        else:
            st.error("กรุณากรอกตัวเลข 1-6 ให้ครบ 3 หลักต่อตา เช่น 123 หรือ 456")

# ==========================================
# 4. ANALYSIS ENGINE (เต็ง / โต๊ด / 11 ไฮโล)
# ==========================================
st.markdown("---")
count_history = len(st.session_state.history)

st.subheader(f"📊 ผลการวิเคราะห์ (สถิติปัจจุบัน: {count_history} ตา)")

if count_history < 5:
    st.warning(f"⏳ **ระบบกำลังสะสมข้อมูล:** กรอกสถิติต่ออีกอย่างน้อย {5 - count_history} ตา เพื่อเริ่มวิเคราะห์ (แนะนำเก็บให้ครบ 25 ตา)")
else:
    df = pd.DataFrame(st.session_state.history)
    
    # 1. ความถี่หน้าเต๋าเดี่ยว (สำหรับเลือกแทงเต็ง)
    all_dice = df[['d1', 'd2', 'd3']].values.flatten()
    dice_counts = pd.Series(all_dice).value_counts().reindex(range(1, 7), fill_value=0)
    
    # 2. ความถี่คู่โต๊ด (สำหรับเลือกแทงโต๊ด)
    pairs = []
    for _, row in df.iterrows():
        d = sorted([row['d1'], row['d2'], row['d3']])
        pairs.append(f"{d[0]}-{d[1]}")
        pairs.append(f"{d[0]}-{d[2]}")
        pairs.append(f"{d[1]}-{d[2]}")
    pair_counts = pd.Series(pairs).value_counts()
    
    # 3. อัตราเกิด 11 ไฮโล
    hilo_count = (df['sum'] == 11).sum()
    hilo_rate = (hilo_count / count_history) * 100
    
    # 4. คำนวณ Entropy (วัดความมั่ว)
    type_counts = df['type'].value_counts()
    probs = [type_counts.get('Low', 0)/count_history, type_counts.get('High', 0)/count_history, hilo_count/count_history]
    probs = [p for p in probs if p > 0]
    entropy = -sum(p * np.log2(p) for p in probs) if probs else 0

    # --------------------------------------
    # DISPLAY METRICS
    # --------------------------------------
    c1, c2, c3 = st.columns(3)
    top_single = dice_counts.idxmax()
    top_pair = pair_counts.index[0] if not pair_counts.empty else "N/A"
    
    c1.metric("เต๋าเดี่ยวที่มาแรงสุด (เต็ง)", f"เลข {top_single}", f"ออก {dice_counts[top_single]} ครั้ง")
    c2.metric("คู่โต๊ดที่ออกบ่อยสุด (โต๊ด)", f"คู่ {top_pair}", f"ออก {pair_counts.iloc[0] if not pair_counts.empty else 0} ครั้ง")
    c3.metric("อัตราออก 11 ไฮโล", f"{hilo_rate:.1f}%", f"{hilo_count} ครั้ง")

    st.markdown("### 🎯 คำแนะนำการแทง (เต็ง / โต๊ด / 11 ไฮโล)")
    
    if entropy > 1.38:
        st.error("🛑 **STOP / WAIT (อย่าเพิ่งแทง):** เต๋ากำลังผันผวนสลับมั่วสูง หากเป็นช่วงย้อนหลัง 25 ตา แนะนำให้พิจารณาเปลี่ยนห้องครับ")
    else:
        col_rec1, col_rec2, col_rec3 = st.columns(3)
        
        # ตัวเลือกที่ 1: แทงเต็งเต๋า (Singles)
        with col_rec1:
            st.markdown("#### 1. ตัวเลือกแทงเต็ง")
            st.success(f"✅ **เต็งเลข: {top_single}**")
            st.write(f"• วางเงิน: **{base_unit} บาท**")
            st.caption(f"เลข {top_single} มีสถิติความถี่สูงสุดในช่วง {count_history} ตาที่ผ่านมา")
            
        # ตัวเลือกที่ 2: แทงโต๊ด (Pairs)
        with col_rec2:
            st.markdown("#### 2. ตัวเลือกแทงโต๊ด")
            st.success(f"✅ **โต๊ดคู่: {top_pair}**")
            st.write(f"• วางเงิน: **{base_unit} บาท**")
            st.caption(f"คู่ {top_pair} จับคู่กันออกบ่อยที่สุดในสแกน")

        # ตัวเลือกที่ 3: แทง 11 ไฮโล (HiLo)
        with col_rec3:
            st.markdown("#### 3. สัญญาณ 11 ไฮโล")
            recent_11_gap = 0
            for idx, r in enumerate(reversed(st.session_state.history)):
                if r['sum'] == 11:
                    recent_11_gap = idx
                    break
                recent_11_gap = len(st.session_state.history)
                
            if recent_11_gap >= 7 and hilo_rate >= 10:
                st.warning(f"⚠️ **ดัก 11 ไฮโล!** (เว้นมา {recent_11_gap} ตาแล้ว)")
                st.write(f"• ติดไว้เบาๆ: **{max(10, round(base_unit * 0.5))} บาท**")
            else:
                st.info("ℹ️ **ยังไม่ต้องดัก 11 ไฮโล** (จังหวะยังไม่สุกงอม)")

    # --------------------------------------
    # SHOW HISTORY TABLE
    # --------------------------------------
    with st.expander("📜 ดูประวัติสถิติทั้งหมดที่กรอกไว้"):
        st.dataframe(df[['raw', 'd1', 'd2', 'd3', 'sum', 'type']], use_container_width=True)
