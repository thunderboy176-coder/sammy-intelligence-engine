import streamlit as st
import pandas as pd
import re
from datetime import datetime
import google.generativeai as genai
import os

# ตั้งค่าหน้าจอ
st.set_page_config(
    page_title="Sammy - E-commerce Intelligence Engine",
    layout="wide",
    page_icon="🐢"
)

# ดึง Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

# สไตล์ UI
st.markdown("""
<style>
    .winning-card {
        background-color: #064e3b;
        border: 1px solid #10b981;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 12px;
    }
    .testing-card {
        background-color: #451a03;
        border: 1px solid #f97316;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# SESSION STATE INITIALIZATION
# -------------------------------------------------------------
if "watchlist" not in st.session_state:
    st.session_state["watchlist"] = [
        {"name": "Bewell", "category": "เก้าอี้เพื่อสุขภาพ / Ergonomic"},
        {"name": "Ergotrend", "category": "เฟอร์นิเจอร์สำนักงาน"},
        {"name": "Dr.PONG", "category": "สกินแคร์ / เวชสำอาง"},
        {"name": "YVIS", "category": "เครื่องประดับแฟชั่น"}
    ]

if "analyzed_ads" not in st.session_state:
    st.session_state["analyzed_ads"] = [
        {
            "id": "AD-9921",
            "brand": "Bewell",
            "caption": "ปวดหลังจากการทำงานนานเกินไปใช่ไหม? เก้าอี้เพื่อสุขภาพ Bewell รุ่น Ergonomic Pro ออกแบบตามหลักสรีรศาสตร์ รับประกัน 3 ปีเต็ม ส่งฟรี ผ่อน 0% นาน 10 เดือน #Bewell #แก้ปวดหลัง #ออฟฟิศซินโดรม",
            "start_date": "2025-11-10",
            "lifespan": 120,
            "type": "Winning Ad",
            "angle": "เน้นแก้ Pain Point (ปวดหลัง) + ผ่อน 0%"
        },
        {
            "id": "AD-9922",
            "brand": "Dr.PONG",
            "caption": "สูตรคุณหมอ 28 วันผิวดีขึ้นจริง! Dr.PONG Barrier X Serum กู้ผิวแพ้ง่าย รีวิวแน่น 5,000 รีวิว #DrPONG #เซรั่มกู้ผิว #รักษาสิว",
            "start_date": "2025-10-01",
            "lifespan": 160,
            "type": "Winning Ad",
            "angle": "เน้นรีวิวแน่น + สูตรแพทย์ผู้เชี่ยวชาญ"
        }
    ]

# ฟังก์ชันวิเคราะห์ด้วย Gemini AI
def analyze_with_sammy(caption, mode):
    if not GEMINI_API_KEY:
        return "⚠️ กรุณาตั้งค่า GEMINI_API_KEY ใน Streamlit Secrets ก่อนใช้งาน"
    
    prompt = f"""
    คุณคือ Sammy - E-commerce Competitive Intelligence & Counter-Strategy Engine 
    วิเคราะห์ข้อความโฆษณาคู่แข่งนี้:
    "{caption}"
    
    โหมดการทำงาน: {mode}
    
    โปรดให้ผลลัพธ์เป็น Action ชัดเจนในรูปแบบ Markdown:
    1. 🎯 วิเคราะห์มุมขายหลัก (Angle & Offer): เขากำลังเล่นโปรโมชันหรือจุดขายอะไร
    2. ⚠️ เจาะจุดตาย (Vulnerability Analysis): ช่องโหว่ที่ทำให้ลูกค้าลังเล
    3. 🥊 หมากแก้ทาง (Counter-Strategy Offer): ข้อเสนอของเราที่จะชนะขาด
    4. ✍️ Copywriting พร้อมยิงแอด: เขียน Hook + Body + CTA สำหรับใช้สู้
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

# -------------------------------------------------------------
# UI LAYOUT
# -------------------------------------------------------------
st.title("🐢 Sammy: E-commerce Competitive Intelligence & Counter-Strategy Engine")
st.caption("ระบบติดตามคู่แข่งอัตโนมัติ สกัด Winning Ads และวางหมากแก้ทางเชิงรุก")

tabs = st.tabs([
    "⭐ 1. Watchlist ติดตามคู่แข่ง (10-20 ร้านค้า)", 
    "📥 2. นำเข้าและคัดแยกแอด (Winning vs Testing)", 
    "🔍 3. สำรวจตลาดและคีย์เวิร์ด (Market Discovery)", 
    "🧠 4. สมองกลวางหมากแก้ทาง (Counter-Strategy)"
])

# ================= TAB 1: WATCHLIST =================
with tabs[0]:
    st.subheader("ระบบ Watchlist ติดตามคู่แข่งอัตโนมัติ")
    st.write("บันทึกรายชื่อเพจหรือแบรนด์คู่แข่ง 10–20 ร้านค้าลงฐานข้อมูลถาวร พร้อมลิงก์ส่องแอดสดแบบคลิกเดียว")
    
    with st.form("add_watchlist_form"):
        col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
        new_brand = col_f1.text_input("ชื่อแบรนด์/ร้านค้าคู่แข่ง:")
        new_cat = col_f2.text_input("หมวดหมู่สินค้า:")
        submitted = col_f3.form_submit_button("➕ บันทึกเข้าระบบ", use_container_width=True)
        
        if submitted and new_brand.strip():
            # ตรวจสอบรูปแบบข้อมูลใน Watchlist ให้เป็น Dictionary เสมอ
            clean_name = new_brand.strip()
            clean_cat = new_cat.strip() if new_cat else "ทั่วไป"
            
            exists = any(
                (item["name"].lower() if isinstance(item, dict) else str(item).lower()) == clean_name.lower() 
                for item in st.session_state["watchlist"]
            )
            
            if not exists:
                st.session_state["watchlist"].append({"name": clean_name, "category": clean_cat})
                st.success(f"บันทึก '{clean_name}' ลงฐานข้อมูลเรียบร้อย!")
                st.rerun()
            else:
                st.warning("มีชื่อแบรนด์นี้อยู่ในระบบแล้ว")

    st.write("---")
    st.markdown("### รายชื่อแบรนด์ใน Watchlist ปัจจุบัน:")
    
    # วนลูปตรวจสอบประเภทข้อมูล ป้องกัน KeyError / TypeError 100%
    for idx, store_item in enumerate(st.session_state["watchlist"]):
        # ถ้าข้อมูลในลิสต์เก่าเป็น String ธรรมดา ให้แปลงเป็น Dict ชั่วคราวหน้างาน
        if isinstance(store_item, str):
            store_item = {"name": store_item, "category": "ทั่วไป"}
            st.session_state["watchlist"][idx] = store_item

        c_w1, c_w2, c_w3 = st.columns([2, 2, 1])
        c_w1.markdown(f"🏢 **{store_item.get('name', 'ไม่ระบุ')}**")
        c_w2.text(f"หมวด: {store_item.get('category', 'ทั่วไป')}")
        
        meta_direct_link = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=TH&q={store_item.get('name', '')}&search_type=keyword_unordered&media_type=all"
        
        btn_col1, btn_col2 = c_w3.columns(2)
        btn_col1.link_button("🔗 ส่องแอด", meta_direct_link)
        if btn_col2.button("🗑️", key=f"del_w_{idx}"):
            st.session_state["watchlist"].pop(idx)
            st.rerun()

# ================= TAB 2: นำเข้าและคัดแยกแอด =================
with tabs[1]:
    st.subheader("ระบบคัดแยก Winning Ads vs Testing Ads อัตโนมัติ")
    st.write("เมื่อคุณไปส่องแอดจาก Meta Ad Library นำข้อมูลมาวางที่นี่ ระบบจะคำนวณอายุแอดและคัดแยกให้ทันที")
    
    with st.form("ingest_ad_form"):
        brand_options = [item["name"] if isinstance(item, dict) else str(item) for item in st.session_state["watchlist"]]
        i_brand = st.selectbox("เลือกแบรนด์ใน Watchlist หรือพิมพ์เพิ่ม:", brand_options if brand_options else ["ทั่วไป"])
        i_caption = st.text_area("ก๊อปปี้แคปชันโฆษณาจาก Meta Ad Library มาวางที่นี่:", height=120)
        
        col_d1, col_d2 = st.columns(2)
        i_start_date = col_d1.date_input("วันที่เริ่มต้นยิงแอด (ดูจากหน้า Meta Library):", value=datetime.now())
        
        submitted_ad = st.form_submit_button("🚀 วิเคราะห์และบันทึกแอดเข้าคลัง", type="primary")
        
        if submitted_ad and i_caption.strip():
            now_date = datetime.now().date()
            lifespan_days = (now_date - i_start_date).days
            if lifespan_days < 0: lifespan_days = 0
            
            ad_type = "Winning Ad" if lifespan_days >= 14 else "Testing Ad"
            
            new_ad_entry = {
                "id": f"AD-{int(datetime.now().timestamp())}",
                "brand": i_brand,
                "caption": i_caption,
                "start_date": str(i_start_date),
                "lifespan": lifespan_days,
                "type": ad_type,
                "angle": "วิเคราะห์โดย Sammy AI"
            }
            
            st.session_state["analyzed_ads"].insert(0, new_ad_entry)
            st.success(f"บันทึกสำเร็จ! คัดแยกสถานะเป็น: **{ad_type}** (รันมาแล้ว {lifespan_days} วัน)")

    st.write("---")
    st.markdown("### 📋 คลังข้อมูลโฆษณาที่ผ่านการคัดแยกแล้ว:")
    
    ads_list = st.session_state["analyzed_ads"]
    for ad in ads_list:
        with st.container(border=True):
            col_a1, col_a2, col_a3 = st.columns([2, 1, 1])
            col_a1.markdown(f"**แบรนด์:** `{ad['brand']}`")
            if ad["type"] == "Winning Ad":
                col_a2.markdown(f"<span style='color:#34d399; font-weight:bold;'>🔥 WINNING AD ({ad['lifespan']} วัน)</span>", unsafe_allow_html=True)
            else:
                col_a2.markdown(f"<span style='color:#fb923c; font-weight:bold;'>🧪 TESTING AD ({ad['lifespan']} วัน)</span>", unsafe_allow_html=True)
            col_a3.write(f"📅 เริ่ม: {ad['start_date']}")
            
            st.text_area("ข้อความโฆษณา:", ad["caption"], height=80, key=f"view_cap_{ad['id']}")
            
            if st.button(f"🧠 ส่งแอดนี้ไปให้ Sammy วางหมากแก้ทาง", key=f"send_strat_{ad['id']}"):
                st.session_state["target_caption_to_solve"] = ad["caption"]
                st.success("ส่งข้อมูลเรียบร้อย! กรุณาสลับไปที่แท็บ '4. สมองกลวางหมากแก้ทาง'")

# ================= TAB 3: สำรวจตลาดและคีย์เวิร์ด =================
with tabs[2]:
    st.subheader("ระบบสำรวจตลาดและคีย์เวิร์ดสด (Market & Keyword Discovery)")
    st.write("วิเคราะห์แฮชแท็ก มุมมองการขาย (Angle) และภาพรวมแคมเปญที่กำลังแข่งขันในตลาด")
    
    market_keyword = st.text_input("ระบุหมวดหมู่สินค้าหรือคีย์เวิร์ดที่ต้องการสกัดภาพรวมตลาด:", placeholder="เช่น เก้าอี้เพื่อสุขภาพ, เซรั่มลดสิว")
    
    if st.button("📊 สกัดข้อมูลภาพรวมตลาด"):
        if market_keyword.strip():
            st.info(f"ผลการวิเคราะห์ภาพรวมตลาดสำหรับคีย์เวิร์ด: **{market_keyword}**")
            
            all_captions = " ".join([a["caption"] for a in st.session_state["analyzed_ads"]])
            hashtags = re.findall(r"#\w+", all_captions)
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.metric("จำนวนแคมเปญที่ตรวจพบในคลัง", f"{len(st.session_state['analyzed_ads'])} แคมเปญ")
                st.markdown("#### Top Viral Hashtags ในตลาด")
                if hashtags:
                    df_h = pd.Series(hashtags).value_counts().reset_index()
                    df_h.columns = ["Hashtag", "ความถี่"]
                    st.dataframe(df_h, use_container_width=True)
                else:
                    st.write("ยังไม่มีข้อมูลแฮชแท็กเพียงพอในระบบ")
            
            with col_m2:
                st.markdown("#### มุมมองการขายหลัก (Angles & Offers)")
                st.success("1. เน้นแก้ Pain Point เฉพาะจุด (เช่น ปวดหลัง, หน้าพัง)\n2. โปรโมชั่นผ่อน 0% และส่งฟรี\n3. การันตีคืนเงิน/รับประกันยาวนาน")
        else:
            st.warning("กรุณากรอกคีย์เวิร์ดสินค้าก่อนสกัดข้อมูล")

# ================= TAB 4: สมองกลวางหมากแก้ทาง =================
with tabs[3]:
    st.subheader("ระบบสมองกลวางหมากแก้ทางเชิงรุก (Counter-Strategy Engine)")
    st.write("แปลง Winning Ad ของคู่แข่งให้เป็นกลยุทธ์และสคริปต์โฆษณาพร้อมยิงสู้")
    
    preset_solve = st.session_state.get("target_caption_to_solve", "")
    solve_input = st.text_area("ข้อความ Winning Ad ของคู่แข่งที่ต้องการแก้ทาง:", value=preset_solve, height=150)
    
    strategy_mode = st.selectbox("เลือกรูปแบบการแก้ทาง:", [
        "เจาะจุดอ่อนเรื่องราคาและเงื่อนไข (Value Counter-Attack)",
        "แคมเปญ Double Day / Mega Sale ดักลูกค้าช่วงโปรโมชัน",
        "แคมเปญชูจุดเด่นเรื่องบริการหลังการขายและการรับประกัน",
        "แคมเปญทักปัญหาจี้ใจดำ (Problem-Solver Hook)"
    ])
    
    if st.button("🔥 เริ่มวางหมากแก้ทางเชิงรุกทันที", type="primary"):
        if not solve_input.strip():
            st.warning("กรุณากรอกข้อความแอดคู่แข่งก่อนครับ")
        else:
            with st.spinner("Sammy กำลังวิเคราะห์จุดตายและสร้างหมากแก้ทาง..."):
                final_output = analyze_with_sammy(solve_input, strategy_mode)
                st.markdown(final_output)
