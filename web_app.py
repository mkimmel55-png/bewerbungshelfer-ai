"""
Bewerbungshelfer AI
Weboberfläche für Version 0.3.0
"""

from flask import Flask, render_template, request
from app import (
    split_items,
    compare_requirements,
    build_summary,
    build_letter,
)

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    letter = None

    if request.method == "POST":
        role = request.form.get("role", "").strip()
        requirements_input = request.form.get(
            "requirements", ""
        ).strip()
        experience = request.form.get(
            "experience", ""
        ).strip()
        qualifications_input = request.form.get(
            "qualifications", ""
        ).strip()
        focus = request.form.get(
            "focus", ""
        ).strip()

        requirements = split_items(requirements_input)
        qualifications = split_items(qualifications_input)

        matched, missing = compare_requirements(
            requirements,
            qualifications,
        )

        result = build_summary(
            role,
            requirements,
            qualifications,
            matched,
            missing,
        )

        letter = build_letter(
            role,
            experience,
            qualifications,
            focus,
            matched,
        )

    return render_template(
        "index.html",
        result=result,
        letter=letter,
    )


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )
