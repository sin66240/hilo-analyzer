import streamlit as st
import numpy as np
import pandas as pd
import re
from collections import Counter
from scipy.stats import chisquare, poisson

# ==========================================
# 1. PAGE SETUP & TITLE
# ==========================================
st.set_page_config(page_title="Hi-Lo Ultimate Math System", page_icon="🎲", layout="wide")

st.title("🎲 ระบบวิเคราะห์ไฮโลขั้นสูง (Full-Range Chi-Square, Poisson & Runs Test)")
st.caption("ระบบคำนวณอัตโนมัติ + รองรับแต้มรวม 3-18 + โต๊ด / เบิ้ล + ขั้นตอนวิเคราะห์เชิงสถิติขั้นสูงแบบจัดเต็ม")

# Initialize Session State
if "history" not in st.session_state:
    st.session_state.history = []
if "betting_started" not in st.session_state:
    st.session_state.betting_started = False
if "active_bet" not in st.session_state:
    st.session_state.active_bet = None
if "last_bet_result" not in st.session_state:
    st.session_state.last_bet_result = None
if "flash_effect" not in st.session_state:
    st.session_state.flash_effect = False

# --- Flash Effect CSS Injection ---
if st.session_state.flash_effect:
    st.markdown("""
        <style>
        @keyframes flash-animation {
            0% { background-color: rgba(255, 255, 255, 0); }
            20% { background-color: rgba(255, 255, 255, 0.85); box-shadow: 0 0 100px rgba(255, 255, 255, 1); }
            100% { background-color: rgba(255, 255, 255, 0); }
        }
        .flash-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            pointer-events: none;
            z-index: 999999;
            animation: flash-animation 0.6s ease-out;
        }
        </style>
        <div class="flash-overlay"></div>
    """, unsafe_allow_html=True)
    st.session_state.flash_effect = False

# ==========================================
# 2. SIDEBAR: MONEY MANAGEMENT
# ==========================================
st.sidebar.header("💰 ระบบบริหารเงินทุน")

capital = st.sidebar.number_input("กรอกเงินทุนปัจจุบัน (บาท):", min_value=100, value=1000, step=100)
target_profit = capital * 0.30
base_unit = max(20, round((capital * 0.02) / 10) * 10)

st.sidebar.markdown(f"""
* **เป้าหมายกำไร (30%):** `{target_profit:,.0f}` บาท
* **หน่วยลงเงินเบื้องต้น (2%):** `{base_unit:,.0f}` บาท
""")

if st.sidebar.button("🔄 รีเซ็ตระบบทั้งหมด"):
    st.session_state.history = []
    st.session_state.betting_started = False
    st.session_state.active_bet = None
    st.session_state.last_bet_result = None
    st.rerun()

# ==========================================
# 3. HELPER FUNCTIONS & PAYOUT TABLES (3-18)
# ==========================================
SUM_PAYOUTS = {
    3: 50.0, 18: 50.0,
    4: 50.0, 17: 50.0,
    5: 30.0, 16: 30.0,
    6: 18.0, 15: 18.0,
    7: 12.0, 14: 12.0,
    8: 8.0, 13: 8.0,
    9: 6.0, 12: 6.0,
    10: 6.0, 11: 6.0
}

# ค่าความน่าจะเป็นทางทฤษฎีของแต้มรวม 3-18 (จาก 216 รูปแบบ)
THEORETICAL_SUM_PROBS = {
    3: 1/216, 18: 1/216,
    4: 3/216, 17: 3/216,
    5: 6/216, 16: 6/216,
    6: 10/216, 15: 10/216,
    7: 15/216, 14: 15/216,
    8: 21/216, 13: 21/216,
    9: 25/216, 12: 25/216,
    10: 27/216, 11: 27/216
}

def parse_multiple_dice_inputs(input_text):
    all_digits = re.findall(r'[1-6]', input_text)
    parsed_groups = []
    for i in range(0, len(all_digits) - len(all_digits) % 3, 3):
        parsed_groups.append([int(all_digits[i]), int(all_digits[i+1]), int(all_digits[i+2])])
    return parsed_groups

