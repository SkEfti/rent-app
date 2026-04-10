import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import time
from streamlit_gsheets import GSheetsConnection 

st.set_page_config(page_title="ভাড়া ব্যবস্থাপনা", page_icon="🏠", layout="centered", initial_sidebar_state="collapsed")

# কনস্ট্যান্ট সেটআপ
ELEC_RATE = 10
GARBAGE_BILL = 60   

BENGALI_MONTHS = ["জানুয়ারি","ফেব্রুয়ারি","মার্চ","এপ্রিল","মে","জুন","জুলাই","আগস্ট","সেপ্টেম্বর","অক্টোবর","নভেম্বর","ডিসেম্বর"]
PREV_MONTH_MAP = {1:"ডিসেম্বর", 2:"জানুয়ারি", 3:"ফেব্রুয়ারি", 4:"মার্চ", 5:"এপ্রিল", 6:"মে", 7:"জুন", 8:"জুলাই", 9:"আগস্ট", 10:"সেপ্টেম্বর", 11:"অক্টোবর", 12:"নভেম্বর"}

# --- CSS (UI ডিজাইন) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Hind Siliguri', sans-serif !important; font-size: 18px; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 8px 12px 50px 12px !important; max-width: 620px !important; }
body  { background: #0d1b2a; color: #e8edf2; }
.stApp { background: #0d1b2a; }
.app-title { text-align:center; color:#f0c040; font-size:1.55rem; font-weight:700; padding:10px 0 2px; }
.app-sub   { text-align:center; color:#6a8da8; font-size:0.9rem; margin-bottom:10px; }
.date-banner { text-align:center; background:#162333; border:1px solid #f0c040; border-radius:10px; padding:7px; color:#f0c040; font-size:1rem; font-weight:600; margin-bottom:12px; }
.card { background:#162333; border:1px solid #1e3a52; border-radius:14px; padding:14px 16px; margin-bottom:12px; }
.card-title { font-size:1.05rem; font-weight:700; color:#f0c040; margin-bottom:10px; display:flex; align-items:center; gap:8px; }
.badge { background:#f0c040; color:#0d1b2a; border-radius:50%; width:24px; height:24px; display:inline-flex; align-items:center; justify-content:center; font-size:0.8rem; font-weight:700; flex-shrink:0; }
.row { display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid #1a2e40; }
.row:last-child { border-bottom:none; }
.rl { color:#7a9ab5; font-size:0.95rem; }
.rv { font-weight:600; color:#e8edf2; font-size:0.98rem; }
.rv.gold { color:#f0c040; } .rv.green { color:#3dd68c; } .rv.red { color:#ff6b6b; } .rv.blue { color:#5bc8f5; }
.pill-row { display:flex; flex-wrap:wrap; gap:6px; margin-top:6px; }
.pill { background:#1a2e40; border:1px solid #2a4a60; border-radius:20px; padding:4px 12px; font-size:0.88rem; color:#b0c8d8; }
.divider { border-top:1px dashed #1e3a52; margin:12px 0; }
.sbox { border-radius:10px; padding:12px; margin-top:8px; }
.sbox.green { background:#0d2219; border:1px solid #2a6647; }
.sbox.red   { background:#220d0d; border:1px solid #6a2a2a; }
.sbox-title { font-size:1rem; font-weight:700; margin-bottom:8px; }
div[data-testid="stSelectbox"] label, div[data-testid="stNumberInput"] label { color:#7a9ab5 !important; font-size:0.95rem !important; font-family:'Hind Siliguri',sans-serif !important; }
div[data-testid="stSelectbox"] > div > div, div[data-testid="stNumberInput"] input { background:#1a2e40 !important; border:1px solid #2a4a60 !important; border-radius:8px !important; color:#e8edf2 !important; font-family:'Hind Siliguri',sans-serif !important; font-size:1rem !important; }
.stTextArea textarea { background:#1a2e40 !important; border:1px solid #2a4a60 !important; color:#c8d8e8 !important; font-size:0.9rem !important; font-family:'Hind Siliguri',sans-serif !important; }
.stButton > button { background:#f0c040 !important; color:#0d1b2a !important; font-weight:700 !important; font-size:1rem !important; font-family:'Hind Siliguri',sans-serif !important; border:none !important; border-radius:10px !important; padding:12px !important; width:100% !important; }
.wa-link { display:block; text-align:center; background:#0e2319; border:2px solid #25d366; border-radius:10px; color:#25d366 !important; font-weight:700; font-size:1rem; padding:12px; text-decoration:none; margin-top:4px; }
.info-box { background:#12263a; border:1px solid #2a5070; border-radius:10px; padding:10px 14px; margin-top:8px; font-size:0.92rem; color:#7a9ab5; }
div[data-testid="stCheckbox"] label { color:#ff6b6b !important; font-size:0.95rem !important; font-weight:600; font-family:'Hind Siliguri',sans-serif !important; }
div[data-testid="stRadio"] p { color: #f0c040 !important; font-size: 1.1rem !important; font-weight: 700 !important; font-family: 'Hind Siliguri', sans-serif !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# গুগল শিট কানেকশন ও ডাটা ফাংশন
# ─────────────────────────────────────────────
SHEET_URL = "https://docs.google.com/spreadsheets/d/1uaa_BTXwBawrAKhWpSA-nQOQvHST68Cv9UeotVFsPYg/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=1) 
def load_data():
    return conn.read(spreadsheet=SHEET_URL)

def save_to_gsheets(df, idx, rent_due, garb_due, elec_due, reading, current_month_str, history_data):
    # ১. মেইন শিট আপডেট (রুম ডাটা)
    df.at[idx, 'বকেয়া ভাড়া']   = rent_due
    df.at[idx, 'বকেয়া ময়লা']    = garb_due
    df.at[idx, 'বকেয়া বিদ্যুৎ']  = elec_due
    df.at[idx, 'আগের রিডিং']    = reading
    df.at[idx, 'সর্বশেষ আপডেট মাস'] = current_month_str
    conn.update(spreadsheet=SHEET_URL, data=df)
    
    # ২. হিস্ট্রি শিট আপডেট (হিস্ট্রি লগ)
    try:
        hist_df = conn.read(spreadsheet=SHEET_URL, worksheet="History", ttl=0)
        updated_hist = pd.concat([hist_df, pd.DataFrame([history_data])], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, worksheet="History", data=updated_hist)
    except:
        conn.update(spreadsheet=SHEET_URL, worksheet="History", data=pd.DataFrame([history_data]))
        
    st.cache_data.clear()

def ensure_phone(p):
    p = str(p).split('.')[0].strip()
    return p if p.startswith('88') else '88' + p

def today_str():
    n = datetime.now()
    return f"{n.day} {BENGALI_MONTHS[n.month-1]}, {n.year}"

# মেইন অ্যাপ লোড
try:
    df = load_data()
except Exception as e:
    st.error(f"ডাটাবেজ কানেক্ট হতে সমস্যা হচ্ছে। Error: {e}")
    st.stop()

st.markdown('<div class="app-title">🏠 ভাড়া ব্যবস্থাপনা সিস্টেম</div>', unsafe_allow_html=True)
st.markdown('<div class="app-sub">Cloud Managed System</div>', unsafe_allow_html=True)
st.markdown(f'<div class="date-banner">📅 {today_str()}</div>', unsafe_allow_html=True)

st.markdown('<div class="card"><div class="card-title"><span class="badge">১</span> রুম/ইউনিট নির্বাচন</div>', unsafe_allow_html=True)
selected_room = st.radio("রুম/ইউনিট নির্বাচন করুন:", df['রুম'].tolist(), label_visibility="collapsed", horizontal=True)

row      = df[df['রুম'] == selected_room].iloc[0]
room_idx = df[df['রুম'] == selected_room].index[0]
room_num = room_idx + 1
has_elec = (room_num <= 6)

past_rent_due = int(row['বকেয়া ভাড়া'])
past_garb_due = int(row['বকেয়া ময়লা'])
past_elec_due = int(row['বকেয়া বিদ্যুৎ'])
prev_reading  = int(row['আগের রিডিং'])

# --- অটো মাস ডিটেকশন লজিক ---
cm = BENGALI_MONTHS[datetime.now().month - 1] # বর্তমান মাস
last_month_val = row.get('সর্বশেষ আপডেট মাস', '')
if pd.isna(last_month_val): last_month_val = ""
auto_due_mode = (str(last_month_val).strip() == cm)

st.markdown(f"""
<div class="pill-row">
  <span class="pill">📞 {row['ফোন নম্বর']}</span>
  <span class="pill">💰 ভাড়া {int(row['নির্ধারিত ভাড়া'])} টাকা</span>
  <span class="pill">{'⚡ বিদ্যুৎ আছে' if has_elec else '🚫 বিদ্যুৎ নেই'}</span>
</div>
""", unsafe_allow_html=True)

if past_rent_due > 0 or past_garb_due > 0 or past_elec_due > 0:
    due_parts = []
    if past_rent_due  > 0: due_parts.append(f"ভাড়া {past_rent_due} ৳")
    if past_garb_due  > 0: due_parts.append(f"ময়লা {past_garb_due} ৳")
    if past_elec_due  > 0: due_parts.append(f"বিদ্যুৎ {past_elec_due} ৳")
    st.markdown(f'<div class="info-box">⚠️ পূর্ববর্তী বকেয়া: {" | ".join(due_parts)}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# ২. বিল হিসাব
# ---------------------------------------------------------
st.markdown('<div class="card"><div class="card-title"><span class="badge">২</span> বিল হিসাব</div>', unsafe_allow_html=True)
pm = PREV_MONTH_MAP[datetime.now().month]

if auto_due_mode:
    fixed_rent = 0
    garbage_this_month = 0
    st.markdown('<div class="info-box" style="color:#3dd68c; text-align:center; border-color:#3dd68c;">✅ এই মাসের বিল আগেই হিসাব করা হয়েছে। এখন শুধুমাত্র বকেয়া পেমেন্ট গ্রহণ করা হচ্ছে।</div>', unsafe_allow_html=True)
else:
    fixed_rent = int(row['নির্ধারিত ভাড়া'])
    garbage_this_month = GARBAGE_BILL

total_rent_payable = fixed_rent + past_rent_due
total_garbage_payable = garbage_this_month + past_garb_due

# UI ডিসপ্লে
if not auto_due_mode:
    st.markdown(f'<div class="row"><span class="rl">🏷️ {pm} মাসের ভাড়া</span><span class="rv">{fixed_rent} টাকা</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="row"><span class="rl">🗑️ {pm} মাসের ময়লা বিল</span><span class="rv">{garbage_this_month} টাকা</span></div>', unsafe_allow_html=True)

if past_rent_due > 0:
    st.markdown(f'<div class="row"><span class="rl">🏷️ পূর্বের বকেয়া ভাড়া</span><span class="rv red">{past_rent_due} টাকা</span></div>', unsafe_allow_html=True)
if past_garb_due > 0:
    st.markdown(f'<div class="row"><span class="rl">🗑️ পূর্বের বকেয়া ময়লা</span><span class="rv red">{past_garb_due} টাকা</span></div>', unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# বিদ্যুৎ বিল হিসাব
current_reading = prev_reading
used_units      = 0
total_elec_payable = 0

if has_elec:
    st.markdown(f'<div class="row"><span class="rl">⚡ সর্বশেষ পরিশোধিত রিডিং</span><span class="rv blue">{prev_reading}</span></div>', unsafe_allow_html=True)
    if auto_due_mode:
        total_elec_payable = past_elec_due
        if past_elec_due > 0:
            st.markdown(f'<div class="row"><span class="rl">⚡ পূর্বের বকেয়া বিদ্যুৎ বিল</span><span class="rv red">{past_elec_due} টাকা</span></div>', unsafe_allow_html=True)
    else:
        current_reading = st.number_input("বর্তমান মিটার রিডিং:", min_value=0, value=0, step=1, key=f"meter_{selected_room}")
        used_units = current_reading - prev_reading if current_reading > prev_reading else 0
        total_elec_payable = used_units * ELEC_RATE
        if past_elec_due > 0:
            st.markdown(f'<div class="row"><span class="rl">⚡ পূর্বের বকেয়া বিদ্যুৎ</span><span class="rv red">{past_elec_due} টাকা</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="row"><span class="rl">⚡ চলতি বিদ্যুৎ ({used_units} ইউনিট × ১০)</span><span class="rv">{total_elec_payable} টাকা</span></div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="row"><span class="rl">⚡ বিদ্যুৎ বিল</span><span class="rv" style="color:#4a6070;">প্রযোজ্য নয়</span></div>', unsafe_allow_html=True)

grand_total = total_rent_payable + total_garbage_payable + total_elec_payable
st.markdown(f'<div class="row"><span class="rl" style="color:#f0c040;font-weight:700;">সর্বমোট প্রদেয় বিল</span><span class="rv gold">{grand_total} টাকা</span></div></div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# ৩. পেমেন্ট ও সেভ
# ---------------------------------------------------------
st.markdown('<div class="card"><div class="card-title"><span class="badge">৩</span> বিল পরিশোধ (Payment)</div>', unsafe_allow_html=True)

received = st.number_input("প্রাপ্ত টাকার পরিমাণ (জমা):", min_value=0, value=0, step=50, key=f"pay_{selected_room}")
process_zero = st.checkbox("❌ এই মাসে কোনো টাকা দেয়নি (0 টাকা পেমেন্ট সেভ করুন)", key=f"zero_{selected_room}")

rem = received
rent_paid    = min(rem, total_rent_payable);    rem -= rent_paid
garbage_paid = min(rem, total_garbage_payable); rem -= garbage_paid
elec_paid    = min(rem, total_elec_payable);    rem -= elec_paid

new_rent_due    = total_rent_payable    - rent_paid
new_garbage_due = total_garbage_payable - garbage_paid
new_elec_due    = total_elec_payable    - elec_paid
total_due       = new_rent_due + new_garbage_due + new_elec_due

paid_elec_units   = elec_paid // ELEC_RATE
new_saved_reading = (prev_reading + paid_elec_units) if has_elec else prev_reading

if received > 0 or process_zero:
    # রসিদ প্রিভিউ
    elec_info = f"{total_elec_payable}"
    if has_elec and not auto_due_mode:
        elec_info += f" (রিডিং: {current_reading}, ব্যবহৃত: {used_units} ইউনিট)"
    elif has_elec and auto_due_mode:
        elec_info += " (পূর্বের বকেয়া রিডিং)"

    mode_text = "(বকেয়া বিল পেমেন্ট)" if auto_due_mode else f"({pm} মাসের বিল — পোস্টপেইড)"
    
    receipt_text = f"ভাড়া রসিদ\n\nইউনিট: {room_num}\nমাস: {cm}\n{mode_text}\n\nভাড়া: {total_rent_payable}\nময়লা বিল: {total_garbage_payable}\nবিদ্যুৎ বিল: {elec_info}\n\nমোট বিল: {grand_total}\nজমা/পরিশোধ: {received} টাকা\n"
    if total_due == 0:
        receipt_text += "\n🎉 সম্পূর্ণ বিল পরিশোধিত। কোনো বকেয়া নেই!"
    else:
        receipt_text += f"\nবর্তমান বকেয়া: {total_due} টাকা\n(ভাড়া: {new_rent_due}, ময়লা: {new_garbage_due}, বিদ্যুৎ: {new_elec_due})"

    st.text_area("রসিদ প্রিভিউ", receipt_text, height=250)

    # হিস্ট্রি ডাটা
    history_data = {
        "তারিখ ও সময়": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        "রুম": f"রুম {room_num}",
        "মাসের নাম": cm,
        "মোট বিল": grand_total,
        "জমা": received,
        "বকেয়া": total_due
    }

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 ক্লাউডে আপডেট ও সেভ করুন"):
            save_to_gsheets(df, room_idx, new_rent_due, new_garbage_due, new_elec_due, new_saved_reading, cm, history_data)
            st.toast("সফলভাবে ক্লাউডে সেভ হয়েছে!", icon="✅")
            st.success("ডেটা সেভ করা সম্পন্ন হয়েছে!")
            time.sleep(1.5)
            st.rerun()

    with col2:
        phone   = ensure_phone(row['ফোন নম্বর'])
        wa_url  = f"https://wa.me/{phone}?text={urllib.parse.quote(receipt_text)}"
        st.markdown(f'<a class="wa-link" href="{wa_url}" target="_blank">📲 WhatsApp-এ রসিদ পাঠান</a>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
