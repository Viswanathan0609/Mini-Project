import streamlit as st
import pandas as pd
from datetime import datetime, date
import smtplib
from email.message import EmailMessage
import os

# ---------------- CONFIG ----------------
SENDER_EMAIL = "yourgmail@gmail.com"       # creator email
APP_PASSWORD = "your_16_char_app_password" # app password
DATA_FILE = "inventory.csv"

# ---------------- EMAIL FUNCTION ----------------
def send_email(to_email, subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(SENDER_EMAIL, APP_PASSWORD)
    server.send_message(msg)
    server.quit()

# ---------------- DATA FUNCTIONS ----------------
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["Item", "Quantity", "Expiry"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

st.title("🥗 FreshMate")

# ---------------- LOGIN PAGE ----------------
if not st.session_state.logged_in:
    st.subheader("🔐 Login")

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

            st.success("Login successful! Email sent 📧")
        else:
            st.warning("Please enter email")

    st.stop()

# ---------------- MAIN APP ----------------
st.success(f"Welcome {st.session_state.user_email}")

df = load_data()

# ---------------- ADD ITEM ----------------
st.subheader("➕ Add Item")

item = st.text_input("Item Name")
quantity = st.text_input("Quantity (eg: 1 kg, 2 litre)")
expiry = st.date_input("Expiry Date")

if st.button("Add Item"):
    df.loc[len(df)] = [item, quantity, expiry]
    save_data(df)
    st.success("Item added")

# ---------------- EXPIRY CHECK ----------------
today = date.today()

for _, row in df.iterrows():
    exp_date = datetime.strptime(str(row["Expiry"]), "%Y-%m-%d").date()
    if exp_date <= today:
        send_email(
            st.session_state.user_email,
            "FreshMate Expiry Alert",
            f"{row['Item']} has expired on {row['Expiry']}"
        )

# ---------------- REMOVE ITEM ----------------
st.subheader("🗑 Remove Used Items")

remove_item = st.selectbox("Select item to remove", [""] + df["Item"].tolist())

if st.button("Remove Item") and remove_item:
    df = df[df["Item"] != remove_item]
    save_data(df)
    st.success("Item removed")

# ---------------- DISPLAY ----------------
st.subheader("📋 Current Inventory")
st.dataframe(df)
