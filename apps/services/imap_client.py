import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from flask import jsonify
import os
import uuid
from config import Config
from apps.utils.db import get_db_connection

ATTACHMENTS_DIR = os.environ.get("ATTACHMENTS_DIR", "attachments/")
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

def decode_header_value(raw_val):
    try:
        val, encoding = decode_header(raw_val)[0]
        return val.decode(encoding or "utf-8", errors="ignore") if isinstance(val, bytes) else val
    except Exception:
        return raw_val

def fetch_and_store_emails_imaplib(email_address, password, imap_server,  user_id, imap_port=993, n_limit=300):
    conn = cur = mail = None
    try:
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        mail.login(email_address, password)
        
        mail.select("Inbox")
        # typ, data = mail.search(None, "ALL")
        typ, data = mail.uid("search", "", "ALL")
        # typ, data = mail.uid("search", "", "SEEN")
        # typ, data = mail.uid("search", "", "UNSEEN")
        if typ != "OK":
            print("UID SEARCH failed")
            return

        uids = data[0].split()
        print(f" Raw UIDs returned: {uids}")
        print(f" Total UIDs: {len(uids)}")

        # exit(0)

        all_uids = data[0].split()
        all_uids = all_uids[-n_limit:] if len(all_uids) > n_limit else all_uids
        print(f" Total emails found in inbox: {len(all_uids)}")
        print(f"Type {typ}")

        all_uids = all_uids[::-1]  # Newest first
        age_uids = all_uids[:n_limit]  # Simulated pagination
        
        typ, folders = mail.list()
        print("Available folders:")
        try:
            for f in folders:
                print(f.decode() if isinstance(f, bytes) else str(f))
        except Exception as e:
            print(f"Error listing folders: {e}")
            
        


        if not all_uids:
            return jsonify({"message": "Inbox is empty"}), 200

        conn = get_db_connection()
        cur = conn.cursor()

        inserted_count = 0
        skipped_count = 0

        for uid in all_uids:
            # uid_str = uid.decode() if isinstance(uid, bytes) else str(uid)
            uid_str = uid.decode().strip() if isinstance(uid, bytes) else str(uid).strip()
            print(f"👉 Fetching UID: '{uid_str}'")
            typ, msg_data = mail.uid("fetch",uid_str, "(RFC822)")
            # print(typ, msg_data)
            print(f"Fetching email with ID: {uid}")
            if typ != "OK" or not msg_data or not isinstance(msg_data[0], tuple):
                skipped_count += 1
                continue

            raw_email = msg_data[0][1]
            if not isinstance(raw_email, bytes):
                skipped_count += 1
                continue

            msg = email.message_from_bytes(raw_email)

            subject = decode_header_value(msg.get("Subject", "(No Subject)"))
            sender = decode_header_value(msg.get("From", ""))
            recipients = decode_header_value(msg.get("To", ""))
            raw_date = msg.get("Date", "")
            try:
                date = parsedate_to_datetime(raw_date)
            except Exception:
                date = None

            message_id = msg.get("Message-ID", "")
            in_reply_to = msg.get("In-Reply-To", "")
            references = decode_header_value(msg.get("References", ""))
 
            # fallback if message-id is missing
            if not message_id:
                message_id = f"<fallback-{uuid.uuid4()}@{email_address.split('@')[-1]}>"

            # Check if already stored
            cur.execute("SELECT id FROM emails WHERE message_id = %s", (message_id,))
            if cur.fetchone():
                skipped_count += 1
                continue

            # Parse body and attachments
            body_text, body_html = "", ""
            attachments = []

            for part in msg.walk():
                content_type = part.get_content_type()
                content_disp = str(part.get("Content-Disposition") or "").lower()
                filename = part.get_filename()
                charset = part.get_content_charset() or "utf-8"

                try:
                    if content_type == "text/plain" and "attachment" not in content_disp:
                        payload = part.get_payload(decode=True)
                        if isinstance(payload, bytes):
                            body_text += payload.decode(charset, errors="ignore")
                    elif content_type == "text/html":
                        payload = part.get_payload(decode=True)
                        if isinstance(payload, bytes):
                            body_html += payload.decode(charset, errors="ignore")
                    elif "attachment" in content_disp or filename:
                        filename = decode_header_value(filename or f"file_{uuid.uuid4().hex}.bin")
                        base, ext = os.path.splitext(filename)
                        counter = 1
                        unique_filename = filename
                        filepath = os.path.join(ATTACHMENTS_DIR, unique_filename)

                        while os.path.exists(filepath):
                            unique_filename = f"{base}_{counter}{ext}"
                            filepath = os.path.join(ATTACHMENTS_DIR, unique_filename)
                            counter += 1

                        payload = part.get_payload(decode=True)
                        # print(payload)
                        # exit(0)
                        if isinstance(payload, bytes):
                            with open(filepath, "wb") as f:
                                f.write(payload)
                            attachments.append((unique_filename, content_type, filepath))
                except Exception as e:
                    print(f" Attachment decode error: {e}")
                    continue

            try:
                cur.execute("""
                    INSERT INTO emails (
                        user_id, uid, subject, sender, recipients,
                        date, body_text, body_html, message_id,
                        in_reply_to, references_ids
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    user_id,
                    uid.decode() if isinstance(uid, bytes) else str(uid),
                    subject,
                    sender,
                    [recipients],
                    date,
                    body_text,
                    body_html or body_text.replace("\n", "<br>"),
                    message_id,
                    in_reply_to,
                    references.split() if isinstance(references, str) else [],
                ))
                result = cur.fetchone()
                if not result:
                    print(f" No ID returned after email insert for subject: {subject}")
                    continue
                email_db_id = result[0]

                for filename, content_type, filepath in attachments:
                    cur.execute("""
                        INSERT INTO attachments (email_id, filename, content_type, file_path)
                        VALUES (%s, %s, %s, %s)
                    """, (email_db_id, filename, content_type, filepath))

                inserted_count += 1
            except Exception as e:
                print(f"DB Insert error: {e}")
                continue

        conn.commit()
        print(f" Emails inserted: {inserted_count}, Skipped: {skipped_count}")
        return jsonify({
            "inserted": inserted_count,
            "skipped": skipped_count,
            "total": len(all_uids)
        }), 200

    except Exception as e:
        print(f"IMAP fetch error: {e}")
        # return jsonify({"error": "IMAP fetch failed"}), 400
        print("IMAP fetch failed:", e)
        return

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        if mail:
            mail.logout()

