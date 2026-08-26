import os, sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g

app=Flask(__name__)
app.secret_key=os.environ.get('SECRET_KEY','change-this-secret')
DB='leads.db'
ADMIN_PASSWORD=os.environ.get('ADMIN_PASSWORD','change-me')

def db():
    if 'db' not in g:
        g.db=sqlite3.connect(DB); g.db.row_factory=sqlite3.Row
    return g.db

@app.teardown_appcontext
def close(e=None):
    x=g.pop('db',None)
    if x: x.close()

def init():
    x=sqlite3.connect(DB)
    x.execute("CREATE TABLE IF NOT EXISTS leads(id INTEGER PRIMARY KEY,created_at TEXT,name TEXT,phone TEXT,email TEXT,service TEXT,notes TEXT,appointment_date TEXT,appointment_time TEXT,status TEXT DEFAULT 'New',source TEXT DEFAULT 'Direct / Unknown')")
    columns=[row[1] for row in x.execute('PRAGMA table_info(leads)').fetchall()]
    if 'source' not in columns:
        x.execute("ALTER TABLE leads ADD COLUMN source TEXT DEFAULT 'Direct / Unknown'")
    x.commit(); x.close()
init()

def admin_required(f):
    @wraps(f)
    def w(*a,**k):
        return f(*a,**k) if session.get('admin') else redirect(url_for('admin_login'))
    return w

@app.route('/',methods=['GET','POST'])
def home():
    if request.method=='POST':
        name=request.form.get('name','').strip(); phone=request.form.get('phone','').strip()
        if not name or not phone: flash('Name and phone are required.'); return redirect('/')
        source=request.form.get('source','').strip() or 'Direct / Unknown'
        x=db(); x.execute('INSERT INTO leads(created_at,name,phone,email,service,notes,appointment_date,appointment_time,source) VALUES(?,?,?,?,?,?,?,?,?)',(datetime.now().isoformat(timespec='seconds'),name,phone,request.form.get('email',''),request.form.get('service',''),request.form.get('notes',''),request.form.get('appointment_date',''),request.form.get('appointment_time',''),source)); x.commit(); return redirect('/thank-you')
    source=request.args.get('source','').strip() or 'Direct / Unknown'
    return render_template('index.html',source=source)

@app.route('/thank-you')
def thanks(): return render_template('thank_you.html')

@app.route('/admin/login',methods=['GET','POST'])
def admin_login():
    if request.method=='POST' and request.form.get('password')==ADMIN_PASSWORD: session['admin']=True; return redirect('/admin')
    return render_template('admin_login.html')

@app.route('/admin')
@admin_required
def admin():
    x=db(); return render_template('admin.html',leads=x.execute('SELECT * FROM leads ORDER BY id DESC').fetchall())

@app.route('/admin/logout')
def logout(): session.clear(); return redirect('/admin/login')

if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)))
