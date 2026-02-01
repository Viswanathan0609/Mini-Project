import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import smtplib
from email.message import EmailMessage
import os

# ================= CONFIGURATION (CREATOR SIDE) =================
# In a real app, use st.secrets for these!
CREATOR_EMAIL = "your-email@gmail.com" 
CREATOR_APP_PASSWORD = "your-app-password" 
DATA_FILE = "inventory.csv"

# ================= EMAIL FUNCTION =================
def send_email(receiver, subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = CREATOR_EMAIL
    msg["To"] = receiver

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(CREATOR_EMAIL, CREATOR_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

# ================= DATA FUNCTIONS =================
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["Item", "Quantity", "Expiry", "LastAlertSent"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# ================= SESSION INIT =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

st.set_page_config(page_title="FreshMate", layout="centered")
st.title("🥗 FreshMate")

# ================= USER LOGIN PAGE =================
if not st.session_state.logged_in:
    st.subheader("👋 Welcome to FreshMate")
    user_name = st.text_input("👤 Your Name")
    user_email = st.text_input("📧 Your Email (to receive alerts)")

    if st.button("Start Tracking"):
        if user_name and user_email:
            st.session_state.logged_in = True
            st.session_state.user_email = user_email
            st.session_state.user_name = user_name
            st.rerun()
        else:
            st.warning("Please enter your details to continue.")
    st.stop()

# ================= MAIN APP =================
st.sidebar.write(f"Logged in as: **{st.session_state.user_name}**")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

df = load_data()

# ================= ADD ITEM =================
st.subheader("➕ Add Grocery Item")
col1, col2 = st.columns(2)

with col1:
    item = st.text_input("Item Name")
    quantity = st.text_input("Quantity (e.g., 1 kg)")
with col2:
    expiry = st.date_input("Expiry Date")

if st.button("Add Item"):
    if item and quantity:
        # Add new row with 'None' for LastAlertSent
        new_row = {"Item": item, "Quantity": quantity, "Expiry": str(expiry), "LastAlertSent": "None"}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success(f"{item} added!")
    else:
        st.warning("Please fill all fields")

# ================= EXPIRY ALERT LOGIC (5 Days Before) =================
today = date.today()
alert_threshold = today + timedelta(days=5)

for index, row in df.iterrows():
    exp_date = datetime.strptime(str(row["Expiry"]), "%Y-%m-%d").date()
    
    # Check if today is exactly 5 days before expiry AND we haven't sent an alert yet
    if exp_date == alert_threshold and row["LastAlertSent"] != str(today):
        subject = f"⚠️ FreshMate: {row['Item']} Expires in 5 Days!"
        body = f"Hello {st.session_state.user_name},\n\nYour {row['Item']} ({row['Quantity']}) will expire on {row['Expiry']}. Use it soon!"
        
        if send_email(st.session_state.user_email, subject, body):
            df.at[index, "LastAlertSent"] = str(today)
            save_data(df)

# ================= REMOVE ITEM =================
st.subheader("🗑 Manage Inventory")
if not df.empty:
    remove_item = st.selectbox("Select item to remove", df["Item"].tolist())
    if st.button("Remove Selected"):
        df = df[df["Item"] != remove_item]
        save_data(df)
        st.rerun()
else:
    st.info("Your pantry is empty.")

# ================= DISPLAY ITEMS =================
st.subheader("📋 Current Inventory")
st.table(df[["Item", "Quantity", "Expiry"]])
