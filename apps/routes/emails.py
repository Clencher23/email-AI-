from flask import Blueprint, request, jsonify, session, json, Response, stream_with_context
import os
from apps.utils.db import get_db_connection
from apps.routes.auth import login_required
from apps.aimodels.aiagent import analyze_email_ai
import traceback

emails_bp = Blueprint("emails", __name__)

@emails_bp.route("/list", methods=["GET"])
@login_required
def list_emails():
    user_id = session.get("user_id")
    print("session user_id =", session.get("user_id"))


    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, subject, sender, date, recipients
            FROM emails
            WHERE user_id = %s
            ORDER BY date DESC
            LIMIT 100
        """, (user_id,))

        emails = [
            {
                "id": row[0],
                "subject": row[1],
                "from": row[2],
                "date": row[3],
                "recipients": row[4]
            } for row in cur.fetchall()
        ]

        cur.close()
        conn.close()

        return jsonify(emails), 200
    except Exception as e:
        print("Error in /emails/list:", e)
        return jsonify({"error": "Failed to fetch emails"}), 500



@emails_bp.route("/<int:email_id>", methods=["GET"])
@login_required
def get_email(email_id):
    try:
        user_id = session.get("user_id")
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, subject, sender, recipients, date,
                   body_text, body_html, in_reply_to, references_ids
            FROM emails
            WHERE id = %s AND user_id = %s
        """, (email_id, user_id))

        row = cur.fetchone()

        if not row:
            return jsonify({"error": "Email not found"}), 404

        # Use HTML body if available, otherwise fallback to plain text
        email_body = row[6] if row[6] else row[5]
        if not email_body:
            email_body = "(No content)"

        email_data = {
            "id": row[0],
            "subject": row[1],
            "from": row[2],
            "recipients": row[3],
            "date": row[4],
            "body": email_body,
            "body_text": row[5],
            "body_html": row[6],
            "in_reply_to": row[7],
            "references_ids": row[8],
            "attachments": []
        }

        cur.execute("""
            SELECT filename, content_type, file_path
            FROM attachments
            WHERE email_id = %s
        """, (email_id,))

        attachments = cur.fetchall()

        email_data["attachments"] = [
            {
                "filename": att[0],
                "content_type": att[1],
                "url": f"/download/{att[0]}"
            } for att in attachments
        ]

        cur.close()
        conn.close()

        return jsonify(email_data), 200
    except Exception as e:
        print("Error in /emails/<id>:", e)
        return jsonify({"error": "Failed to fetch email"}), 500

# @emails_bp.route("/refresh", methods=["POST"])
# @login_required
# def refresh_emails():
#     try:
#         user_id = session.get("user_id")
#         email = session.get("email")
#         password = session.get("password")
#         imap_host = session.get("imap_host")
#         imap_port = session.get("imap_port")

#         if not all([email, password, imap_host, user_id]):
#             return jsonify({"error": "Missing session details"}), 400

#         from apps.services.imap_client import fetch_and_store_emails_imaplib
#         return fetch_and_store_emails_imaplib(email, password, imap_host, user_id, imap_port)
#     except Exception as e:
#         print("Refresh failed:", e)
#         return jsonify({"error": "Refresh failed"}), 500


@emails_bp.route("/<int:email_id>/analyze", methods=["POST"])
# @login_required
# def analyze_email(email_id):
#     user_id = session.get("user_id")
#     action = request.json.get("action", "analyze")  # default = "analyze"

    # try:
    #     # Fetch the email
    #     conn = get_db_connection()
    #     cur = conn.cursor()
    #     cur.execute("""
    #         SELECT subject, sender, body_text, attachments
    #         FROM emails
    #         WHERE id = %s AND user_id = %s
    #     """, (email_id, user_id))

    #     row = cur.fetchone()
    #     subject, sender, body, attachments_json = row
    #     cur.close()
    #     conn.close()

    #     if not row:
    #         return jsonify({"error": "Email not found"}), 404

    #     subject, sender, body, attachments_json = row
    #     attachments = json.loads(attachments_json or "[]")

    #     # Load the files (from disk)
    #     files_data = []
    #     for att in attachments:
    #         filepath = os.path.join(os.getenv("ATTACHMENTS_DIR", "attachments"), att["stored_filename"])
    #         if os.path.exists(filepath):
    #             with open(filepath, "rb") as f:
    #                 files_data.append({
    #                     "filename": att["filename"],
    #                     "bytes": f.read()
    #                 })


    #                 print("Email ID:", email_id)
    #                 print("User ID:", user_id)
    #                 print("Action:", action)
    #                 print("Email DB row:", row)
    #                 print("Attachments JSON:", attachments_json)
    #                 print("Resolved files:", files_data)


    #     # Stream the AI response
    #     def generate():
    #         try:
    #             for chunk in analyze_email_ai(subject, sender, body, files=files_data, action=action):
    #                 yield f"data: {json.dumps(chunk)}\n\n"
    #         except Exception as e:
    #             traceback.print_exc()
    #             yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
                

    #     # return Response(stream_with_context(generate()), mimetype='text/event-stream')
    #     return jsonify({"ok": True, "subject": subject, "body": body, "attachments": attachments})


    # except Exception as e:
    #     print("Error in /analyze:", e)
    #     return jsonify({"error": "Failed to analyze email"}), 500


def analyze_email(email_id):
    user_id = session.get("user_id")
    print("Session user_id:", session.get("user_id"))

    action = request.json.get("action", "analyze")  # or "draft_reply"

    try:
        # DB connection
        conn = get_db_connection()
        cur = conn.cursor()

        # 📬 Fetch email
        cur.execute("""
            SELECT subject, sender, body_text
            FROM emails
            WHERE id = %s AND user_id = %s
        """, (email_id, user_id))
        row = cur.fetchone()

        if not row:
            return jsonify({"error": "Email not found"}), 404

        subject, sender, body = row

        # 📎 Fetch attachments from related table
        cur.execute("""
            SELECT filename, file_path
            FROM attachments
            WHERE email_id = %s
        """, (email_id,))
        attachments = [{"filename": r[0], "file_path": r[1]} for r in cur.fetchall()]

        cur.close()
        conn.close()

        # 🧾 Load files from disk
        files_data = []
        for att in attachments:
            if os.path.exists(att["file_path"]):
                with open(att["file_path"], "rb") as f:
                    files_data.append({
                        "filename": att["filename"],
                        "bytes": f.read()
                    })

        # 🧠 Stream AI response
        def generate():
            try:
                for chunk in analyze_email_ai(
                    subject=subject,
                    sender=sender,
                    body=body or "",
                    files=files_data,
                    action=action
                ):
                    yield f"data: {json.dumps(chunk)}\n\n"
            except Exception as e:
                traceback.print_exc()
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

        return Response(stream_with_context(generate()), mimetype='text/event-stream')

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Failed to analyze email"}), 500