def calculate_round_pnl(bet_info, dice_list, total_sum):
    combo_target = bet_info.get("combo_target") 
    combo_unit = bet_info.get("combo_unit", 0)
    combo_odds = 5.0 

    double_target = bet_info.get("double_target") 
    double_unit = bet_info.get("double_unit", 0)
    double_odds = 10.0 

    sum_target = bet_info.get("sum_target") 
    sum_unit = bet_info.get("sum_unit", 0)
    sum_odds = SUM_PAYOUTS.get(sum_target, 6.0)

    total_bet = combo_unit + double_unit + sum_unit
    total_payout = 0

    if combo_target:
        n1, n2 = map(int, combo_target.split("-"))
        if (n1 in dice_list) and (n2 in dice_list):
            total_payout += combo_unit * (combo_odds + 1)

    if double_target:
        d_num = int(double_target.split("-")[0])
        if dice_list.count(d_num) >= 2:
            total_payout += double_unit * (double_odds + 1)

    if sum_target and total_sum == sum_target:
        total_payout += sum_unit * (sum_odds + 1)

    net_pnl = total_payout - total_bet
    return net_pnl, total_bet

# ==========================================
# 4. INPUT SECTION
# ==========================================
st.subheader("📥 ป้อนผลลูกเต๋า (กรอกทีละชุด หรือวางพร้อมกันหลายชุดก็ได้)")

col_in, col_btn = st.columns([3, 1])
with col_in:
    dice_input = st.text_area("วางผลเต๋า เช่น '123 654 556 214' หรือวางต่อกันหลายๆ บรรทัดได้เลย:", key="dice_input_key", height=100)

with col_btn:
    st.write("") 
    submit_btn = st.button("บันทึกผลทั้งหมด 🎲", use_container_width=True, type="primary")
    undo_btn = st.button("ลบสถิติล่าสุด 🗑️", use_container_width=True)

if undo_btn:
    if len(st.session_state.history) > 0:
        st.session_state.history.pop()
        st.session_state.last_bet_result = None
        st.toast("🗑️ ลบสถิติตาล่าสุดเรียบร้อยแล้ว!")
        st.rerun()
    else:
        st.warning("⚠️ ไม่มีสถิติให้ลบครับ")

if submit_btn and dice_input:
    dice_groups = parse_multiple_dice_inputs(dice_input)
    
    if len(dice_groups) > 0:
        added_count = 0
        for parsed_dice in dice_groups:
            d1, d2, d3 = parsed_dice
            total_sum = d1 + d2 + d3
            
            if st.session_state.betting_started and st.session_state.active_bet:
                net_pnl, total_bet = calculate_round_pnl(
                    st.session_state.active_bet, 
                    [d1, d2, d3], 
                    total_sum
                )
                
                if net_pnl > 0:
                    st.session_state.last_bet_result = {
                        "status": "WIN", 
                        "msg": f"🎉 **ชนะ!** บวกสุทธิ +{net_pnl:,.0f} บาท (ผลออก {d1}-{d2}-{d3} = {total_sum})"
                    }
                elif net_pnl == 0:
                    st.session_state.last_bet_result = {
                        "status": "DRAW", 
                        "msg": f"⚖️ **เท่าทุน!** ได้-เสีย 0 บาท (ผลออก {d1}-{d2}-{d3} = {total_sum})"
                    }
                else:
                    st.session_state.last_bet_result = {
                        "status": "LOSS", 
                        "msg": f"💥 **แพ้!** ติดลบ -{abs(net_pnl):,.0f} บาท (ผลออก {d1}-{d2}-{d3} = {total_sum})"
                    }

            st.session_state.history.append({
                "Round": len(st.session_state.history) + 1,
                "D1": d1, "D2": d2, "D3": d3,
                "Sum": total_sum
            })
            added_count += 1

        st.session_state.flash_effect = True
        st.toast(f"✅ บันทึกสถิติเพิ่มสำเร็จ {added_count} ชุด!", icon="🎲")
        st.rerun()
    else:
        st.error("⚠️ ไม่พบตัวเลข 1-6 ที่ครบ 3 ตัว กรุณาตรวจสอบตัวเลขอีกครั้ง")

