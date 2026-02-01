import streamlit as st
import pandas as pd
import os
import smtplib
from email.message import EmailMessage
from datetime import date, timedelta

# =============================
# CREATOR EMAIL CONFIG
# =============================
SENDER_EMAIL = "yourgmail@gmail.com"        # 👈 creator gmail
APP_PASSWORD = "abcdefghijklmnop"           # 👈 16-char app password
DATA_FILE = "inventory.csv"

# =============================
# EMAIL FUNCTION
# =============================
def send_email(to_email, subject, body):
    try:
        msg = EmailMessage()
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        st.error("Email sending failed")

# =============================
# DATA HANDLING
# =============================
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=[
            "Username", "UserEmail",
            "Item", "Quantity", "Unit", "Expiry",
            "ReminderSent", "ExpiredSent"
        ])
    return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# =============================
# SESSION
# =============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# =============================
# LOGIN PAGE
# =============================
if not st.session_state.logged_in:
    st.title("🔐 FreshMate Login")

    username = st.text_input("Username")
    user_email = st.text_input("Email Address")

    if st.button("Login"):
        if username and user_email:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.user_email = user_email
            st.success("Login successful")
            st.rerun()
        else:
            st.warning("All fields required")

    st.stop()

# =============================
# MAIN APP
# =============================
st.title("🥗 FreshMate – Fridge Inventory Tracker")
st.write(f"Welcome **{st.session_state.username}**")

df = load_data()

# =============================
# ADD ITEM
# =============================
st.subheader("➕ Add Item")
with st.form("add_item"):
    item = st.text_input("Item Name")
    qty = st.number_input("Quantity", min_value=0.1)
    unit = st.selectbox("Unit", ["kg", "g", "litre", "ml", "packs", "pieces"])
    expiry = st.date_input("Expiry Date")
    add = st.form_submit_button("Add")

    if add:
        new_row = {
            "Username": st.session_state.username,
            "UserEmail": st.session_state.user_email,
            "Item": item,
            "Quantity": qty,
            "Unit": unit,
            "Expiry": expiry,
            "ReminderSent": False,
            "ExpiredSent": False
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success("Item added")

# =============================
# NOTIFICATION LOGIC (NON-REPEATING)
# =============================
today = date.today()

for i, row in df.iterrows():
    if row["UserEmail"] != st.session_state.user_email:
        continue

    expiry_date = pd.to_datetime(row["Expiry"]).date()
    days_left = (expiry_date - today).days

    # 3 DAY REMINDER
    if days_left == 3 and not row["ReminderSent"]:
        send_email(
            row["UserEmail"],
            "⏰ FreshMate Reminder",
            f"Your item '{row['Item']}' will expire in 3 days."
        )
        df.at[i, "ReminderSent"] = True

    # EXPIRED ALERT
    if days_left < 0 and not row["ExpiredSent"]:
        send_email(
            row["UserEmail"],
            "❌ FreshMate Alert",
            f"Your item '{row['Item']}' has expired."
        )
        df.at[i, "ExpiredSent"] = True

save_data(df)

# =============================
# DISPLAY INVENTORY
# =============================
st.subheader("📋 Your Items")
user_df = df[df["UserEmail"] == st.session_state.user_email]

st.dataframe(user_df[["Item", "Quantity", "Unit", "Expiry"]])

# =============================
# REMOVE ITEM
# =============================
st.subheader("✅ Remove Used Item")
remove_item = st.selectbox("Select item", user_df["Item"].tolist())

if st.button("Remove"):
    df = df[~((df["Item"] == remove_item) &
              (df["UserEmail"] == st.session_state.user_email))]
    save_data(df)
    st.success("Item removed")
    st.rerun()
