import streamlit as st
import numpy as np
import pandas as pd
import re

# ==========================================
# 1. PAGE SETUP & TITLE
# ==========================================
st.set_page_config(page_title="Hi-Lo Automated Math System", page_icon="🎲", layout="wide")

st.title("🎲 ระบบวิเคราะห์ไฮโลอัตโนมัติ (Automated Win/Loss & Bet Tracking)")
st.caption("ระบบคำนวณแพ้/ชนะอัตโนมัติ + รองรับวางสถิติชุดใหญ่ + 4 สูตรคณิตศาสตร์ขั้นสูง + Stop-Loss")

# Initialize Session State
if "history" not in st.session_state:
    st.session_state.history = []
if "betting_started" not in st.session_state:
    st.session_state.betting_started = False
if "consecutive_losses" not in st.session_state:
    st.session_state.consecutive_losses = 0
if "cooldown_counter" not in st.session_state:
    st.session_state.cooldown_counter = 0
if "active_bet" not in st.session_state:
    st.session_state.active_bet = None
if "last_bet_result" not in st.session_state:
    st.session_state.last_bet_result = None

# ==========================================
# 2. SIDEBAR: MONEY MANAGEMENT & SYSTEM CONTROL
# ==========================================
st.sidebar.header("💰 ระบบบริหารเงินทุน")

capital = st.sidebar.number_input("กรอกเงินทุนปัจจุบัน (บาท):", min_value=100, value=1000, step=100)
target_profit = capital * 0.30
base_unit = max(20, round((capital * 0.035) / 10) * 10)

st.sidebar.markdown(f"""
* **เป้าหมายกำไร (30%):** `{target_profit:,.0f}` บาท
* **หน่วยลงเงินเบื้องต้น (3.5%):** `{base_unit:,.0f}` บาท
""")

if st.sidebar.button("🔄 รีเซ็ตระบบทั้งหมด"):
    st.session_state.history = []
    st.session_state.betting_started = False
    st.session_state.consecutive_losses = 0
    st.session_state.cooldown_counter = 0
    st.session_state.active_bet = None
    st.session_state.last_bet_result = None
    st.rerun()

# ==========================================
# 3. HELPER FUNCTIONS & ADVANCED MATH CALCULATIONS
# ==========================================
def parse_multiple_dice_inputs(input_text):
    """ ดึงตัวเลข 1-6 ทั้งหมด ออกมาจัดกลุ่มละ 3 ตัว (รองรับหลายชุดพร้อมกัน) """
    all_digits = re.findall(r'[1-6]', input_text)
    # แบ่งตัวเลขเป็นกลุ่ม กลุ่มละ 3 ตัว
    parsed_groups = []
    for i in range(0, len(all_digits) - len(all_digits) % 3, 3):
        parsed_groups.append([int(all_digits[i]), int(all_digits[i+1]), int(all_digits[i+2])])
    return parsed_groups

def calculate_round_pnl(bet_info, dice_list, total_sum, result_type):
    main_target = bet_info.get("target")
    main_unit = bet_info.get("main_unit", 0)
    
    combo_target = bet_info.get("combo_target")
    combo_unit = bet_info.get("combo_unit", 0)
    combo_odds = bet_info.get("combo_odds", 3.0)
    
    hilo11_active = bet_info.get("hilo11_active", False)
    hilo11_unit = bet_info.get("hilo11_unit", 0)
    
    total_bet = main_unit + combo_unit + hilo11_unit
    total_payout = 0

    if result_type == main_target:
        total_payout += main_unit * 2

    if combo_target:
        win_combo = False
        if combo_target == "1-ต่ำ" and (total_sum <= 10) and (1 in dice_list): win_combo = True
        elif combo_target == "6-สูง" and (total_sum >= 12) and (6 in dice_list): win_combo = True
        elif combo_target == "4-สูง" and (total_sum >= 12) and (4 in dice_list): win_combo = True
        elif combo_target == "3-ต่ำ" and (total_sum <= 10) and (3 in dice_list): win_combo = True
        elif combo_target == "6-ต่ำ" and (total_sum <= 10) and (6 in dice_list): win_combo = True
        elif combo_target == "5-ต่ำ" and (total_sum <= 10) and (5 in dice_list): win_combo = True
        
        if win_combo:
            total_payout += combo_unit * (combo_odds + 1)

    if hilo11_active and total_sum == 11:
        total_payout += hilo11_unit * (7 + 1)

    net_pnl = total_payout - total_bet
    return net_pnl, total_bet