if st.session_state.last_bet_result:
    res = st.session_state.last_bet_result
    if res["status"] == "WIN":
        st.success(res["msg"])
    elif res["status"] == "DRAW":
        st.info(res["msg"])
    elif res["status"] == "LOSS":
        st.error(res["msg"])

# ==========================================
# 5. ADVANCED MATH ENGINE (DECAY, RUNS TEST, CHI-SQUARE & POISSON)
# ==========================================
history_df = pd.DataFrame(st.session_state.history)
total_rounds = len(history_df)

st.divider()

if total_rounds < 15:
    st.info(f"⏳ **ระบบกำลังสะสมสถิติ (Warm-Up Phase):** ต้องการอีก {15 - total_rounds} ตา เพื่อเริ่มประมวลผลด้วยโมเดลสถิติขั้นสูง")
    st.session_state.betting_started = False
else:
    st.session_state.betting_started = True

if total_rounds >= 15:
    decay = np.exp(-0.08 * np.arange(total_rounds)[::-1])
    combo_counts = Counter()
    double_counts = Counter()
    sum_counts = Counter()

    for idx, row in history_df.iterrows():
        d_list = sorted([row["D1"], row["D2"], row["D3"]])
        w = decay[idx]
        
        pairs = [(d_list[0], d_list[1]), (d_list[0], d_list[2]), (d_list[1], d_list[2])]
        for p1, p2 in pairs:
            if p1 != p2:
                combo_counts[f"{p1}-{p2}"] += w
            else:
                double_counts[f"{p1}-{p1}"] += w
                
        sum_counts[row["Sum"]] += w

    top_combo = combo_counts.most_common(1)[0][0] if combo_counts else "5-6"
    top_double = double_counts.most_common(1)[0][0] if double_counts else "6-6"
    
    # ผสานการวิเคราะห์ Poisson สำหรับเลขเบิ้ลที่เว้นช่วงนานเกินไป
    recent_doubles_gap = 0
    for idx, row in history_df.iloc[::-1].iterrows():
        d_list = [row["D1"], row["D2"], row["D3"]]
        if len(set(d_list)) < 3: # มีเบิ้ล
            break
        recent_doubles_gap += 1

    top_sum = sum_counts.most_common(1)[0][0] if sum_counts else 10
    sum_odds_val = SUM_PAYOUTS.get(top_sum, 6.0)

    # Chi-Square Goodness-of-Fit ตรวจสอบความเบี่ยงเบนของแต้มรวม
    observed_freqs = [sum_counts.get(s, 0.1) for s in range(3, 19)]
    expected_freqs = [total_rounds * THEORETICAL_SUM_PROBS[s] for s in range(3, 19)]
    chi2_val, p_value = chisquare(f_obs=observed_freqs, f_exp=expected_freqs)

    # Runs Test ตรวจสอบความผันผวน
    recent_sums = history_df["Sum"].tail(10).tolist()
    runs = 1
    for i in range(1, len(recent_sums)):
        if (recent_sums[i] >= 11) != (recent_sums[i-1] >= 11):
            runs += 1

    is_choppy = (runs >= 8)

    st.subheader("🎯 คำแนะนำการเดิมพันตาถัดไป (Next Bet Recommendation)")

    if is_choppy:
        st.warning("⚠️ **กราฟเปลี่ยนหน้าผันผวนสูง (High Choppiness / Runs Test):** แนะนำให้ **พักสังเกตการณ์ (WAIT)** ในตานี้")
        st.session_state.active_bet = None
    else:
        combo_unit = max(20, round(base_unit * 1.5 / 10) * 10)
        double_unit = max(20, round(base_unit * (1.2 if recent_doubles_gap > 6 else 0.5) / 10) * 10) # ปรับทบเงินเบิ้ลถ้าทิ้งช่วงนานตาม Poisson
        sum_unit = max(20, round(base_unit * 0.8 / 10) * 10)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("🎲 โต๊ดคู่เต็ง (Combo)", top_combo)
            st.write(f"👉 **วางเงินโต๊ดคู่:** `{combo_unit:,.0f}` บาท (จ่าย 5 เท่า)")
        
        with c2:
            double_status = f"เว้นช่วง {recent_doubles_gap} ตา" + (" (จังหวะ Poisson เหมาะดัก)" if recent_doubles_gap > 5 else "")
            st.metric("👯 เลขเบิ้ลเต็ง (Double)", top_double, double_status)
            st.write(f"👉 **วางเงินเบิ้ล:** `{double_unit:,.0f}` บาท (จ่าย 10 เท่า)")
            
        with c3:
            st.metric("🎯 แต้มรวมเป้าหมาย (3-18)", f"{top_sum} แต้ม", f"Chi2 p={p_value:.2f}")
            st.write(f"👉 **วางเงินแต้มรวม:** `{sum_unit:,.0f}` บาท (จ่าย {sum_odds_val:,.0f} เท่า)")

        st.session_state.active_bet = {
            "combo_target": top_combo,
            "combo_unit": combo_unit,
            "double_target": top_double,
            "double_unit": double_unit,
            "sum_target": top_sum,
            "sum_unit": sum_unit
        }

