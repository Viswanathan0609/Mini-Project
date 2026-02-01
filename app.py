import streamlit as st
import pandas as pd
from datetime import date
import smtplib
from email.message import EmailMessage
import os

# ---------------- CONFIG ----------------
DATA_FILE = "inventory.csv"

st.set_page_config(page_title="FreshMate", layout="centered")
st.title("🥗 FreshMate – Smart Fridge Tracker")

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
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["Username", "Item", "Quantity", "Unit", "Expiry"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ---------------- LOGIN PAGE ----------------
if not st.session_state.logged_in:
    st.subheader("🔐 Login")

    username = st.text_input("👤 Username")
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
                    f"Hello {username},\n\nYou have logged into FreshMate successfully."
                )

                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.email = email
                st.session_state.password = app_password

                st.success("Login successful! Email sent 📩")
                st.rerun()

            except Exception as e:
                st.error("❌ Email login failed. Check App Password.")

        else:
            st.warning("Please fill all fields")

    st.stop()

# ---------------- MAIN APP ----------------
st.success(f"Welcome {st.session_state.username} 👋")
st.write(f"Logged in as: **{st.session_state.email}**")

df = load_data()

# ---------------- ADD ITEM ----------------
st.subheader("➕ Add Item")

item = st.text_input("Item Name")
quantity = st.number_input("Quantity", min_value=1, step=1)
unit = st.selectbox("Unit", ["kg", "g", "litre", "ml", "packs", "pieces"])
expiry = st.date_input("Expiry Date")

if st.button("Add Item"):
    if item:
        new_row = {
            "Username": st.session_state.username,
            "Item": item,
            "Quantity": quantity,
            "Unit": unit,
            "Expiry": expiry
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success("Item added successfully ✅")
    else:
        st.warning("Item name is required")

# ---------------- EXPIRY ALERT ----------------
today = date.today()

user_df = df[df["Username"] == st.session_state.username]

for _, row in user_df.iterrows():
    if pd.to_datetime(row["Expiry"]).date() <= today:
        try:
            send_email(
                st.session_state.email,
                st.session_state.password,
                st.session_state.email,
                "⚠️ FreshMate Expiry Alert",
                f"""
Hello {st.session_state.username},

Your item "{row['Item']}" ({row['Quantity']} {row['Unit']})
has expired on {row['Expiry']}.

Please use or discard it.

– FreshMate
"""
            )
        except:
            pass

# ---------------- REMOVE ITEM ----------------
st.subheader("🗑 Remove Item")

items_list = user_df["Item"].tolist()
remove_item = st.selectbox("Select item", [""] + items_list)

if st.button("Remove"):
    if remove_item:
        df = df[~((df["Item"] == remove_item) & (df["Username"] == st.session_state.username))]
        save_data(df)
        st.success("Item removed successfully 🗑")

# ---------------- DISPLAY ITEMS ----------------
st.subheader("📋 Your Items")
st.dataframe(user_df, use_container_width=True)
