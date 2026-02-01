import streamlit as st
import pandas as pd
from datetime import date
import smtplib
from email.message import EmailMessage
import os

# ---------------- CONFIG ----------------
DATA_FILE = "inventory.csv"

st.set_page_config(
    page_title="FreshMate – Smart Groceries Tracker",
    layout="centered"
)

# ---------------- EMAIL FUNCTION ----------------
def send_email(sender, app_password, receiver, subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender, app_password)
    server.send_message(msg)
    server.quit()

# ---------------- DATA FUNCTIONS ----------------
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)

        # Auto add missing columns
        for col in ["PreAlertSent", "AlertSent"]:
            if col not in df.columns:
                df[col] = False

        return df

    return pd.DataFrame(
        columns=[
            "Username", "Item", "Quantity",
            "Unit", "Expiry", "PreAlertSent", "AlertSent"
        ]
    )

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ==================================================
# 🔐 LOGIN PAGE
# ==================================================
if not st.session_state.logged_in:
    st.markdown("## 🥗 FreshMate – Smart Fridge Tracker")
    st.markdown("### 🔐 Login")

    username = st.text_input("👤 Username")
    email = st.text_input("📧 Email Address")
    app_password = st.text_input("🔑 Gmail App Password", type="password")

    if st.button("Login", use_container_width=True):
        if not username or not email or not app_password:
            st.warning("Please fill all fields")
        else:
            try:
                send_email(
                    email,
                    app_password,
                    email,
                    "FreshMate Login Successful",
                    f"Hello {username},\n\nYou have logged into FreshMate successfully."
                )

                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.email = email
                st.session_state.password = app_password

                st.success("Login successful 📩")
                st.rerun()

            except:
                st.error("❌ Invalid Gmail App Password")

    st.stop()

# ==================================================
# 🏠 MAIN APP
# ==================================================
st.success(f"Welcome {st.session_state.username} 👋")
st.caption(f"Logged in as: {st.session_state.email}")

df = load_data()

# ---------------- ADD ITEM ----------------
st.subheader("➕ Add Item")

item = st.text_input("Item Name")
quantity = st.number_input("Quantity", min_value=1, step=1)
unit = st.selectbox("Unit", ["kg", "g", "litre", "ml", "pack", "pieces"])
expiry = st.date_input("Expiry Date")

if st.button("Add Item"):
    if item:
        new_row = {
            "Username": st.session_state.username,
            "Item": item,
            "Quantity": quantity,
            "Unit": unit,
            "Expiry": expiry,
            "PreAlertSent": False,
            "AlertSent": False
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success("Item added successfully ✅")
    else:
        st.warning("Item name is required")

# ---------------- ALERT LOGIC ----------------
today = date.today()
user_df = df[df["Username"] == st.session_state.username]

for idx, row in user_df.iterrows():
    expiry_date = pd.to_datetime(row["Expiry"]).date()
    days_left = (expiry_date - today).days

    # ⚠️ 5 DAYS BEFORE ALERT
    if 0 < days_left <= 3 and not row["PreAlertSent"]:
        try:
            send_email(
                st.session_state.email,
                st.session_state.password,
                st.session_state.email,
                "⏳ FreshMate – Expiry Approaching",
                f"""
Hello {st.session_state.username},

Your item "{row['Item']}" will expire in {days_left} day(s).
Expiry Date: {row['Expiry']}

Please plan to use it soon.

– FreshMate
"""
            )
            df.loc[idx, "PreAlertSent"] = True
        except:
            pass

    # ❌ EXPIRED ALERT
    if expiry_date <= today and not row["AlertSent"]:
        try:
            send_email(
                st.session_state.email,
                st.session_state.password,
                st.session_state.email,
                "⚠️ FreshMate – Item Expired",
                f"""
Hello {st.session_state.username},

Your item "{row['Item']}" has expired on {row['Expiry']}.

Please discard it if unused.

– FreshMate
"""
            )
            df.loc[idx, "AlertSent"] = True
        except:
            pass

save_data(df)

# ---------------- REMOVE ITEM ----------------
st.subheader("🗑 Remove Item")

items = user_df["Item"].tolist()
remove_item = st.selectbox("Select item", [""] + items)

if st.button("Remove"):
    if remove_item:
        df = df[~(
            (df["Item"] == remove_item) &
            (df["Username"] == st.session_state.username)
        )]
        save_data(df)
        st.success("Item removed 🗑")

# ---------------- DISPLAY ITEMS ----------------
st.subheader("📋 Your Items")
st.dataframe(
    user_df.sort_values("Expiry"),
    use_container_width=True
)
