import streamlit as st
import pandas as pd
from datetime import date, datetime
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
    return pd.DataFrame(columns=["User", "Item", "Quantity", "Unit", "Expiry"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# ================= SESSION INIT =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

st.set_page_config(page_title="FreshMate", layout="centered")
st.title("🥗 FreshMate – Smart Groceries Tracker")

# ================= LOGIN PAGE =================
if not st.session_state.logged_in:
    st.subheader("🔐 Login")

    username = st.text_input("👤 User Name")
    email = st.text_input("📧 Email Address")
    app_password = st.text_input("🔑 Gmail App Password", type="password")

    if st.button("Login"):
        if username and email and app_password:
            try:
                send_email(
                    email,
                    app_password,
                    email,
                    "FreshMate Login Successful",
                    f"Hi {username},\n\nYou have successfully logged in to FreshMate."
                )

                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.email = email
                st.session_state.password = app_password

                st.success("Login successful! Email sent 📩")

            except:
                st.error("Login failed ❌ Check email or app password")
        else:
            st.warning("Please fill all fields")

    st.stop()

# ================= MAIN APP =================
st.success(f"Welcome {st.session_state.username} 👋")
st.write(f"Logged in as: **{st.session_state.email}**")

df = load_data()

# ================= ADD ITEM =================
st.subheader("➕ Add Grocery Item")

item = st.text_input("Item Name")

qty = st.number_input("Quantity", min_value=1, step=1)

unit = st.selectbox(
    "Unit",
    ["kg", "g", "litre", "ml", "pack", "pieces"]
)

expiry = st.date_input("Expiry Date")

if st.button("Add Item"):
    if item:
        df.loc[len(df)] = [
            st.session_state.username,
            item,
            qty,
            unit,
            expiry
        ]
        save_data(df)
        st.success("Item added successfully ✅")
    else:
        st.warning("Item name is required")

# ================= EXPIRY ALERT =================
today = date.today()

for _, row in df.iterrows():
    exp = datetime.strptime(str(row["Expiry"]), "%Y-%m-%d").date()
    if exp <= today and row["User"] == st.session_state.username:
        try:
            send_email(
                st.session_state.email,
                st.session_state.password,
                st.session_state.email,
                "⚠️ FreshMate Expiry Alert",
                f"""
Hello {st.session_state.username},

Your item "{row['Item']}" ({row['Quantity']} {row['Unit']})
expired on {row['Expiry']}.

Please use or discard it.

– FreshMate
"""
            )
        except:
            pass

# ================= REMOVE ITEM =================
st.subheader("🗑 Remove Item")

user_items = df[df["User"] == st.session_state.username]["Item"].tolist()

remove_item = st.selectbox("Select item to remove", [""] + user_items)

if st.button("Remove"):
    if remove_item:
        df = df[~((df["Item"] == remove_item) & (df["User"] == st.session_state.username))]
        save_data(df)
        st.success("Item removed 🗑")

# ================= DISPLAY ITEMS =================
st.subheader("📋 Your Stored Items")

user_df = df[df["User"] == st.session_state.username]
st.dataframe(user_df, use_container_width=True)
