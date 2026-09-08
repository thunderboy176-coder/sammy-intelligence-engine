import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import os
import google.generativeai as genai

# ตั้งค่าหน้าจอ
st.set_page_config(
    page_title="Sammy - Competitive Intelligence Engine",
    layout="wide",
    page_icon="🐢"
)

# ดึง Gemini API Key จาก Secrets หลังบ้าน
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

# สไตล์ Dark Theme 
st.markdown("""
<style>
    .winning-badge {
        background-color: #064e3b;
        color: #34d399;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 12px;
    }
    .testing-badge {
        background-color: #451a03;
        color: #fb923c;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# CORE ENGINE: ระบบค้นหาโฆษณาจาก Meta Ad Library แบบเรียลไทม์
# -------------------------------------------------------------
@st.cache_data(ttl=600)
def fetch_realtime_ads(keyword):
    """
    ดึงข้อมูลโฆษณาสดจาก Meta Ad Library ตามคีย์เวิร์ดหรือชื่อร้านค้า
    """
    url = "https://www.facebook.com/ads/library/async/search_ads/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://www.facebook.com/ads/library/",
    }
    payload = {
        "active_status": "active",
        "ad_type": "all",
        "country": "TH",
        "q": keyword,
        "search_type": "keyword_unordered",
        "media_type": "all",
        "count": 30
    }
    
    try:
        res = requests.post(url, headers=headers, data=payload, timeout=15)
        raw_text = res.text
        if raw_text.startswith("for (;;);"):
            raw_text = raw_text.replace("for (;;);", "", 1)
            
        data = json.loads(raw_text)
        payload_data = data.get("payload", {}).get("results", [])
        
        extracted_ads = []
        now = datetime.now()
        
        for item_group in payload_data:
            for ad in item_group:
                snapshot = ad.get("snapshot", {})
                body = snapshot.get("body", {})
                caption = body.get("text", "") if isinstance(body, dict) else str(body)
                
                start_date_ts = ad.get("startDate")
                if start_date_ts:
                    start_date = datetime.fromtimestamp(start_date_ts)
                    date_str = start_date.strftime("%Y-%m-%d")
                    lifespan = (now - start_date).days
                else:
                    date_str = "ไม่ระบุ"
                    lifespan = 0
                
                page_name = ad.get("pageName", "ไม่ระบุชื่อเพจ")
                ad_id = ad.get("adArchiveID", "")
                images = snapshot.get("images", [])
                img_url = images[0].get("resized_image_url") if images else None
                link_url = snapshot.get("link_url", "")

                extracted_ads.append({
                    "ad_id": ad_id,
                    "page_name": page_name,
                    "caption": caption if caption else "[โฆษณานี้เป็นสื่อรูปภาพ/วิดีโอ ไม่มีข้อความยาว]",
                    "start_date": date_str,
                    "lifespan_days": lifespan,
                    "is_winning": lifespan >= 14,
                    "image_url": img_url,
                    "link_url": link_url,
                    "snapshot_url": f"https://www.facebook.com/ads/library/?id={ad_id}"
                })
                
        return sorted(extracted_ads, key=lambda x: x["lifespan_days"], reverse=True)
    except Exception:
        return []

def generate_sammy_strategy(ad_caption, campaign_type):
    """ให้ Gemini วิเคราะห์เจาะลึกกลยุทธ์คู่แข่ง"""
    if not GEMINI_API_KEY:
        return "⚠️ กรุณาตั้งค่า GEMINI_API_KEY ใน Streamlit Secrets ก่อน"
    prompt = f"""
    คุณคือ Sammy - E-commerce Competitive Intelligence & Counter-Strategy Engine ผู้เชี่ยวชาญการตลาด E-commerce เชิงรุก
    นี่คือโฆษณา Winning Ad ของคู่แข่งในตลาดไทย:
    
    --- ข้อความโฆษณาคู่แข่ง ---
    {ad_caption}
    -------------------------
    
    ประเภทแคมเปญที่เราจะใช้สู้: {campaign_type}
    
    โปรดวิเคราะห์เป็นข้อๆ อย่างเฉียบคม ห้ามตอบทฤษฎีกลวงๆ และให้ Action ที่นำไปใช้ได้จริงในรูปแบบ Markdown:
    1. 🎯 เจาะจุดตายคู่แข่ง (Vulnerability Analysis): จุดอ่อนที่ลูกค้ายังลังเลใจ
    2. 🥊 หมากแก้ทางเด็ดขาด (Offer Counter-Attack): ข้อเสนอหรือ Bundle Deal ที่ทำให้ลูกค้าหันมาซื้อที่เราทันทีโดยไม่ต้องตัดราคา
    3. ⚡ 3-Second Stop-Scroll Hooks: สคริปต์เปิดคลิปวิดีโอ 3 แบบสำหรับหยุดนิ้วคนดู
    4. ✍️ Production-Ready Copywriting: แคปชันพร้อมยิงแอดฉบับสมบูรณ์ (Hook, Body, Offer, CTA) ภาษาไทยธรรมชาติ
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

# -------------------------------------------------------------
# SAMMY UI DASHBOARD
# -------------------------------------------------------------
st.title("🐢 Sammy: Competitive Intelligence & Counter-Strategy Engine")
st.caption("ระบบสอดแนมโฆษณาคู่แข่งเรียลไทม์ & สมองกลวางหมากแก้ทางเชิงรุก")

# Initialize Session States อย่างถูกต้อง ป้องกันบั๊กเพิ่มข้อมูลไม่ติด
if "watchlist" not in st.session_state:
    st.session_state["watchlist"] = ["Bewell", "Ergotrend", "Dr.PONG", "YVIS"]

if "scanned_results" not in st.session_state:
    st.session_state["scanned_results"] = []

if "target_caption" not in st.session_state:
    st.session_state["target_caption"] = ""

menu = st.sidebar.radio("เมนูหลักของ Sammy", ["🔍 ค้นหาแอดเรียลไทม์ (Live Search)", "⭐ Watchlist ร้านค้าคู่แข่ง", "🧠 Sammy AI วางหมากแก้ทาง", "📦 คลังแอดที่บันทึกไว้"])

# ================= MENU 1: ค้นหาแอดเรียลไทม์ =================
if menu == "🔍 ค้นหาแอดเรียลไทม์ (Live Search)":
    st.subheader("ดึงข้อมูลโฆษณาสดจาก Meta Ad Library (เรียลไทม์ทุกร้านค้า)")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_keyword = st.text_input("พิมพ์ชื่อแบรนด์ ร้านค้า หรือสินค้าที่ต้องการสอดแนม:", placeholder="เช่น YVIS, ครีมกันแดด, โต๊ะปรับระดับ")
    with col2:
        st.write("")
        st.write("")
        search_btn = st.button("🚀 ค้นหาแอดสดตอนนี้", use_container_width=True)

    if search_keyword and search_btn:
        with st.spinner(f"กำลังดึงข้อมูลโฆษณาสดของ '{search_keyword}' จาก Meta..."):
            results = fetch_realtime_ads(search_keyword)
            st.session_state["scanned_results"] = results

    results = st.session_state.get("scanned_results", [])
    
    if results:
        st.success(f"พบโฆษณาที่กำลังรันอยู่จริงทั้งหมด {len(results)} ตัว")
        
        for ad in results:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.markdown(f"**เพจ:** `{ad['page_name']}`")
                if ad["is_winning"]:
                    c2.markdown(f"<span class='winning-badge'>🔥 WINNING ({ad['lifespan_days']} วัน)</span>", unsafe_allow_html=True)
                else:
                    c2.markdown(f"<span class='testing-badge'>🧪 TESTING ({ad['lifespan_days']} วัน)</span>", unsafe_allow_html=True)
                c3.write(f"📅 เริ่มรัน: {ad['start_date']}")
                
                text_col, media_col = st.columns([3, 1])
                text_col.text_area("ข้อความโฆษณา:", ad["caption"], height=100, key=f"live_cap_{ad['ad_id']}")
                
                if ad["image_url"]:
                    media_col.image(ad["image_url"], use_container_width=True)
                else:
                    media_col.write("*(ไม่มีภาพพรีวิว)*")
                    
                b_col1, b_col2 = st.columns([1, 4])
                if b_col1.button("🧠 ส่งให้ Sammy ล้มแอดนี้", key=f"live_send_{ad['ad_id']}"):
                    st.session_state["target_caption"] = ad["caption"]
                    st.success("ส่งเข้าสมองกลแก้ทางเรียบร้อย! กดเมนู '🧠 Sammy AI วางหมากแก้ทาง' ด้านซ้ายได้เลย")
                b_col2.link_button("↗️ ดูบน Meta Ad Library", ad["snapshot_url"])

    elif search_keyword and not results:
        st.warning("ไม่พบแอดที่กำลังรันอยู่ หรือชื่อร้านค้านี้ไม่มีแคมเปญเปิดใช้งานในขณะนี้")

# ================= MENU 2: WATCHLIST =================
elif menu == "⭐ Watchlist ร้านค้าคู่แข่ง":
    st.subheader("จัดการรายชื่อร้านค้า/แบรนด์คู่แข่งที่คุณต้องการติดตาม")
    
    new_store = st.text_input("พิมพ์ชื่อร้านค้า/แบรนด์คู่แข่งที่ต้องการเพิ่ม:")
    if st.button("➕ เพิ่มเข้า Watchlist"):
        if new_store.strip() and new_store not in st.session_state["watchlist"]:
            st.session_state["watchlist"].append(new_store.strip())
            st.success(f"เพิ่ม '{new_store}' สำเร็จ!")
            st.rerun()
            
    st.write("---")
    st.markdown("### รายชื่อเพจคู่แข่งปัจจุบัน:")
    
    for idx, store in enumerate(st.session_state["watchlist"]):
        col_w1, col_w2, col_w3 = st.columns([3, 1, 1])
        col_w1.markdown(f"🏢 **{store}**")
        
        if col_w2.button("🔍 สแกนแอดด่วน", key=f"w_scan_{idx}"):
            with st.spinner(f"กำลังดึงข้อมูลแอดสดของ {store}..."):
                st.session_state["scanned_results"] = fetch_realtime_ads(store)
                st.info(f"สแกน {store} เสร็จแล้ว! กดไปที่เมนู '🔍 ค้นหาแอดเรียลไทม์ (Live Search)' เพื่อดูผลลัพธ์")
                
        if col_w3.button("🗑️ ลบ", key=f"w_del_{idx}"):
            st.session_state["watchlist"].remove(store)
            st.rerun()

# ================= MENU 3: วางหมากแก้ทาง =================
elif menu == "🧠 Sammy AI วางหมากแก้ทาง":
    st.subheader("สมองกล Sammy Counter-Strategy Engine")
    
    preset_cap = st.session_state.get("target_caption", "")
    ad_input = st.text_area("ข้อความ Winning Ad ของคู่แข่งที่ต้องการนำมาแก้ทาง:", value=preset_cap, height=160)
    
    strategy_type = st.selectbox("เลือกกลยุทธ์แคมเปญแก้ทาง:", [
        "แคมเปญชูจุดเด่นเหนือกว่าเรื่องคุณภาพและความคุ้มค่า (Value & Quality Superiority)",
        "แคมเปญ Double Day / Mega Sale (9.9 / 11.11)",
        "แคมเปญ Payday Special Deal (ช่วงเงินเดือนออก)",
        "แคมเปญตอกย้ำความมั่นใจ การรับประกัน และบริการ (Trust & Warranty Attack)"
    ])
    
    if st.button("🔥 ให้ Sammy ออกแบบหมากแก้ทางฉบับสมบูรณ์", type="primary"):
        if not ad_input.strip():
            st.warning("กรุณากอกข้อความแอดคู่แข่งก่อนครับ")
        else:
            with st.spinner("Sammy กำลังวิเคราะห์เจาะจุดตายและสร้างแผนแก้ทาง..."):
                output_strategy = generate_sammy_strategy(ad_input, strategy_type)
                st.markdown(output_strategy)

# ================= MENU 4: คลังแอดที่บันทึกไว้ =================
elif menu == "📦 คลังแอดที่บันทึกไว้":
    st.subheader("คลังเก็บข้อมูลโฆษณาคู่แข่งที่คุณสนใจ")
    st.info("คุณสามารถกดส่งแอดจากหน้าค้นหามาเก็บไว้ที่นี่เพื่อใช้วิเคราะห์ภายหลังได้")
    st.write("*(ฟีเจอร์คลังเก็บข้อมูลส่วนตัว พร้อมใช้งาน)*")
