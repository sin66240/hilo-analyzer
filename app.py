import streamlit as st
import numpy as np
import pandas as pd
import re

# ==========================================
# 1. PAGE SETUP & TITLE
# ==========================================
st.set_page_config(page_title="Custom Hi-Lo Math System", page_icon="🎲", layout="wide")

st.title("🎲 ระบบวิเคราะห์ไฮโล (กติกาพิเศษ: 11 จ่าย 7 เท่า / 6สูง 1ต่ำ / 5ต่ำ 6ต่ำ)")
st.caption("คำนวณด้วย Markov Chain + Decay Weight + Dynamic Kelly (ปรับอัตราจ่ายเฉพาะ)")

# Initialize Session State
if "history" not in st.session_state:
    st.session_state.history = []
if "consecutive_losses" not in st.session_state:
    st.session_state.consecutive_losses = 0
if "cooldown_counter" not in st.session_state:
    st.session_state.cooldown_counter = 0

# ==========================================
# 2. SIDEBAR: MONEY MANAGEMENT & STOP-LOSS STATUS
# ==========================================
st.sidebar.header("💰 ระบบบริหารเงินทุน")

capital = st.sidebar.number_input("กรอกเงินทุนปัจจุบัน (บาท):", min_value=100, value=1000, step=100)
target_profit = capital * 0.30
base_unit = max(20, round((capital * 0.035) / 10) * 10)

st.sidebar.markdown("---")
st.sidebar.metric("🎯 เป้าหมายกำไร (+30%)", f"{target_profit:,.0f} บาท")
st.sidebar.metric("💵 Base Unit พื้นฐาน", f"{base_unit:,.0f} บาท")
st.sidebar.markdown("---")

st.sidebar.subheader("🛡️ สถานะ Stop-Loss")
st.sidebar.write(f"• แทงผิดติดกันปัจจุบัน: **{st.session_state.consecutive_losses} ตา**")
if st.session_state.cooldown_counter > 0:
    st.sidebar.error(f"🛑 อยู่ในช่วงพักดูสถานการณ์: เหลืออีก **{st.session_state.cooldown_counter} ตา**")

if st.sidebar.button("⚠️ ล้างประวัติข้อมูล (เมื่อย้ายห้อง)", type="primary"):
    st.session_state.history = []
    st.session_state.consecutive_losses = 0
    st.session_state.cooldown_counter = 0
    st.rerun()

# ==========================================
# 3. INPUT SECTION & RECORD WIN/LOSS
# ==========================================
st.subheader("📥 ป้อนผลทอยลูกเต๋ารวดเร็ว")
st.info("💡 **รูปแบบการกรอก:** พิมพ์ตัวเลข 3 หลัก เว้นวรรคได้ เช่น `223 123 453 456 665` (แนะนำสแกน 25 ตาแรก)")

input_text = st.text_area("กรอกชุดตัวเลขผลทอย:", placeholder="เช่น 223 123 453 456 665", height=100)

if st.button("📥 บันทึกชุดตัวเลข", type="primary"):
    if input_text.strip():
        matches = re.findall(r'[1-6]{3}', input_text)
        if matches:
            for m in matches:
                d1, d2, d3 = int(m[0]), int(m[1]), int(m[2])
                total_sum = d1 + d2 + d3
                result_type = "11-HiLo" if total_sum == 11 else ("Low" if total_sum <= 10 else "High")
                    
                st.session_state.history.append({
                    "d1": d1, "d2": d2, "d3": d3,
                    "sum": total_sum, "type": result_type, "raw": f"{d1}{d2}{d3}"
                })
                
                if st.session_state.cooldown_counter > 0:
                    st.session_state.cooldown_counter -= 1

            st.success(f"เพิ่มสถิติสำเร็จ {len(matches)} ตา!")
            st.rerun()
        else:
            st.error("กรุณากรอกตัวเลข 1-6 ให้ครบ 3 หลักต่อตา เช่น 123 หรือ 456")

