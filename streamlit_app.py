"""Streamlit-Oberfläche für Bewerbungshelfer AI."""

import streamlit as st

from app import (
    build_letter,
    build_summary,
    extract_resume_profile,
    extract_resume_text,
    split_items,
)
from auth import (
    consume_analysis_credit,
    current_user_email,
    get_profile,
    is_logged_in,
    login,
    logout,
    register,
)
from web_app import (
    compare_requirements,
    calculate_match_rate,
    extract_requirements,
    extract_role,
)


st.set_page_config(
    page_title="Bewerbungshelfer AI",
    page_icon="📝",
    layout="wide",
)


st.html(
    """
    <style>
    .block-container {
        max-width: 1150px;
        padding-top: 2rem;
    }

    .hero {
        padding: 2rem;
        border-radius: 1.2rem;
        background: linear-gradient(135deg, #173b67, #2b72c7);
        color: white;
        margin-bottom: 1.5rem;
    }

    .hero h1 {
        margin: 0;
        font-size: clamp(2rem, 5vw, 3.2rem);
    }

    .hero p {
        margin: .7rem 0 0;
        font-size: 1.1rem;
        opacity: .95;
    }

    .card {
        border: 1px solid #e1e5eb;
        border-radius: 1rem;
        padding: 1.25rem;
        background: white;
        min-height: 190px;
    }

    .card h3 {
        margin-top: 0;
    }

    .price-card {
        border: 1px solid #d8e0ea;
        border-radius: 1rem;
        padding: 1.3rem;
        background: white;
        min-height: 250px;
    }

    .price-card h3 {
        margin-top: 0;
    }

    .price {
        font-size: 1.8rem;
        font-weight: 700;
        color: #173b67;
    }

    [data-testid="stMetricValue"] {
        color: #173b67;
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #173b67, #2b72c7);
        border: none;
        color: white;
        border-radius: 0.65rem;
        font-weight: 600;
    }

    div.stButton > button[kind="primary"]:hover {
        background: #173b67;
        color: white;
        border: none;
    }
    </style>
    """
)


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

if "page" not in st.session_state:
    st.session_state["page"] = "Start"

if "resume_text" not in st.session_state:
    st.session_state["resume_text"] = ""

if "resume_profile" not in st.session_state:
    st.session_state["resume_profile"] = {
        "experience": "",
        "qualifications": "",
        "focus": "",
    }


# ---------------------------------------------------------
# HILFSFUNKTIONEN
# ---------------------------------------------------------

def go_to_checker():
    if is_logged_in():
        st.session_state["page"] = "Bewerbung prüfen"
    else:
        st.session_state["page"] = "Konto"


def show_hero(title: str, text: str):
    st.html(
        f"""
        <div class="hero">
            <h1>{title}</h1>
            <p>{text}</p>
        </div>
        """
    )


# ---------------------------------------------------------
# KONTO / LOGIN
# ---------------------------------------------------------

