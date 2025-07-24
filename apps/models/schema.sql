--  Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    imap_host TEXT,
    imap_port INT,
    password_encrypted TEXT,
    created_at TIMESTAMP DEFAULT now()
);

--  Emails Table
CREATE TABLE IF NOT EXISTS emails (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    uid TEXT NOT NULL,
    subject TEXT,
    sender TEXT,
    recipients TEXT[],
    date TIMESTAMP,
    body_text TEXT,
    body_html TEXT,
    message_id TEXT UNIQUE,
    in_reply_to TEXT,
    references_ids TEXT[], -- renamed to avoid SQL reserved word "references"
    thread_id INTEGER,
    fetched_at TIMESTAMP DEFAULT now()
);

--  Attachments Table
CREATE TABLE IF NOT EXISTS attachments (
    id SERIAL PRIMARY KEY,
    email_id INTEGER REFERENCES emails(id) ON DELETE CASCADE,
    filename TEXT,
    content_type TEXT,
    file_path TEXT,
    uploaded_at TIMESTAMP DEFAULT now()
);
