import streamlit as st
import pandas as pd
from datetime import date
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# ---------------- CONFIG ----------------
SENDGRID_API_KEY = "PASTE_YOUR_API_KEY_HERE"
FROM_EMAIL = "verified_sender@yourdomain.com"

# ---------------- EMAIL FUNCTION ----------------
def send_email(to_email, subject, content):
    try:
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            plain_text_content=content
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
    except Exception as e:
        st.error("Email failed")

# ---------------- SESSION INIT ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "email" not in st.session_state:
    st.session_state.email = ""

if "items" not in st.session_state:
    st.session_state.items = pd.DataFrame(
        columns=["Item", "Quantity", "Unit", "Expiry Date"]
    )

# ---------------- LOGIN PAGE ----------------
if not st.session_state.logged_in:
    st.title("🔐 FreshMate Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if email and password:
            st.session_state.logged_in = True
            st.session_state.email = email

            send_email(
                email,
                "FreshMate Login Successful",
                "You have successfully logged in to FreshMate."
            )

            st.success("Login successful! Email sent 📧")
        else:
            st.warning("Please enter email and password")

# ---------------- MAIN APP ----------------
else:
    st.title("🥗 FreshMate – Fridge Manager")
    st.write(f"**Logged in as:** {st.session_state.email}")

    st.subheader("➕ Add Item")
    item = st.text_input("Item name")
    qty = st.number_input("Quantity", min_value=1)
    unit = st.selectbox("Unit", ["kg", "litres", "pieces"])
    expiry = st.date_input("Expiry Date")

    if st.button("Add Item"):
        new_row = {
            "Item": item,
            "Quantity": qty,
            "Unit": unit,
            "Expiry Date": expiry
        }
        st.session_state.items = pd.concat(
            [st.session_state.items, pd.DataFrame([new_row])],
            ignore_index=True
        )
        st.success("Item added")

    # ---------------- DISPLAY ITEMS ----------------
    st.subheader("📋 Inventory")
    if not st.session_state.items.empty:
        st.dataframe(st.session_state.items)

        # ---------------- REMOVE ITEM ----------------
        remove_item = st.selectbox(
            "Remove item",
            st.session_state.items["Item"]
        )

        if st.button("Remove Selected Item"):
            st.session_state.items = st.session_state.items[
                st.session_state.items["Item"] != remove_item
            ]
            st.success("Item removed")

        # ---------------- EXPIRY CHECK ----------------
        today = date.today()
        expired_items = st.session_state.items[
            st.session_state.items["Expiry Date"] < today
        ]

        if not expired_items.empty:
            for _, row in expired_items.iterrows():
                send_email(
                    st.session_state.email,
                    "⚠ FreshMate Expiry Alert",
                    f"{row['Item']} has expired. Please use or discard it."
                )
            st.warning("Expiry alert sent to your email!")

    else:
        st.info("No items added yet")

    # ---------------- LOGOUT ----------------
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.email = ""
        st.session_state.items = pd.DataFrame(
            columns=["Item", "Quantity", "Unit", "Expiry Date"]
        )
        st.experimental_rerun()