def show_account():

    show_hero(
        "Konto",
        "Anmelden oder kostenlos registrieren und 2 Bewerbungsanalysen erhalten.",
    )

    if is_logged_in():

        st.success(
            f"Angemeldet als {current_user_email()}"
        )

        try:
            profile = get_profile()
        except Exception as exc:
            st.error(
                f"Profil konnte nicht geladen werden: {exc}"
            )
            return

        if profile:
            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Tarif",
                str(
                    profile.get(
                        "plan",
                        "free",
                    )
                ).upper(),
            )

            c2.metric(
                "Verbleibende Analysen",
                profile.get(
                    "credits",
                    0,
                ),
            )

            c3.metric(
                "Bisher genutzt",
                profile.get(
                    "analyses_used",
                    0,
                ),
            )

        if st.button(
            "Zur Bewerbungsprüfung",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["page"] = "Bewerbung prüfen"
            st.rerun()

        if st.button(
            "Abmelden",
            use_container_width=True,
        ):
            logout()
            st.session_state["page"] = "Start"
            st.rerun()

        return


    login_tab, register_tab = st.tabs(
        [
            "Anmelden",
            "Registrieren",
        ]
    )


    with login_tab:

        with st.form(
            "login_form"
        ):

            email = st.text_input(
                "E-Mail-Adresse",
                key="login_email",
            )

            password = st.text_input(
                "Passwort",
                type="password",
                key="login_password",
            )

            submitted = st.form_submit_button(
                "Anmelden",
                type="primary",
                use_container_width=True,
            )


        if submitted:

            if (
                not email.strip()
                or not password
            ):
                st.error(
                    "Bitte E-Mail-Adresse und Passwort eingeben."
                )

            else:
                try:
                    login(
                        email,
                        password,
                    )

                    st.success(
                        "Anmeldung erfolgreich."
                    )

                    st.session_state[
                        "page"
                    ] = "Bewerbung prüfen"

                    st.rerun()

                except Exception as exc:
                    st.error(
                        "Anmeldung fehlgeschlagen. "
                        "Bitte E-Mail-Adresse, Passwort "
                        "und E-Mail-Bestätigung prüfen."
                    )

                    st.caption(
                        str(exc)
                    )


    with register_tab:

        st.info(
            "Neue Konten erhalten einmalig "
            "2 kostenlose vollständige Analysen."
        )

        with st.form(
            "register_form"
        ):

            email = st.text_input(
                "E-Mail-Adresse",
                key="register_email",
            )

            password = st.text_input(
                "Passwort",
                type="password",
                key="register_password",
            )

            password_repeat = st.text_input(
                "Passwort wiederholen",
                type="password",
                key="register_password_repeat",
            )

            privacy_ok = st.checkbox(
                "Ich akzeptiere, dass meine Kontodaten "
                "zur Bereitstellung des Dienstes verarbeitet werden."
            )

            submitted = st.form_submit_button(
                "Kostenlos registrieren",
                type="primary",
                use_container_width=True,
            )


        if submitted:

            if not email.strip():
                st.error(
                    "Bitte eine E-Mail-Adresse eingeben."
                )

            elif len(password) < 8:
                st.error(
                    "Das Passwort muss mindestens "
                    "8 Zeichen lang sein."
                )

            elif password != password_repeat:
                st.error(
                    "Die Passwörter stimmen nicht überein."
                )

            elif not privacy_ok:
                st.error(
                    "Bitte die Datenschutzhinweise bestätigen."
                )

            else:

                try:
                    result = register(
                        email,
                        password,
                    )

                    if result[
                        "needs_email_confirmation"
                    ]:
                        st.success(
                            "Registrierung erfolgreich. "
                            "Bitte öffne jetzt die "
                            "Bestätigungs-E-Mail von Supabase "
                            "und bestätige deine Adresse. "
                            "Danach kannst du dich anmelden."
                        )

                    else:
                        st.success(
                            "Registrierung erfolgreich. "
                            "Du kannst dich jetzt anmelden."
                        )

                except Exception as exc:
                    st.error(
                        f"Registrierung fehlgeschlagen: {exc}"
                    )


# ---------------------------------------------------------
# STARTSEITE
# ---------------------------------------------------------

def show_start():

    show_hero(
        "Bewerbungshelfer AI",
        "Prüfe, wie gut dein Profil zu einer Stellenanzeige passt "
        "und verbessere gezielt die entscheidenden Punkte.",
    )

    st.subheader(
        "So funktioniert es"
    )

    col1, col2, col3 = st.columns(3)


    with col1:
        st.html(
            """
            <div class="card">
                <h3>1. Stellenanzeige einfügen</h3>
                <p>
                    Die App erkennt Stellenbezeichnung,
                    Anforderungen und wichtige Schlüsselbegriffe.
                </p>
            </div>
            """
        )


    with col2:
        st.html(
            """
            <div class="card">
                <h3>2. Lebenslauf prüfen</h3>
                <p>
                    Lade PDF, DOCX oder TXT hoch
                    oder trage deine Erfahrungen manuell ein.
                </p>
            </div>
            """
        )


    with col3:
        st.html(
            """
            <div class="card">
                <h3>3. Ergebnis erhalten</h3>
                <p>
                    Du bekommst einen Match-Score,
                    fehlende Anforderungen und einen Anschreiben-Entwurf.
                </p>
            </div>
            """
        )


    st.markdown(
        "### Kostenlos starten"
    )

    st.write(
        "✓ Kostenloses Benutzerkonto  \n"
        "✓ 2 vollständige Analysen zum Testen  \n"
        "✓ Stellenanzeigen analysieren  \n"
        "✓ Lebenslauf auslesen  \n"
        "✓ Match-Score berechnen  \n"
        "✓ fehlende Anforderungen erkennen  \n"
        "✓ Anschreiben-Entwurf erstellen"
    )

    st.info(
        "Premium-Zahlungen sind noch nicht aktiviert. "
        "Die Konten- und Credit-Grundlage ist bereits "
        "für die spätere Zahlungsanbindung vorbereitet."
    )

    st.button(
        "2 kostenlose Analysen sichern",
        type="primary",
        use_container_width=True,
        on_click=go_to_checker,
    )


# ---------------------------------------------------------
# PREISSEITE
# ---------------------------------------------------------

def show_prices():

    show_hero(
        "Preise",
        "Kostenlos starten. Premium-Tarife werden "
        "nach Abschluss der Zahlungsintegration freigeschaltet.",
    )

    col1, col2, col3 = st.columns(3)


    with col1:
        st.html(
            """
            <div class="price-card">
                <h3>Free</h3>
                <div class="price">0 €</div>
                <p>Zum Testen.</p>
                <p>
                    ✓ Benutzerkonto<br>
                    ✓ 2 Analysen einmalig<br>
                    ✓ Match-Score<br>
                    ✓ fehlende Anforderungen<br>
                    ✓ Anschreiben-Entwurf
                </p>
            </div>
            """
        )


    with col2:
        st.html(
            """
            <div class="price-card">
                <h3>5 Bewerbungen</h3>
                <div class="price">12,99 €</div>
                <p>Geplant</p>
                <p>
                    ✓ 5 weitere Analysen<br>
                    ✓ vollständige Optimierung<br>
                    ✓ erweiterte Anschreiben<br>
                    ✓ Export-Funktionen
                </p>
            </div>
            """
        )


    with col3:
        st.html(
            """
            <div class="price-card">
                <h3>Pro</h3>
                <div class="price">9,99 € / Monat</div>
                <p>Geplant</p>
                <p>
                    ✓ mehrere Bewerbungen<br>
                    ✓ Premium-Analyse<br>
                    ✓ Bewerbungshistorie<br>
                    ✓ weitere KI-Funktionen
                </p>
            </div>
            """
        )


    st.caption(
        "Die kostenpflichtigen Tarife sind "
        "noch nicht buchbar."
    )


# ---------------------------------------------------------
# BEWERBUNGSPRÜFUNG
# ---------------------------------------------------------

def show_checker():

    if not is_logged_in():

        st.warning(
            "Für die Bewerbungsprüfung brauchst du "
            "ein kostenloses Konto."
        )

        if st.button(
            "Jetzt anmelden oder registrieren",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["page"] = "Konto"
            st.rerun()

        return


    try:
        profile = get_profile()
    except Exception as exc:
        st.error(
            f"Kontostand konnte nicht geladen werden: {exc}"
        )
        return


    credits = (
        int(
            profile.get(
                "credits",
                0,
            )
        )
        if profile
        else 0
    )

    plan = (
        str(
            profile.get(
                "plan",
                "free",
            )
        )
        if profile
        else "free"
    )


    show_hero(
        "Bewerbung prüfen",
        "Stellenanzeige verstehen. Profil prüfen. "
        "Bewerbung gezielt verbessern.",
    )


    if plan == "pro":
        st.success(
            "Pro-Konto · Analysen ohne Credit-Abzug"
        )

    else:
        st.info(
            f"Angemeldet als {current_user_email()} · "
            f"Verbleibende Analysen: {credits}"
        )


    if (
        plan != "pro"
        and credits <= 0
    ):
        st.warning(
            "Deine kostenlosen Analysen sind aufgebraucht. "
            "Die Bezahlfunktion wird als Nächstes freigeschaltet."
        )

        if st.button(
            "Preise ansehen",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["page"] = "Preise"
            st.rerun()

        return


    st.caption(
        "Unterstützung bei der Vorbereitung – "
        "keine automatische Einstellungsentscheidung."
    )

    st.info(
        "Datenschutz: Hochgeladene Lebensläufe werden "
        "in dieser App-Sitzung verarbeitet. "
        "Bitte prüfe alle automatisch erkannten Angaben."
    )


    # -----------------------------------------------------
    # SCHRITT 1
    # -----------------------------------------------------

    st.progress(
        0.25,
        text="Schritt 1 von 4 · Stellenanzeige",
    )

    st.subheader(
        "1. Stellenanzeige"
    )


    job_ad = st.text_area(
        "Komplette Stellenanzeige einfügen",
        height=240,
        placeholder=(
            "Kopiere hier die vollständige Anzeige hinein. "
            "Stellenbezeichnung, Anforderungen, Erfahrung "
            "und Schlüsselbegriffe werden daraus erkannt."
        ),
    )


    col_a, col_b = st.columns(2)


    with col_a:
        role = st.text_input(
            "Stellenbezeichnung (optional)",
            placeholder="z. B. Projektmanager (m/w/d)",
        )


    with col_b:
        requirements_text = st.text_area(
            "Anforderungen manuell",
            height=100,
            placeholder="Eine Anforderung pro Zeile",
        )


    if job_ad.strip():

        detected_role = extract_role(
            job_ad
        )

        detected_requirements = extract_requirements(
            job_ad
        )

        if (
            not role.strip()
            and detected_role
        ):
            role = detected_role

        if (
            not requirements_text.strip()
            and detected_requirements
        ):
            requirements_text = detected_requirements


        with st.expander(
            "Erkannte Stelleninformationen prüfen",
            expanded=True,
        ):

            role = st.text_input(
                "Erkannte Stellenbezeichnung",
                value=role,
                key="detected_role",
            )

            requirements_text = st.text_area(
                "Erkannte Anforderungen",
                value=requirements_text,
                height=160,
                key="detected_requirements",
            )


    # -----------------------------------------------------
    # SCHRITT 2
    # -----------------------------------------------------

    st.progress(
        0.5,
        text="Schritt 2 von 4 · Lebenslauf",
    )

    st.subheader(
        "2. Lebenslauf und persönliche Daten"
    )


    uploaded_resume = st.file_uploader(
        "Lebenslauf hochladen",
        type=[
            "pdf",
            "docx",
            "txt",
        ],
        help="Unterstützt PDF, DOCX und TXT.",
    )


    if (
        uploaded_resume is not None
        and uploaded_resume.name
        != st.session_state.get(
            "resume_filename"
        )
    ):

        try:

            resume_text = extract_resume_text(
                uploaded_resume
            )

            st.session_state[
                "resume_text"
            ] = resume_text

            st.session_state[
                "resume_profile"
            ] = extract_resume_profile(
                resume_text
            )

            st.session_state[
                "resume_filename"
            ] = uploaded_resume.name

            st.success(
                f"{uploaded_resume.name} wurde gelesen. "
                "Bitte die Vorschläge prüfen."
            )

        except ValueError as exc:

            st.session_state[
                "resume_text"
            ] = ""

            st.session_state[
                "resume_profile"
            ] = {
                "experience": "",
                "qualifications": "",
                "focus": "",
            }

            st.error(
                str(exc)
            )


    profile_data = st.session_state[
        "resume_profile"
    ]


    with st.expander(
        "Erkannten Lebenslauftext anzeigen",
        expanded=bool(
            st.session_state[
                "resume_text"
            ]
        ),
    ):

        if st.session_state[
            "resume_text"
        ]:

            st.text_area(
                "Ausgelesener Text",
                value=st.session_state[
                    "resume_text"
                ],
                height=180,
                key="resume_text_review",
            )

        else:

            st.caption(
                "Noch kein Lebenslauf hochgeladen. "
                "Du kannst die Felder auch manuell ausfüllen."
            )


    experience = st.text_area(
        "Berufserfahrung",
        value=profile_data.get(
            "experience",
            "",
        ),
        height=120,
        placeholder="Nur echte Erfahrungen angeben.",
    )


    qualifications_text = st.text_area(
        "Qualifikationen, Abschlüsse, Führerscheine und Sprachen",
        value=profile_data.get(
            "qualifications",
            "",
        ),
        height=120,
        placeholder=(
            "z. B. Ausbildung, Abschluss, "
            "Führerscheinklassen, Deutsch B2"
        ),
    )


    focus = st.text_area(
        "Persönliche Stärken",
        value=profile_data.get(
            "focus",
            "",
        ),
        height=90,
        placeholder=(
            "z. B. zuverlässige und "
            "selbstständige Arbeitsweise"
        ),
    )


    # -----------------------------------------------------
    # SCHRITT 3
    # -----------------------------------------------------

    st.progress(
        0.75,
        text="Schritt 3 von 4 · Analyse",
    )

    st.subheader(
        "3. Analyse"
    )

    st.caption(
        "Ein Credit wird nur bei einer erfolgreich "
        "gestarteten vollständigen Analyse verbraucht."
    )


    submitted = st.button(
        "Analyse starten",
        type="primary",
        use_container_width=True,
    )


    if submitted:

        role = role.strip()
        requirements_text = requirements_text.strip()
        qualifications_text = qualifications_text.strip()
        experience = experience.strip()
        focus = focus.strip()


        if not role:
            st.error(
                "Bitte eine Stellenbezeichnung eingeben."
            )
            return


        if not requirements_text:
            st.error(
                "Bitte mindestens eine Stellenanforderung eingeben."
            )
            return


        if not qualifications_text:
            st.error(
                "Bitte mindestens eine vorhandene Qualifikation eingeben."
            )
            return


        try:

            requirements = split_items(
                requirements_text
            )

            qualifications = split_items(
                qualifications_text
            )

            matched, missing, details = compare_requirements(
                requirements,
                experience,
                qualifications_text,
                focus,
            )

            match_rate = calculate_match_rate(
                details
            )

            letter = build_letter(
                role,
                experience,
                qualifications,
                focus,
                matched,
            )

        except Exception as exc:

            st.error(
                f"Analyse konnte nicht erstellt werden: {exc}"
            )
            return


        try:

            credit_result = consume_analysis_credit()

        except Exception as exc:

            st.error(
                f"Credit konnte nicht geprüft werden: {exc}"
            )
            return


        if not credit_result[
            "allowed"
        ]:

            st.warning(
                "Deine kostenlosen Analysen sind aufgebraucht."
            )
            return


        st.session_state[
            "letter"
        ] = letter


        # -------------------------------------------------
        # SCHRITT 4
        # -------------------------------------------------

        st.progress(
            1.0,
            text="Schritt 4 von 4 · Ergebnis",
        )

        st.subheader(
            "4. Ergebnis"
        )


        if credit_result[
            "plan"
        ] != "pro":

            st.success(
                f"Analyse erstellt. "
                f"Verbleibende Analysen: "
                f"{credit_result['remaining']}"
            )


        st.metric(
            "Match-Score",
            f"{match_rate} %",
            help=(
                "Orientierung anhand der erkannten Anforderungen. "
                "Kein Einstellungsurteil."
            ),
        )


        col1, col2 = st.columns(2)


        with col1:

            st.markdown(
                "**Passende Anforderungen**"
            )

            if matched:

                for item in matched:
                    st.success(
                        item
                    )

            else:

                st.info(
                    "Keine eindeutigen Treffer"
                )


        with col2:

            st.markdown(
                "**Fehlende oder nicht erkannte Anforderungen**"
            )

            if missing:

                for item in missing:
                    st.warning(
                        item
                    )

            else:

                st.success(
                    "Keine"
                )


        with st.expander(
            "Zusammenfassung"
        ):

            st.text(
                build_summary(
                    role,
                    requirements,
                    qualifications,
                    matched,
                    missing,
                )
            )


        st.subheader(
            "Verbesserungsvorschläge"
        )


        if missing:

            st.warning(
                "Prüfe, ob du zu den fehlenden Anforderungen "
                "echte Nachweise oder konkrete Beispiele ergänzen kannst. "
                "Erfinde keine Angaben."
            )

        else:

            st.success(
                "Alle erkannten Anforderungen haben mindestens "
                "eine passende Angabe im Profil."
            )


        st.subheader(
            "Anschreiben-Entwurf"
        )


        st.text_area(
            "Entwurf",
            value=st.session_state[
                "letter"
            ],
            height=320,
        )


        st.download_button(
            "Anschreiben als TXT herunterladen",
            data=st.session_state[
                "letter"
            ],
            file_name="anschreiben.txt",
            mime="text/plain",
        )


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

st.sidebar.title(
    "Bewerbungshelfer AI"
)


if is_logged_in():

    st.sidebar.caption(
        f"Angemeldet: {current_user_email()}"
    )

    try:

        sidebar_profile = get_profile()

        if sidebar_profile:

            if (
                sidebar_profile.get(
                    "plan"
                )
                == "pro"
            ):
                st.sidebar.success(
                    "Pro"
                )

            else:
                st.sidebar.info(
                    f"Analysen übrig: "
                    f"{sidebar_profile.get('credits', 0)}"
                )

    except Exception:
        pass

else:

    st.sidebar.caption(
        "Nicht angemeldet"
    )


if st.sidebar.button(
    "Start",
    use_container_width=True,
):
    st.session_state[
        "page"
    ] = "Start"


if st.sidebar.button(
    "Bewerbung prüfen",
    use_container_width=True,
):

    st.session_state[
        "page"
    ] = (
        "Bewerbung prüfen"
        if is_logged_in()
        else "Konto"
    )


if st.sidebar.button(
    "Konto",
    use_container_width=True,
):
    st.session_state[
        "page"
    ] = "Konto"


if st.sidebar.button(
    "Preise",
    use_container_width=True,
):
    st.session_state[
        "page"
    ] = "Preise"


if is_logged_in():

    if st.sidebar.button(
        "Abmelden",
        use_container_width=True,
    ):

        logout()

        st.session_state[
            "page"
        ] = "Start"

        st.rerun()


st.sidebar.divider()

st.sidebar.caption(
    "Beta-Version"
)

st.sidebar.caption(
    "Keine automatische Einstellungsentscheidung."
)


# ---------------------------------------------------------
# SEITENANZEIGE
# ---------------------------------------------------------

if (
    st.session_state["page"]
    == "Start"
):
    show_start()

elif (
    st.session_state["page"]
    == "Bewerbung prüfen"
):
    show_checker()

elif (
    st.session_state["page"]
    == "Konto"
):
    show_account()

elif (
    st.session_state["page"]
    == "Preise"
):
    show_prices()
