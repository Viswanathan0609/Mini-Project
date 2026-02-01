import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import smtplib
from email.message import EmailMessage
import os

DATA_FILE = "inventory.csv"

# ================= EMAIL FUNCTION =================
def send_email(sender, password, receiver, subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender, password)
    server.send_message(msg)
    server.quit()

# ================= DATA FUNCTIONS =================
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    # Added 'AlertSent' column to track if notification was already fired
    return pd.DataFrame(columns=["Item", "Quantity", "Expiry", "AlertSent"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# ================= SESSION INIT =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

st.set_page_config(page_title="FreshMate Creator", layout="centered")
st.title("🥗 FreshMate: Admin Panel")

# ================= CREATOR LOGIN =================
if not st.session_state.logged_in:
    st.subheader("🔐 Creator Login")
    
    creator_name = st.text_input("👤 Creator Name")
    email = st.text_input("📧 Gmail Address")
    app_password = st.text_input("🔑 Gmail App Password", type="password")

    if st.button("Login"):
        if email and app_password:
            try:
                # Test connection and send login confirmation
                send_email(email, app_password, email, "FreshMate System Active", f"Hello {creator_name}, your inventory system is now online.")
                st.session_state.logged_in = True
                st.session_state.email = email
                st.session_state.password = app_password
                st.session_state.name = creator_name
                st.rerun()
            except Exception:
                st.error("Login failed ❌ Please check your Gmail App Password settings.")
        else:
            st.warning("Please fill all fields")
    st.stop()

# ================= MAIN APP =================
st.success(f"Welcome, {st.session_state.name} | System Active")
df = load_data()

# ================= ADD ITEM =================
st.subheader("➕ Add Grocery Item")
c1, c2 = st.columns(2)
with c1:
    item = st.text_input("Item Name")
    quantity = st.text_input("Quantity")
with c2:
    expiry = st.date_input("Expiry Date")

if st.button("Add Item"):
    if item and quantity:
        # Default AlertSent to 'No'
        new_data = pd.DataFrame([[item, quantity, str(expiry), "No"]], columns=df.columns)
        df = pd.concat([df, new_data], ignore_index=True)
        save_data(df)
        st.success(f"{item} added to inventory!")
        st.rerun()

# ================= AUTOMATED 5-DAY ALERT LOGIC =================
today = date.today()
alert_date = today + timedelta(days=5)

for index, row in df.iterrows():
    item_expiry = datetime.strptime(str(row["Expiry"]), "%Y-%m-%d").date()
    
    # Condition: Exactly 5 days before expiry AND notification hasn't been sent yet
    if item_expiry == alert_date and row["AlertSent"] == "No":
        try:
            subject = f"🔔 Expiry Alert: {row['Item']}"
            body = f"Reminder: Your {row['Item']} ({row['Quantity']}) expires in 5 days ({row['Expiry']})."
            
            send_email(st.session_state.email, st.session_state.password, st.session_state.email, subject, body)
            
            # Update dataframe so it doesn't send again
            df.at[index, "AlertSent"] = "Yes"
            save_data(df)
            st.info(f"Notification sent for {row['Item']}")
        except Exception as e:
            st.error(f"Failed to send alert for {row['Item']}")

# ================= REMOVE ITEM =================
st.subheader("🗑 Remove Item")
if not df.empty:
    remove_selection = st.selectbox("Select item to remove", ["Select..."] + df["Item"].tolist())
    if st.button("Confirm Removal"):
        if remove_selection != "Select...":
            df = df[df["Item"] != remove_selection]
            save_data(df)
            st.success("Item removed.")
            st.rerun()

# ================= DISPLAY =================
st.subheader("📋 Current Stock")
st.dataframe(df, use_container_width=True)

if st.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()
