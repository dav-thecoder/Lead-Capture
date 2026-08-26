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
    x.executescript('''CREATE TABLE IF NOT EXISTS leads(id INTEGER PRIMARY KEY,created_at TEXT,name TEXT,phone TEXT,email TEXT,service TEXT,notes TEXT,appointment_date TEXT,appointment_time TEXT,status TEXT DEFAULT 'New'); CREATE TABLE IF NOT EXISTS visits(id INTEGER PRIMARY KEY,visited_at TEXT,ip TEXT,user_agent TEXT,referrer TEXT);''')
    x.commit(); x.close()
init()

def admin_required(f):
    @wraps(f)
    def w(*a,**k):
        return f(*a,**k) if session.get('admin') else redirect(url_for('admin_login'))
    return w

@app.before_request
def visit():
    if request.path.startswith('/admin') or request.endpoint=='static': return
    x=db(); x.execute('INSERT INTO visits(visited_at,ip,user_agent,referrer) VALUES(?,?,?,?)',(datetime.now().isoformat(timespec='seconds'),request.headers.get('X-Forwarded-For',request.remote_addr),request.headers.get('User-Agent','')[:500],request.referrer or '')); x.commit()

@app.route('/',methods=['GET','POST'])
def home():
    if request.method=='POST':
        name=request.form.get('name','').strip(); phone=request.form.get('phone','').strip()
        if not name or not phone: flash('Name and phone are required.'); return redirect('/')
        x=db(); x.execute('INSERT INTO leads(created_at,name,phone,email,service,notes,appointment_date,appointment_time) VALUES(?,?,?,?,?,?,?,?)',(datetime.now().isoformat(timespec='seconds'),name,phone,request.form.get('email',''),request.form.get('service',''),request.form.get('notes',''),request.form.get('appointment_date',''),request.form.get('appointment_time',''))); x.commit(); return redirect('/thank-you')
    return render_template('index.html')

@app.route('/thank-you')
def thanks(): return render_template('thank_you.html')

@app.route('/admin/login',methods=['GET','POST'])
def admin_login():
    if request.method=='POST' and request.form.get('password')==ADMIN_PASSWORD: session['admin']=True; return redirect('/admin')
    return render_template('admin_login.html')

@app.route('/admin')
@admin_required
def admin():
    x=db(); return render_template('admin.html',leads=x.execute('SELECT * FROM leads ORDER BY id DESC').fetchall(),visits=x.execute('SELECT * FROM visits ORDER BY id DESC LIMIT 250').fetchall())

@app.route('/admin/logout')
def logout(): session.clear(); return redirect('/admin/login')

if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)))