# ==========================================
# 4. INPUT SECTION & AUTOMATED EVALUATION
# ==========================================
st.subheader("📥 ป้อนผลลูกเต๋า (กรอกทีละชุด หรือวางพร้อมกันหลายชุดก็ได้)")

col_in, col_btn = st.columns([3, 1])
with col_in:
    dice_input = st.text_area("วางผลเต๋า เช่น '123 654 112 456' หรือวางต่อกันหลายๆ บรรทัดได้เลย:", key="dice_input_key", height=100)

with col_btn:
    st.write("") 
    st.write("")
    submit_btn = st.button("บันทึกผลทั้งหมด 🎲", use_container_width=True)

if submit_btn and dice_input:
    dice_groups = parse_multiple_dice_inputs(dice_input)
    
    if len(dice_groups) > 0:
        added_count = 0
        for parsed_dice in dice_groups:
            d1, d2, d3 = parsed_dice
            total_sum = d1 + d2 + d3
            
            if total_sum == 11:
                result_type = "11-HiLo"
            elif total_sum >= 12:
                result_type = "High"
            else:
                result_type = "Low"
                
            # ประมวลผลเดิมพันเฉพาะถ้าอยู่ในช่วงเดินเงินจริง
            if st.session_state.betting_started and st.session_state.active_bet:
                if st.session_state.cooldown_counter > 0:
                    st.session_state.cooldown_counter -= 1
                    st.session_state.last_bet_result = {
                        "status": "WAIT", 
                        "msg": f"⏸️ **อยู่ในช่วงพักสังเกตการณ์ (Stop-Loss)** เหลืออีก {st.session_state.cooldown_counter} ตา"
                    }
                else:
                    net_pnl, total_bet = calculate_round_pnl(
                        st.session_state.active_bet, 
                        [d1, d2, d3], 
                        total_sum, 
                        result_type
                    )
                    
                    if net_pnl > 0:
                        st.session_state.consecutive_losses = 0
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
                        st.session_state.consecutive_losses += 1
                        if st.session_state.consecutive_losses >= 2:
                            st.session_state.cooldown_counter = 4
                        st.session_state.last_bet_result = {
                            "status": "LOSS", 
                            "msg": f"💥 **แพ้!** ติดลบ -{abs(net_pnl):,.0f} บาท (ผลออก {d1}-{d2}-{d3} = {total_sum})"
                        }

            # บันทึกเข้า History
            st.session_state.history.append({
                "Round": len(st.session_state.history) + 1,
                "D1": d1, "D2": d2, "D3": d3,
                "Sum": total_sum,
                "Type": result_type
            })
            added_count += 1

        st.toast(f"✅ บันทึกสถิติเพิ่มสำเร็จ {added_count} ชุด!", icon="🎲")
        st.rerun()
    else:
        st.error("⚠️ ไม่พบตัวเลข 1-6 ที่ครบ 3 ตัว กรุณาตรวจสอบตัวเลขอีกครั้ง")

# แสดงแถบแจ้งเตือนผลการเดิมพันของตาล่าสุด
if st.session_state.last_bet_result:
    res = st.session_state.last_bet_result
    if res["status"] == "WIN":
        st.success(res["msg"])
    elif res["status"] == "DRAW":
        st.info(res["msg"])
    elif res["status"] == "LOSS":
        st.error(res["msg"])
    else:
        st.warning(res["msg"])

# ==========================================
# 5. STATS DISPLAY & MATH ANALYSIS ENGINE
# ==========================================
history_df = pd.DataFrame(st.session_state.history)
total_rounds = len(history_df)

st.divider()
st.subheader(f"📊 ประวัติและวิเคราะห์ผล (บันทึกแล้ว {total_rounds} ตา)")

if total_rounds < 25:
    st.info(f"⏳ **ระบบกำลังสะสมสถิติ (Warm-Up Phase):** ต้องการอีก {25 - total_rounds} ตา เพื่อเริ่มวิเคราะห์ด้วยระบบคณิตศาสตร์ขั้นสูง")
    st.session_state.betting_started = False
else:
    st.session_state.betting_started = True

