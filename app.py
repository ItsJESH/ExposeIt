import random
from flask import *
import mysql.connector
import datetime
import string
import os
import base64
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'JayShreeMahakal'
UPLOAD_FOLDER = 'static/pics/'
app.config['UPLOAD_DATA'] = UPLOAD_FOLDER
allowed_extensions = ('png', 'jpg', 'jpeg')

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'expoit'
}


def get_connection():
    return mysql.connector.connect(**db_config)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def create_user_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS agents (
        name VARCHAR(255),
        email VARCHAR(255) NOT NULL PRIMARY KEY,
        password VARCHAR(255),
        mobile VARCHAR(255),
        age VARCHAR(255),
        gender VARCHAR(255),
        datejoin VARCHAR(255)
        )
        """
    )
    conn.commit()
    cursor.close()
    conn.close()


def create_data_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS exposes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        text VARCHAR(10000),
        file LONGBLOB,
        fname VARCHAR(255),
        email VARCHAR(255) NOT NULL,
        FOREIGN KEY (email) REFERENCES agents(email),
        dateofpost VARCHAR(255)
        )
        """
    )


def create_del_data():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deletedExposes (
        did INT AUTO_INCREMENT PRIMARY KEY,
        pid varchar(255) NOT NULL,
        text VARCHAR(10000),
        file LONGBLOB,
        fname VARCHAR(255),
        email VARCHAR(255) NOT NULL,
        FOREIGN KEY (email) REFERENCES agents(email),
        dateofpost VARCHAR(255),
        dateofdeleted VARCHAR(255));
    """)
    conn.commit()
    cursor.close()
    conn.close()


create_user_table()
create_data_table()
create_del_data()


@app.route('/')
def home():
    if "email" not in session:
        return redirect(url_for('login'))
    con = get_connection()
    cursor = con.cursor(dictionary=True)
    cursor.execute("SELECT text,file,fname FROM exposes ORDER BY id DESC")
    data = cursor.fetchall()
    # print(data)
    cursor.close()
    con.close()
    fname = None
    for i in data:
        if i["fname"]:
            bdata = base64.b64decode(i["file"])
            file = open(app.config['UPLOAD_DATA'] + i["fname"], 'wb')
            file.write(bdata)
            file.close()
    return render_template('home.html', data=data)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            con = get_connection()
            cur = con.cursor()
            cur.execute("SELECT password FROM agents WHERE email=%s", (email,))
            key = cur.fetchone()
            if key is None:
                flash('User Not Found. Register Now', 'danger')
                return redirect(url_for('login'))
            key = str(key[0])
            if password != key:
                flash('Wrong password', 'danger')
                return redirect(url_for('login'))
            else:
                session['email'] = email
                return redirect(url_for('home'))

        except:
            return "Something went wrong!!"


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html")

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        cpassword = request.form['cpassword']
        mobile = request.form['mobile']
        age = request.form['age']
        gender = request.form['gender']
        datejoin = str(datetime.date.today())

        if password != cpassword:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))

        try:
            con = get_connection()
            cur = con.cursor()
            cur.execute("SELECT email FROM agents WHERE email=%s", (email,))
            result = cur.fetchone()
            if result is not None:
                result = result[0]
                if result == email:
                    flash("Email Already Registered", "danger")
                    return redirect(url_for('register'))

            cur.execute(
                "INSERT INTO agents (name, email, password, mobile, age, gender,datejoin) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                (name, email, password, mobile, age, gender, datejoin))
            con.commit()
            cur.close()
            con.close()
            flash("Registered Successfully", "success")
            return redirect(url_for('register'))
        except:
            return "Something went wrong"


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if "email" not in session:
        return redirect(url_for('login'))
    if request.method == 'GET':
        return render_template('upload.html')

    if request.method == 'POST':
        data = request.form['datawrite']
        email = session['email']
        uploaddate = str(datetime.datetime.today())
        file = request.files['file']
        try:
            if file.filename == '':
                con = get_connection()
                cur = con.cursor()
                cur.execute(
                    "INSERT INTO exposes(text, email, dateofpost) values (%s,%s,%s)", (data, email, uploaddate)
                )
                con.commit()
                cur.close()
                con.close()
                flash("Exposed Successfully", "success")
                return redirect(url_for('upload'))
            else:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_DATA'], filename))
                    file = open(app.config['UPLOAD_DATA'] + filename, 'rb').read()
                    file = base64.b64encode(file)
                    ext = filename.split('.')[-1]
                    nfilename = ''.join(
                        random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in
                        range(7)) + '.' + ext
                    con = get_connection()
                    cur = con.cursor()
                    cur.execute("INSERT INTO exposes(text, email,file,fname, dateofpost) values(%s, %s, %s, %s, %s)",
                                (data, email, file, nfilename, uploaddate))
                    con.commit()
                    cur.close()
                    os.remove(''.join([app.config['UPLOAD_DATA'], filename]))
                    flash("Exposed Successfully", "success")
                    return redirect(url_for('upload'))
                else:
                    flash("File Format not Supported", "danger")
                    return redirect(url_for('upload'))
        except:
            return "Something went wrong"


@app.route('/user', methods=['GET', 'POST'])
def user():
    if "email" not in session:
        return redirect(url_for('login'))

    email = session['email']
    con = get_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM agents WHERE email=%s", (email,))
    userdata = cur.fetchone()
    cur.execute("SELECT id,text,fname,file FROM exposes WHERE email=%s ORDER BY id DESC", (email,))
    userexposes = cur.fetchall()
    cur.close()
    con.close()
    fname = None
    for i in userexposes:
        if (i["fname"]):
            bdata = base64.b64decode(i["file"])
            file = open(app.config['UPLOAD_DATA'] + i["fname"], 'wb')
            file.write(bdata)
            file.close()
    return render_template('user.html', userdata=userdata, userexposes=userexposes)


@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('login'))


@app.route('/dtex/<int:id>')
def dtex(id):
    con = get_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("Select * from exposes WHERE id=%s", (id,))
    result = cur.fetchone()
    cur.execute("DELETE FROM exposes WHERE id=%s", (id,))
    con.commit()
    cur.close()
    con.close()
    con = get_connection()
    cur = con.cursor()
    datatxt = result['text']
    pid = result['id']
    email = result['email']
    pd = result['dateofpost']
    file = result['file']
    fname = result['fname']
    dd = str(datetime.datetime.today())
    if fname is None:
        cur.execute("INSERT INTO deletedExposes(pid,text,email,dateofpost,dateofdeleted) VALUES (%s, %s, %s, %s,%s)",
                    (pid, datatxt, email, pd, dd))

    else:
        cur.execute(
            "INSERT INTO deletedExposes(pid,text,email,file,fname,dateofpost,dateofdeleted) VALUES (%s, %s, %s, %s,%s,%s,%s)",
            (pid, datatxt, email, file, fname, pd, dd))

    con.commit()
    cur.close()
    con.close()
    return redirect(url_for('user'))


@app.route('/tandc')
def tandc():
    return render_template('tandc.html')


if __name__ == '__main__':
    app.run(debug=True)
