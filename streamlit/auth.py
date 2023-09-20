from typing import Iterable, Set
from hashlib import sha256

import streamlit as st


@st.cache_data
def get_hashed_password(password: str) -> str:
    return sha256(password.encode("utf-8")).hexdigest()


def check_authentication():
    """Returns `True` if the user had a correct password."""

    def logout():
        """Logs out the user from the service by deleting its session data."""
        del st.session_state["password_correct"]
        del st.session_state["username"]

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        # hash of the password
        password_hash: str = get_hashed_password(st.session_state["password"])
        if (
            st.session_state["username"] in st.secrets["credentials"]
            and password_hash == st.secrets["credentials"][st.session_state["username"]]
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show inputs for username + password.
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Il nome utente o la password non sono corretti.")
        return False
    else:
        # Password correct.
        with st.sidebar:
            st.info(f"Utente corrente: **{st.session_state['username']}**")
            st.button("Logout", on_click=logout)
            st.divider()
        st.session_state["username"] = st.session_state["username"]
        return True


@st.cache_data
def to_set(iterable: Iterable[str]) -> Set[str]:
    """Converts an iterable (a user role list) to set."""
    return set(iterable)


def check_roles(roles: Iterable[str]) -> bool:
    """Returns `True` if the user's roles are between the ones neeeded."""
    roles: Set[str] = to_set(roles)
    user_roles: Set[str] = to_set(st.secrets["roles"][st.session_state["username"]])
    if len(roles & user_roles) == 0:
        st.error("😕 Non hai i permessi necessari per accedere a questa pagina.")
        st.session_state["username"] = st.session_state["username"]
        return False
    return True