if total_rounds > 0:
    st.dataframe(history_df.tail(15), use_container_width=True)

    # --------------------------------------
    # MATH ENGINE
    # --------------------------------------
    if total_rounds >= 5:
        types = history_df["Type"].tolist()
        states = ["Low", "High", "11-HiLo"]
        transition_counts = {s1: {s2: 0 for s2 in states} for s1 in states}
        
        for i in range(len(types) - 1):
            s_curr = types[i]
            s_next = types[i+1]
            if s_curr in states and s_next in states:
                transition_counts[s_curr][s_next] += 1
                
        last_state = types[-1]
        current_transitions = transition_counts[last_state]
        sum_trans = sum(current_transitions.values())
        
        markov_probs = {}
        for s in states:
            markov_probs[s] = (current_transitions[s] / sum_trans) if sum_trans > 0 else 0.333

        decay_factor = np.exp(-0.1 * np.arange(total_rounds)[::-1])
        weighted_high = np.sum((history_df["Type"] == "High") * decay_factor) / np.sum(decay_factor)
        weighted_low = np.sum((history_df["Type"] == "Low") * decay_factor) / np.sum(decay_factor)
        
        recent_7 = history_df["Type"].tail(7).value_counts(normalize=True)
        entropy = -np.sum(recent_7 * np.log2(recent_7 + 1e-9))
        
        recent_11_gap = 0
        for t in reversed(types):
            if t == "11-HiLo":
                break
            recent_11_gap += 1

        # --------------------------------------
        # SYSTEM DECISION & RECOMMENDATION
        # --------------------------------------
        st.divider()
        st.subheader("🎯 คำแนะนำการเดิมพันตาถัดไป (Next Bet Recommendation)")

        if st.session_state.cooldown_counter > 0:
            st.warning(f"🛑 **ระบบสั่งหยุดพัก (Stop-Loss Active):** แพ้ติดกัน ปิดการวางเงินอีก {st.session_state.cooldown_counter} ตา เพื่อรอกราฟนิ่ง")
            st.session_state.active_bet = None
        elif entropy > 1.25:
            st.warning("⚠️ **Entropy สูงเกินไป (>1.25):** เค้าเต๋ามั่วและสลับผันผวน แนะนำให้ **พัก (WAIT)** ชั่วคราว")
            st.session_state.active_bet = None
        else:
            prob_high = (markov_probs["High"] * 0.6) + (weighted_high * 0.4)
            prob_low = (markov_probs["Low"] * 0.6) + (weighted_low * 0.4)
            
            if prob_high > prob_low:
                predicted_next_state = "High"
                win_prob = prob_high
            else:
                predicted_next_state = "Low"
                win_prob = prob_low

            b_main = 1.0
            p_main = win_prob
            q_main = 1 - p_main
            kelly_f = max(0, (b_main * p_main - q_main) / b_main) * 0.15
            
            main_bet_amount = max(base_unit, round((capital * kelly_f) / 10) * 10) if kelly_f > 0 else base_unit
            
            hilo11_active = (recent_11_gap >= 7)
            hilo11_bet_amount = max(20, round(main_bet_amount * 0.2 / 10) * 10) if hilo11_active else 0

            combo_target = "6-สูง" if predicted_next_state == "High" else "1-ต่ำ"
            combo_bet_amount = max(20, round(main_bet_amount * 0.3 / 10) * 10)
            combo_odds = 3.0

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("ฝั่งหลักที่แนะนำ", predicted_next_state, f"มั่นใจ {win_prob*100:.1f}%")
                st.write(f"👉 **วางเงินฝั่งหลัก:** `{main_bet_amount:,.0f}` บาท")
            
            with c2:
                st.metric("หน้าควบเสริม (Combo)", combo_target)
                st.write(f"👉 **วางเงินหน้าควบ:** `{combo_bet_amount:,.0f}` บาท (จ่าย 3 เท่า)")
                
            with c3:
                hilo_status = "⚠️ ควรดัก!" if hilo11_active else "ปกติ"
                st.metric("สถิติ 11-ไฮโล", f"หายไป {recent_11_gap} ตา", hilo_status)
                if hilo11_active:
                    st.write(f"👉 **วางเงินดัก 11:** `{hilo11_bet_amount:,.0f}` บาท (จ่าย 7 เท่า)")
                else:
                    st.write("👉 **วางเงินดัก 11:** `-`")

            st.session_state.active_bet = {
                "target": predicted_next_state,
                "main_unit": main_bet_amount,
                "combo_target": combo_target,
                "combo_unit": combo_bet_amount,
                "combo_odds": combo_odds,
                "hilo11_active": hilo11_active,
                "hilo11_unit": hilo11_bet_amount
            }st.sidebar.markdown(f"""
* **เป้าหมายกำไร (30%):** `{target_profit:,.0f}` บาท
* **หน่วยลงเงินเบื้องต้น (3.5%):** `{base_unit:,.0f}` บาท
""")

