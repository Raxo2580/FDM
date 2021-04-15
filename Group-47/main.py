from flask import Flask, render_template, request, redirect, url_for, flash, session, logging
from flask_mysqldb import MySQL

from functools import wraps



app= Flask(__name__)
app.secret_key="flash message"

app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="fdmapp"
mysql=MySQL(app)

@app.route('/')

def Index():
    if session.get('position') == "ADMIN":
        flash('You are now logged in', 'success')
        return redirect(url_for('Admin'))
    elif session.get('position') == "MANAGER":
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM employees WHERE username=%s", (session.get('username'),))
        id_data = cur.fetchone()
        flash('You are now logged in', 'success')
        return redirect(url_for('Manager', id_data=id_data))
    elif session.get('position') == "EMPLOYEE":
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM employees WHERE username=%s", (session.get('username'),))
        id_data = cur.fetchone()
        flash('You are now logged in', 'success')
        return redirect(url_for('Employee', id_data=id_data))
    else:
        return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('position') == "ADMIN":
        flash('You are now logged in', 'success')
        return redirect(url_for('Admin'))
    elif session.get('position') == "MANAGER":
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM employees WHERE username=%s", (session.get('username'),))
        id_data = cur.fetchone()
        flash('You are now logged in', 'success')
        return redirect(url_for('Manager', id_data=id_data))
    elif session.get('position') == "EMPLOYEE":
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM employees WHERE username=%s", (session.get('username'),))
        id_data = cur.fetchone()
        flash('You are now logged in', 'success')
        return redirect(url_for('Employee', id_data=id_data))
    else:
        if request.method == 'POST':
            # Get Form Fields
            username = request.form['username']
            password_a = request.form['password']

            cur = mysql.connection.cursor()

            # Get user by username
            result = cur.execute("select position from employees where username=%s and password=%s", (username, password_a))


            if result > 0:
                position, = cur.fetchone()
                userid = cur.execute("select id from employees where username=%s", (username,))
                uid, = cur.fetchone()
                #flash('You are now logged in', 'success')
                session['position'] = position
                if position == 'ADMIN':
                    session['logged_in'] = True
                    session['username'] = username
                    flash('You are now logged in', 'success')
                    return redirect(url_for('Admin'))
                elif position == 'MANAGER':
                    session['logged_in'] = True
                    session['username'] = username
                    flash('You are now logged in', 'success')
                    return redirect(url_for('Manager', id_data=uid))
                session['logged_in'] = True
                session['username'] = username
                flash('You are now logged in', 'success')
                return redirect(url_for('Employee', id_data=uid))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)

                cur.close()

        return render_template('login.html')

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/logout', methods=['GET'])
@is_logged_in
def logout():
    session.pop('position', None)
    session.clear

    return redirect(url_for('login',error='Session expired!'))

@app.route('/Admin')
@is_logged_in
def Admin():
    if session['position'] == 'ADMIN':
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM employees")
        data = cur.fetchall()
        cur.close()
        return render_template("index.html", employees=data)
    return redirect(url_for('login',error='Session expired!'))


@app.route('/Manager/<string:id_data>', methods=['POST', 'GET'])
@is_logged_in
def Manager(id_data):
    if session['position'] == 'MANAGER':
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM expenses WHERE status=%s", ("Unverified",))
        data = cur.fetchall()
        cur.close()
        d = [data, id_data]
        return render_template('manager.html', d=d)
    return redirect(url_for('login',error='Session expired!'))


@app.route('/Employee/<string:id_data>', methods=['POST', 'GET'])
@is_logged_in
def Employee(id_data):
    if session['position'] == 'EMPLOYEE' or session['position'] == 'MANAGER':
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM expenses WHERE Uid=%s", (id_data,))
        data = cur.fetchall()
        d = [data, id_data]
        cur.close()
        return render_template('employee.html', d=d)
    return redirect(url_for('login',error='Session expired!'))


@app.route('/insert', methods=['POST'])
@is_logged_in
def insert():
    if session['position'] == 'ADMIN':
        if request.method=="POST":
            flash('Added Successfully')
            name = request.form['name']
            position = request.form['position']
            position = position.upper()
            email = request.form['email']
            username = request.form['username']
            password = request.form['password']

            cur=mysql.connection.cursor()
            cur.execute("INSERT INTO  employees(name, position, email, username, password) VALUES(%s, %s, %s, %s, %s)",(name, position, email, username, password))
            mysql.connection.commit()
            return redirect(url_for('Admin'))
    return redirect(url_for('login',error='Session expired!'))