# บันทึกผลการแทง (เพื่อคุมกฎ Stop-Loss)
if len(st.session_state.history) >= 5 and st.session_state.cooldown_counter == 0:
    st.markdown("##### 📌 บันทึกผลการเดิมพันตานี้ (เพื่อติดตามกฎ Stop-Loss)")
    col_w, col_l = st.columns(2)
    if col_w.button("✅ ตานี้แทงชนะ (Win)", use_container_width=True):
        st.session_state.consecutive_losses = 0
        st.success("บันทึกผลชนะ: รีเซ็ตนับผลแพ้เป็น 0")
        st.rerun()
    if col_l.button("❌ ตานี้แทงแพ้ (Loss)", use_container_width=True):
        st.session_state.consecutive_losses += 1
        if st.session_state.consecutive_losses >= 2:
            st.session_state.cooldown_counter = 4  # พักสังเกตการณ์ 4 ตา
        st.warning(f"บันทึกผลแพ้: สะสมแพ้ติดกัน {st.session_state.consecutive_losses} ตา")
        st.rerun()

# ==========================================
# 4. ADVANCED MATH ENGINE & SPECIAL PAYOUTS
# ==========================================
st.markdown("---")
count_history = len(st.session_state.history)

st.subheader(f"📊 ผลการวิเคราะห์ (สถิติปัจจุบัน: {count_history} ตา)")

if count_history < 5:
    st.warning(f"⏳ **ระบบกำลังสะสมข้อมูล:** กรอกสถิติต่ออีกอย่างน้อย {5 - count_history} ตา เพื่อเริ่มวิเคราะห์")
