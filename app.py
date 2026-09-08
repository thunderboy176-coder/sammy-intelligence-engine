import streamlit as st
import pandas as pd
import re
from datetime import datetime
import google.generativeai as genai
import os

# ตั้งค่าหน้าจอ
st.set_page_config(
    page_title="Sammy - E-commerce Competitive Intelligence Engine",
    layout="wide",
    page_icon="🐢"
)

# ดึง Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

# สไตล์ UI โทนเข้มพรีเมียม
st.markdown("""
<style>
    .winning-card {
        background: linear-gradient(135deg, #064e3b 0%, #022c22 100%);
        border: 1px solid #10b981;
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);
    }
    .testing-card {
        background: linear-gradient(135deg, #451a03 0%, #1c0a00 100%);
        border: 1px solid #f97316;
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(249, 115, 22, 0.1);
    }
    .metric-container {
        background-color: #0b1626;
        border: 1px solid #1e293b;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. INITIALIZE DATABASE (Watchlist 10-20 ร้านค้า & Ad Database)
# -------------------------------------------------------------
if "watchlist_stores" not in st.session_state:
    st.session_state["watchlist_stores"] = [
        {"id": 1, "name": "Bewell", "category": "เก้าอี้เพื่อสุขภาพ / Ergonomic", "platform": "Meta / IG"},
        {"id": 2, "name": "Ergotrend", "category": "เฟอร์นิเจอร์สำนักงาน", "platform": "Meta / IG"},
        {"id": 3, "name": "Dr.PONG", "category": "สกินแคร์ / เวชสำอาง", "platform": "Meta / TikTok"},
        {"id": 4, "name": "YVIS", "category": "เครื่องประดับแฟชั่น", "platform": "Meta / IG"},
        {"id": 5, "name": "Royal Canin Thailand", "category": "อาหารสัตว์เลี้ยง", "platform": "Meta"}
    ]

if "master_ads_db" not in st.session_state:
    st.session_state["master_ads_db"] = [
        {
            "id": "AD-881",
            "brand": "Bewell",
            "keyword": "เก้าอี้เพื่อสุขภาพ",
            "caption": "ปวดหลังจากการทำงานนานเกินไปใช่ไหม? เก้าอี้เพื่อสุขภาพ Bewell รุ่น Ergonomic Pro ออกแบบตามหลักสรีรศาสตร์ รองรับกระดูกสันหลังส่วนเอว รับประกัน 3 ปีเต็ม ส่งฟรีทั่วไทย ผ่อน 0% นาน 10 เดือน #Bewell #แก้ปวดหลัง #ออฟฟิศซินโดรม #เก้าอี้เพื่อสุขภาพ",
            "media_type": "วิดีโอ (Video)",
            "start_date": "2025-11-10",
            "lifespan": 120,
            "type": "Winning Ad",
            "landing_url": "https://www.bewellthailand.com"
        },
        {
            "id": "AD-882",
            "brand": "Dr.PONG",
            "keyword": "เซรั่มลดสิว",
            "caption": "สูตรคุณหมอ 28 วันผิวดีขึ้นจริง! Dr.PONG Barrier X Serum กู้ผิวแพ้ง่าย เสริมเกราะป้องกันผิวแข็งแรง รีวิวแน่น 5,000 รีวิว #DrPONG #เซรั่มกู้ผิว #รักษาสิว #ผิวแพ้ง่าย",
            "media_type": "รูปภาพ (Image)",
            "start_date": "2025-10-01",
            "lifespan": 160,
            "type": "Winning Ad",
            "landing_url": "https://www.drpong.in.th"
        },
        {
            "id": "AD-883",
            "brand": "YVIS",
            "keyword": "เครื่องประดับ",
            "caption": "สร้อยคอเงินแท้ 925 โดนน้ำไม่ลอก ไม่ดำ ใส่ติดตัวได้ตลอด 24 ชม. ราคาหลักร้อยแต่ดูแพงมาก #YVIS #สร้อยคอ #เครื่องประดับ",
            "media_type": "วิดีโอ (Video)",
            "start_date": "2026-05-01",
            "lifespan": 5,
            "type": "Testing Ad",
            "landing_url": "https://www.yvis.com"
        }
    ]

# สมองกล Gemini Counter-Strategy Engine
def generate_counter_strategy(caption, angle_mode):
    if not GEMINI_API_KEY:
        return "⚠️ กรุณาตั้งค่า GEMINI_API_KEY ใน Streamlit Secrets ก่อนใช้งานระบบวิเคราะห์"
    
    prompt = f"""
    คุณคือ Sammy - E-commerce Competitive Intelligence & Counter-Strategy Engine มืออาชีพ
    นี่คือข้อความ Winning Ad ของคู่แข่งที่กำลังทำเงินในตลาด:
    "{caption}"
    
    โหมดหมากแก้ทาง: {angle_mode}
    
    จงวิเคราะห์และสร้างกลยุทธ์สู้ศึกในรูปแบบ Markdown ที่เฉียบคม นำไปใช้ทำกำไรได้ทันที:
    1. 🎯 วิเคราะห์จุดตายคู่แข่ง (Vulnerability Analysis): จุดอ่อนที่ลูกค้ายังลังเล หรือช่องโหว่ของโปรโมชันเขา
    2. 🥊 หมากแก้ทางเด็ดขาด (Counter-Strategy Offer): ออกแบบ Bundle Deal หรือข้อเสนอที่เหนือกว่าโดยไม่ต้องลดราคาแข่ง
    3. ⚡ 3-Second Stop-Scroll Hooks (3 แบบ): สคริปต์เปิดคลิปสู้เพื่อดึงสายตาคนไถฟีด
    4. ✍️ Production-Ready Copywriting: แคปชันพร้อมยิงแอดฉบับสมบูรณ์ (Hook, Body, Offer, CTA)
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"เกิดข้อผิดพลาด: {e}"

# -------------------------------------------------------------
# UI DASHBOARD LAYOUT
# -------------------------------------------------------------
st.title("🐢 Sammy: Competitive Intelligence & Counter-Strategy Engine")
st.caption("ระบบสอดแนมโฆษณาคู่แข่งอัตโนมัติ | สกัด Winning Ads | วิเคราะห์ตลาด | วางหมากแก้ทาง")

tabs = st.tabs([
    "⭐ 1. Watchlist ติดตามคู่แข่ง",
    "📡 2. คลังวิเคราะห์แอด (Winning vs Testing)",
    "📊 3. สำรวจตลาดและคีย์เวิร์ด (Market Discovery)",
    "🧠 4. สมองกลวางหมากแก้ทาง (Counter-Strategy)"
])

# ================= TAB 1: WATCHLIST =================
with tabs[0]:
    st.subheader("ระบบ Watchlist ติดตามแบรนด์คู่แข่ง (10–20 ร้านค้า)")
    st.write("บันทึกรายชื่อร้านค้าเพื่อจัดระเบียบการสอดแนม พร้อมลิงก์ดึงข้อมูลเชิงลึก")
    
    with st.form("watchlist_form"):
        col_w1, col_w2, col_w3, col_w4 = st.columns([2, 2, 1, 1])
        store_name = col_w1.text_input("ชื่อแบรนด์/ร้านค้า:")
        store_cat = col_w2.text_input("หมวดหมู่สินค้า:")
        store_plat = col_w3.selectbox("แพลตฟอร์ม:", ["Meta / IG", "TikTok", "Omni-channel"])
        add_store_btn = col_w4.form_submit_button("➕ เพิ่มร้าน", use_container_width=True)
        
        if add_store_btn and store_name.strip():
            exists = any(s["name"].lower() == store_name.strip().lower() for s in st.session_state["watchlist_stores"])
            if not exists:
                st.session_state["watchlist_stores"].append({
                    "id": len(st.session_state["watchlist_stores"]) + 1,
                    "name": store_name.strip(),
                    "category": store_cat.strip() if store_cat else "ทั่วไป",
                    "platform": store_plat
                })
                st.success(f"เพิ่ม '{store_name.strip()}' เข้า Watchlist สำเร็จ!")
                st.rerun()
            else:
                st.warning("มีชื่อแบรนด์นี้อยู่ในระบบแล้ว")

    st.markdown("### 📋 รายชื่อร้านค้าใน Watchlist ทั้งหมด:")
    
    for idx, store in enumerate(st.session_state["watchlist_stores"]):
        c1, c2, c3, c4, c5 = st.columns([2, 2, 1, 1, 1])
        c1.markdown(f"🏢 **{store['name']}**")
        c2.text(f"หมวด: {store['category']}")
        c3.text(f"แพลตฟอร์ม: {store['platform']}")
        
        meta_url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=TH&q={store['name']}&search_type=keyword_unordered&media_type=all"
        c4.link_button("🔗 ส่องแอดสด", meta_url)
        
        if c5.button("🗑️ ลบ", key=f"del_store_{idx}"):
            st.session_state["watchlist_stores"].pop(idx)
            st.rerun()

# ================= TAB 2: คลังวิเคราะห์แอด (Winning vs Testing) =================
with tabs[1]:
    st.subheader("ระบบคำนวณ Ad Lifespan และคัดแยก Winning Ads อัตโนมัติ")
    st.write("บันทึกข้อมูลโฆษณาที่กวาดมาได้ ระบบจะคำนวณอายุแอดทันที: **Winning Ads (>14 วัน)** คือตัวทำเงินที่อัดงบเลี้ยงไว้ | **Testing Ads (<7 วัน)** คือแอดทดสอบตลาด")
    
    with st.expander("📥 เปิดฟอร์มนำเข้าโฆษณาคู่แข่งเข้าระบบกลาง", expanded=False):
        with st.form("ingest_ad_database"):
            selected_brand = st.selectbox("เลือกแบรนด์คู่แข่งจาก Watchlist:", [s["name"] for s in st.session_state["watchlist_stores"]])
            ad_keyword = st.text_input("คีย์เวิร์ดสินค้า (เช่น เก้าอี้เพื่อสุขภาพ, เซรั่มลดสิว):")
            ad_caption = st.text_area("ข้อความโฆษณา (Caption ดิบ):", height=120)
            
            col_in1, col_in2 = st.columns(2)
            ad_media = col_in1.selectbox("รูปแบบสื่อโฆษณา:", ["วิดีโอ (Video)", "รูปภาพ (Image)", "แคโรเซล (Carousel)"])
            ad_start_date = col_in2.date_input("วันที่เริ่มต้นยิงแอด (เช็คจาก Meta Ad Library):", value=datetime.now())
            
            save_ad_btn = st.form_submit_button("🚀 คำนวณอายุแอดและบันทึก", type="primary")
            
            if save_ad_btn and ad_caption.strip():
                now_date = datetime.now().date()
                lifespan_days = (now_date - ad_start_date).days
                if lifespan_days < 0: lifespan_days = 0
                
                ad_status = "Winning Ad" if lifespan_days >= 14 else "Testing Ad"
                
                new_entry = {
                    "id": f"AD-{int(datetime.now().timestamp())}",
                    "brand": selected_brand,
                    "keyword": ad_keyword.strip() if ad_keyword else "ทั่วไป",
                    "caption": ad_caption,
                    "media_type": ad_media,
                    "start_date": str(ad_start_date),
                    "lifespan": lifespan_days,
                    "type": ad_status,
                    "landing_url": "https://www.facebook.com/ads/library/"
                }
                
                st.session_state["master_ads_db"].insert(0, new_entry)
                st.success(f"บันทึกสำเร็จ! ระบบจัดหมวดหมู่ให้เป็น: **{ad_status}** (รันต่อเนื่องมาแล้ว {lifespan_days} วัน)")

    st.write("---")
    st.markdown("### 📊 คลังวิเคราะห์โฆษณา (Intelligence Master Grid):")
    
    filter_tab = st.radio("ตัวกรองแสดงผล:", ["ทั้งหมด", "🔥 เฉพาะ Winning Ads (ตัวทำเงิน)", "🧪 เฉพาะ Testing Ads (แอดใหม่)"], horizontal=True)
    
    filtered_ads = st.session_state["master_ads_db"]
    if filter_tab == "🔥 เฉพาะ Winning Ads (ตัวทำเงิน)":
        filtered_ads = [a for a in st.session_state["master_ads_db"] if a["type"] == "Winning Ad"]
    elif filter_tab == "🧪 เฉพาะ Testing Ads (แอดใหม่)":
        filtered_ads = [a for a in st.session_state["master_ads_db"] if a["type"] == "Testing Ad"]

    for ad in filtered_ads:
        card_style = "winning-card" if ad["type"] == "Winning Ad" else "testing-card"
        
        st.markdown(f"""
        <div class="{card_style}">
            <h4>🏢 แบรนด์: {ad['brand']} &nbsp;|&nbsp; หมวด: {ad['keyword']}</h4>
            <p><b>สถานะ:</b> {ad['type']} (อายุแอด: <b>{ad['lifespan']} วัน</b>) | <b>รูปแบบสื่อ:</b> {ad['media_type']} | <b>เริ่มยิง:</b> {ad['start_date']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.text_area("แคปชันโฆษณา:", ad["caption"], height=80, key=f"master_cap_{ad['id']}")
        
        b_c1, b_c2 = st.columns([1, 4])
        if b_c1.button("🧠 ส่งให้ Sammy วางหมากแก้ทาง", key=f"btn_solve_{ad['id']}"):
            st.session_state["target_caption_to_solve"] = ad["caption"]
            st.success("ส่งข้อมูลไปที่สมองกลเรียบร้อย! กดสลับไปที่แท็บ '4. สมองกลวางหมากแก้ทาง'")
        b_c2.write("")

# ================= TAB 3: สำรวจตลาดและคีย์เวิร์ด =================
with tabs[2]:
    st.subheader("ระบบสำรวจตลาดและคีย์เวิร์ดสด (Market & Keyword Discovery)")
    st.write("พิมพ์ค้นหาหมวดหมู่สินค้าเพื่อดูภาพรวมตลาด สกัด Top Viral Hashtags และเจาะมุมมองการขายของเจ้าตลาด")
    
    col_s1, col_s2 = st.columns([3, 1])
    search_market_kw = col_s1.text_input("พิมพ์คีย์เวิร์ดสินค้าที่ต้องการสำรวจ:", placeholder="เช่น เก้าอี้เพื่อสุขภาพ, เซรั่มลดสิว, อาหารแมว")
    search_market_btn = col_s2.button("🔍 วิเคราะห์ตลาดสด", use_container_width=True)
    
    if search_market_kw and search_market_btn:
        market_results = [
            a for a in st.session_state["master_ads_db"]
            if search_market_kw.lower() in a["keyword"].lower() or 
               search_market_kw.lower() in a["caption"].lower() or 
               search_market_kw.lower() in a["brand"].lower()
        ]
        
        st.info(f"ผลการวิเคราะห์ภาพรวมตลาดสำหรับคีย์เวิร์ด: **{search_market_kw}** (พบแคมเปญในฐานข้อมูล {len(market_results)} แคมเปญ)")
        
        if market_results:
            all_text = " ".join([a["caption"] for a in market_results])
            hashtags = re.findall(r"#\w+", all_text)
            
            res_c1, res_c2 = st.columns(2)
            with res_c1:
                st.metric("จำนวนแคมเปญที่กำลังแข่งขันในตลาดนี้", f"{len(market_results)} แคมเปญ")
                st.markdown("#### 🔥 Top Viral Hashtags ในหมวดนี้")
                if hashtags:
                    df_hashtags = pd.Series(hashtags).value_counts().reset_index()
                    df_hashtags.columns = ["Hashtag", "ความถี่ที่พบ"]
                    st.dataframe(df_hashtags, use_container_width=True)
                else:
                    st.write("ไม่พบแฮชแท็กในแคมเปญหมวดนี้")
            
            with res_c2:
                st.markdown("#### 🎯 มุมมองการขายหลัก (Angles & Offers ที่เจ้าตลาดเล่น)")
                st.success("1. **Pain Point Solution:** ชูจุดเด่นแก้ปัญหาเฉพาะจุดแบบเห็นผลชัดเจน\n2. **Financial Incentive:** ชูโปรโมชันผ่อน 0% หรือส่งฟรีเก็บเงินปลายทาง\n3. **Social Proof & Warranty:** เน้นรีวิวแน่นและรับประกันสินค้าหลักปี")
        else:
            st.warning(f"ยังไม่มีข้อมูลของ '{search_market_kw}' ในคลัง กรุณานำเข้าข้อมูลแอดหมวดนี้ในแท็บที่ 2 ก่อน เพื่อให้ระบบสกัดข้อมูลตลาดได้เต็มรูปแบบ")

# ================= TAB 4: สมองกลวางหมากแก้ทาง =================
with tabs[3]:
    st.subheader("ระบบสมองกลวางหมากแก้ทางเชิงรุก (Counter-Strategy Engine)")
    st.write("นำ Winning Ad ของคู่แข่งมาวิเคราะห์จุดตาย และสร้างข้อเสนอพร้อมสคริปต์สู้แบบเหนือชั้น")
    
    preset_text = st.session_state.get("target_caption_to_solve", "")
    input_ad_to_counter = st.text_area("ข้อความ Winning Ad ของคู่แข่งที่ต้องการล้ม:", value=preset_text, height=150)
    
    counter_mode = st.selectbox("เลือกกลยุทธ์แคมเปญแก้ทาง:", [
        "เจาะจุดอ่อนเรื่องราคาและเงื่อนไข (Value Counter-Attack)",
        "แคมเปญ Double Day / Mega Sale ดักลูกค้าช่วงโปรโมชันใหญ่",
        "แคมเปญชูจุดเด่นเรื่องบริการหลังการขายและการรับประกันเหนือกว่า",
        "แคมเปญทักปัญหาจี้ใจดำ (Problem-Solver Hook)"
    ])
    
    if st.button("🔥 ให้ Sammy เริ่มวางหมากแก้ทางเชิงรุก", type="primary"):
        if not input_ad_to_counter.strip():
            st.warning("กรุณากรอกข้อความแอดคู่แข่งก่อนครับ")
        else:
            with st.spinner("Sammy กำลังวิเคราะห์จุดตายและออกแบบหมากแก้ทาง..."):
                strategy_output = generate_counter_strategy(input_ad_to_counter, counter_mode)
                st.markdown(strategy_output)
