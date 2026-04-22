import streamlit as st
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd

if "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

# ===== SHEET CONNECT =====
def get_sheet():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key("1KZ4bnjGkOAjCy_vto-ESkcyl7LessM4IQmfMlSICFC0").sheet1
        return sheet
    except:
        return None

st.set_page_config(page_title="Power AI Admin", page_icon="🔐", layout="wide")

st.markdown("""
<style>
.stApp { background: #0a0a0a; }
* { color: white !important; }
#MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ===== LOGIN =====
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
    st.markdown("<h1 style='text-align:center; color:#7b2fff'>🔐 Admin Login</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        username = st.text_input("Username:")
        password = st.text_input("Password:", type="password")
        
        if st.button("Login", use_container_width=True):
            if username == "dheeraj" and password == "power2024":
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("❌ Wrong Username or Password!")
else:
    # ===== DASHBOARD =====
    col1, col2 = st.columns([6,1])
    with col1:
        st.markdown("<h1>⚡ Power AI — Admin Dashboard</h1>", unsafe_allow_html=True)
    with col2:
        if st.button("🚪 Logout"):
            st.session_state.admin_logged_in = False
            st.rerun()

    st.divider()

    sheet = get_sheet()
    if sheet:
        data = sheet.get_all_records()
        if data:
            df = pd.DataFrame(data)

            # ===== STATS =====
            col1, col2, col3 = st.columns(3)
            col1.metric("📊 Total Sawaal", len(df))
            col2.metric("👥 Sessions", df["Session ID"].nunique())
            col3.metric("📅 Aaj ke Sawaal", len(df[df["Timestamp"].str.startswith(datetime.now().strftime("%Y-%m-%d"))]))

            st.divider()

            # ===== SEARCH =====
            search = st.text_input("🔍 Search karo:")
            if search:
                df = df[df["User Question"].str.contains(search, case=False, na=False)]

            # ===== TABLE =====
            st.dataframe(
                df,
                use_container_width=True,
                column_config={
                    "Timestamp": "🕐 Time",
                    "User Question": "❓ Sawaal",
                    "Bot Answer": "🤖 Jawab",
                    "Session ID": "👤 User"
                }
            )

            # ===== DOWNLOAD =====
            csv = df.to_csv(index=False)
            st.download_button("⬇️ CSV Download Karo", csv, "power_ai_data.csv", "text/csv")
        else:
            st.info("Abhi koi data nahi hai!")
    else:
        st.error("Sheet connect nahi hui!")