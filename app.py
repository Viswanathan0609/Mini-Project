import streamlit as st
import pandas as pd
from datetime import date, timedelta
import smtplib
from email.message import EmailMessage
import os

# ==================================================
# 🔐 CREATOR EMAIL CONFIG (ONLY CREATOR)
# ==================================================
CREATOR_EMAIL = "yourgmail@gmail.com"          # creator email
CREATOR_APP_PASSWORD = "abcdefghijklmnop"     # 16-char app password
DATA_FILE = "inventory.csv"

# ==================================================
# 📧 EMAIL FUNCTION
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
    except Exception as e:
        st.error("❌ Email notification failed")

# ==================================================
# 📦 DATA FUNCTIONS
# ==================================================
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=[
            "Username",
            "UserEmail",
            "Item",
            "Quantity",
            "Unit",
            "Expiry",
            "ReminderSent",
            "ExpiredSent"
        ])
    return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# ==================================================
# 🔑 SESSION INIT
# ==================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

st.set_page_config(page_title="FreshMate", layout="centered")
st.title("🥗 FreshMate")

# ==================================================
# 🔐 LOGIN PAGE (NO PASSWORD FROM USER)
# ==================================================
if not st.session_state.logged_in:
    st.subheader("🔐 Login")

    username = st.text_input("Username")
    email = st.text_input("Email Address")

    if st.button("Login"):
        if username and email:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.email = email

            send_email(
                email,
                "FreshMate Login Successful",
                f"Hello {username},\n\nYou have successfully logged in to FreshMate."
            )

            st.success("Login successful! Email sent 📩")
            st.rerun()
        else:
            st.warning("Please fill all fields")

    st.stop()

# ==================================================
# 🏠 MAIN APP
# ==================================================
st.success(f"Welcome {st.session_state.username}")

df = load_data()

# ==================================================
# ➕ ADD ITEM
# ==================================================
st.subheader("➕ Add Grocery Item")

with st.form("add_item"):
    item = st.text_input("Item Name")
    quantity = st.number_input("Quantity", min_value=0.1)
    unit = st.selectbox("Unit", ["kg", "g", "litre", "ml", "packs", "pieces"])
    expiry = st.date_input("Expiry Date")
    add = st.form_submit_button("Add Item")

    if add:
        if item:
            new_row = {
                "Username": st.session_state.username,
                "UserEmail": st.session_state.email,
                "Item": item,
                "Quantity": quantity,
                "Unit": unit,
                "Expiry": expiry,
                "ReminderSent": False,
                "ExpiredSent": False
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)
            st.success("Item added successfully")
        else:
            st.warning("Item name required")

# ==================================================
# 🔔 EXPIRY NOTIFICATIONS (NO REPEAT)
# ==================================================
today = date.today()

for i, row in df.iterrows():
    if row["UserEmail"] != st.session_state.email:
        continue

    expiry_date = pd.to_datetime(row["Expiry"]).date()
    days_left = (expiry_date - today).days

    # ⏰ 3-day reminder
    if days_left == 3 and not row["ReminderSent"]:
        send_email(
            row["UserEmail"],
            "⏰ FreshMate Reminder",
            f"Your item '{row['Item']}' will expire in 3 days."
        )
        df.at[i, "ReminderSent"] = True

    # ❌ expired alert
    if days_left < 0 and not row["ExpiredSent"]:
        send_email(
            row["UserEmail"],
            "❌ FreshMate Alert",
            f"Your item '{row['Item']}' has expired."
        )
        df.at[i, "ExpiredSent"] = True

save_data(df)

# ==================================================
# 📋 DISPLAY ITEMS
# ==================================================
st.subheader("📋 Your Inventory")

user_df = df[df["UserEmail"] == st.session_state.email]
st.dataframe(user_df[["Item", "Quantity", "Unit", "Expiry"]], use_container_width=True)

# ==================================================
# 🗑 REMOVE ITEM
# ==================================================
st.subheader("🗑 Remove Used Item")

if not user_df.empty:
    remove_item = st.selectbox("Select item", user_df["Item"].tolist())
    if st.button("Remove"):
        df = df[~((df["Item"] == remove_item) &
                  (df["UserEmail"] == st.session_state.email))]
        save_data(df)
        st.success("Item removed")
        st.rerun()