@app.route('/expense/<string:id_data>', methods=['POST', 'GET'])
@is_logged_in
def expense(id_data):
    if session['position'] == 'MANAGER' or session['position'] == 'EMPLOYEE':
        if request.method =="POST":
            flash('Submitted Successfully')
            subject = request.form['subject']
            comment = request.form['comment']
            cost = request.form['cost']

            cur = mysql.connection.cursor()
            result = cur.execute("SELECT name FROM employees WHERE id=%s", (id_data,))
            owner, = cur.fetchone()
            cur.execute("INSERT INTO  expenses(owner, subject, comment, cost, status, Uid) VALUES(%s, %s, %s, %s, %s, %s)", (owner, subject, comment, cost, "Unverified", id_data))
            mysql.connection.commit()
            return redirect(url_for('Employee', id_data=id_data))
    return redirect(url_for('login',error='Session expired!'))

@app.route('/approve/<string:id_data>', methods = ['POST','GET'])
@is_logged_in
def approve(id_data):
    if session['position'] == 'MANAGER':
        flash('Expense approved!')
        cur = mysql.connection.cursor()
        cur.execute('UPDATE expenses SET status=%s WHERE id=%s', ("Approved", id_data))
        result = cur.execute("SELECT id FROM employees WHERE id=(SELECT Uid FROM expenses WHERE id=%s)", (id_data,))
        uid, = cur.fetchone()
        mysql.connection.commit()
        return redirect(url_for('Manager', id_data=uid))
    return redirect(url_for('login',error='Session expired!'))

@app.route('/disapprove/<string:id_data>', methods = ['POST','GET'])
@is_logged_in
def disapprove(id_data):
    if session['position'] == 'MANAGER':
        flash('Expense disapproved!')
        cur = mysql.connection.cursor()
        cur.execute('UPDATE expenses SET status=%s WHERE id=%s', ("Disapproved", id_data))
        result = cur.execute("SELECT id FROM employees WHERE id=(SELECT Uid FROM expenses WHERE id=%s)", (id_data,))
        uid, = cur.fetchone()
        mysql.connection.commit()
        return redirect(url_for('Manager', id_data=uid))
    return redirect(url_for('login',error='Session expired!'))

@app.route('/update', methods=['POST','GET'])
@is_logged_in
def update():
    if session['position'] == 'ADMIN':
        if request.method=='POST':
            id_data = request.form['id']
            name = request.form['name']
            position = request.form['position']
            position = position.upper()
            email = request.form['email']
            username = request.form['username']
            password = request.form['password']

            cur = mysql.connection.cursor()
            cur.execute("""UPDATE employees SET name=%s, position=%s, email=%s, username=%s, password=%s WHERE id=%s""" ,(name,position,email,username,password, id_data))
            flash("Updated Successfully")
            mysql.connection.commit()
            return redirect(url_for('Admin'))
    return redirect(url_for('login',error='Session expired!'))


@app.route('/delete/<string:id_data>', methods = ['POST','GET'])
@is_logged_in
def delete(id_data):
    if session['position'] == 'ADMIN':
        flash('Deleted Successfully')
        cur = mysql.connection.cursor()
        cur.execute('DELETE FROM employees WHERE id=%s', (id_data) )
        mysql.connection.commit()
        return redirect(url_for('Admin'))
    return redirect(url_for('login',error='Session expired!'))

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/recover', methods = ['POST', 'GET'])
def recover():
    account = request.form['account']
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM employees WHERE username=%s", (account,))
    try:
        uid, = cur.fetchone()
        cur.execute("SELECT Q1, Q2, Q3 FROM employees WHERE id=%s", (uid,))
        data = cur.fetchall()
        mysql.connection.commit()
        return render_template('recover.html', d=[data, uid])
    except TypeError:
        error = 'User does not exist!'
        return render_template('login.html', error=error)

@app.route('/verify/<string:id_data>', methods = ['POST', 'GET'])
def verify(id_data):
    a = [request.form['A1'], request.form['A2'], request.form['A3']]
    cur = mysql.connection.cursor()
    cur.execute("SELECT A1 FROM employees WHERE id=%s", (id_data,))
    a1, = cur.fetchone()
    cur.execute("SELECT A2 FROM employees WHERE id=%s", (id_data,))
    a2, = cur.fetchone()
    cur.execute("SELECT A3 FROM employees WHERE id=%s", (id_data,))
    a3, = cur.fetchone()
    answer = [a1, a2, a3]
    print(answer)
    for i in range(0,3):
        if answer[i] != a[i]:
            error = 'Your answers does not match'
            return render_template('login.html', error=error)
    return render_template('changePass.html', d=id_data)
@app.route('/changePass/<string:id_data>', methods = ['POST', 'GET'])
def changePass(id_data):
    password = request.form['newPass']
    confirm = request.form['confirm']
    if password == confirm:
        cur = mysql.connection.cursor()
        cur.execute("""UPDATE employees SET password=%s WHERE id=%s""", (password, id_data))
        flash("Updated Successfully")
        mysql.connection.commit()
        return redirect('/login')
    else:
        flash("Confirmation does not match!")
        return render_template('changePass.html', d=id_data)
if __name__=="__main__":
    app.run(debug=True)