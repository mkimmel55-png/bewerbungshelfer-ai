"""Streamlit-Oberfläche für Bewerbungshelfer AI."""

import streamlit as st

from app import (
    build_letter,
    build_summary,
    calculate_match_rate,
    compare_requirements,
    extract_resume_profile,
    extract_resume_text,
    split_items,
)


st.set_page_config(
    page_title="Bewerbungshelfer AI",
    page_icon="📝",
    layout="wide",
)

st.markdown("""
<style>
.hero { padding: 1.25rem 1.5rem; border-radius: 1rem; background: linear-gradient(135deg,#173b67,#2b72c7); color: white; margin-bottom: 1rem; }
.hero h1 { margin: 0; font-size: clamp(1.8rem, 4vw, 2.8rem); }
.hero p { margin: .5rem 0 0; opacity: .9; }
.step { color: #2b72c7; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; font-size: .78rem; }
[data-testid="stMetricValue"] { color: #173b67; }
</style>
<div class="hero"><h1>Bewerbungshelfer AI</h1><p>Stellenanzeige verstehen. Profil prüfen. Bewerbung gezielt verbessern.</p></div>
""", unsafe_allow_html=True)
st.caption("Version 0.9.0 · Unterstützung bei der Vorbereitung – keine automatische Einstellungsentscheidung.")
st.info("Datenschutz: Hochgeladene Lebensläufe werden nur während dieser Sitzung verarbeitet und nicht dauerhaft gespeichert. Bitte prüfe alle erkannten Angaben.")

if "resume_text" not in st.session_state:
    st.session_state["resume_text"] = ""
if "resume_profile" not in st.session_state:
    st.session_state["resume_profile"] = {"experience": "", "qualifications": "", "focus": ""}

st.progress(0.25, text="Schritt 1 von 4 · Stellenanzeige")
st.subheader("1. Stellenanzeige")
job_ad = st.text_area(
    "Komplette Stellenanzeige einfügen",
    height=240,
    placeholder="Kopiere hier die vollständige Anzeige hinein. Stellenbezeichnung, Anforderungen, Erfahrung und Schlüsselbegriffe werden daraus erkannt.",
    help="Die automatische Erkennung ist eine Orientierung. Du kannst alle Felder danach bearbeiten.",
)
col_a, col_b = st.columns(2)
with col_a:
    role = st.text_input("Stellenbezeichnung (optional)", placeholder="z. B. Projektmanager (m/w/d)")
with col_b:
    requirements_text = st.text_area("Anforderungen manuell (Alternative)", height=100, placeholder="Eine Anforderung pro Zeile")

if job_ad.strip():
    from web_app import extract_requirements, extract_role
    detected_role = extract_role(job_ad)
    detected_requirements = extract_requirements(job_ad)
    if not role.strip() and detected_role:
        role = detected_role
    if not requirements_text.strip() and detected_requirements:
        requirements_text = detected_requirements
    with st.expander("Erkannte Stelleninformationen prüfen", expanded=True):
        st.caption("Diese Werte werden nur übernommen, wenn du sie im nächsten Schritt bestätigst bzw. bearbeitest.")
        role = st.text_input("Erkannte Stellenbezeichnung", value=role, key="detected_role")
        requirements_text = st.text_area("Erkannte Anforderungen", value=requirements_text, height=160, key="detected_requirements")

st.progress(0.5, text="Schritt 2 von 4 · Lebenslauf")
st.subheader("2. Lebenslauf und persönliche Daten")
uploaded_resume = st.file_uploader("Lebenslauf hochladen", type=["pdf", "docx", "txt"], help="Unterstützt PDF, DOCX und TXT. Die Datei wird nicht dauerhaft gespeichert.")
if uploaded_resume is not None and uploaded_resume.name != st.session_state.get("resume_filename"):
    try:
        resume_text = extract_resume_text(uploaded_resume)
        st.session_state["resume_text"] = resume_text
        st.session_state["resume_profile"] = extract_resume_profile(resume_text)
        st.session_state["resume_filename"] = uploaded_resume.name
        st.success(f"{uploaded_resume.name} wurde gelesen. Bitte die Vorschläge prüfen und korrigieren.")
    except ValueError as exc:
        st.session_state["resume_text"] = ""
        st.session_state["resume_profile"] = {"experience": "", "qualifications": "", "focus": ""}
        st.error(str(exc))

profile = st.session_state["resume_profile"]
with st.expander("Erkannten Lebenslauftext anzeigen", expanded=bool(st.session_state["resume_text"])):
    if st.session_state["resume_text"]:
        st.text_area("Ausgelesener Text", value=st.session_state["resume_text"], height=180, key="resume_text_review")
    else:
        st.caption("Noch kein Lebenslauf hochgeladen. Du kannst die Felder auch manuell ausfüllen.")

experience = st.text_area("Berufserfahrung", value=profile.get("experience", ""), height=120, placeholder="Nur echte Erfahrungen angeben.")
qualifications_text = st.text_area("Qualifikationen, Abschlüsse, Führerscheine und Sprachen", value=profile.get("qualifications", ""), height=120, placeholder="z. B. Ausbildung, Abschluss, Führerscheinklassen, Deutsch B2")
focus = st.text_area("Persönliche Stärken", value=profile.get("focus", ""), height=90, placeholder="z. B. zuverlässige und selbstständige Arbeitsweise")

st.progress(0.75, text="Schritt 3 von 4 · Analyse")
st.subheader("3. Analyse")
st.caption("Die Angaben werden konservativ verglichen. Nicht belegte Qualifikationen werden nicht ergänzt.")
submitted = st.button("Bewerbung analysieren", type="primary", use_container_width=True)

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
        matched, missing = compare_requirements(requirements, qualifications, experience)
        match_rate = calculate_match_rate(requirements, matched)

        st.session_state["letter"] = build_letter(
            role, experience, qualifications, focus, matched
        )

        st.progress(1.0, text="Schritt 4 von 4 · Ergebnis")
        st.subheader("4. Ergebnis")
        st.metric("Trefferquote", f"{match_rate} %", help="Gewichtete Orientierung anhand der erkannten Anforderungen; kein Einstellungsurteil.")

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

        st.subheader("Verbesserungsvorschläge")
        if missing:
            st.warning("Prüfe, ob du zu den fehlenden Anforderungen echte Nachweise oder konkrete Beispiele ergänzen kannst. Erfinde keine Angaben.")
        else:
            st.success("Alle erkannten Anforderungen haben mindestens eine passende Angabe im Profil.")

        st.subheader("Anschreiben-Entwurf")
        st.text_area("Entwurf", value=st.session_state["letter"], height=320)
        st.download_button(
            "Anschreiben als TXT herunterladen",
            data=st.session_state["letter"],
            file_name="anschreiben.txt",
            mime="text/plain",
        )