if st.sidebar.button("🔄 รีเซ็ตระบบทั้งหมด"):
    st.session_state.history = []
    st.session_state.betting_started = False
    st.session_state.consecutive_losses = 0
    st.session_state.cooldown_counter = 0
    st.session_state.active_bet = None
    st.session_state.last_bet_result = None
    st.rerun()

# ==========================================
# 3. HELPER FUNCTIONS & ADVANCED MATH CALCULATIONS
# ==========================================
def parse_dice_input(input_str):
    """ แปลงข้อความตัวเลข 3 ตัว เช่น '123' หรือ '1 2 3' หรือ '1,2,3' เป็น List """
    digits = re.findall(r'[1-6]', input_str)
    if len(digits) == 3:
        return [int(d) for d in digits]
    return None

def calculate_round_pnl(bet_info, dice_list, total_sum, result_type):
    """
    คำนวณกำไร/ขาดทุนสุทธิ (Net PnL) ของตานั้นๆ แบบละเอียดทุกหน้าเดิมพัน
    """
    main_target = bet_info.get("target")
    main_unit = bet_info.get("main_unit", 0)
    
    combo_target = bet_info.get("combo_target")
    combo_unit = bet_info.get("combo_unit", 0)
    combo_odds = bet_info.get("combo_odds", 3.0)
    
    hilo11_active = bet_info.get("hilo11_active", False)
    hilo11_unit = bet_info.get("hilo11_unit", 0)
    
    total_bet = main_unit + combo_unit + hilo11_unit
    total_payout = 0

    # 1. คำนวณฝั่งหลัก (High / Low / 11-HiLo) - อัตราจ่าย 1 เท่า
    if result_type == main_target:
        total_payout += main_unit * 2 # คืนทุน + กำไร 1 เท่า

    # 2. คำนวณหน้าควบพิเศษ
    if combo_target:
        win_combo = False
        if combo_target == "1-ต่ำ" and (total_sum <= 10) and (1 in dice_list): win_combo = True
        elif combo_target == "6-สูง" and (total_sum >= 12) and (6 in dice_list): win_combo = True
        elif combo_target == "4-สูง" and (total_sum >= 12) and (4 in dice_list): win_combo = True
        elif combo_target == "3-ต่ำ" and (total_sum <= 10) and (3 in dice_list): win_combo = True
        elif combo_target == "6-ต่ำ" and (total_sum <= 10) and (6 in dice_list): win_combo = True
        elif combo_target == "5-ต่ำ" and (total_sum <= 10) and (5 in dice_list): win_combo = True
        
        if win_combo:
            total_payout += combo_unit * (combo_odds + 1) # คืนทุน + กำไรตามอัตราจ่าย

    # 3. คำนวณการดัก 11 ไฮโล - อัตราจ่าย 7 เท่า
    if hilo11_active and total_sum == 11:
        total_payout += hilo11_unit * (7 + 1) # คืนทุน + กำไร 7 เท่า

    net_pnl = total_payout - total_bet
    return net_pnl, total_bet

# ==========================================
# 4. INPUT SECTION & AUTOMATED EVALUATION
# ==========================================
st.subheader("📥 ป้อนผลลูกเต๋า")

col_in, col_btn = st.columns([3, 1])
with col_in:
    dice_input = st.text_input("กรอกผลเต๋า 3 ลูก (เช่น 123, 654, 1 1 2):", key="dice_input_key")

with col_btn:
    st.write("") # Spacer
    st.write("")
    submit_btn = st.button("บันทึกผล 🎲", use_container_width=True)

