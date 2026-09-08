import streamlit as st
import os
import pandas as pd
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

# สไตล์ Dark Theme
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
# ฐานข้อมูลตัวอย่างแอดจริงของแบรนด์ชั้นนำในไทย (Hard Data Preset)
# -------------------------------------------------------------
PRESET_DATABASE = {
    "bewell": [
        {
            "ad_id": "BW-001",
            "page_name": "Bewell เก้าอี้เพื่อสุขภาพ",
            "caption": "ปวดหลังจากการทำงานนานเกินไปใช่ไหม? เก้าอี้เพื่อสุขภาพ Bewell รุ่น Ergonomic Pro ออกแบบตามหลักสรีรศาสตร์ รองรับกระดูกสันหลังส่วนเอวได้สมบูรณ์แบบ รับประกันนาน 3 ปีเต็ม ส่งฟรีทั่วไทย พร้อมผ่อน 0% นาน 10 เดือน!",
            "start_date": "2025-11-10",
            "lifespan_days": 120,
            "is_winning": True,
            "link_url": "https://www.bewellthailand.com"
        },
        {
            "ad_id": "BW-002",
            "page_name": "Bewell เก้าอี้เพื่อสุขภาพ",
            "caption": "โปรโมชั่นต้อนรับเดือนใหม่! ซื้อเก้าอี้เพื่อสุขภาพคู่กับเบาะรองนั่ง Bewell รับส่วนลดทันที 1,500 บาท จำนวนจำกัดเพียง 50 สิทธิ์แรกเท่านั้น คลิกดูรายละเอียดเลย!",
            "start_date": "2026-03-01",
            "lifespan_days": 8,
            "is_winning": False,
            "link_url": "https://www.bewellthailand.com"
        }
    ],
    "ergotrend": [
        {
            "ad_id": "ET-101",
            "page_name": "Ergotrend เก้าอี้สำนักงาน",
            "caption": "จบปัญหาออฟฟิศซินโดรมด้วย Ergotrend Human Scale ปรับระดับได้ 6 จุดรองรับทุกสรีระ นั่งทำงาน 10 ชั่วโมงก็ไม่เมื่อย ทดลองนั่งได้แล้ววันนี้ที่ showroom ทุกสาขา",
            "start_date": "2025-08-15",
            "lifespan_days": 210,
            "is_winning": True,
            "link_url": "https://www.ergotrend.com"
        }
    ],
    "dr.pong": [
        {
            "ad_id": "DP-201",
            "page_name": "Dr.PONG ครีมลดสิวและฝ้า",
            "caption": "สูตรคุณหมอ 28 วันผิวดีขึ้นจริง! Dr.PONG Barrier X Serum กู้ผิวแพ้ง่าย เสริมเกราะป้องกันผิวแข็งแรง ปราศจากสารพาราเบนและน้ำหอม รีวิวแน่นจากผู้ใช้จริงกว่า 5,000 คน",
            "start_date": "2025-10-01",
            "lifespan_days": 160,
            "is_winning": True,
            "link_url": "https://www.drpong.in.th"
        }
    ]
}

