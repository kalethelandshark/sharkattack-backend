from flask import Flask, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

app = Flask(__name__)

# Setup credentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

@app.route('/api/get-code')
def get_code():
    try:
        sheet = client.open("Shark Codes").worksheet("Codes")
        records = sheet.get_all_records()

        for i, row in enumerate(records):
            if str(row["Used?"]).upper() != "TRUE":
                code = row["Code"]
                sheet.update_acell(f"B{i+2}", "TRUE")
                return jsonify({"code": code})

        return jsonify({"code": "OUT-OF-CODES"})
    except Exception as e:
        print("Error occurred:", e)  # Logs to Render console
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
