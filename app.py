from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import wikipedia

app = Flask(__name__)
app.secret_key = "super-secret"

DB_FILE = "database.db"

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS questions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  question TEXT,
                  answer TEXT,
                  chapter TEXT,
                  status TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- Home Route ---
@app.route("/")
def home():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT question, answer, chapter FROM questions WHERE status='approved'")
    approved = c.fetchall()
    conn.close()
    return render_template("index.html", approved=approved)

# --- Submit Q/A ---
@app.route("/submit", methods=["POST"])
def submit():
    q = request.form["question"]
    a = request.form["answer"]
    chap = request.form["chapter"]

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO questions (question, answer, chapter, status) VALUES (?,?,?,?)",
              (q, a, chap, "pending"))
    conn.commit()
    conn.close()
    return "✅ Submitted for Approval. Wait for Admin."

# --- Wikipedia Search ---
@app.route("/wiki", methods=["POST"])
def wiki_search():
    query = request.form["query"]
    try:
        summary = wikipedia.summary(query, sentences=3, auto_suggest=True, redirect=True)
    except Exception as e:
        summary = f"⚠️ Error: {str(e)}"
    return render_template("wiki.html", query=query, summary=summary)

# --- Admin Panel ---
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form.get("password") == "admin123":
            session["admin"] = True
    if not session.get("admin"):
        return '''<form method="post">
                   <input type="password" name="password" placeholder="Admin Password">
                   <button>Login</button></form>'''

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, question, answer, chapter FROM questions WHERE status='pending'")
    pending = c.fetchall()
    conn.close()
    return render_template("admin.html", pending=pending)

# --- Approve ---
@app.route("/approve/<int:qid>")
def approve(qid):
    if not session.get("admin"): return "Unauthorized"
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE questions SET status='approved' WHERE id=?", (qid,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

# --- Reject ---
@app.route("/reject/<int:qid>")
def reject(qid):
    if not session.get("admin"): return "Unauthorized"
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM questions WHERE id=?", (qid,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(debug=True)