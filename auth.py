"""Supabase-Authentifizierung und Credit-Verwaltung für Bewerbungshelfer AI."""

import streamlit as st
from supabase import Client, create_client


def _get_secret(name: str) -> str:
    try:
        value = st.secrets["supabase"][name]
    except Exception as exc:
        raise RuntimeError(
            "Supabase ist noch nicht konfiguriert. "
            "Bitte URL und anon_key in den Streamlit-Secrets eintragen."
        ) from exc

    if not value:
        raise RuntimeError(
            f"Supabase-Secret '{name}' ist leer."
        )

    return str(value)


def get_supabase() -> Client:
    if "_supabase_client" not in st.session_state:
        st.session_state["_supabase_client"] = create_client(
            _get_secret("url"),
            _get_secret("anon_key"),
        )

    return st.session_state["_supabase_client"]


def is_logged_in() -> bool:
    return bool(
        st.session_state.get("auth_user_id")
    )


def current_user_id() -> str | None:
    return st.session_state.get(
        "auth_user_id"
    )


def current_user_email() -> str | None:
    return st.session_state.get(
        "auth_user_email"
    )


def register(email: str, password: str) -> dict:
    supabase = get_supabase()

    response = supabase.auth.sign_up(
        {
            "email": email.strip().lower(),
            "password": password,
        }
    )

    user = getattr(
        response,
        "user",
        None,
    )

    session = getattr(
        response,
        "session",
        None,
    )

    return {
        "user": user,
        "session": session,
        "needs_email_confirmation": bool(
            user and not session
        ),
    }


def login(email: str, password: str) -> None:
    supabase = get_supabase()

    response = (
        supabase.auth.sign_in_with_password(
            {
                "email": email.strip().lower(),
                "password": password,
            }
        )
    )

    user = getattr(
        response,
        "user",
        None,
    )

    if not user:
        raise RuntimeError(
            "Anmeldung fehlgeschlagen."
        )

    st.session_state[
        "auth_user_id"
    ] = str(user.id)

    st.session_state[
        "auth_user_email"
    ] = str(
        user.email or email
    ).lower()


def logout() -> None:
    try:
        get_supabase().auth.sign_out()
    except Exception:
        pass

    keys_to_remove = [
        "_supabase_client",
        "auth_user_id",
        "auth_user_email",
        "resume_text",
        "resume_profile",
        "resume_filename",
        "letter",
        "analysis_result",
    ]

    for key in keys_to_remove:
        st.session_state.pop(
            key,
            None,
        )


def get_profile() -> dict | None:
    if not is_logged_in():
        return None

    response = (
        get_supabase()
        .table("profiles")
        .select(
            "id,email,plan,credits,analyses_used,created_at"
        )
        .eq(
            "id",
            current_user_id(),
        )
        .single()
        .execute()
    )

    return response.data


def consume_analysis_credit() -> dict:
    if not is_logged_in():
        return {
            "allowed": False,
            "remaining": 0,
            "plan": "free",
        }

    response = (
        get_supabase()
        .rpc(
            "consume_analysis_credit"
        )
        .execute()
    )

    data = response.data

    if isinstance(
        data,
        list,
    ):
        data = (
            data[0]
            if data
            else {}
        )

    if not isinstance(
        data,
        dict,
    ):
        raise RuntimeError(
            "Ungültige Antwort "
            "der Credit-Funktion."
        )

    return {
        "allowed": bool(
            data.get("allowed")
        ),
        "remaining": int(
            data.get("remaining") or 0
        ),
        "plan": str(
            data.get("plan") or "free"
        ),
    }
