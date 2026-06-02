"""
Backend Flask — Examen Méthodologie & Communication
15 QCM (15 pts) + 1 Question ouverte (5 pts) = 20 pts
Avec sauvegarde automatique sur disque
"""
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import json, csv, io, os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ── Fichiers de sauvegarde ──────────────────────────────────────────────────
DATA_DIR = '/tmp'
COPIES_FILE = os.path.join(DATA_DIR, 'copies.json')
STATUS_FILE = os.path.join(DATA_DIR, 'status.json')

def load_copies():
    try:
        if os.path.exists(COPIES_FILE):
            with open(COPIES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except: pass
    return []

def save_copies(copies):
    try:
        with open(COPIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(copies, f, ensure_ascii=False)
    except Exception as e:
        print(f"[ERREUR save_copies] {e}")

def load_status():
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except: pass
    return {"status": "none"}

def save_status(status):
    try:
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(status, f)
    except Exception as e:
        print(f"[ERREUR save_status] {e}")

# ── Charger les données au démarrage ───────────────────────────────────────
exam_status = load_status()
copies = load_copies()
print(f"[DÉMARRAGE] Statut: {exam_status['status']} | Copies chargées: {len(copies)}")

# ── Statut ──────────────────────────────────────────────────────────────────
@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(exam_status)

@app.route('/api/status', methods=['POST'])
def set_status():
    data = request.get_json()
    exam_status['status'] = data.get('status', 'none')
    save_status(exam_status)
    print(f"[STATUT] → {exam_status['status']}")
    return jsonify({"ok": True})

# ── Copies ───────────────────────────────────────────────────────────────────
@app.route('/api/copies', methods=['GET'])
def get_copies():
    return jsonify(copies)

@app.route('/api/copies', methods=['POST'])
def add_copy():
    record = request.get_json()
    record['server_time'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    copies.append(record)
    save_copies(copies)
    has_open = '✓' if record.get('openAnswer') else '✗'
    print(f"[COPIE] {record.get('name')} | QCM: {record.get('score')}/15 | Ouverte: {has_open} | Total copies: {len(copies)}")
    return jsonify({"ok": True}), 201

@app.route('/api/copies/clear', methods=['POST'])
def clear_copies():
    copies.clear()
    save_copies(copies)
    print("[COPIES] Toutes supprimées")
    return jsonify({"ok": True})

@app.route('/api/copies/<int:idx>', methods=['DELETE'])
def delete_copy(idx):
    if 0 <= idx < len(copies):
        removed = copies.pop(idx)
        save_copies(copies)
        print(f"[COPIE SUPPRIMÉE] {removed.get('name')}")
        return jsonify({"ok": True})
    return jsonify({"error": "Index invalide"}), 404

# ── Stats ────────────────────────────────────────────────────────────────────
@app.route('/api/stats', methods=['GET'])
def get_stats():
    if not copies:
        return jsonify({"total": 0, "avg": 0, "max": 0, "min": 0})
    scores = [c.get('score', 0) for c in copies]
    open_count = sum(1 for c in copies if c.get('openAnswer', '').strip())
    return jsonify({
        "total":      len(copies),
        "avg":        round(sum(scores) / len(scores), 2),
        "max":        round(max(scores), 2),
        "min":        round(min(scores), 2),
        "open_count": open_count
    })

# ── Export CSV ────────────────────────────────────────────────────────────────
@app.route('/api/export', methods=['GET'])
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['#', 'Nom', 'Matricule', 'Filière', 'Groupe', 'Score QCM/15', 'Réponse ouverte', 'Date'])
    for i, c in enumerate(copies, 1):
        writer.writerow([i, c.get('name'), c.get('matricule'), c.get('filiere'),
                         c.get('group'), c.get('score'), c.get('openAnswer', ''), c.get('timestamp')])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=copies_exam.csv"}
    )

# ── Health check ──────────────────────────────────────────────────────────────
@app.route('/', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "copies": len(copies),
        "exam": exam_status['status']
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