def generate_sammy_counter_strategy(ad_caption, campaign_type):
    """สมองกล Sammy วิเคราะห์เจาะลึกกลยุทธ์คู่แข่ง"""
    if not GEMINI_API_KEY:
        return "⚠️ กรุณาตั้งค่า GEMINI_API_KEY ใน Streamlit Secrets ก่อนใช้งานระบบวิเคราะห์"
        
    prompt = f"""
    คุณคือ Sammy - E-commerce Competitive Intelligence & Counter-Strategy Engine ผู้เชี่ยวชาญด้านกลยุทธ์การตลาดและการแข่งขันเชิงรุก
    นี่คือโฆษณา Winning Ad ของคู่แข่งที่กำลังรันอยู่ในตลาดไทย:
    
    --- ข้อมูลโฆษณาคู่แข่ง ---
    {ad_caption}
    -------------------------
    
    ประเภทแคมเปญที่เราจะใช้สู้: {campaign_type}
    
    โปรดวิเคราะห์เจาะจง ห้ามตอบทฤษฎีกลวง ๆ และส่งมอบผลลัพธ์เป็น Action พร้อมใช้งานในรูปแบบ Markdown:
    1. 🎯 เจาะจุดตายคู่แข่ง (Vulnerability Analysis): วิเคราะห์จุดอ่อนของโปรโมชันหรือข้อเสนอของคู่แข่งเจ้านี้ที่ลูกค้ายังลังเล (เช่น ราคาแพงเกินไป, ระยะเวลาประกัน, เงื่อนไขของแถม)
    2. 🥊 หมากแก้ทางเด็ดขาด (Offer Counter-Attack): ออกแบบข้อเสนอ Bundle Deal หรือความคุ้มค่าที่จะดึงลูกค้าให้หันมาซื้อที่เราโดยไม่ต้องสงครามราคา
    3. ⚡ 3-Second Stop-Scroll Hooks: ขอสคริปต์เปิดคลิปวิดีโอ 3 แบบสำหรับหยุดนิ้วคนดูที่กำลังไถฟีดเจอแอดคู่แข่ง
    4. ✍️ Production-Ready Copywriting: เขียนแคปชันพร้อมยิงแอดฉบับสมบูรณ์ (มี Hook, Body, Offer, CTA) ภาษาไทยธรรมชาติพร้อมใช้งานทันที
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการเรียกใช้งาน Gemini: {e}"

# -------------------------------------------------------------
# SAMMY UI DASHBOARD
# -------------------------------------------------------------
st.title("🐢 Sammy: Competitive Intelligence & Counter-Strategy Engine")
st.caption("ระบบสอดแนมโฆษณาคู่แข่ง & สมองกลวางหมากแก้ทางเชิงรุก (Production Ready)")

# Session State
if "watchlist" not in st.session_state:
    st.session_state["watchlist"] = ["Bewell", "Ergotrend", "Dr.PONG"]

if "active_ads" not in st.session_state:
    st.session_state["active_ads"] = PRESET_DATABASE["bewell"]

menu = st.sidebar.radio("เมนูหลักของ Sammy", ["🔍 ฐานข้อมูลแอดคู่แข่ง (Database)", "📥 นำเข้าข้อมูลแอด (Quick Ingestion)", "🧠 Sammy AI วางหมากแก้ทาง", "⭐ Watchlist ร้านค้าคู่แข่ง"])

# ================= MENU 1: ฐานข้อมูลแอดคู่แข่ง =================
if menu == "🔍 ฐานข้อมูลแอดคู่แข่ง (Database)":
    st.subheader("ฐานข้อมูลโฆษณาคู่แข่งและตัวทำเงิน (Hard Data & Winning Ads)")
    
    selected_brand = st.selectbox("เลือกแบรนด์หรือค้นหาในระบบ:", ["Bewell", "Ergotrend", "Dr.PONG"])
    
    if st.button("📂 โหลดข้อมูลแอดของแบรนด์นี้"):
        key = selected_brand.lower()
        if key in PRESET_DATABASE:
            st.session_state["active_ads"] = PRESET_DATABASE[key]
        else:
            # สร้างข้อมูลจำลองกรณีค้นหาแบรนด์อื่น
            st.session_state["active_ads"] = [
                {
                    "ad_id": "GEN-001",
                    "page_name": selected_brand,
                    "caption": f"โปรโมชั่นสุดคุ้มจาก {selected_brand} สินค้าคุณภาพคัดสรรเพื่อคุณ ส่งฟรีทั่วไทย รับประกันความพอใจ คืนเงินใน 7 วัน",
                    "start_date": "2026-01-10",
                    "lifespan_days": 45,
                    "is_winning": True,
                    "link_url": "https://www.facebook.com"
                }
            ]

    ads = st.session_state.get("active_ads", [])
    
    if ads:
        total_ads = len(ads)
        winning_ads = [a for a in ads if a["is_winning"]]
        
        m1, m2 = st.columns(2)
        m1.metric("โฆษณาทั้งหมดในระบบ", f"{total_ads} ตัว")
        m2.metric("Winning Ads (รันเกิน 14 วัน)", f"{len(winning_ads)} ตัว", delta="แอดทำเงินเจ้าตลาด")
        
        st.write("---")
        
        for ad in ads:
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
                
                st.text_area("ข้อความโฆษณา (Raw Caption)", ad["caption"], height=100, key=f"db_cap_{ad['ad_id']}")
                
                b1, b2 = st.columns([1, 4])
                with b1:
                    if st.button("🧠 ส่งให้ Sammy ล้มแอดนี้", key=f"db_send_{ad['ad_id']}"):
                        st.session_state["target_caption"] = ad["caption"]
                        st.success("ส่งข้อมูลให้ Sammy เรียบร้อย! กดสลับไปที่เมนู '🧠 Sammy AI วางหมากแก้ทาง'")
                with b2:
                    st.link_button("🔗 ลิงก์ปลายทางแบรนด์", ad["link_url"])

# ================= MENU 2: นำเข้าข้อมูลแอด =================
elif menu == "📥 นำเข้าข้อมูลแอด (Quick Ingestion)":
    st.subheader("ช่องทางนำเข้าข้อความแอดคู่แข่งจากหน้า Meta Ad Library")
    st.info("💡 วิธีใช้งาน: เปิดหน้า Meta Ad Library ค้นหาแบรนด์ที่ต้องการ ก๊อปปี้ข้อความโฆษณาตัวที่ยิงนานที่สุด แล้วนำมาวางที่นี่")
    
    p_name = st.text_input("ชื่อเพจคู่แข่ง:", placeholder="เช่น พรีมายา, สมุนไพรคุณยาย")
    p_caption = st.text_area("วางข้อความโฆษณา (Caption) ของคู่แข่ง:", placeholder="วางข้อความที่ก๊อปปี้มาที่นี่...", height=180)
    p_days = st.number_input("ประมาณอายุแอดที่รัน (วัน):", min_value=1, max_value=365, value=20)
    
    if st.button("📥 บันทึกและส่งเข้าสมองกลแก้ทาง", type="primary"):
        if p_caption.strip():
            new_item = {
                "ad_id": f"MANUAL-{int(datetime.now().timestamp())}",
                "page_name": p_name if p_name else "คู่แข่งทั่วไป",
                "caption": p_caption,
                "start_date": "ข้อมูลนำเข้าเอง",
                "lifespan_days": int(p_days),
                "is_winning": p_days >= 14,
                "link_url": "https://www.facebook.com/ads/library/"
            }
            if "active_ads" not in st.session_state:
                st.session_state["active_ads"] = []
            st.session_state["active_ads"].insert(0, new_item)
            st.session_state["target_caption"] = p_caption
            st.success("บันทึกข้อมูลและส่งให้ Sammy เรียบร้อย! สามารถสลับไปเมนู '🧠 Sammy AI วางหมากแก้ทาง' ได้ทันที")
        else:
            st.warning("กรุณาวางข้อความแอดก่อนบันทึก")

# ================= MENU 3: SAMMY AI วางหมากแก้ทาง =================
elif menu == "🧠 Sammy AI วางหมากแก้ทาง":
    st.subheader("สมองกล Sammy Counter-Strategy Engine")
    
    preset = st.session_state.get("target_caption", "")
    ad_target = st.text_area("ข้อความ Winning Ad ของคู่แข่งที่ต้องการนำมาแก้ทาง:", value=preset, height=160)
    
    campaign_theme = st.selectbox("เลือกกลยุทธ์แคมเปญแก้ทาง:", [
        "แคมเปญชูจุดเด่นเหนือกว่าเรื่องคุณภาพและความคุ้มค่า (Value & Quality Superiority)",
        "แคมเปญ Double Day / Mega Sale (9.9 / 11.11)",
        "แคมเปญ Payday Special Deal (ช่วงเงินเดือนออก)",
        "แคมเปญตอกย้ำความมั่นใจ การรับประกัน และบริการ (Trust & Warranty Attack)"
    ])
    
    if st.button("🔥 ให้ Sammy ออกแบบหมากแก้ทางฉบับสมบูรณ์", type="primary"):
        if not ad_target.strip():
            st.warning("กรุณากรอกข้อความแอดคู่แข่งก่อนครับ")
        else:
            with st.spinner("Sammy กำลังวิเคราะห์เจาะจุดตายและสร้างแผนแก้ทาง..."):
                result = generate_sammy_counter_strategy(ad_target, campaign_theme)
                st.markdown(result)

# ================= MENU 4: WATCHLIST =================
elif menu == "⭐ Watchlist ร้านค้าคู่แข่ง":
    st.subheader("รายชื่อเพจแบรนด์คู่แข่งใน Watchlist ของคุณ")
    
    new_w = st.text_input("เพิ่มชื่อแบรนด์หรือร้านค้าคู่แข่ง:")
    if st.button("➕ เพิ่มเข้ารายชื่อ"):
        if new_w.strip() and new_w not in st.session_state["watchlist"]:
            st.session_state["watchlist"].append(new_w.strip())
            st.success(f"บันทึก '{new_w}' สำเร็จ!")
            
    st.write("---")
    for idx, brand in enumerate(st.session_state["watchlist"]):
        col_b1, col_b2 = st.columns([3, 1])
        col_b1.markdown(f"🏢 **{brand}**")
        if col_b2.button("🗑️ ลบ", key=f"w_del_{idx}"):
            st.session_state["watchlist"].remove(brand)
            st.rerun()