if submit_btn and dice_input:
    parsed_dice = parse_dice_input(dice_input)
    if parsed_dice:
        d1, d2, d3 = parsed_dice
        total_sum = d1 + d2 + d3
        
        if total_sum == 11:
            result_type = "11-HiLo"
        elif total_sum >= 12:
            result_type = "High"
        else:
            result_type = "Low"
            
        # ถ้าอยู่ในช่วงเดินเงินจริง และมีคำแนะนำค้างอยู่ ให้ประมวลผลชนะ/แพ้/เท่าทุน อัตโนมัติ
        if st.session_state.betting_started and st.session_state.active_bet:
            if st.session_state.cooldown_counter > 0:
                st.session_state.cooldown_counter -= 1
                st.session_state.last_bet_result = {
                    "status": "WAIT", 
                    "msg": f"⏸️ **อยู่ในช่วงพักสังเกตการณ์ (Stop-Loss)** เหลืออีก {st.session_state.cooldown_counter} ตา"
                }
            else:
                net_pnl, total_bet = calculate_round_pnl(
                    st.session_state.active_bet, 
                    [d1, d2, d3], 
                    total_sum, 
                    result_type
                )
                
                if net_pnl > 0:
                    st.session_state.consecutive_losses = 0
                    st.session_state.last_bet_result = {
                        "status": "WIN", 
                        "msg": f"🎉 **ชนะ!** บวกสุทธิ +{net_pnl:,.0f} บาท (ผลออก {d1}-{d2}-{d3} = {total_sum})"
                    }
                elif net_pnl == 0:
                    # เท่าทุน (Draw) ไม่นับว่าแพ้ และไม่เพิ่ม consecutive_losses
                    st.session_state.last_bet_result = {
                        "status": "DRAW", 
                        "msg": f"⚖️ **เท่าทุน (เจ๊าะแจะ)!** ได้-เสีย 0 บาท (ผลออก {d1}-{d2}-{d3} = {total_sum})"
                    }
                else:
                    st.session_state.consecutive_losses += 1
                    if st.session_state.consecutive_losses >= 2:
                        st.session_state.cooldown_counter = 4
                    st.session_state.last_bet_result = {
                        "status": "LOSS", 
                        "msg": f"💥 **แพ้!** ติดลบ -{abs(net_pnl):,.0f} บาท (ผลออก {d1}-{d2}-{d3} = {total_sum})"
                    }

        # บันทึกเข้า History
        st.session_state.history.append({
            "Round": len(st.session_state.history) + 1,
            "D1": d1, "D2": d2, "D3": d3,
            "Sum": total_sum,
            "Type": result_type
        })
        st.rerun()
    else:
        st.error("⚠️ กรุณากรอกตัวเลข 1-6 ให้ครบ 3 ตัว")

# แสดงแถบแจ้งเตือนผลการเดิมพันของตาล่าสุด
if st.session_state.last_bet_result:
    res = st.session_state.last_bet_result
    if res["status"] == "WIN":
        st.success(res["msg"])
    elif res["status"] == "DRAW":
        st.info(res["msg"])
    elif res["status"] == "LOSS":
        st.error(res["msg"])
    else:
        st.warning(res["msg"])

# ==========================================
# 5. STATS DISPLAY & MATH ANALYSIS ENGINE
# ==========================================
history_df = pd.DataFrame(st.session_state.history)
total_rounds = len(history_df)

st.divider()
st.subheader(f"📊 ประวัติและวิเคราะห์ผล (บันทึกแล้ว {total_rounds} ตา)")

if total_rounds < 25:
    st.info(f"⏳ **ระบบกำลังสะสมสถิติ (Warm-Up Phase):** ต้องการอีก {25 - total_rounds} ตา เพื่อเริ่มวิเคราะห์ด้วยระบบคณิตศาสตร์ขั้นสูง")
    st.session_state.betting_started = False
else:
    st.session_state.betting_started = True