# ==========================================
# 6. STATS DISPLAY
# ==========================================
if total_rounds > 0:
    st.divider()
    st.subheader(f"📊 ประวัติการกรอกสถิติ (บันทึกแล้ว {total_rounds} ตา)")
    st.dataframe(history_df.tail(15), use_container_width=True)            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            pointer-events: none;
            z-index: 999999;
            animation: flash-animation 0.6s ease-out;
        }
        </style>
        <div class="flash-overlay"></div>
    """, unsafe_allow_html=True)
    st.session_state.flash_effect = False

# ==========================================
# 2. SIDEBAR: MONEY MANAGEMENT
# ==========================================
st.sidebar.header("💰 ระบบบริหารเงินทุน")

capital = st.sidebar.number_input("กรอกเงินทุนปัจจุบัน (บาท):", min_value=100, value=1000, step=100)
target_profit = capital * 0.30
base_unit = max(20, round((capital * 0.02) / 10) * 10)

st.sidebar.markdown(f"""
* **เป้าหมายกำไร (30%):** `{target_profit:,.0f}` บาท
* **หน่วยลงเงินเบื้องต้น (2%):** `{base_unit:,.0f}` บาท
""")

if st.sidebar.button("🔄 รีเซ็ตระบบทั้งหมด"):
    st.session_state.history = []
    st.session_state.betting_started = False
    st.session_state.active_bet = None
    st.session_state.last_bet_result = None
    st.rerun()

# ==========================================
# 3. HELPER FUNCTIONS & PAYOUT TABLES (3-18)
# ==========================================
SUM_PAYOUTS = {
    3: 50.0, 18: 50.0,
    4: 50.0, 17: 50.0,
    5: 30.0, 16: 30.0,
    6: 18.0, 15: 18.0,
    7: 12.0, 14: 12.0,
    8: 8.0, 13: 8.0,
    9: 6.0, 12: 6.0,
    10: 6.0, 11: 6.0
}

def parse_multiple_dice_inputs(input_text):
    all_digits = re.findall(r'[1-6]', input_text)
    parsed_groups = []
    for i in range(0, len(all_digits) - len(all_digits) % 3, 3):
        parsed_groups.append([int(all_digits[i]), int(all_digits[i+1]), int(all_digits[i+2])])
    return parsed_groups

def calculate_round_pnl(bet_info, dice_list, total_sum):
    combo_target = bet_info.get("combo_target") 
    combo_unit = bet_info.get("combo_unit", 0)
    combo_odds = 5.0 

    double_target = bet_info.get("double_target") 
    double_unit = bet_info.get("double_unit", 0)
    double_odds = 10.0 

    sum_target = bet_info.get("sum_target") 
    sum_unit = bet_info.get("sum_unit", 0)
    sum_odds = SUM_PAYOUTS.get(sum_target, 6.0)

    total_bet = combo_unit + double_unit + sum_unit
    total_payout = 0

    if combo_target:
        n1, n2 = map(int, combo_target.split("-"))
        if (n1 in dice_list) and (n2 in dice_list):
            total_payout += combo_unit * (combo_odds + 1)

    if double_target:
        d_num = int(double_target.split("-")[0])
        if dice_list.count(d_num) >= 2:
            total_payout += double_unit * (double_odds + 1)

    if sum_target and total_sum == sum_target:
        total_payout += sum_unit * (sum_odds + 1)

    net_pnl = total_payout - total_bet
    return net_pnl, total_bet

# ==========================================
# 4. INPUT SECTION
# ==========================================
st.subheader("📥 ป้อนผลลูกเต๋า (กรอกทีละชุด หรือวางพร้อมกันหลายชุดก็ได้)")

col_in, col_btn = st.columns([3, 1])
with col_in:
    dice_input = st.text_area("วางผลเต๋า เช่น '123 654 556 214' หรือวางต่อกันหลายๆ บรรทัดได้เลย:", key="dice_input_key", height=100)

with col_btn:
    st.write("") 
    submit_btn = st.button("บันทึกผลทั้งหมด 🎲", use_container_width=True, type="primary")
    undo_btn = st.button("ลบสถิติล่าสุด 🗑️", use_container_width=True)

if undo_btn:
    if len(st.session_state.history) > 0:
        st.session_state.history.pop()
        st.session_state.last_bet_result = None
        st.toast("🗑️ ลบสถิติตาล่าสุดเรียบร้อยแล้ว!")
        st.rerun()
    else:
        st.warning("⚠️ ไม่มีสถิติให้ลบครับ")

if submit_btn and dice_input:
    dice_groups = parse_multiple_dice_inputs(dice_input)
    
    if len(dice_groups) > 0:
        added_count = 0
        for parsed_dice in dice_groups:
            d1, d2, d3 = parsed_dice
            total_sum = d1 + d2 + d3
            
            if st.session_state.betting_started and st.session_state.active_bet:
                net_pnl, total_bet = calculate_round_pnl(
                    st.session_state.active_bet, 
                    [d1, d2, d3], 
                    total_sum
                )
                
                if net_pnl > 0:
                    st.session_state.last_bet_result = {
                        "status": "WIN", 
                        "msg": f"🎉 **ชนะ!** บวกสุทธิ +{net_pnl:,.0f} บาท (ผลออก {d1}-{d2}-{d3} = {total_sum})"
                    }
                elif net_pnl == 0:
                    st.session_state.last_bet_result = {
                        "status": "DRAW", 
                        "msg": f"⚖️ **เท่าทุน!** ได้-เสีย 0 บาท (ผลออก {d1}-{d2}-{d3} = {total_sum})"
                    }
                else:
                    st.session_state.last_bet_result = {
                        "status": "LOSS", 
                        "msg": f"💥 **แพ้!** ติดลบ -{abs(net_pnl):,.0f} บาท (ผลออก {d1}-{d2}-{d3} = {total_sum})"
                    }

            st.session_state.history.append({
                "Round": len(st.session_state.history) + 1,
                "D1": d1, "D2": d2, "D3": d3,
                "Sum": total_sum
            })
            added_count += 1

        st.session_state.flash_effect = True
        st.toast(f"✅ บันทึกสถิติเพิ่มสำเร็จ {added_count} ชุด!", icon="🎲")
        st.rerun()
    else:
        st.error("⚠️ ไม่พบตัวเลข 1-6 ที่ครบ 3 ตัว กรุณาตรวจสอบตัวเลขอีกครั้ง")

if st.session_state.last_bet_result:
    res = st.session_state.last_bet_result
    if res["status"] == "WIN":
        st.success(res["msg"])
    elif res["status"] == "DRAW":
        st.info(res["msg"])
    elif res["status"] == "LOSS":
        st.error(res["msg"])

# ==========================================
# 5. MATH ENGINE (3-18 TOTALS + COMBO + DOUBLES)
# ==========================================
history_df = pd.DataFrame(st.session_state.history)
total_rounds = len(history_df)

st.divider()

if total_rounds < 15:
    st.info(f"⏳ **ระบบกำลังสะสมสถิติ (Warm-Up Phase):** ต้องการอีก {15 - total_rounds} ตา เพื่อเริ่มคำนวณสูตรโต๊ด/เบิ้ล/แต้มรวม 3-18")
    st.session_state.betting_started = False
else:
    st.session_state.betting_started = True

if total_rounds >= 15:
    decay = np.exp(-0.08 * np.arange(total_rounds)[::-1])
    combo_counts = Counter()
    double_counts = Counter()
    sum_counts = Counter()

    for idx, row in history_df.iterrows():
        d_list = sorted([row["D1"], row["D2"], row["D3"]])
        w = decay[idx]
        
        pairs = [(d_list[0], d_list[1]), (d_list[0], d_list[2]), (d_list[1], d_list[2])]
        for p1, p2 in pairs:
            if p1 != p2:
                combo_counts[f"{p1}-{p2}"] += w
            else:
                double_counts[f"{p1}-{p1}"] += w
                
        sum_counts[row["Sum"]] += w

    top_combo = combo_counts.most_common(1)[0][0] if combo_counts else "5-6"
    top_double = double_counts.most_common(1)[0][0] if double_counts else "6-6"
    top_sum = sum_counts.most_common(1)[0][0] if sum_counts else 10
    sum_odds_val = SUM_PAYOUTS.get(top_sum, 6.0)

    # Runs Test ตรวจสอบความนิ่ง
    recent_sums = history_df["Sum"].tail(10).tolist()
    runs = 1
    for i in range(1, len(recent_sums)):
        if (recent_sums[i] >= 11) != (recent_sums[i-1] >= 11):
            runs += 1

    is_choppy = (runs >= 8)

    st.subheader("🎯 คำแนะนำการเดิมพันตาถัดไป (Next Bet Recommendation)")

    if is_choppy:
        st.warning("⚠️ **กราฟเปลี่ยนหน้าผันผวนสูง (High Choppiness):** แนะนำให้ **พักสังเกตการณ์ (WAIT)** ในตานี้")
        st.session_state.active_bet = None
    else:
        combo_unit = max(20, round(base_unit * 1.5 / 10) * 10)
        double_unit = max(20, round(base_unit * 0.5 / 10) * 10)
        sum_unit = max(20, round(base_unit * 0.8 / 10) * 10)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("🎲 โต๊ดคู่เต็ง (Combo)", top_combo)
            st.write(f"👉 **วางเงินโต๊ดคู่:** `{combo_unit:,.0f}` บาท (จ่าย 5 เท่า)")
        
        with c2:
            st.metric("👯 เลขเบิ้ลเต็ง (Double)", top_double)
            st.write(f"👉 **วางเงินเบิ้ล:** `{double_unit:,.0f}` บาท (จ่าย 10 เท่า)")
            
        with c3:
            st.metric("🎯 แต้มรวมเป้าหมาย (3-18)", f"{top_sum} แต้ม")
            st.write(f"👉 **วางเงินแต้มรวม:** `{sum_unit:,.0f}` บาท (จ่าย {sum_odds_val:,.0f} เท่า)")

        st.session_state.active_bet = {
            "combo_target": top_combo,
            "combo_unit": combo_unit,
            "double_target": top_double,
            "double_unit": double_unit,
            "sum_target": top_sum,
            "sum_unit": sum_unit
        }

# ==========================================
# 6. STATS DISPLAY
# ==========================================
if total_rounds > 0:
    st.divider()
    st.subheader(f"📊 ประวัติการกรอกสถิติ (บันทึกแล้ว {total_rounds} ตา)")
    st.dataframe(history_df.tail(15), use_container_width=True)
