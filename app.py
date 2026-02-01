import streamlit as st
import pandas as pd
from datetime import date, datetime
import smtplib
from email.message import EmailMessage
import os

# ================= CREATOR CONFIG =================
SENDER_EMAIL = "yourgmail@gmail.com"          # CREATOR EMAIL
APP_PASSWORD = "YOUR_16_CHAR_APP_PASSWORD"    # CREATOR APP PASSWORD
DATA_FILE = "inventory.csv"

# ================= EMAIL FUNCTION =================
def send_email(receiver, subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(SENDER_EMAIL, APP_PASSWORD)
    server.send_message(msg)
    server.quit()

# ================= DATA HANDLING =================
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["Item", "Quantity", "Expiry"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# ================= SESSION =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

st.set_page_config(page_title="FreshMate", layout="centered")
st.title("🥗 FreshMate")

# ================= LOGIN PAGE =================
if not st.session_state.logged_in:
    st.subheader("📧 Email Login")

    email = st.text_input("Enter your email")

    if st.button("Login"):
        if email:
            st.session_state.logged_in = True
            st.session_state.user_email = email

            send_email(
                email,
                "FreshMate Login Successful",
                "You have successfully logged in to FreshMate."
            )

            st.success("Login successful! Email sent 📬")
        else:
            st.warning("Please enter a valid email")

    st.stop()

# ================= MAIN APP =================
st.success(f"Welcome {st.session_state.user_email}")

df = load_data()

# ================= ADD ITEM =================
st.subheader("➕ Add Item")

item = st.text_input("Item Name")
quantity = st.text_input("Quantity (e.g., 1 kg, 2 packets)")
expiry = st.date_input("Expiry Date")

if st.button("Add Item"):
    if item and quantity:
        df.loc[len(df)] = [item, quantity, expiry]
        save_data(df)
        st.success("Item added successfully")
    else:
        st.warning("Fill all fields")

# ================= EXPIRY NOTIFICATION =================
today = date.today()

for _, row in df.iterrows():
    exp = datetime.strptime(str(row["Expiry"]), "%Y-%m-%d").date()
    if exp <= today:
        send_email(
            st.session_state.user_email,
            "FreshMate Expiry Alert",
            f"⚠️ {row['Item']} expired on {row['Expiry']}.\nPlease use or discard it."
        )

# ================= REMOVE ITEM =================
st.subheader("🗑 Remove Item")

remove_item = st.selectbox(
    "Select item",
    [""] + df["Item"].tolist()
)

if st.button("Remove"):
    if remove_item:
        df = df[df["Item"] != remove_item]
        save_data(df)
        st.success("Item removed")

# ================= DISPLAY =================
st.subheader("📋 Stored Items")
st.dataframe(df, use_container_width=True)