if total_rounds > 0:
    st.dataframe(history_df.tail(10), use_container_width=True)

    # --------------------------------------
    # MATH ENGINE (Markov + Recency Decay + Entropy + Kelly)
    # --------------------------------------
    if total_rounds >= 5:
        # A. Markov Chain Transition Matrix
        types = history_df["Type"].tolist()
        states = ["Low", "High", "11-HiLo"]
        transition_counts = {s1: {s2: 0 for s2 in states} for s1 in states}
        
        for i in range(len(types) - 1):
            s_curr = types[i]
            s_next = types[i+1]
            if s_curr in states and s_next in states:
                transition_counts[s_curr][s_next] += 1
                
        last_state = types[-1]
        current_transitions = transition_counts[last_state]
        sum_trans = sum(current_transitions.values())
        
        markov_probs = {}
        for s in states:
            markov_probs[s] = (current_transitions[s] / sum_trans) if sum_trans > 0 else 0.333

        # B. Exponential Recency Decay (λ = 0.1)
        decay_factor = np.exp(-0.1 * np.arange(total_rounds)[::-1])
        weighted_high = np.sum((history_df["Type"] == "High") * decay_factor) / np.sum(decay_factor)
        weighted_low = np.sum((history_df["Type"] == "Low") * decay_factor) / np.sum(decay_factor)
        
        # C. Windowed Entropy (7 ตาล่าสุด)
        recent_7 = history_df["Type"].tail(7).value_counts(normalize=True)
        entropy = -np.sum(recent_7 * np.log2(recent_7 + 1e-9))
        
        # D. 11-HiLo Gap Tracker
        recent_11_gap = 0
        for t in reversed(types):
            if t == "11-HiLo":
                break
            recent_11_gap += 1

        # --------------------------------------
        # SYSTEM DECISION & RECOMMENDATION
        # --------------------------------------
        st.divider()
        st.subheader("🎯 คำแนะนำการเดิมพันตาถัดไป (Next Bet Recommendation)")

        if st.session_state.cooldown_counter > 0:
            st.warning(f"🛑 **ระบบสั่งหยุดพัก (Stop-Loss Active):** แพ้ติดกัน ปิดการวางเงินอีก {st.session_state.cooldown_counter} ตา เพื่อรอกราฟนิ่ง")
            st.session_state.active_bet = None
        elif entropy > 1.25:
            st.warning("⚠️ **Entropy สูงเกินไป (>1.25):** เค้าเต๋ามั่วและสลับผันผวน แนะนำให้ **พัก (WAIT)** ชั่วคราว")
            st.session_state.active_bet = None
        else:
            # หาฝั่งที่มีความน่าจะเป็นสูงสุดจาก Markov + Decay
            prob_high = (markov_probs["High"] * 0.6) + (weighted_high * 0.4)
            prob_low = (markov_probs["Low"] * 0.6) + (weighted_low * 0.4)
            
            if prob_high > prob_low:
                predicted_next_state = "High"
                win_prob = prob_high
            else:
                predicted_next_state = "Low"
                win_prob = prob_low

            # คำนวณ Fractional Kelly (15%) สำหรับฝั่งหลัก
            b_main = 1.0 # อัตราจ่าย 1 เท่า
            p_main = win_prob
            q_main = 1 - p_main
            kelly_f = max(0, (b_main * p_main - q_main) / b_main) * 0.15
            
            main_bet_amount = max(base_unit, round((capital * kelly_f) / 10) * 10) if kelly_f > 0 else base_unit
            
            # การดัก 11 ไฮโล (ถ้าไม่เห็น 11 เกิน 7 ตา)
            hilo11_active = (recent_11_gap >= 7)
            hilo11_bet_amount = max(20, round(main_bet_amount * 0.2 / 10) * 10) if hilo11_active else 0

            # ตรวจสอบหน้าควบยอดนิยม
            combo_target = "6-สูง" if predicted_next_state == "High" else "1-ต่ำ"
            combo_bet_amount = max(20, round(main_bet_amount * 0.3 / 10) * 10)
            combo_odds = 3.0 # อัตราจ่ายประมาณ 3 เท่า

            # แสดงผลการวิเคราะห์
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("ฝั่งหลักที่แนะนำ", predicted_next_state, f"มั่นใจ {win_prob*100:.1f}%")
                st.write(f"👉 **วางเงินฝั่งหลัก:** `{main_bet_amount:,.0f}` บาท")
            
            with c2:
                st.metric("หน้าควบเสริม (Combo)", combo_target)
                st.write(f"👉 **วางเงินหน้าควบ:** `{combo_bet_amount:,.0f}` บาท (จ่าย 3 เท่า)")
                
            with c3:
                hilo_status = "⚠️ ควรดัก!" if hilo11_active else "ปกติ"
                st.metric("สถิติ 11-ไฮโล", f"หายไป {recent_11_gap} ตา", hilo_status)
                if hilo11_active:
                    st.write(f"👉 **วางเงินดัก 11:** `{hilo11_bet_amount:,.0f}` บาท (จ่าย 7 เท่า)")
                else:
                    st.write("👉 **วางเงินดัก 11:** `-`")

            # บันทึก Active Bet สำหรับคำนวณ Net PnL ในตาถัดไป
            st.session_state.active_bet = {
                "target": predicted_next_state,
                "main_unit": main_bet_amount,
                "combo_target": combo_target,
                "combo_unit": combo_bet_amount,
                "combo_odds": combo_odds,
                "hilo11_active": hilo11_active,
                "hilo11_unit": hilo11_bet_amount
            }
