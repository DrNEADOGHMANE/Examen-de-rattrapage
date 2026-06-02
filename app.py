"""
Backend Flask — Examen TEC
15 QCM (15 pts) + 1 Question ouverte (5 pts) = 20 pts
Sauvegarde persistante via SQLite
"""
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import json, csv, io, os, sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ── Base de données SQLite ─────────────────────────────────────────────────
# Sur Render : montez un disque persistant sur /data et changez DB_PATH
DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), 'exam_data.db'))

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS copies (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            data      TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    # Statut par défaut
    conn.execute('''
        INSERT OR IGNORE INTO settings (key, value) VALUES ('status', 'none')
    ''')
    conn.commit()
    conn.close()
    print(f"[DB] Initialisée : {DB_PATH}")

init_db()

# ── Helpers ────────────────────────────────────────────────────────────────
def db_get_status():
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key='status'").fetchone()
    conn.close()
    return row['value'] if row else 'none'

def db_set_status(s):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('status', ?)", (s,))
    conn.commit()
    conn.close()

def db_get_copies():
    conn = get_db()
    rows = conn.execute("SELECT id, data FROM copies ORDER BY id ASC").fetchall()
    conn.close()
    result = []
    for i, row in enumerate(rows):
        c = json.loads(row['data'])
        c['_db_id'] = row['id']
        c['_idx'] = i
        result.append(c)
    return result

def db_add_copy(record):
    conn = get_db()
    conn.execute("INSERT INTO copies (data) VALUES (?)", (json.dumps(record, ensure_ascii=False),))
    conn.commit()
    conn.close()

def db_update_copy(db_id, record):
    conn = get_db()
    conn.execute("UPDATE copies SET data=? WHERE id=?", (json.dumps(record, ensure_ascii=False), db_id))
    conn.commit()
    conn.close()

def db_delete_copy(db_id):
    conn = get_db()
    conn.execute("DELETE FROM copies WHERE id=?", (db_id,))
    conn.commit()
    conn.close()

def db_clear_copies():
    conn = get_db()
    conn.execute("DELETE FROM copies")
    conn.commit()
    conn.close()

# ── Statut ─────────────────────────────────────────────────────────────────
@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({"status": db_get_status()})

@app.route('/api/status', methods=['POST'])
def set_status():
    data = request.get_json()
    s = data.get('status', 'none')
    db_set_status(s)
    print(f"[STATUT] → {s}")
    return jsonify({"ok": True})

# ── Copies ─────────────────────────────────────────────────────────────────
@app.route('/api/copies', methods=['GET'])
def get_copies():
    return jsonify(db_get_copies())

@app.route('/api/copies', methods=['POST'])
def add_copy():
    record = request.get_json()
    record['server_time'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    db_add_copy(record)
    copies_count = len(db_get_copies())
    has_open = '✓' if record.get('openAnswer') else '✗'
    print(f"[COPIE] {record.get('name')} | QCM: {record.get('score')}/15 | Ouverte: {has_open} | Total: {copies_count}")
    return jsonify({"ok": True}), 201

@app.route('/api/copies/clear', methods=['POST'])
def clear_copies():
    db_clear_copies()
    print("[COPIES] Toutes supprimées")
    return jsonify({"ok": True})

@app.route('/api/copies/<int:idx>/open_score', methods=['POST'])
def set_open_score(idx):
    copies = db_get_copies()
    if 0 <= idx < len(copies):
        c = copies[idx]
        data = request.get_json()
        open_score = data.get('openScore')
        if open_score is None or not (0 <= float(open_score) <= 5):
            return jsonify({"error": "Note invalide"}), 400
        c['openScore']   = float(open_score)
        c['totalScore']  = round((c.get('score', 0) + float(open_score)), 2)
        db_update_copy(c['_db_id'], {k: v for k, v in c.items() if not k.startswith('_')})
        print(f"[NOTE OUVERTE] {c.get('name')} → {open_score}/5 | Total: {c['totalScore']}/20")
        return jsonify({"ok": True, "totalScore": c['totalScore']})
    return jsonify({"error": "Index invalide"}), 404

@app.route('/api/copies/<int:idx>', methods=['DELETE'])
def delete_copy(idx):
    copies = db_get_copies()
    if 0 <= idx < len(copies):
        c = copies[idx]
        db_delete_copy(c['_db_id'])
        print(f"[COPIE SUPPRIMÉE] {c.get('name')}")
        return jsonify({"ok": True})
    return jsonify({"error": "Index invalide"}), 404

# ── Stats ──────────────────────────────────────────────────────────────────
@app.route('/api/stats', methods=['GET'])
def get_stats():
    copies = db_get_copies()
    if not copies:
        return jsonify({"total": 0, "avg": 0, "max": 0, "min": 0})
    scores = [c.get('totalScore', c.get('score', 0)) for c in copies]
    open_count = sum(1 for c in copies if c.get('openAnswer', '').strip())
    return jsonify({
        "total":      len(copies),
        "avg":        round(sum(scores) / len(scores), 2),
        "max":        round(max(scores), 2),
        "min":        round(min(scores), 2),
        "open_count": open_count
    })

# ── Export CSV ─────────────────────────────────────────────────────────────
@app.route('/api/export', methods=['GET'])
def export_csv():
    copies = db_get_copies()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['#', 'Nom', 'Matricule', 'Filière', 'Groupe', 'Score QCM/15', 'Note Ouverte/5', 'Total/20', 'Réponse ouverte', 'Date'])
    for i, c in enumerate(copies, 1):
        writer.writerow([
            i, c.get('name'), c.get('matricule'), c.get('filiere'),
            c.get('group'), c.get('score'), c.get('openScore', ''),
            c.get('totalScore', ''), c.get('openAnswer', ''), c.get('timestamp')
        ])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=copies_exam.csv"}
    )

# ── Health check ───────────────────────────────────────────────────────────
@app.route('/', methods=['GET'])
def health():
    copies = db_get_copies()
    return jsonify({
        "status": "ok",
        "copies": len(copies),
        "exam":   db_get_status()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
