"""Streamlit-Oberfläche für Bewerbungshelfer AI."""

import streamlit as st

from app import (
    build_letter,
    build_summary,
    calculate_match_rate,
    compare_requirements,
    split_items,
)


st.set_page_config(
    page_title="Bewerbungshelfer AI",
    page_icon="📝",
    layout="centered",
)

st.title("Bewerbungshelfer AI")
st.caption("Version 0.5.1 · Die Anwendung erfindet keine Qualifikationen.")

with st.form("application_form"):
    role = st.text_input("Stellenbezeichnung")
    requirements_text = st.text_area(
        "Stellenanforderungen",
        help="Mehrere Anforderungen mit Komma oder Semikolon trennen.",
    )
    experience = st.text_area("Passende Berufserfahrung")
    qualifications_text = st.text_area(
        "Vorhandene Qualifikationen",
        help="Mehrere Qualifikationen mit Komma oder Semikolon trennen.",
    )
    focus = st.text_area("Was soll besonders hervorgehoben werden?")
    submitted = st.form_submit_button("Analysieren")

if submitted:
    role = role.strip()
    requirements_text = requirements_text.strip()
    qualifications_text = qualifications_text.strip()
    experience = experience.strip()
    focus = focus.strip()

    if not role:
        st.error("Bitte eine Stellenbezeichnung eingeben.")
    elif not requirements_text:
        st.error("Bitte mindestens eine Stellenanforderung eingeben.")
    elif not qualifications_text:
        st.error("Bitte mindestens eine vorhandene Qualifikation eingeben.")
    else:
        requirements = split_items(requirements_text)
        qualifications = split_items(qualifications_text)
        matched, missing = compare_requirements(requirements, qualifications)
        match_rate = calculate_match_rate(requirements, matched)

        st.session_state["letter"] = build_letter(
            role, experience, qualifications, focus, matched
        )

        st.subheader("Trefferquote")
        st.progress(match_rate / 100, text=f"{match_rate} %")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Passende Anforderungen**")
            if matched:
                for item in matched:
                    st.success(item)
            else:
                st.info("Keine eindeutigen Treffer")
        with col2:
            st.markdown("**Fehlende oder nicht erkannte Anforderungen**")
            if missing:
                for item in missing:
                    st.warning(item)
            else:
                st.success("Keine")

        with st.expander("Zusammenfassung"):
            st.text(build_summary(role, requirements, qualifications, matched, missing))

        st.subheader("Anschreiben-Entwurf")
        st.text_area("Entwurf", value=st.session_state["letter"], height=320)
        st.download_button(
            "Anschreiben als TXT herunterladen",
            data=st.session_state["letter"],
            file_name="anschreiben.txt",
            mime="text/plain",
        )
