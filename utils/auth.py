"""
Authentication utilities for Tastytrade API
Handles OAuth token exchange and dxFeed streamer token retrieval
"""
import os
import sys
import json
import time
import requests


# Token file paths
TOKEN_FILE = "tasty_token.json"
STREAMER_TOKEN_FILE = "streamer_token.json"



import streamlit as st

def load_credentials():
    try:
        return {
            "client_id": st.secrets["CLIENT_ID"],
            "client_secret": st.secrets["CLIENT_SECRET"],
            "refresh_token": st.secrets["REFRESH_TOKEN"],
        }
    except KeyError:
        raise ValueError(
            "Missing required secrets. Please set CLIENT_ID, CLIENT_SECRET, and REFRESH_TOKEN in Streamlit Cloud Secrets."
        )



def get_access_token(force_refresh=False):

    if not force_refresh and "access_token_data" in st.session_state:
        token_data = st.session_state.access_token_data
        expires_at = token_data["expires_at"]

        if expires_at > time.time() + 60:
            return token_data["access_token"]

    credentials = load_credentials()

    data = {
        "grant_type": "refresh_token",
        "refresh_token": credentials["refresh_token"],
        "client_id": credentials["client_id"],
        "client_secret": credentials["client_secret"],
    }

    response = requests.post(
        "https://api.tastytrade.com/oauth/token",
        data=data
    )

    if response.status_code != 200:
        raise Exception(f"Token error: {response.text}")

    token_response = response.json()
    access_token = token_response["access_token"]
    expires_in = token_response.get("expires_in", 900)

    st.session_state.access_token_data = {
        "access_token": access_token,
        "expires_at": time.time() + expires_in,
    }

    return access_token


def get_streamer_token(access_token=None, force_refresh=False):

    if not force_refresh and "streamer_token_data" in st.session_state:
        token_data = st.session_state.streamer_token_data
        if token_data["expires_at"] > time.time() + 300:
            return token_data["token"]

    if access_token is None:
        access_token = get_access_token()

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(
        "https://api.tastyworks.com/api-quote-tokens",
        headers=headers
    )

    if response.status_code != 200:
        raise Exception(f"Streamer token error: {response.text}")

    result = response.json()
    streamer_token = result["data"]["token"]

    st.session_state.streamer_token_data = {
        "token": streamer_token,
        "expires_at": time.time() + (20 * 3600)
    }

    return streamer_token



def ensure_streamer_token():
    """
    Ensure we have a valid streamer token with automatic expiration checking.
    This is the main function used by the dashboard.

    Returns:
        str: dxFeed streamer token (always valid)
    """
    # get_streamer_token now handles caching and expiration checking automatically
    return get_streamer_token()


if __name__ == "__main__":
    """Test authentication flow"""
    print("Testing authentication flow...\n")

    # Test loading credentials
    try:
        creds = load_credentials()
        print(f"✅ Credentials loaded successfully\n")
    except Exception as e:
        print(f"❌ Error loading credentials: {e}\n")
        exit(1)

    # Test getting access token
    try:
        access_token = get_access_token()
        print(f"✅ Access token obtained successfully\n")
    except Exception as e:
        print(f"❌ Error getting access token: {e}\n")
        exit(1)

    # Test getting streamer token
    try:
        streamer_token = get_streamer_token(access_token)
        print(f"✅ Streamer token obtained successfully\n")
    except Exception as e:
        print(f"❌ Error getting streamer token: {e}\n")
        exit(1)

    print("✅ All authentication tests passed!")
