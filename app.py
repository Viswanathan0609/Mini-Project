import streamlit as st
import pandas as pd
import os
import smtplib
from email.message import EmailMessage
from datetime import date

# ==================================================
# 🔐 CREATOR EMAIL CONFIG (ONLY CREATOR USES THIS)
# ==================================================
CREATOR_EMAIL = "yourgmail@gmail.com"      # 👈 creator Gmail ONLY
CREATOR_APP_PASSWORD = "abcdefghijklmnop" # 👈 16-char App Password ONLY

DATA_FILE = "inventory.csv"

# ==================================================
# 📧 EMAIL FUNCTION (USERS NEVER SEE PASSWORD)
# ==================================================
def send_email(to_email, subject, body):
    try:
        msg = EmailMessage()
        msg["From"] = CREATOR_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(CREATOR_EMAIL, CREATOR_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception:
        st.error("❌ Notification failed")

# ==================================================
# 📦 DATA FUNCTIONS
# ==================================================
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

# ==================================================
# 🔑 SESSION STATE
# ==================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ==================================================
# 🔐 LOGIN PAGE (NO PASSWORD ASKED)
# ==================================================
if not st.session_state.logged_in:
    st.title("🔐 FreshMate Login")

    username = st.text_input("Username")
    user_email = st.text_input("Email Address")

    if st.button("Login"):
        if username and user_email:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.user_email = user_email
            st.success("Login Successful")
            st.rerun()
        else:
            st.warning("All fields are required")

    st.stop()

# ==================================================
# 🏠 MAIN APP
# ==================================================
st.title("🥗 FreshMate – Fridge Inventory & Alerts")
st.write(f"Welcome **{st.session_state.username}**")

df = load_data()

# ==================================================
# ➕ ADD ITEM
# ==================================================
st.subheader("➕ Add Item")

with st.form("add_item"):
    item = st.text_input("Item Name")
    qty = st.number_input("Quantity", min_value=0.1)
    unit = st.selectbox("Unit", ["kg", "g", "litre", "ml", "packs", "pieces"])
    expiry = st.date_input("Expiry Date")
    add = st.form_submit_button("Add Item")

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
        st.success("Item added successfully")

# ==================================================
# 🔔 EMAIL NOTIFICATION LOGIC (NO REPEAT)
# ==================================================
today = date.today()

for i, row in df.iterrows():
    if row["UserEmail"] != st.session_state.user_email:
        continue

    expiry_date = pd.to_datetime(row["Expiry"]).date()
    days_left = (expiry_date - today).days

    # ⏰ 3-DAY REMINDER (ONLY ONCE)
    if days_left == 3 and not row["ReminderSent"]:
        send_email(
            row["UserEmail"],
            "⏰ FreshMate Reminder",
            f"""
Hello {row['Username']},

Your item "{row['Item']}" will expire in 3 days.
Please use it soon to avoid waste.

– FreshMate
"""
        )
        df.at[i, "ReminderSent"] = True

    # ❌ EXPIRED ALERT (ONLY ONCE)
    if days_left < 0 and not row["ExpiredSent"]:
        send_email(
            row["UserEmail"],
            "❌ FreshMate Alert – Expired",
            f"""
Hello {row['Username']},

Your item "{row['Item']}" has expired.
Please discard it.

– FreshMate
"""
        )
        df.at[i, "ExpiredSent"] = True

save_data(df)

# ==================================================
# 📋 DISPLAY INVENTORY
# ==================================================
st.subheader("📋 Your Inventory")

user_df = df[df["UserEmail"] == st.session_state.user_email]
st.dataframe(user_df[["Item", "Quantity", "Unit", "Expiry"]])

# ==================================================
# ❌ REMOVE USED ITEM
# ==================================================
st.subheader("✅ Remove Used Item")

if not user_df.empty:
    remove_item = st.selectbox("Select Item", user_df["Item"].tolist())
    if st.button("Remove Item"):
        df = df[~((df["Item"] == remove_item) &
                  (df["UserEmail"] == st.session_state.user_email))]
        save_data(df)
        st.success("Item removed")
        st.rerun()