else:
    df = pd.DataFrame(st.session_state.history)
    
    # ----------------------------------------------------
    # 1. Recency Decay Weight Calculation
    # ----------------------------------------------------
    lambda_decay = np.log(2) / 7
    weights = np.exp(-lambda_decay * np.arange(count_history)[::-1])
    weights_sum = weights.sum()
    
    # 2. คำนวณความน่าจะเป็นของหน้าควบพิเศษ (Special Combo Probabilities)
    p_1low = sum(w for i, w in enumerate(weights) if df.loc[i, 'sum'] <= 10 and (1 in [df.loc[i, 'd1'], df.loc[i, 'd2'], df.loc[i, 'd3']])) / weights_sum
    p_6high = sum(w for i, w in enumerate(weights) if df.loc[i, 'sum'] >= 12 and (6 in [df.loc[i, 'd1'], df.loc[i, 'd2'], df.loc[i, 'd3']])) / weights_sum
    p_4high = sum(w for i, w in enumerate(weights) if df.loc[i, 'sum'] >= 12 and (4 in [df.loc[i, 'd1'], df.loc[i, 'd2'], df.loc[i, 'd3']])) / weights_sum
    p_3low = sum(w for i, w in enumerate(weights) if df.loc[i, 'sum'] <= 10 and (3 in [df.loc[i, 'd1'], df.loc[i, 'd2'], df.loc[i, 'd3']])) / weights_sum
    p_6low = sum(w for i, w in enumerate(weights) if df.loc[i, 'sum'] <= 10 and (6 in [df.loc[i, 'd1'], df.loc[i, 'd2'], df.loc[i, 'd3']])) / weights_sum
    p_5low = sum(w for i, w in enumerate(weights) if df.loc[i, 'sum'] <= 10 and (5 in [df.loc[i, 'd1'], df.loc[i, 'd2'], df.loc[i, 'd3']])) / weights_sum
    
    # รวมกลุ่มหน้าควบพร้อมอัตราจ่าย
    combos = [
        {"name": "1-ต่ำ", "p": p_1low, "b": 2.0},
        {"name": "6-สูง", "p": p_6high, "b": 2.0},
        {"name": "4-สูง", "p": p_4high, "b": 3.0},
        {"name": "3-ต่ำ", "p": p_3low, "b": 3.0},
        {"name": "6-ต่ำ", "p": p_6low, "b": 5.0},
        {"name": "5-ต่ำ", "p": p_5low, "b": 5.0}
    ]
    
    # ----------------------------------------------------
    # 3. Dynamic Kelly คำนวณหาหน้าควบที่คุ้มค่าที่สุด
    # ----------------------------------------------------
    best_combo = None
    max_kelly_val = -1
    
    for c in combos:
        p_val = c['p']
        b_val = c['b']
        kelly_f = (p_val * (b_val + 1) - 1) / b_val if b_val > 0 else 0
        if kelly_f > max_kelly_val:
            max_kelly_val = kelly_f
            best_combo = c
            best_combo['kelly_f'] = kelly_f

    # ----------------------------------------------------
    # 4. Markov Chain (แทงฝั่งปกติ)
    # ----------------------------------------------------
    states = ["Low", "High", "11-HiLo"]
    state_to_idx = {s: i for i, s in enumerate(states)}
    transition_matrix = np.zeros((3, 3))
    
    for i in range(count_history - 1):
        curr_state = df.loc[i, 'type']
        next_state = df.loc[i+1, 'type']
        transition_matrix[state_to_idx[curr_state]][state_to_idx[next_state]] += 1
        
    row_sums = transition_matrix.sum(axis=1, keepdims=True)
    prob_transition = np.divide(transition_matrix, row_sums, out=np.zeros_like(transition_matrix), where=row_sums!=0)
    
    last_state = df.iloc[-1]['type']
    next_state_probs = prob_transition[state_to_idx[last_state]]
    predicted_next_state = states[np.argmax(next_state_probs)]
    predicted_state_prob = np.max(next_state_probs)

    # ----------------------------------------------------
    # 5. Windowed Entropy (7 ตาล่าสุด)
    # ----------------------------------------------------
    recent_types = df['type'].tail(min(7, count_history)).value_counts(normalize=True)
    recent_entropy = -sum(p * np.log2(p) for p in recent_types if p > 0)

    # ----------------------------------------------------
    # DISPLAY RESULTS
    # ----------------------------------------------------
    c1, c2, c3 = st.columns(3)
    c1.metric("ทิศทางเค้าเต๋า (Markov)", f"{predicted_next_state}", f"โอกาส {predicted_state_prob*100:.0f}%")
    c2.metric("หน้าควบอัตราจ่ายสูงเด่นสุด", f"{best_combo['name']}", f"จ่าย {best_combo['b']:.0f} เท่า")
    c3.metric("Recent Entropy", f"{recent_entropy:.2f}", "ยิ่งต่ำยิ่งกราฟสวย")

    st.markdown("### 🎯 คำแนะนำการเดิมพันตานี้")
    
    if st.session_state.cooldown_counter > 0:
        st.error(f"🛑 **STOP-LOSS ACTIVATED:** แทงผิดติดกัน {st.session_state.consecutive_losses} ตา! หยุดพักสังเกตการณ์อีก **{st.session_state.cooldown_counter} ตา**")
    elif recent_entropy > 1.25:
        st.error(f"🛑 **EARLY WARNING (Entropy สูง {recent_entropy:.2f}):** ช่วง 7 ตาล่าสุดเค้าเต๋าสลับมั่ว สั่ง **WAIT (หยุดพัก)** เพื่อป้องกันสูตรแตก")
    else:
        col_rec1, col_rec2, col_rec3 = st.columns(3)
        
        # เลือก 1: แทงฝั่ง
        with col_rec1:
            st.markdown("#### 1. แทงฝั่ง (Markov)")
            st.success(f"✅ **แทง: {predicted_next_state}**")
            st.write(f"• วางเงิน: **{base_unit} บาท**")
            
        # เลือก 2: แทงหน้าควบอัตราจ่ายสูง
        with col_rec2:
            st.markdown("#### 2. แทงหน้าควบ (Dynamic Kelly)")
            if best_combo['kelly_f'] > 0:
                calc_bet = max(base_unit, round((capital * (best_combo['kelly_f'] * 0.15)) / 10) * 10)
                st.success(f"✅ **แทง: {best_combo['name']}** (จ่าย {best_combo['b']:.0f} เท่า)")
                st.write(f"• วางเงิน: **{calc_bet:,.0f} บาท**")
            else:
                st.info("ℹ️ **ยังไม่มีหน้าควบที่คุ้มความเสี่ยง**")

        # เลือก 3: สัญญาณ 11 ไฮโล (จ่าย 7 เท่า)
        with col_rec3:
            st.markdown("#### 3. สัญญาณ 11 ไฮโล (จ่าย 7 เท่า)")
            recent_11_gap = 0
            for idx, r in enumerate(reversed(st.session_state.history)):
                if r['sum'] == 11:
                    recent_11_gap = idx
                    break
                recent_11_gap = len(st.session_state.history)
                
            if recent_11_gap >= 7:
                st.warning(f"⚠️ **ดัก 11 ไฮโล!** (เว้นมา {recent_11_gap} ตา)")
                st.write(f"• วางเงินเบาๆ: **{max(10, round(base_unit * 0.5))} บาท**")
            else:
                st.info("ℹ️ **ยังไม่ต้องดัก 11 ไฮโล**")

    with st.expander("📜 ดูประวัติสถิติทั้งหมดที่กรอกไว้"):
        st.dataframe(df[['raw', 'd1', 'd2', 'd3', 'sum', 'type']], use_container_width=True)
