import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import os
import google.generativeai as genai

# ตั้งค่าหน้าจอ
st.set_page_config(
    page_title="Sammy - E-commerce Intelligence Engine",
    layout="wide",
    page_icon="🐢"
)

# ดึง Gemini API Key จาก Secrets หลังบ้าน
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

# สไตล์หน้าเว็บ Dark Theme สวยหรู
st.markdown("""
<style>
    .metric-card {
        background-color: #0b1626;
        border: 1px solid #1e293b;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 10px;
    }
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
# CORE ENGINE: ดึงข้อมูลสดจาก Meta Ad Library โดยตรง (ไม่ต้องใช้ Token)
# -------------------------------------------------------------
def search_meta_library_direct(keyword, count=30):
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
        "session_id": "8b3dfb7b-232e-4b47-b86e-909d94998901",
        "count": count
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
                    "caption": caption,
                    "start_date": date_str,
                    "lifespan_days": lifespan,
                    "is_winning": lifespan >= 14,
                    "image_url": img_url,
                    "link_url": link_url,
                    "snapshot_url": f"https://www.facebook.com/ads/library/?id={ad_id}"
                })
                
        return sorted(extracted_ads, key=lambda x: x["lifespan_days"], reverse=True)
    except Exception as e:
        st.error(f"ระบบไม่สามารถดึงข้อมูลสดได้ชั่วคราว: {e}")
        return []

def generate_sammy_counter_strategy(ad_caption, campaign_type):
    """สมองกล Sammy วิเคราะห์เจาะลึกกลยุทธ์คู่แข่ง"""
    prompt = f"""
    คุณคือ Sammy - E-commerce Competitive Intelligence & Counter-Strategy Engine ผู้เชี่ยวชาญด้านกลยุทธ์การตลาดและการแข่งขันเชิงรุก
    นี่คือโฆษณา Winning Ad ของคู่แข่งที่กำลังรันอยู่ในตลาดไทย:
    
    --- ข้อมูลโฆษณาคู่แข่ง ---
    {ad_caption}
    -------------------------
    
    ประเภทแคมเปญที่เราจะใช้สู้: {campaign_type}
    
    โปรดวิเคราะห์เจาะจง ห้ามตอบทฤษฎีกลวง ๆ และส่งมอบผลลัพธ์เป็น Action พร้อมใช้งานในรูปแบบ Markdown:
    1. 🎯 เจาะจุดตายคู่แข่ง (Vulnerability Analysis): วิเคราะห์จุดอ่อนของโปรโมชันหรือข้อเสนอของคู่แข่งเจ้านี้ที่ลูกค้ายังลังเล
    2. 🥊 หมากแก้ทางเด็ดขาด (Offer Counter-Attack): ออกแบบข้อเสนอ Bundle Deal หรือความคุ้มค่าที่จะดึงลูกค้าให้หันมาซื้อที่เราโดยไม่ต้องสงครามราคา
    3. ⚡ 3-Second Stop-Scroll Hooks: ขอสคริปต์เปิดคลิปวิดีโอ 3 แบบสำหรับหยุดนิ้วคนดูที่กำลังไถฟีดเจอแอดคู่แข่ง
    4. ✍️ Production-Ready Copywriting: เขียนแคปชันพร้อมยิงแอดฉบับสมบูรณ์ (มี Hook, Body, Offer, CTA) ภาษาไทยธรรมชาติพร้อมใช้งานทันที
    """
    response = model.generate_content(prompt)
    return response.text

# -------------------------------------------------------------
# SAMMY UI DASHBOARD
# -------------------------------------------------------------
st.title("🐢 Sammy: Competitive Intelligence & Counter-Strategy Engine")
st.caption("ระบบสอดแนมข้อมูลดิบโฆษณาคู่แข่งจากตลาดจริง & สมองกลวางหมากแก้ทางเชิงรุก")

# Session State สำหรับ Watchlist
if "watchlist" not in st.session_state:
    st.session_state["watchlist"] = ["Bewell", "Ergotrend", "Dr.PONG"]

menu = st.sidebar.radio("เมนูหลักของ Sammy", ["🔍 สแกนแอด & ดึงข้อมูลดิบ", "🧠 Sammy AI วางหมากแก้ทาง", "⭐ Watchlist ร้านค้าคู่แข่ง", "📊 วิเคราะห์ตลาดรวม"])

# ================= MENU 1: สแกนแอดคู่แข่ง =================
if menu == "🔍 สแกนแอด & ดึงข้อมูลดิบ":
    st.subheader("ดึงข้อมูลโฆษณาสดจาก Meta Ad Library (Hard Data)")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("พิมพ์ชื่อแบรนด์คู่แข่ง หรือ คีย์เวิร์ดสินค้า:", placeholder="เช่น Bewell, ครีมลดฝ้า, เก้าอี้สุขภาพ")
    with col2:
        st.write("")
        st.write("")
        scan_btn = st.button("🚀 สแกนหา Winning Ads", use_container_width=True)

    if query and scan_btn:
        with st.spinner(f"Sammy กำลังดึงข้อมูลโฆษณาสดของ '{query}'..."):
            ads_data = search_meta_library_direct(query, count=40)
            st.session_state["sammy_ads"] = ads_data

    if "sammy_ads" in st.session_state and st.session_state["sammy_ads"]:
        ads = st.session_state["sammy_ads"]
        
        total_ads = len(ads)
        winning_ads = [a for a in ads if a["is_winning"]]
        testing_ads = [a for a in ads if not a["is_winning"]]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("โฆษณาทั้งหมดที่กำลังรัน", f"{total_ads} ตัว")
        m2.metric("Winning Ads (รันเกิน 14 วัน)", f"{len(winning_ads)} ตัว", delta="แอดทำเงินเจ้าตลาด")
        m3.metric("Testing Ads (แอดทดสอบใหม่)", f"{len(testing_ads)} ตัว")
        
        st.write("---")
        
        filter_choice = st.radio("ตัวกรองแสดงผล:", ["ทั้งหมด", "เฉพาะ Winning Ads (ตัวทำเงิน)", "เฉพาะ Testing Ads (แอดใหม่)"], horizontal=True)
        
        display_ads = ads
        if filter_choice == "เฉพาะ Winning Ads (ตัวทำเงิน)":
            display_ads = winning_ads
        elif filter_choice == "เฉพาะ Testing Ads (แอดใหม่)":
            display_ads = testing_ads

        for ad in display_ads:
            with st.container(border=True):
                top_c1, top_c2, top_c3 = st.columns([2, 1, 1])
                with top_c1:
                    st.markdown(f"**เพจ:** `{ad['page_name']}` | **ID:** `{ad['ad_id']}`")
                with top_c2:
                    if ad["is_winning"]:
                        st.markdown(f"<span class='winning-badge'>🔥 WINNING ({ad['lifespan_days']} วัน)</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span class='testing-badge'>🧪 TESTING ({ad['lifespan_days']} วัน)</span>", unsafe_allow_html=True)
                with top_c3:
                    st.write(f"📅 เริ่มรัน: {ad['start_date']}")
                
                cont_c, med_c = st.columns([3, 1])
                with cont_c:
                    st.text_area("ข้อความโฆษณา (Raw Caption)", ad["caption"] if ad["caption"] else "[โฆษณานี้เป็นรูปภาพหรือวิดีโอไม่มีข้อความบรรยาย]", height=105, key=f"s_cap_{ad['ad_id']}")
                    if ad["link_url"]:
                        st.markdown(f"🔗 **ลิงก์:** [{ad['link_url']}]({ad['link_url']})")
                
                with med_c:
                    if ad["image_url"]:
                        st.image(ad["image_url"], use_container_width=True)
                    else:
                        st.write("*(ไม่มีรูปพรีวิว)*")
                    
                    if st.button("🧠 ส่งให้ Sammy ล้มแอดนี้", key=f"send_{ad['ad_id']}"):
                        st.session_state["target_caption"] = ad["caption"]
                        st.success("ส่งข้อมูลให้ Sammy เรียบร้อย! กดสลับไปที่เมนู 'Sammy AI วางหมากแก้ทาง'")
                        
                    st.link_button("↗️ ดูบน Meta", ad["snapshot_url"], use_container_width=True)

    elif "sammy_ads" in st.session_state and not st.session_state["sammy_ads"]:
        st.warning("ไม่พบข้อมูลโฆษณา กรุณาลองเปลี่ยนคำค้นหา")

# ================= MENU 2: SAMMY AI วางหมากแก้ทาง =================
elif menu == "🧠 Sammy AI วางหมากแก้ทาง":
    st.subheader("สมองกล Sammy Counter-Strategy Engine")
    
    preset = st.session_state.get("target_caption", "")
    ad_target = st.text_area("ข้อความ Winning Ad ของคู่แข่งที่ต้องการนำมาแก้ทาง:", value=preset, height=150)
    
    campaign_theme = st.selectbox("เลือกกลยุทธ์แคมเปญแก้ทาง:", [
        "แคมเปญชูจุดเด่นเหนือกว่าเรื่องคุณภาพและความคุ้มค่า (Value & Quality Superiority)",
        "แคมเปญ Double Day / Mega Sale (9.9 / 11.11)",
        "แคมเปญ Payday Special Deal (ช่วงเงินเดือนออก)",
        "แคมเปญตอกย้ำความมั่นใจ การรับประกัน และบริการ (Trust & Warranty Attack)"
    ])
    
    if st.button("🔥 ให้ Sammy ออกแบบหมากแก้ทางฉบับสมบูรณ์", type="primary"):
        if not ad_target.strip():
            st.warning("กรุณากอกข้อความแอดคู่แข่งก่อนครับ")
        elif not GEMINI_API_KEY:
            st.error("⚠️ ไม่พบคีย์ GEMINI_API_KEY กรุณาตั้งค่าใน Secrets ก่อนใช้งาน")
        else:
            with st.spinner("Sammy กำลังวิเคราะห์เจาะจุดตายและสร้างแผนแก้ทาง..."):
                result = generate_sammy_counter_strategy(ad_target, campaign_theme)
                st.markdown(result)

# ================= MENU 3: WATCHLIST =================
elif menu == "⭐ Watchlist ร้านค้าคู่แข่ง":
    st.subheader("รายชื่อเพจแบรนด์คู่แข่งใน Watchlist ของคุณ")
    
    new_w = st.text_input("เพิ่มชื่อแบรนด์หรือร้านค้าคู่แข่ง:")
    if st.button("➕ เพิ่มเข้ารายชื่อ"):
        if new_w.strip() and new_w not in st.session_state["watchlist"]:
            st.session_state["watchlist"].append(new_w.strip())
            st.success(f"บันทึก '{new_w}' สำเร็จ!")
            
    st.write("---")
    for idx, brand in enumerate(st.session_state["watchlist"]):
        col_b1, col_b2, col_b3 = st.columns([3, 1, 1])
        col_b1.markdown(f"🏢 **{brand}**")
        if col_b2.button("🔍 สแกนแอดด่วน", key=f"w_scan_{idx}"):
            with st.spinner(f"กำลังดึงข้อมูล {brand}..."):
                st.session_state["sammy_ads"] = search_meta_library_direct(brand, count=30)
                st.info("สแกนเสร็จแล้ว! กดสลับไปที่เมนู 'สแกนแอด & ดึงข้อมูลดิบ' เพื่อดูข้อมูล")
        if col_b3.button("🗑️ ลบ", key=f"w_del_{idx}"):
            st.session_state["watchlist"].remove(brand)
            st.rerun()

# ================= MENU 4: สรุปวิเคราะห์ตลาด =================
elif menu == "📊 วิเคราะห์ตลาดรวม":
    st.subheader("สรุปภาพรวมข้อมูลดิบในตลาด (Market Extraction)")
    if "sammy_ads" in st.session_state and st.session_state["sammy_ads"]:
        ads = st.session_state["sammy_ads"]
        
        all_text = " ".join([a["caption"] for a in ads if a["caption"]])
        hashtags = re.findall(r"#\w+", all_text)
        
        st.markdown("#### 1. แฮชแท็กยอดนิยมที่ใช้ในตลาด")
        if hashtags:
            df_h = pd.Series(hashtags).value_counts().reset_index()
            df_h.columns = ["Hashtag", "ความถี่ที่พบ"]
            st.dataframe(df_h.head(10), use_container_width=True)
        else:
            st.write("ไม่พบแฮชแท็กในชุดข้อมูลนี้")
            
        st.markdown("#### 2. ตารางสรุปอายุแอดและพฤติกรรมคู่แข่ง")
        df_summary = pd.DataFrame([{
            "แบรนด์": a["page_name"],
            "อายุแอด (วัน)": a["lifespan_days"],
            "สถานะ": "🔥 WINNING" if a["is_winning"] else "🧪 TESTING",
            "เริ่มรันเมื่อ": a["start_date"]
        } for a in ads])
        st.dataframe(df_summary, use_container_width=True)
    else:
        st.info("กรุณาไปที่เมนู 'สแกนแอด & ดึงข้อมูลดิบ' แล้วกดค้นหาข้อมูลเพื่อดึงข้อมูลงสานมาก่อนครับ")
