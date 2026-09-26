"""
Bewerbungshelfer AI
Weboberfläche für Version 0.5.1
"""

from io import BytesIO

from flask import Flask, render_template, request, send_file

from app import (
    split_items,
    compare_requirements,
    calculate_match_rate,
    build_summary,
    build_letter,
)

app = Flask(__name__)

last_letter = ""


@app.route("/", methods=["GET", "POST"])
def index():
    global last_letter

    result = None
    letter = None
    matched = []
    missing = []
    match_rate = None
    error = None

    form_data = {
        "role": "",
        "requirements": "",
        "experience": "",
        "qualifications": "",
        "focus": "",
    }

    if request.method == "POST":
        form_data["role"] = request.form.get("role", "").strip()
        form_data["requirements"] = request.form.get(
            "requirements", ""
        ).strip()
        form_data["experience"] = request.form.get(
            "experience", ""
        ).strip()
        form_data["qualifications"] = request.form.get(
            "qualifications", ""
        ).strip()
        form_data["focus"] = request.form.get(
            "focus", ""
        ).strip()

        if not form_data["role"]:
            error = "Bitte eine Stellenbezeichnung eingeben."

        elif not form_data["requirements"]:
            error = "Bitte mindestens eine Stellenanforderung eingeben."

        elif not form_data["qualifications"]:
            error = "Bitte mindestens eine vorhandene Qualifikation eingeben."

        else:
            requirements = split_items(
                form_data["requirements"]
            )

            qualifications = split_items(
                form_data["qualifications"]
            )

            matched, missing = compare_requirements(
                requirements,
                qualifications,
            )
            match_rate = calculate_match_rate(
                requirements,
                matched,
            )

            result = build_summary(
                form_data["role"],
                requirements,
                qualifications,
                matched,
                missing,
            )

            letter = build_letter(
                form_data["role"],
                form_data["experience"],
                qualifications,
                form_data["focus"],
                matched,
            )

            last_letter = letter

    return render_template(
        "index.html",
        result=result,
        letter=letter,
        matched=matched,
        missing=missing,
        match_rate=match_rate,
        error=error,
        form_data=form_data,
    )


@app.route("/download-letter")
def download_letter():
    if not last_letter:
        return "Noch kein Anschreiben vorhanden.", 400

    file_data = BytesIO(
        last_letter.encode("utf-8")
    )

    return send_file(
        file_data,
        as_attachment=True,
        download_name="anschreiben.txt",
        mimetype="text/plain; charset=utf-8",
    )


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )
