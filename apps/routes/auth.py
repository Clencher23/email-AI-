from flask import Blueprint, request, jsonify, session, redirect, current_app
import threading
from imapclient import IMAPClient
from apps.utils.db import get_db_connection
from apps.services.imap_client import fetch_and_store_emails_imaplib

auth_bp = Blueprint("auth", __name__)


app_instance = None

def set_app_instance(app):
    global app_instance
    app_instance = app

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json

    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    email = data.get("email")
    password = data.get("password")
    imap_host = data.get("imap_host", "mail.24livehost.com")
    # imap_host = data.get("imap_host", "mail.dotsquares.com")
    # imap_host = data.get("imap_host", "imap.gmail.com")
    imap_port = data.get("imap_port", 993)

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    email = str(email).strip()
    password = str(password).strip()
    imap_host = str(imap_host).strip()
    imap_port = int(imap_port)

    print("IMAP HOST:", imap_host)
    print("PORT:", imap_port)
    print("EMAIL:", email)

    try:
        # Test IMAP login
        with IMAPClient(imap_host, port=imap_port, ssl=True) as client:
            client.login(email, password)
            client.select_folder("INBOX")

        # DB user check or create
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        result = cur.fetchone()

        if result:
            user_id = result[0]
        else:
            cur.execute("""
                INSERT INTO users (email, imap_host, imap_port)
                VALUES (%s, %s, %s) RETURNING id
            """, (email, imap_host, imap_port))
            row = cur.fetchone()
            if row is None:
                cur.close()
                conn.close()
                return jsonify({"error": "Failed to create user"}), 500
            user_id = row[0]
            conn.commit()

        cur.close()
        conn.close()

        session["user_id"] = user_id
        session["email"] = email
        session["password"] = password
        session["imap_host"] = imap_host


        def run_fetch_with_context(app, email, password, imap_host, user_id):
            with app.app_context():
                fetch_and_store_emails_imaplib(
                    email_address=email,
                    password=password,
                    imap_server=imap_host,
                    user_id=user_id
                )

        threading.Thread(
            target=run_fetch_with_context,
            args=(app_instance, email, password, imap_host, user_id),
            daemon=True
        ).start()

        return jsonify({"message": "Login successful", "user_id": user_id}), 200

    except Exception as e:
        print("Login failed", str(e))
        # return jsonify({"error": str(e)}), 401
        return jsonify({"error": "Login failed"}), 401


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200


def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapper