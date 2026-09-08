import streamlit as st
import pandas as pd
import re
from datetime import datetime
import os
import urllib.parse
import google.generativeai as genai
from apify_client import ApifyClient

# --- ตั้งค่าหน้าจอ ---
st.set_page_config(
    page_title="Sammy - E-commerce Competitive Intelligence Engine",
    layout="wide",
    page_icon="🐢"
)

# ดึง Key จาก Streamlit Secrets
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN") or st.secrets.get("APIFY_API_TOKEN", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel("gemini-1.5-flash")

apify_client = ApifyClient(APIFY_API_TOKEN) if APIFY_API_TOKEN else None

# สไตล์ UI
st.markdown("""
<style>
    .winning-card {
        background: linear-gradient(135deg, #064e3b 0%, #022c22 100%);
        border: 1px solid #10b981;
        padding: 18px;
        border-radius: 14px;
        margin-bottom: 12px;
    }
    .testing-card {
        background: linear-gradient(135deg, #451a03 0%, #1c0a00 100%);
        border: 1px solid #f97316;
        padding: 18px;
        border-radius: 14px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. FAST ENGINE: ดึงแอดสดอัตโนมัติความเร็วสูง (Direct API Gateway)
# -------------------------------------------------------------
def fetch_live_ads_gateway(search_query, max_results=15):
    """ส่งคำขอไปยัง Fast Scraper บน Apify ใช้เวลาเพียง 5-15 วินาที"""
    if not apify_client:
        st.error("⚠️ ไม่พบ APIFY_API_TOKEN กรุณาตั้งค่าใน Streamlit Secrets")
        return []

    # ลิงก์ปลายทาง Meta Ad Library TH
    encoded_query = urllib.parse.quote(search_query)
    target_meta_url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=TH&q={encoded_query}&search_type=keyword_unordered&media_type=all"

    # ใช้ Actor ที่ทำงานเร็วที่สุดและรองรับ URL ตรง
    # รันแบบจำกัดจำนวนผลลัพธ์เพื่อความรวดเร็ว ไม่ให้ค้างนาน
    run_input = {
        "startUrls": [{"url": target_meta_url}],
        "resultsLimit": max_results,
        "maxAds": max_results
    }

    try:
        # สั่งรัน Actor โดยใช้ตัวเลือกที่สกัดข้อมูลไวกว่า
        run = apify_client.actor("curious_coder/facebook-ads-library-scraper").call(
            run_input=run_input
        )
        
        # กรณี fallback หาก actor ตัวแรกมีปัญหา
        if not run:
            run = apify_client.actor("apify/facebook-ads-scraper").call(run_input=run_input)

        dataset_items = apify_client.dataset(run["defaultDatasetId"]).list_items().items
        
        extracted = []
        now = datetime.now()

        for item in dataset_items:
            # ดึงข้อความแคปชันจากโครงสร้างต่างๆ
            snapshot = item.get("snapshot", {})
            body_info = snapshot.get("body", {}) if isinstance(snapshot, dict) else {}
            
            caption = (
                item.get("caption") or 
                item.get("text") or 
                item.get("adCreativeBody") or 
                (body_info.get("text") if isinstance(body_info, dict) else "") or
                ""
            )
            
            start_date_raw = (
                item.get("startDate") or 
                item.get("adDeliveryStartDate") or 
                item.get("startedRunningDate") or 
                item.get("start_date") or ""
            )
            
            page_name = (
                item.get("pageName") or 
                item.get("advertiserName") or 
                item.get("page_name") or 
                search_query
            )
            
            ad_id = str(item.get("id") or item.get("adArchiveId") or item.get("ad_id") or int(datetime.now().timestamp()))
            
            # คำนวณอายุโฆษณา (Ad Lifespan)
            lifespan = 0
            clean_date = "กำลังรันสด"
            if start_date_raw:
                try:
                    # แปลงทั้งแบบ timestamp และ string ISO
                    if isinstance(start_date_raw, (int, float)):
                        ad_date = datetime.fromtimestamp(start_date_raw)
                        clean_date = ad_date.strftime("%Y-%m-%d")
                    else:
                        clean_date = str(start_date_raw).split("T")[0]
                        ad_date = datetime.strptime(clean_date, "%Y-%m-%d")
                    lifespan = (now - ad_date).days
                except Exception:
                    clean_date = "กำลังรันสด"

            if lifespan < 0:
                lifespan = 0

            is_winning = lifespan >= 14

            # สื่อโฆษณา
            media_url = item.get("displayUrl") or item.get("videoUrl") or item.get("imageUrl") or None
            link_url = item.get("linkUrl") or f"https://www.facebook.com/ads/library/?id={ad_id}"

            extracted.append({
                "ad_id": ad_id,
                "brand": page_name,
                "caption": caption if caption else "[โฆษณาประเภทรูปภาพ/วิดีโอ ไม่มีข้อความยาว]",
                "start_date": clean_date,
                "lifespan": lifespan,
                "type": "Winning Ad" if is_winning else "Testing Ad",
                "media_url": media_url,
                "link_url": link_url
            })

        # เรียงลำดับเอา Winning Ads (รันนานสุด) ขึ้นก่อน
        return sorted(extracted, key=lambda x: x["lifespan"], reverse=True)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
        return []

# สมองกล Gemini วางหมากแก้ทาง
def generate_sammy_counter_strategy(brand, caption, lifespan, strategy_mode):
    if not GEMINI_API_KEY:
        return "⚠️ กรุณาตั้งค่า GEMINI_API_KEY ใน Streamlit Secrets"
        
    prompt = f"""
    คุณคือ Sammy - E-commerce Competitive Intelligence & Counter-Strategy Engine
    วิเคราะห์โฆษณาของแบรนด์ '{brand}' (อายุแอด {lifespan} วัน):
    "{caption}"
    
    โหมดกลยุทธ์: {strategy_mode}
    
    ส่งมอบ Action Plan ที่นำไปใช้งานยิงแอดได้จริงทันทีในรูปแบบ Markdown:
    1. 🎯 ชี้จุดตายคู่แข่ง (Vulnerability Analysis): หาช่องโหว่ของโปรโมชันหรือข้อเสนอที่ทำให้ลูกค้ายังลังเล
    2. 🥊 Offer ชนะขาด (Counter-Strategy Offer): ข้อเสนอหรือ Bundle Deal ฝั่งเราที่ทำให้ลูกค้ารู้สึกคุ้มกว่าโดยไม่ต้องเล่นสงครามราคา
    3. ⚡ Hook 3 วินาทีแรก (3-Second Stop-Scroll Hooks): สคริปต์เปิดคลิปวิดีโอ 3 แบบสำหรับดักสายตาลูกค้า
    4. ✍️ แคปชันและแฮชแท็กพร้อมยิงแอด (Production-Ready Copywriting): ข้อความยิงแอดฉบับสมบูรณ์ (Hook, Body, Offer, CTA)
    """
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

# -------------------------------------------------------------
# 2. SESSION STATES
# -------------------------------------------------------------
if "watchlist_stores" not in st.session_state:
    st.session_state["watchlist_stores"] = [
        {"name": "Bewell", "category": "เก้าอี้เพื่อสุขภาพ"},
        {"name": "Ergotrend", "category": "เฟอร์นิเจอร์สำนักงาน"},
        {"name": "Dr.PONG", "category": "สกินแคร์ / เวชสำอาง"},
        {"name": "Royal Canin Thailand", "category": "อาหารแมว / สัตว์เลี้ยง"}
    ]

if "live_scanned_ads" not in st.session_state:
    st.session_state["live_scanned_ads"] = []

if "target_for_ai" not in st.session_state:
    st.session_state["target_for_ai"] = None

# -------------------------------------------------------------
# 3. UI DASHBOARD
# -------------------------------------------------------------
st.title("🐢 Sammy: Automated E-commerce Intelligence Engine")
st.caption("ระบบกวาดข้อมูลแอดสดอัตโนมัติ 100% ผ่าน Gateway | คัดแยก Winning Ads | เจาะตลาด | วางหมากแก้ทาง")

tabs = st.tabs([
    "🔍 1. สแกนแอดสดอัตโนมัติ (Live Spy)",
    "⭐ 2. Watchlist ติดตามคู่แข่ง (10-20 ร้าน)",
    "📊 3. สเกาท์ตลาดและคีย์เวิร์ด (Market Discovery)",
    "🧠 4. สมองกลวางหมากแก้ทาง (Counter-Strategy)"
])

# ================= TAB 1: สแกนแอดสดอัตโนมัติ =================
with tabs[0]:
    st.subheader("ดึงข้อมูลโฆษณาสดจาก Meta Ad Library อัตโนมัติ (Real-time Scraping)")
    st.write("พิมพ์ชื่อร้านค้า แบรนด์ หรือคีย์เวิร์ด ระบบจะส่ง Proxy Gateway ไปกวาดแอดสดมาลงตารางทันที")
    
    col1, col2 = st.columns([3, 1])
    query_input = col1.text_input("พิมพ์ชื่อร้านค้าหรือคีย์เวิร์ดที่ต้องการสอดแนม:", placeholder="เช่น อาหารแมว, Bewell, YVIS")
    run_btn = col2.button("🚀 สแกนหา Winning Ads เดี๋ยวนี้", use_container_width=True)

    if query_input and run_btn:
        with st.spinner(f"⚡ กำลังส่ง Fast Gateway ไปดึงแอดสดของ '{query_input}' (ใช้เวลาประมาณ 10-15 วินาที)..."):
            ads_data = fetch_live_ads_gateway(query_input, max_results=15)
            st.session_state["live_scanned_ads"] = ads_data

    ads = st.session_state.get("live_scanned_ads", [])
    
    if ads:
        total = len(ads)
        winning = [a for a in ads if a["type"] == "Winning Ad"]
        testing = [a for a in ads if a["type"] == "Testing Ad"]

        m1, m2, m3 = st.columns(3)
        m1.metric("แอดสดที่กำลังรันทั้งหมด", f"{total} ตัว")
        m2.metric("🔥 Winning Ads (รันเกิน 14 วัน)", f"{len(winning)} ตัว", delta="แอดทำเงินอัดงบ")
        m3.metric("🧪 Testing Ads (แอดทดสอบใหม่)", f"{len(testing)} ตัว")

        st.write("---")
        
        filter_opt = st.radio("ตัวกรองแอด:", ["ทั้งหมด", "เฉพาะ Winning Ads (รันนาน)", "เฉพาะ Testing Ads (แอดใหม่)"], horizontal=True)
        display_list = ads
        if filter_opt == "เฉพาะ Winning Ads (รันนาน)":
            display_list = winning
        elif filter_opt == "เฉพาะ Testing Ads (แอดใหม่)":
            display_list = testing

        for ad in display_list:
            card_class = "winning-card" if ad["type"] == "Winning Ad" else "testing-card"
            
            st.markdown(f"""
            <div class="{card_class}">
                <h4>🏢 แบรนด์: {ad['brand']}</h4>
                <p><b>สถานะ:</b> {ad['type']} (อายุแอด: <b>{ad['lifespan']} วัน</b>) &nbsp;|&nbsp; <b>เริ่มยิงเมื่อ:</b> {ad['start_date']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            t_col, m_col = st.columns([3, 1])
            t_col.text_area("ข้อความโฆษณา (Caption):", ad["caption"], height=100, key=f"ad_cap_{ad['ad_id']}")
            
            if ad["media_url"]:
                m_col.image(ad["media_url"], use_container_width=True)
            else:
                m_col.write("*(ไม่มีภาพพรีวิว)*")

            b1, b2 = st.columns([1, 4])
            if b1.button("🧠 วางหมากแก้ทางแอดนี้", key=f"ai_btn_{ad['ad_id']}"):
                st.session_state["target_for_ai"] = ad
                st.success("ส่งข้อมูลเข้าสมองกลเรียบร้อย! สลับไปที่แท็บ '4. สมองกลวางหมากแก้ทาง' ได้เลย")
            b2.link_button("🔗 ลิงก์ปลายทางโฆษณา", ad["link_url"])

    elif query_input and not ads and run_btn:
        st.warning("ไม่พบโฆษณาที่กำลังรันอยู่ หรือคำค้นหาไม่ตรงกับแคมเปญที่เปิดใช้งาน")

# ================= TAB 2: WATCHLIST =================
with tabs[1]:
    st.subheader("ระบบ Watchlist ติดตามคู่แข่งอัตโนมัติ (10–20 ร้านค้า)")
    
    with st.form("add_watch_form"):
        w_c1, w_c2, w_c3 = st.columns([2, 2, 1])
        new_brand = w_c1.text_input("ชื่อแบรนด์คู่แข่ง:")
        new_cat = w_c2.text_input("หมวดหมู่สินค้า:")
        w_submit = w_c3.form_submit_button("➕ ปักหมุดร้าน", use_container_width=True)
        
        if w_submit and new_brand.strip():
            exists = any(s["name"].lower() == new_brand.strip().lower() for s in st.session_state["watchlist_stores"])
            if not exists:
                st.session_state["watchlist_stores"].append({"name": new_brand.strip(), "category": new_cat.strip() if new_cat else "ทั่วไป"})
                st.success(f"บันทึก '{new_brand}' เข้า Watchlist สำเร็จ!")
                st.rerun()

    st.write("---")
    for idx, store in enumerate(st.session_state["watchlist_stores"]):
        c_name, c_cat, c_scan, c_del = st.columns([2, 2, 1, 1])
        c_name.markdown(f"🏢 **{store['name']}**")
        c_cat.text(f"หมวด: {store['category']}")
        
        if c_scan.button("⚡ สแกนแอดสด", key=f"scan_w_{idx}"):
            with st.spinner(f"กำลังส่ง Fast Gateway กวาดแอดสดของ {store['name']}..."):
                st.session_state["live_scanned_ads"] = fetch_live_ads_gateway(store['name'], max_results=15)
                st.info(f"สแกน {store['name']} เสร็จแล้ว! สลับไปที่แท็บ '1. สแกนแอดสดอัตโนมัติ' เพื่อดูผลลัพธ์")
                
        if c_del.button("🗑️", key=f"del_w_{idx}"):
            st.session_state["watchlist_stores"].pop(idx)
            st.rerun()

# ================= TAB 3: สเกาท์ตลาดและคีย์เวิร์ด =================
with tabs[2]:
    st.subheader("ระบบสำรวจตลาดและคีย์เวิร์ดสด (Market & Trend Discovery)")
    
    if st.session_state["live_scanned_ads"]:
        ads_pool = st.session_state["live_scanned_ads"]
        all_text = " ".join([a["caption"] for a in ads_pool if a["caption"]])
        hashtags = re.findall(r"#\w+", all_text)
        
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.metric("จำนวนแคมเปญที่ตรวจพบ", f"{len(ads_pool)} แคมเปญ")
            st.markdown("#### 🔥 Top Viral Hashtags ที่ใช้ในตลาดขณะนี้")
            if hashtags:
                df_hash = pd.Series(hashtags).value_counts().reset_index()
                df_hash.columns = ["Hashtag", "ความถี่ที่พบ"]
                st.dataframe(df_hash.head(10), use_container_width=True)
            else:
                st.write("ไม่พบแฮชแท็กในชุดข้อมูลนี้")

        with col_res2:
            st.markdown("#### 🎯 มุมมองการขายหลัก (Angles & Offers ที่คู่แข่งใช้)")
            st.success("1. **Pain Point Focus:** ชี้ปัญหาเฉพาะจุดเพื่อสร้างความต้องการด่วน\n2. **Trust & Social Proof:** ชูรีวิว ความน่าเชื่อถือ หรือการรับประกัน\n3. **Frictionless Buying:** จัดโปรโมชันส่งฟรี หรือมีบริการเก็บเงินปลายทาง")
    else:
        st.info("กรุณาไปที่แท็บ '1. สแกนแอดสดอัตโนมัติ' แล้วกดสแกนสินค้าหรือร้านค้าอย่างน้อย 1 ครั้ง เพื่อให้ระบบดึงข้อมูลมาสเกาท์ตลาดครับ")

# ================= TAB 4: สมองกลวางหมากแก้ทาง =================
with tabs[3]:
    st.subheader("ระบบสมองกลวางหมากแก้ทางเชิงรุก (Practical Counter-Strategy)")
    
    target_ad = st.session_state.get("target_for_ai")
    
    default_brand = target_ad["brand"] if target_ad else "คู่แข่ง"
    default_caption = target_ad["caption"] if target_ad else ""
    default_lifespan = target_ad["lifespan"] if target_ad else 14

    ai_brand = st.text_input("แบรนด์คู่แข่ง:", value=default_brand)
    ai_caption = st.text_area("ข้อความโฆษณา Winning Ad ที่ต้องการแก้ทาง:", value=default_caption, height=130)
    
    strat_mode = st.selectbox("เลือกรูปแบบการแก้ทาง:", [
        "เจาะจุดอ่อนเรื่องราคาและเงื่อนไข (Value Counter-Attack)",
        "แคมเปญ Double Day / Mega Sale ดักลูกค้าช่วงโปรโมชัน",
        "แคมเปญชูจุดเด่นเรื่องบริการหลังการขายและการรับประกัน",
        "แคมเปญทักปัญหาจี้ใจดำ (Problem-Solver Hook)"
    ])
    
    if st.button("🔥 เริ่มวางหมากแก้ทางเชิงรุกทันที", type="primary"):
        if not ai_caption.strip():
            st.warning("กรุณากรอกหรือเลือกข้อความแอดคู่แข่งก่อนครับ")
        else:
            with st.spinner("Sammy กำลังวิเคราะห์จุดตาย ออกแบบ Offer และสร้างสคริปต์สู้..."):
                output = generate_sammy_counter_strategy(ai_brand, ai_caption, default_lifespan, strat_mode)
                st.markdown(output)
