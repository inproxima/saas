from dotenv import load_dotenv
import streamlit as st
import os
import stripe
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import requests
import numpy as np

load_dotenv()

def resend_verification(email):
    # Call FastAPI email verification service
    verification_url = os.getenv("VERIFICATION_URL")
    data = {'email': email, 'id':'sting'}
    response = requests.post(verification_url, json=data)
    if response.status_code != 200:
        st.error(f"Failed to resend verification email: {response.text}")
    else:
        st.success("Verification email resent successfully!")


def is_email_subscribed(email):
    # Initialize the Stripe API with the given key
    stripe.api_key = os.getenv("STRIPE_API_KEY")

    # List customers with the given email address
    customers = stripe.Customer.list(email=email)

    for customer in customers:
        # For each customer, list their subscriptions
        subscriptions = stripe.Subscription.list(customer=customer.id)
        
        # If any active subscription is found, return True
        for subscription in subscriptions:
            if subscription['status'] == 'active':
                return True

    # If no active subscriptions found, return False
    print(f"No active subscriptions found for {email}")
    return False

def reset_password():
    if st.session_state['authentication_status']:
        try:
            if st.session_state['authenticator'].reset_password(st.session_state['username'], 'Reset password'):
                st.success('Password modified successfully')
        except Exception as e:
            st.error(e)

def send_email(subject, message, to_address):
    # Your send_email logic, unchanged from before
    subject = "Email varificaiton"
    from_address = 'inproxima@gmail.com'
    password = os.getenv("YOUR_EMAIL_PASS")
    msg = MIMEMultipart()
    msg['From'] = "Soroush's SaaS - Email verification <" + from_address + ">"
    msg['To'] = to_address
    msg['Subject'] = subject
    html_message = (MIMEText(message, 'html'))
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(from_address, password)
        server.sendmail(from_address, to_address, html_message.as_string())


def forgot_username():
    try:
        username_forgot_username, email_forgot_username = st.session_state['authenticator'].forgot_username('Forgot username')
        if username_forgot_username:
            subject = 'Your Username'
            message = f'Your username is: {username_forgot_username}'
            send_email(subject, message, email_forgot_username)
            st.success('Username sent securely')
        else:
            st.error('Email not found. Register below.')
    except Exception as e:
        st.error(e)

def forgot_password():
    try:
        username_forgot_pw, email_forgot_password, random_password = st.session_state['authenticator'].forgot_password('Forgot password')
        if username_forgot_pw:
            subject = 'Your new Password'
            message = f'Your new  password is: {random_password}. Please login and reset your password.'
            send_email(subject, message, email_forgot_password)
            st.success('New password sent securely')
        else:
            st.error('Username not found. Register below.')
    except Exception as e:
        st.error(e)


def register_new_user():
    try:
        if st.session_state['authenticator'].register_user('Register user', preauthorization=False):
            st.success('Great! Now please complete registration by confirming your email address. Then login above!')
    except Exception as e:
        st.error(e)
