import os, sqlite3
from functools import wraps
from datetime import datetime
from flask import Flask, request, redirect, render_template_string, send_file, session
import pandas as pd

app = Flask(__name__)
app.secret_key = "lvr-2026-final"
LOGIN_USER = "admin"
LOGIN_PASS = "lvr123"

BASE_DIR = os.path.abspath(".")
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
DB_PATH = os.path.join(BASE_DIR, 'database.db')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def login_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if not session.get('logged_in'):
            return redirect('/login')
        return f(*a, **kw)
    return dec

def init_db():
    conn=sqlite3.connect(DB_PATH)
    conn.execute('CREATE TABLE IF NOT EXISTS inmates (inmate_id TEXT PRIMARY KEY, inmate_name TEXT, court_declaring TEXT, judgement_number TEXT, judgement_date TEXT, court_order_file TEXT, gd_no TEXT, police_station TEXT, home_name TEXT, date_of_admission TEXT, history_ticket_file TEXT, age INTEGER, medical_health TEXT)')
    conn.commit(); conn.close()
init_db()

def save_file(f):
    if f and f.filename:
        name=datetime.now().strftime("%H%M%S_")+f.filename
        f.save(os.path.join(UPLOAD_FOLDER,name))
        return name
    return ""

STYLE = """
<style>
body{font-family:Arial;background:#f4f6f9;margin:0;padding:20px}
.box{max-width:900px;margin:auto;background:white;padding:30px;border-radius:12px;box-shadow:0 4px 15px rgba(0,0,0,0.1)}
h2{text-align:center;color:#1a3c6e}
label{font-weight:bold;display:block;margin-top:18px;font-size:16px}
input, textarea, select{width:100%;padding:14px;font-size:16px;border:1.5px solid #ccc;border-radius:8px;margin-top:6px;box-sizing:border-box}
button{width:100%;padding:15px;background:#2c5aa0;color:white;font-size:18px;border:none;border-radius:8px;margin-top:25px;cursor:pointer;font-weight:bold}
</style>
"""

FORM_HTML = STYLE + """
<div class="box">
<h2>LVR Beleghata - Inmate Entry</h2>
<div style="text-align:right"><a href="/list">View List</a> <a href="/logout">Logout</a></div>
<form method="POST" enctype="multipart/form-data">
<label>Inmate ID *</label><input name="inmate_id" required>
<label>Inmate Name *</label><input name="inmate_name" required>
<label>Date of Admission *</label><input type="date" name="date_of_admission" required>
<label>GD No</label><input name="gd_no">
<label>Police Station</label><input name="police_station">
<button>Save Entry</button>
</form></div>
"""

@app.route('/login', methods=['GET','POST'])
def login():
    err=""
    if request.method=='POST':
        if request.form['username']=="admin" and request.form['password']=="lvr123":
            session['logged_in']=True
            return redirect('/')
        else: err="Wrong!"
    return render_template_string(STYLE+f'<div class="box"><h2>LVR Login</h2><p style="color:red">{err}</p><form method="POST"><input name="username" placeholder="admin"><input type="password" name="password" placeholder="lvr123"><button>Login</button></form></div>')

@app.route('/logout')
def logout(): session.clear(); return redirect('/login')

@app.route('/', methods=['GET','POST'])
def form():
    if not session.get('logged_in'): return redirect('/login')
    if request.method=='POST':
        conn=sqlite3.connect(DB_PATH)
        try:
            conn.execute("INSERT INTO inmates VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",(request.form['inmate_id'],request.form.get('inmate_name',''),request.form.get('court_declaring',''),request.form.get('judgement_number',''),request.form.get('judgement_date',''),"",request.form.get('gd_no',''),request.form.get('police_station',''),"",request.form.get('date_of_admission',''),"",None,""))
            conn.commit()
        except Exception as e: return f"ID Exists! {e} <a href='/'>Back</a>"
        finally: conn.close()
        return redirect('/list')
    return render_template_string(FORM_HTML)

@app.route('/list')
def lv():
    if not session.get('logged_in'): return redirect('/login')
    conn=sqlite3.connect(DB_PATH); cur=conn.cursor(); cur.execute("SELECT * FROM inmates ORDER BY date_of_admission DESC"); rows=cur.fetchall(); conn.close()
    html = STYLE + "<div class='box'><h2>List - Total %s</h2><a href='/'>+ New</a> <a href='/export' style='background:green'>Export Excel</a><table border=1>" % len(rows)
    for r in rows: html+=f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[9]}</td></tr>"
    html+="</table></div>"
    return html

@app.route('/export')
def ex():
    if not session.get('logged_in'): return redirect('/login')
    conn=sqlite3.connect(DB_PATH); df=pd.read_sql_query("SELECT * FROM inmates",conn); conn.close()
    path=os.path.join(BASE_DIR,f"LVR_{datetime.now().strftime('%d%m%Y')}.xlsx")
    df.to_excel(path,index=False)
    return send_file(path,as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)