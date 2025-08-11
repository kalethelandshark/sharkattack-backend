from flask import Flask, jsonify
from flask_cors import CORS
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# ---- CORS: allow your domain(s). You can override with ALLOWED_ORIGINS env var (comma-separated).
_default_origins = "https://sharkattackgaming.com,https://www.sharkattackgaming.com"
allowed_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",") if o.strip()]
CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

# ---- Google Sheets auth from ENV (no file needed)
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

# Lazy-init so /api/health still works even if creds are missing
_gspread_client = None
def get_gspread_client():
    global _gspread_client
    if _gspread_client:
        return _gspread_client

    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if not creds_json:
        raise RuntimeError(
            "Missing GOOGLE_CREDENTIALS_JSON env var. "
            "Add it in Railway -> Service -> Variables (paste the full credentials.json)."
        )

    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
    _gspread_client = gspread.authorize(creds)
    return _gspread_client

# Optional: override sheet names via env
WORKBOOK_NAME = os.getenv("SHEET_WORKBOOK", "Shark Codes")
WORKSHEET_NAME = os.getenv("SHEET_WORKSHEET", "Codes")

@app.route("/api/get-code")
def get_code():
    try:
        client = get_gspread_client()
        sheet = client.open(WORKBOOK_NAME).worksheet(WORKSHEET_NAME)
        records = sheet.get_all_records()

        for i, row in enumerate(records):
            # Expect columns "Code" and "Used?" in the worksheet header row
            if str(row.get("Used?", "")).upper() != "TRUE":
                code = row.get("Code", "").strip()
                # Mark as used in column B (adjust if your "Used?" column is different)
                sheet.update_acell(f"B{i+2}", "TRUE")
                return jsonify({"code": code or "OUT-OF-CODES"})

        return jsonify({"code": "OUT-OF-CODES"})
    except Exception as e:
        # Log to stdout for Railway logs
        print("Error in /api/get-code:", repr(e))
        return jsonify({"error": "Failed to fetch code"}), 500

@app.route("/api/health")
def health_check():
    has_creds = bool(os.getenv("GOOGLE_CREDENTIALS_JSON"))
    return jsonify({"status": "ok", "has_credentials": has_creds})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)), debug=os.getenv("FLASK_DEBUG") == "1")
