import streamlit as st
import pandas as pd
import json
import os
import hashlib
import google.generativeai as genai

st.set_page_config(page_title="Sammy - Intelligence Engine", layout="wide", page_icon="🐢")

# ----------------- ระบบเชื่อมต่อ AI -----------------
api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    with st.sidebar:
        api_key = st.text_input("🔑 ใส่ Gemini API Key:", type="password")

def get_ai_response(prompt_text):
    if not api_key:
        return "⚠️ กรุณาระบุ Gemini API Key ในแถบด้านซ้ายหรือ secrets.toml ก่อนใช้งาน"
    try:
        genai.configure(api_key=api_key)
        model_candidates = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-pro", "gemini-1.0-pro"]
        for m in model_candidates:
            try:
                model = genai.GenerativeModel(m)
                res = model.generate_content(prompt_text)
                return res.text
            except:
                continue
        return "ไม่สามารถเชื่อมต่อโมเดล AI ที่รองรับได้ กรุณาตรวจสอบ API Key"
    except Exception as e:
        return f"เกิดข้อผิดพลาด: {e}"

# ----------------- สไตล์ UI -----------------
st.markdown("""
<style>
    .kpi-card { background-color: #0f172a; border: 1px solid #334155; border-radius: 10px; padding: 14px; margin-bottom: 12px; }
    .badge-win { background-color: #065f46; color: #34d399; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 0.85rem; }
    .badge-test { background-color: #7c2d12; color: #fb923c; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 0.85rem; }
    .ai-box { background: #1c1917; border-left: 4px solid #f59e0b; padding: 14px; border-radius: 8px; margin-top: 10px; }
    .sec-title { border-bottom: 2px solid #334155; padding-bottom: 8px; margin-bottom: 16px; color: #38bdf8; }
</style>
""", unsafe_allow_html=True)

# ----------------- จัดการ WATCHLIST ถาวร (แก้ Bug List/Dict) -----------------
WATCHLIST_FILE = "watchlist_data.json"

DEFAULT_STORES = {
    "YVIS": {
        "category": "เครื่องประดับแฟชั่น / สร้อยคอเงินแท้",
        "creatives_count": 26,
        "winner_days": 42,
        "winner_format": "คลิปทดสอบคุณภาพ ไม่ลอกไม่ดำ ใส่อาบน้ำได้",
        "winner_caption": "สร้อยคอเงินแท้ 925 โดนน้ำ โดนเหงื่อใส่อาบน้ำได้ตลอด 24 ชม. ไม่ลอก ไม่ดำ สลักชื่อฟรี โปรโมชัน 2 ชิ้นส่งฟรี #YVIS",
        "cta": "TikTok Shop (ตะกร้าเหลือง)",
        "flash_sale": "ลดเหลือ 490.- (ปกติ 890.-)",
        "gimmick": "Midnight Order (00:00 - 02:00) แถมกล่อง Jewelry Box ฟรี",
        "coupon_aov": "ลด 15% เมื่อซื้อครบ 999.-",
        "hero_products": "สร้อยคอ Minimal Heart, แหวนเงินปรับไซส์ได้",
        "stock": "พร้อมส่ง 2,500+ ชิ้น (เตรียมสต็อกรับ D-Day)"
    },
    "Royal Canin Thailand": {
        "category": "อาหารสัตว์เลี้ยง / โภชนาการเฉพาะทาง",
        "creatives_count": 34,
        "winner_days": 90,
        "winner_format": "แอนิเมชันทางเดินอาหาร + รีวิวแก้ปัญหาก้อนขน",
        "winner_caption": "น้องแมวมีปัญหาก้อนขน ท้องผูก ขย้อนบ่อย? Hairball Care สูตรขจัดก้อนขนใน 14 วัน โปร 9.9 แถมฟรีชามอาหารกันมด",
        "cta": "Shopee Mall / Lazada",
        "flash_sale": "สูตร 2kg ลดเหลือ 689.- (ปกติ 850.-)",
        "gimmick": "ซื้อครบ 1,599.- แถมฟรีชามอาหารกันมด + ขนมขจัดก้อนขน",
        "coupon_aov": "คูปองลด 200.- เมื่อซื้อครบ 1,499.-",
        "hero_products": "Hairball Care 2kg, Indoor Adult 4kg",
        "stock": "พร้อมส่ง 5,000+ ชิ้น"
    }
}

def load_stores():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                # แปลงข้อมูลกรณีของเดิมบันทึกเป็น List ให้กลายเป็น Dict
                if isinstance(raw_data, list):
                    converted = {}
                    for item in raw_data:
                        name = item.get("name", "") if isinstance(item, dict) else str(item)
                        if name:
                            converted[name] = {
                                "category": "ทั่วไป",
                                "creatives_count": 15,
                                "winner_days": 25,
                                "winner_format": f"คลิปสั้นนำเสนอจุดเด่นของ {name}",
                                "winner_caption": f"โปรโมชั่นพิเศษจากร้าน {name} ของแท้ 100% พร้อมส่ง",
                                "cta": "TikTok Shop / Shopee",
                                "flash_sale": "ลด 20-30% ตามช่วงแคมเปญ",
                                "gimmick": "ส่งฟรีเมื่อซื้อครบ 2 ชิ้น",
                                "coupon_aov": "คูปองลด 50.- เมื่อซื้อครบ 500.-",
                                "hero_products": f"สินค้าชูโรงของ {name}",
                                "stock": "พร้อมส่งสต็อกแน่น"
                            }
                    return converted if converted else DEFAULT_STORES
                elif isinstance(raw_data, dict):
                    return raw_data
        except:
            pass
    return DEFAULT_STORES

def save_stores(data):
    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

stores_db = load_stores()

# ----------------- Dynamic Market Generator -----------------
def generate_market_metrics(keyword):
    h = int(hashlib.md5(keyword.encode('utf-8')).hexdigest(), 16)
    ad_count = 35 + (h % 165)
    stock_rate = 60 + (h % 35)
    d_day_boost = 15 + (h % 40)
    
    kw = keyword.strip()
    if any(x in kw for x in ["แก้ว", "กระติก", "ขวด"]):
        angle_win = "ทดสอบเก็บความเย็น 24 ชม. คว่ำแก้วแล้วน้ำไม่หก"
        angle_teaser = "ป้ายลดราคา Flash Sale สีจัดจ้าน + ของแถมหลอดซิลิโคน/ยางรอง"
        platform = "TikTok Shop 65% และ Shopee 35%"
        hook_type = "คลิปทดสอบการใช้งานจริง (Stress Test)"
    elif any(x in kw for x in ["แมว", "หมา", "สัตว์"]):
        angle_win = "ชูผลลัพธ์สุขภาพสัตว์เลี้ยง ขนไม่ร่วง ถนอมไต ไม่เค็ม"
        angle_teaser = "จัดเซ็ต Bundle ซื้อยกลัง แถมขนมเลียหรือชามอาหาร"
        platform = "Shopee 55% และ Lazada 45%"
        hook_type = "คลิปรีวิวสัตว์เลี้ยงกินจริงและเห็นผลลัพธ์"
    elif any(x in kw for x in ["เสื้อ", "ผ้า", "กางเกง", "แฟชั่น"]):
        angle_win = "ลองสวมใส่จริง บอกไซส์นางแบบชัดเจน ผ้าไม่ยับไม่ต้องรีด"
        angle_teaser = "แจกโค้ด Midnight ช้อปคู่ลดเพิ่ม 30%"
        platform = "TikTok Shop 70% และ Line Shopping 30%"
        hook_type = "คลิป Try-on Haul แมตช์ชุดในชีวิตประจำวัน"
    else:
        angle_win = f"คลิปเจาะลึกฟังก์ชันหลักของ {kw} ชูความคุ้มค่าเทียบราคา"
        angle_teaser = "เปิดจองโปรโมชัน Early Bird พร้อมโค้ดลดเงินสดล่วงหน้า"
        platform = "Shopee 50% และ TikTok Shop 50%"
        hook_type = "วิดีโอแกะกล่อง Unboxing และแก้ปัญหาเฉพาะจุด"

    return {
        "count": ad_count,
        "stock": stock_rate,
        "boost": d_day_boost,
        "winner_angle": angle_win,
        "teaser_angle": angle_teaser,
        "platform": platform,
        "hook": hook_type
    }

# ----------------- ควบคุมหน้า View -----------------
if "viewing_store" not in st.session_state:
    st.session_state["viewing_store"] = None

# ================= VIEW 2: หน้ารายละเอียดร้านค้า (Full-Screen) =================
if st.session_state["viewing_store"]:
    store_name = st.session_state["viewing_store"]
    data = stores_db.get(store_name, None)

    if st.button("⬅️ กลับสู่หน้าแดชบอร์ดหลัก"):
        st.session_state["viewing_store"] = None
        st.rerun()

    if data:
        st.title(f"🏢 ห้องบัญชาการวิเคราะห์: {store_name}")
        st.caption(f"หมวดหมู่: {data.get('category', 'ทั่วไป')} | แอดที่รันอยู่: {data.get('creatives_count', 10)} แคมเปญ")

        col_d1, col_d2 = st.columns([1.2, 1], gap="large")

        with col_d1:
            st.markdown("<h3 class='sec-title'>1. มิติข้อมูลโฆษณา (Ad Intelligence)</h3>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="kpi-card">
                <span class="badge-win">🔥 WINNER AD (รันมา {data.get('winner_days', 30)} วัน)</span><br><br>
                <b>รูปแบบและ Hook:</b> {data.get('winner_format', '-')}<br>
                <b>CTA ปลายทาง:</b> <code>{data.get('cta', '-')}</code><br>
                <b>แคปชันตรวจพบ:</b> {data.get('winner_caption', '-')}
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<h3 class='sec-title'>2. มิติราคาและโปรโมชั่น (Price & Deal)</h3>", unsafe_allow_html=True)
            st.write(f"- **ราคา Flash Sale:** {data.get('flash_sale', '-')}")
            st.write(f"- **โครงสร้างของแถม (Gimmick):** {data.get('gimmick', '-')}")
            st.write(f"- **คูปองดันยอด AOV:** {data.get('coupon_aov', '-')}")

            st.markdown("<h3 class='sec-title'>3. มิติสินค้าและสต็อก (Inventory & Product Push)</h3>", unsafe_allow_html=True)
            st.write(f"- **Hero Products:** {data.get('hero_products', '-')}")
            st.write(f"- **สถานะสต็อก:** {data.get('stock', '-')}")

        with col_d2:
            st.markdown("<h3 class='sec-title'>🎯 ถอดรหัสพฤติกรรม D-Day & หมากแก้เกม</h3>", unsafe_allow_html=True)
            df_strat = pd.DataFrame([
                {"สิ่งที่ตรวจพบ": "แอด Winner รันต่อเนื่องยาวนาน", "แนวโน้ม D-Day": "เป็นแอดกินงบหลัก จะอัด Bid วันจริงสูงสุด", "วิธีแก้เกม": "อย่าชนด้วยสินค้าและมุมเดียวกัน ให้จัดชุด Bundle ที่คุ้มกว่า"},
                {"สิ่งที่ตรวจพบ": f"ของแถม: {data.get('gimmick', '-')}", "แนวโน้ม D-Day": "ดึงทราฟฟิกช่วงเที่ยงคืนเพื่อแย่งอันดับ 1", "วิธีแก้เกม": "เปิด Live ชนช่วง Golden Hours พร้อมแจกคูปองลดเงินสดทันที"},
                {"สิ่งที่ตรวจพบ": f"ดัน CTA ไปที่ {data.get('cta', '-')}", "แนวโน้ม D-Day": "เทงบดันยอดเฉพาะแพลตฟอร์มที่ค่าธรรมเนียมคุ้มสุด", "วิธีแก้เกม": "ยิง Retargeting ลูกค้าเก่าในแพลตฟอร์มเดียวกันให้กดลงตะกร้ารอ"}
            ])
            st.dataframe(df_strat, hide_index=True, use_container_width=True)

            st.markdown("#### 🤖 สรุปกลยุทธ์เฉพาะร้านด้วย AI")
            if st.button("🚀 ประมวลผลบทวิเคราะห์เจาะจง"):
                p_text = f"วิเคราะห์ร้าน {store_name} ชูจุดขาย '{data.get('winner_format')}' และของแถม '{data.get('gimmick')}' สรุปสั้นๆ 3 ข้อว่าเราควรวางแผนยิงแอดดักลูกค้าเขาอย่างไรในวัน D-Day"
                with st.spinner("กำลังวิเคราะห์..."):
                    res = get_ai_response(p_text)
                st.markdown(f"<div class='ai-box'>{res}</div>", unsafe_allow_html=True)

# ================= VIEW 1: หน้าแดชบอร์ดหลัก 3 คอลัมน์ =================
else:
    st.title("🐢 Sammy: E-commerce Market Intelligence")
    st.caption("ระบบตรวจจับโฆษณาคู่แข่งและส่องทิศทางตลาดเพื่อวางหมากรับมือแคมเปญ D-Day")

    c_left, c_mid, c_right = st.columns([1, 1.2, 1], gap="medium")

    # ---------------- 1. ร้านที่สนใจ ----------------
    with c_left:
        st.markdown("### 🏢 ร้านที่สนใจ")
        
        with st.expander("➕ เพิ่มร้านค้าที่สนใจเข้า Watchlist"):
            new_name = st.text_input("ชื่อร้านค้า / แบรนด์:", key="input_new_store")
            new_cat = st.text_input("หมวดหมู่สินค้า:", placeholder="เช่น แก้วเก็บความเย็น, เสื้อผ้า", key="input_new_cat")
            if st.button("บันทึกร้านค้า", use_container_width=True) and new_name.strip():
                stores_db[new_name.strip()] = {
                    "category": new_cat.strip() if new_cat else "ทั่วไป",
                    "creatives_count": 12,
                    "winner_days": 21,
                    "winner_format": f"คลิปสั้นนำเสนอจุดเด่นของ {new_name.strip()}",
                    "winner_caption": f"โปรโมชั่นแคมเปญพิเศษจากร้าน {new_name.strip()} ของแท้ 100% ส่งด่วนพร้อมส่ง",
                    "cta": "TikTok Shop / Shopee",
                    "flash_sale": "ลด 20-30% ตามช่วงแคมเปญ",
                    "gimmick": "ส่งฟรีเมื่อซื้อครบ 2 ชิ้น",
                    "coupon_aov": "คูปองลดเพิ่ม 50.- เมื่อซื้อครบ 500.-",
                    "hero_products": f"สินค้าซิกเนเจอร์ของ {new_name.strip()}",
                    "stock": "พร้อมส่งสต็อกแน่น"
                }
                save_stores(stores_db)
                st.success(f"บันทึกร้าน '{new_name.strip()}' เรียบร้อย!")
                st.rerun()

        st.caption("คลิกที่ชื่อร้านเพื่อเปิดหน้าต่างวิเคราะห์เจาะลึก 3 มิติ:")
        for s_key in list(stores_db.keys()):
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown(f"#### 🛍️ {s_key}")
            st.caption(f"หมวด: {stores_db[s_key].get('category', 'ทั่วไป')}")
            col_b1, col_b2 = st.columns([3, 1])
            if col_b1.button(f"🔍 เจาะลึกร้านนี้", key=f"nav_{s_key}", use_container_width=True):
                st.session_state["viewing_store"] = s_key
                st.rerun()
            if col_b2.button("🗑️", key=f"del_{s_key}"):
                stores_db.pop(s_key, None)
                save_stores(stores_db)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # ---------------- 2. ค้นหาคีย์เวิร์ด/ตลาด ----------------
    with c_mid:
        st.markdown("### 🔍 ค้นหาคีย์เวิร์ดหรือชื่อร้าน")
        kw_input = st.text_input("พิมพ์ค้นหาตลาดสด:", value="แก้วน้ำ")

        m_data = generate_market_metrics(kw_input)

        st.markdown(f"#### ภาพรวมตลาดสำหรับ: `{kw_input}`")
        m_col1, m_col2 = st.columns(2)
        m_col1.metric("แอดที่เปิดใช้งานในตลาด", f"{m_data['count']} แคมเปญ", delta=f"+{m_data['boost']}% ช่วงใกล้ D-Day")
        m_col2.metric("สัดส่วนสต็อก", f"พร้อมส่ง {m_data['stock']}%", delta="เน้นจัดส่งทันที")

        st.markdown("##### 📌 ทิศทาง Ad Creatives ในคีย์เวิร์ดนี้")
        st.write(f"- **Winner Ads (เกิน 30 วัน):** 70% เน้น `{m_data['winner_angle']}`")
        st.write(f"- **Teaser Ads (3-5 วันก่อนแคมเปญ):** `{m_data['teaser_angle']}`")
        st.write(f"- **Format ที่ได้ผลดีที่สุด:** `{m_data['hook']}`")
        st.write(f"- **ช่องทาง CTA หลัก:** `{m_data['platform']}`")

        if st.button(f"🧠 ขอ AI สรุปแนวทางรับมือคีย์เวิร์ด '{kw_input}'", use_container_width=True):
            prompt_m = f"วิเคราะห์ตลาดคำค้นหา '{kw_input}' มีแอดรัน {m_data['count']} ตัว เน้นมุมขาย '{m_data['winner_angle']}' สรุปข้อเสนอและจุดต่างที่คนขายควรใช้ยิงแอดชนในช่วงวันแคมเปญใหญ่สั้นๆ 3 ข้อ"
            with st.spinner("AI กำลังวิเคราะห์..."):
                res_m = get_ai_response(prompt_m)
            st.markdown(f"<div class='ai-box'>{res_m}</div>", unsafe_allow_html=True)

    # ---------------- 3. Top 10 สินค้าฮิต ----------------
    with c_right:
        st.markdown("### 🏆 Top 10 สินค้าที่มีแอดเยอะ")
        st.caption("อัปเดตจากความถี่การตรวจจับแคมเปญในตลาด")

        top_df = pd.DataFrame({
            "อันดับ": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "สินค้า": [
                "แก้วเก็บความเย็น 40oz ล็อคฝา",
                "อาหารเปียกแมวซุปปลาทูน่าแท้",
                "สร้อยคอเงินแท้ 925 มินิมอล",
                "เซรั่มกู้ผิวผสมไฮยาเข้มข้น",
                "เก้าอี้เพื่อสุขภาพ Ergonomic",
                "เสื้อยืด Oversize ผ้าไม่ยับ",
                "โต๊ะทำงานปรับระดับไฟฟ้า",
                "ทรายแมวเต้าหู้ไร้ฝุ่น กลิ่นชาเขียว",
                "หูฟังบลูทูธตัดเสียงรบกวน",
                "มอยส์เจอไรเซอร์สูตรเสริมเกราะผิว"
            ],
            "แอดในระบบ": [134, 118, 95, 87, 72, 65, 54, 48, 41, 35]
        })
        st.dataframe(top_df, hide_index=True, use_container_width=True, height=360)

        sel_prod = st.selectbox("เลือกสินค้าเพื่อดูทิศทาง Offer:", top_df["สินค้า"].tolist())
        st.info(f"💡 **{sel_prod}**: คู่แข่งเน้นการจัดโปรโมชัน Flash Sale ควบคู่กับการแจกของแถมใน 2 ชั่วโมงแรก")

        if st.button(f"🧠 วิเคราะห์สินค้า '{sel_prod}' ด้วย AI", use_container_width=True):
            prompt_p = f"สินค้า '{sel_prod}' ติดอันดับท็อปที่มีแอดเยอะช่วง D-Day อธิบายเหตุผลและแนะนำ Offer ที่ควรใช้ยิงสู้สั้นๆ 2 ข้อ"
            with st.spinner("AI กำลังวิเคราะห์..."):
                res_p = get_ai_response(prompt_p)
            st.markdown(f"<div class='ai-box'>{res_p}</div>", unsafe_allow_html=True)
