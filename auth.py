"""
Sign-in gate for Peace of Mind.

Reads a [users] table from Streamlit secrets:

    [users]
    deedee = "some-long-passphrase"
    sam    = "another-passphrase"

Each user gets their own folder under data/, so signing in as `deedee`
shows only deedee's records. If no [users] table is configured the app
runs unlocked in single-user mode and says so plainly.
"""
import hmac
import streamlit as st

import data_store as ds


def _configured_users() -> dict:
    try:
        users = st.secrets.get("users", None)
    except Exception:
        return {}
    if not users:
        return {}
    try:
        return {str(k): str(v) for k, v in dict(users).items()}
    except Exception:
        return {}


def _check(username: str, password: str, users: dict) -> bool:
    """Constant-time comparison, and never leaks which field was wrong."""
    expected = users.get(username)
    if expected is None:
        # still burn a comparison so a bad username isn't faster than a bad password
        hmac.compare_digest("x" * 12, "y" * 12)
        return False
    return hmac.compare_digest(password, expected)


def login_gate() -> str:
    """
    Returns the signed-in username, or halts the script on the login screen.
    Also points data_store at that user's private folder.
    """
    users = _configured_users()

    # No accounts configured -> unlocked single-user mode.
    if not users:
        ds.set_user("default")
        st.session_state["_unlocked_mode"] = True
        return "default"

    if st.session_state.get("auth_user"):
        ds.set_user(st.session_state["auth_user"])
        return st.session_state["auth_user"]

    st.markdown("### 🕊️ Peace of Mind")
    st.caption("Sign in to see your own records.")

    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")

    if submitted:
        if _check(username.strip(), password, users):
            st.session_state["auth_user"] = username.strip()
            ds.set_user(username.strip())
            st.rerun()
        else:
            st.error("That username and password combination didn't work.")

    st.stop()


def sign_out_button() -> None:
    if st.session_state.get("auth_user"):
        if st.sidebar.button("Sign out"):
            for k in ("auth_user", "chat_history", "vinny_greeted"):
                st.session_state.pop(k, None)
            st.rerun()
