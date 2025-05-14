import pymysql
pymysql.install_as_MySQLdb()  # Заміна MySQLdb на PyMySQL

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import re
from datetime import datetime, time, timedelta

app = Flask(__name__)
app.secret_key = 'many random bytes'

# Конфігурація підключення до бази даних
app.config['MYSQL_HOST'] = 'yamabiko.proxy.rlwy.net'
app.config['MYSQL_PORT'] = 36229
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'RkktkRGZwdXAwXkEwtecHgYSdJEKGjFj'
app.config['MYSQL_DB'] = 'railway'

# Функція для створення підключення до бази даних
def get_db_connection():
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        port=app.config['MYSQL_PORT'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB'],
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/contestants_table')
def contestants():
    if 'access_right' not in session:
        return redirect(url_for('login'))

    access_right = session['access_right']
    search_query = request.args.get('query', '')

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if search_query:
            search_query = f"%{search_query}%"
            cur.execute("""
                SELECT * FROM contestant
                WHERE
                    contestant_id LIKE %s OR
                    name LIKE %s OR
                    surname LIKE %s OR
                    city LIKE %s OR
                    age LIKE %s
                ORDER BY contestant_id ASC
            """, (search_query, search_query, search_query, search_query, search_query))
        else:
            cur.execute("SELECT * FROM contestant ORDER BY contestant_id ASC")

        contestants_data = cur.fetchall()
        cur.close()
        conn.close()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(contestants_data)

        return render_template('contestants_table.html', contestants=contestants_data, role=access_right)

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/songs_table')
def songs():
    if 'access_right' not in session:
        return redirect(url_for('login'))

    access_right = session['access_right']
    search_query = request.args.get('query', '')

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if search_query:
            search_query = f"%{search_query}%"
            if access_right == 'guest':
                query = """
                    SELECT
                        s.song_id,
                        s.title,
                        CONCAT(c.name, ' ', c.surname) AS contestant_name
                    FROM
                        Song s
                    JOIN
                        Contestant c ON s.contestant_id = c.contestant_id
                    WHERE
                        s.song_id LIKE %s OR
                        s.title LIKE %s OR
                        c.name LIKE %s OR
                        c.surname LIKE %s
                    ORDER BY
                        s.song_id ASC
                """
                cur.execute(query, (search_query, search_query, search_query, search_query))
            else:
                query = """
                    SELECT
                        song_id,
                        title,
                        contestant_id
                    FROM
                        Song
                    WHERE
                        song_id LIKE %s OR
                        title LIKE %s OR
                        contestant_id LIKE %s
                    ORDER BY
                        song_id ASC
                """
                cur.execute(query, (search_query, search_query, search_query))
        else:
            if access_right == 'guest':
                query = """
                    SELECT
                        s.song_id,
                        s.title,
                        CONCAT(c.name, ' ', c.surname) AS contestant_name
                    FROM
                        Song s
                    JOIN
                        Contestant c ON s.contestant_id = c.contestant_id
                    ORDER BY
                        s.song_id ASC
                """
            else:
                query = "SELECT * FROM Song ORDER BY song_id ASC"
            cur.execute(query)

        songs_data = cur.fetchall()
        cur.close()
        conn.close()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(songs_data)

        return render_template('songs_table.html', songs=songs_data, role=access_right)

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/broadcasts_table')
def broadcasts():
    if 'access_right' not in session:
        return redirect(url_for('login'))

    access_right = session['access_right']
    search_query = request.args.get('query', '')

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if search_query:
            search_query = f"%{search_query}%"
            cur.execute("""
                SELECT * FROM broadcast
                WHERE
                    broadcast_id LIKE %s OR
                    description LIKE %s OR
                    broadcast_date LIKE %s OR
                    broadcast_time LIKE %s
                ORDER BY broadcast_id ASC
            """, (search_query, search_query, search_query, search_query))
        else:
            cur.execute("SELECT * FROM broadcast ORDER BY broadcast_id ASC")

        broadcasts_data = cur.fetchall()
        cur.close()
        conn.close()

        def convert_for_json(value):
            if isinstance(value, datetime):
                return value.strftime('%Y-%m-%d')
            elif isinstance(value, timedelta):
                return str(value)
            return value

        broadcasts_list = []
        for broadcast in broadcasts_data:
            broadcasts_list.append(tuple(convert_for_json(b) if isinstance(b, (datetime, timedelta)) else b for b in broadcast))

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(broadcasts_list)

        return render_template('broadcasts_table.html', broadcasts=broadcasts_data, role=access_right)

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/performances_table')
def performances():
    if 'access_right' not in session:
        return redirect(url_for('login'))

    access_right = session['access_right']
    search_query = request.args.get('query', '')

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if search_query:
            search_query = f"%{search_query}%"
            if access_right == 'guest':
                query = """
                    SELECT
                        p.performance_id,
                        b.description AS broadcast_description,
                        CONCAT(c.name, ' ', c.surname) AS contestant_name,
                        s.title AS song_title,
                        p.sequence_number
                    FROM
                        Performance p
                    JOIN
                        Broadcast b ON p.broadcast_id = b.broadcast_id
                    JOIN
                        Contestant c ON p.contestant_id = c.contestant_id
                    JOIN
                        Song s ON p.song_id = s.song_id
                    WHERE
                        p.performance_id LIKE %s OR
                        b.description LIKE %s OR
                        c.name LIKE %s OR
                        c.surname LIKE %s OR
                        s.title LIKE %s OR
                        CAST(p.sequence_number AS CHAR) LIKE %s
                    ORDER BY
                        p.performance_id ASC
                """
                cur.execute(query, (search_query, search_query, search_query, search_query, search_query, search_query))
            else:
                query = """
                    SELECT
                        performance_id,
                        broadcast_id,
                        contestant_id,
                        song_id,
                        sequence_number
                    FROM
                        Performance
                    WHERE
                        performance_id LIKE %s OR
                        broadcast_id LIKE %s OR
                        contestant_id LIKE %s OR
                        song_id LIKE %s OR
                        sequence_number LIKE %s
                    ORDER BY
                        broadcast_id ASC
                """
                cur.execute(query, (search_query, search_query, search_query, search_query, search_query))
        else:
            if access_right == 'guest':
                query = """
                    SELECT
                        p.performance_id,
                        b.description AS broadcast_description,
                        CONCAT(c.name, ' ', c.surname) AS contestant_name,
                        s.title AS song_title,
                        p.sequence_number
                    FROM
                        Performance p
                    JOIN
                        Broadcast b ON p.broadcast_id = b.broadcast_id
                    JOIN
                        Contestant c ON p.contestant_id = c.contestant_id
                    JOIN
                        Song s ON p.song_id = s.song_id
                    ORDER BY
                        p.broadcast_id, p.sequence_number ASC
                """
            else:
                query = "SELECT * FROM Performance ORDER BY broadcast_id, sequence_number ASC"
            cur.execute(query)

        performances_data = cur.fetchall()
        cur.close()
        conn.close()

        def convert_for_json(value):
            if isinstance(value, datetime):
                return value.strftime('%Y-%m-%d')
            elif isinstance(value, timedelta):
                return str(value)
            return value

        performances_list = []
        for performance in performances_data:
            performances_list.append(tuple(convert_for_json(p) if isinstance(p, (datetime, timedelta)) else p for p in performance))

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(performances_list)

        return render_template('performances_table.html', performances=performances_data, role=access_right)

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/smses_table')
def smses():
    if 'access_right' not in session:
        return redirect(url_for('login'))

    access_right = session['access_right']
    search_query = request.args.get('query', '')

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if access_right == 'guest':
            if search_query:
                search_query = f"%{search_query}%"
                cur.execute("""
                    SELECT
                        SMSes.sms_id,
                        SMSes.phone_number,
                        Broadcast.description AS broadcast_description,
                        CONCAT(Contestant.name, ' ', Contestant.surname) AS contestant_full_name
                    FROM
                        smses
                    JOIN
                        Broadcast ON SMSes.broadcast_id = Broadcast.broadcast_id
                    JOIN
                        Contestant ON SMSes.contestant_id = Contestant.contestant_id
                    WHERE
                        SMSes.sms_id LIKE %s OR
                        SMSes.phone_number LIKE %s OR
                        Broadcast.description LIKE %s OR
                        CONCAT(Contestant.name, ' ', Contestant.surname) LIKE %s
                    ORDER BY
                        SMSes.broadcast_id ASC
                """, (search_query, search_query, search_query, search_query))
            else:
                cur.execute("""
                    SELECT
                        SMSes.sms_id,
                        SMSes.phone_number,
                        Broadcast.description AS broadcast_description,
                        CONCAT(Contestant.name, ' ', Contestant.surname) AS contestant_full_name
                    FROM
                        smses
                    JOIN
                        Broadcast ON SMSes.broadcast_id = Broadcast.broadcast_id
                    JOIN
                        Contestant ON SMSes.contestant_id = Contestant.contestant_id
                    ORDER BY
                        SMSes.broadcast_id ASC
                """)
        else:
            if search_query:
                search_query = f"%{search_query}%"
                cur.execute("""
                    SELECT * FROM smses
                    WHERE
                        sms_id LIKE %s OR
                        phone_number LIKE %s OR
                        broadcast_id LIKE %s OR
                        contestant_id LIKE %s
                    ORDER BY
                        contestant_id ASC
                """, (search_query, search_query, search_query, search_query))
            else:
                cur.execute("SELECT * FROM smses ORDER BY broadcast_id, contestant_id ASC")

        smses_data = cur.fetchall()
        cur.close()
        conn.close()

        def convert_for_json(value):
            if isinstance(value, datetime):
                return value.strftime('%Y-%m-%d')
            elif isinstance(value, timedelta):
                return str(value)
            return value

        smses_list = []
        for sms in smses_data:
            smses_list.append(tuple(convert_for_json(b) if isinstance(b, (datetime, timedelta)) else b for b in sms))

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(smses_list)

        return render_template('smses_table.html', smses=smses_data, role=access_right)

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/calls_table')
def calls():
    if 'access_right' not in session:
        return redirect(url_for('login'))

    access_right = session['access_right']
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        search_query = request.args.get('query', '')

        if access_right == 'guest':
            if search_query:
                search_query = f"%{search_query}%"
                cur.execute("""
                    SELECT
                        Calls.call_id,
                        Calls.phone_number,
                        Broadcast.description AS broadcast_description,
                        CONCAT(Contestant.name, ' ', Contestant.surname) AS contestant_full_name
                    FROM
                        Calls
                    JOIN
                        Broadcast ON Calls.broadcast_id = Broadcast.broadcast_id
                    JOIN
                        Contestant ON Calls.contestant_id = Contestant.contestant_id
                    WHERE
                        Calls.phone_number LIKE %s OR
                        Broadcast.description LIKE %s OR
                        CONCAT(Contestant.name, ' ', Contestant.surname) LIKE %s
                    ORDER BY
                        Calls.broadcast_id ASC
                """, (search_query, search_query, search_query))
            else:
                cur.execute("""
                    SELECT
                        Calls.call_id,
                        Calls.phone_number,
                        Broadcast.description AS broadcast_description,
                        CONCAT(Contestant.name, ' ', Contestant.surname) AS contestant_full_name
                    FROM
                        Calls
                    JOIN
                        Broadcast ON Calls.broadcast_id = Broadcast.broadcast_id
                    JOIN
                        Contestant ON Calls.contestant_id = Contestant.contestant_id
                    ORDER BY
                        Calls.broadcast_id ASC
                """)
        else:
            if search_query:
                search_query = f"%{search_query}%"
                cur.execute("""
                    SELECT
                        Calls.call_id,
                        Calls.phone_number,
                        Calls.broadcast_id,
                        Calls.contestant_id,
                        Broadcast.description AS broadcast_description,
                        CONCAT(Contestant.name, ' ', Contestant.surname) AS contestant_full_name
                    FROM
                        Calls
                    JOIN
                        Broadcast ON Calls.broadcast_id = Broadcast.broadcast_id
                    JOIN
                        Contestant ON Calls.contestant_id = Contestant.contestant_id
                    WHERE
                        Calls.call_id LIKE %s OR
                        Calls.phone_number LIKE %s OR
                        Calls.broadcast_id LIKE %s OR
                        Calls.contestant_id LIKE %s OR
                        Broadcast.description LIKE %s OR
                        CONCAT(Contestant.name, ' ', Contestant.surname) LIKE %s
                    ORDER BY
                        Calls.call_id ASC
                """, (search_query, search_query, search_query, search_query, search_query, search_query))
            else:
                cur.execute("""
                    SELECT
                        Calls.call_id,
                        Calls.phone_number,
                        Calls.broadcast_id,
                        Calls.contestant_id,
                        Broadcast.description AS broadcast_description,
                        CONCAT(Contestant.name, ' ', Contestant.surname) AS contestant_full_name
                    FROM
                        Calls
                    JOIN
                        Broadcast ON Calls.broadcast_id = Broadcast.broadcast_id
                    JOIN
                        Contestant ON Calls.contestant_id = Contestant.contestant_id
                    ORDER BY
                        Calls.call_id ASC
                """)

        calls_data = cur.fetchall()
        cur.close()
        conn.close()

        def convert_for_json(value):
            if isinstance(value, datetime):
                return value.strftime('%Y-%m-%d')
            elif isinstance(value, timedelta):
                return str(value)
            return value

        calls_list = []
        for call in calls_data:
            calls_list.append(tuple(convert_for_json(b) if isinstance(b, (datetime, timedelta)) else b for b in call))

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(calls_list)

        return render_template('calls_table.html', calls=calls_data, role=access_right)

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/juries_table')
def juries():
    if 'access_right' not in session:
        return redirect(url_for('login'))

    access_right = session['access_right']
    search_query = request.args.get('query', '')

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if search_query:
            search_query = f"%{search_query}%"
            cur.execute("""
                SELECT * FROM jury
                WHERE
                    jury_id LIKE %s OR
                    name LIKE %s OR
                    surname LIKE %s OR
                    position LIKE %s
                ORDER BY jury_id ASC
            """, (search_query, search_query, search_query, search_query))
        else:
            cur.execute("SELECT * FROM jury ORDER BY jury_id ASC")

        juries_data = cur.fetchall()
        cur.close()
        conn.close()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(juries_data)

        return render_template('juries_table.html', juries=juries_data, role=access_right)

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/juryVoting_table')
def juryVoting():
    if 'access_right' not in session:
        return redirect(url_for('login'))

    access_right = session['access_right']
    search_query = request.args.get('query', '')

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if access_right == 'guest':
            if search_query:
                search_query = f"%{search_query}%"
                cur.execute("""
                    SELECT
                        JuryVoting.vote_id,
                        CONCAT(Contestant.name, ' ', Contestant.surname) AS contestant_full_name,
                        CONCAT(Jury.name, ' ', Jury.surname) AS jury_full_name,
                        Broadcast.description AS broadcast_description,
                        JuryVoting.score
                    FROM
                        JuryVoting
                    JOIN
                        Contestant ON JuryVoting.contestant_id = Contestant.contestant_id
                    JOIN
                        Jury ON JuryVoting.jury_id = Jury.jury_id
                    JOIN
                        Broadcast ON JuryVoting.broadcast_id = Broadcast.broadcast_id
                    WHERE
                        JuryVoting.vote_id LIKE %s OR
                        Contestant.name LIKE %s OR
                        Contestant.surname LIKE %s OR
                        Jury.name LIKE %s OR
                        Jury.surname LIKE %s OR
                        Broadcast.description LIKE %s OR
                        CAST(JuryVoting.score AS CHAR) LIKE %s
                    ORDER BY
                        JuryVoting.vote_id ASC
                """, (search_query, search_query, search_query, search_query, search_query, search_query, search_query))
            else:
                cur.execute("""
                    SELECT
                        JuryVoting.vote_id,
                        CONCAT(Contestant.name, ' ', Contestant.surname) AS contestant_full_name,
                        CONCAT(Jury.name, ' ', Jury.surname) AS jury_full_name,
                        Broadcast.description AS broadcast_description,
                        JuryVoting.score
                    FROM
                        JuryVoting
                    JOIN
                        Contestant ON JuryVoting.contestant_id = Contestant.contestant_id
                    JOIN
                        Jury ON JuryVoting.jury_id = Jury.jury_id
                    JOIN
                        Broadcast ON JuryVoting.broadcast_id = Broadcast.broadcast_id
                    ORDER BY
                        JuryVoting.vote_id ASC
                """)
        else:
            if search_query:
                search_query = f"%{search_query}%"
                cur.execute("""
                    SELECT * FROM JuryVoting
                    WHERE
                        vote_id LIKE %s OR
                        contestant_id LIKE %s OR
                        jury_id LIKE %s OR
                        broadcast_id LIKE %s OR
                        CAST(score AS CHAR) LIKE %s
                    ORDER BY vote_id ASC
                """, (search_query, search_query, search_query, search_query, search_query))
            else:
                cur.execute("SELECT * FROM JuryVoting ORDER BY broadcast_id, jury_id, contestant_id ASC")

        juryVoting_data = cur.fetchall()
        cur.close()
        conn.close()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(juryVoting_data)

        return render_template('juryVoting_table.html', juryVoting=juryVoting_data, role=access_right)

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    flash('Ви успішно вийшли із системи', 'info')
    return redirect(url_for('login'))

@app.route('/home')
def Index():
    if 'access_right' not in session:
        return redirect(url_for('login'))

    access_right = session['access_right']
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM contestant ORDER BY contestant_id ASC")
        workers_data = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('index2.html', workers=workers_data, role=access_right)
    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM `keys` WHERE login=%s AND password=%s", (login, password))
            user = cur.fetchone()
            cur.close()
            conn.close()

            if user:
                session['login'] = user['login']
                session['access_right'] = user['access_right']
                print(f"User logged in: {user['login']}, Role: {user['access_right']}")
                flash(f'Авторизація успішна. Вітаємо, {user["login"]}!', 'info')
                return redirect(url_for('Index'))
            else:
                flash('Невірний логін або пароль', 'error')
                return render_template('login.html')

        except Exception as e:
            print("Error:", e)
            flash('Сталася помилка при авторизації', 'error')
            return render_template('login.html')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        access_right = 'guest'

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) FROM `keys` WHERE login = %s", (login,))
            existing_user_count = cur.fetchone()['COUNT(*)']

            if existing_user_count > 0:
                flash('Логін вже існує. Спробуйте інший логін.', 'error')
                cur.close()
                conn.close()
                return redirect(url_for('register'))

            cur.execute("INSERT INTO `keys` (login, password, access_right) VALUES (%s, %s, %s)", (login, password, access_right))
            conn.commit()
            cur.close()
            conn.close()

            flash('Реєстрація успішна. Ви можете увійти як гість.', 'info')
            return redirect(url_for('login'))

        except Exception as e:
            print("Error:", e)
            flash('Сталася помилка при реєстрації', 'error')
            return render_template('register.html')

    return render_template('register.html')

@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    if request.method == 'POST':
        login = request.form['login']

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT password FROM `keys` WHERE login=%s", (login,))
            result = cur.fetchone()
            cur.close()
            conn.close()

            if result:
                password = result['password']
                flash(f'Ваш пароль: {password}', 'info')
            else:
                flash('Логін не знайдено', 'error')

        except Exception as e:
            print("Error:", e)
            flash('Сталася помилка при відновленні пароля', 'error')

    return render_template('login.html')

@app.route('/adminpanel')
def adminpanel():
    if 'access_right' not in session:
        return redirect(url_for('login'))

    user_role = session['access_right']
    if user_role == 'owner':
        allowed_roles = ['administrator', 'operator', 'guest']
    elif user_role == 'administrator':
        allowed_roles = ['operator', 'guest']
    else:
        flash('У вас немає прав для доступу до цієї сторінки.', 'error')
        return redirect(url_for('Index'))

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM `keys` ORDER BY id ASC")
        users_data = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('adminpanel.html', allowed_roles=allowed_roles, users=users_data, role=user_role)
    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/add_user', methods=['POST'])
def add_user():
    if 'access_right' not in session:
        flash('Будь ласка, увійдіть для доступу до цієї сторінки.', 'error')
        return redirect(url_for('login'))

    login = request.form['login']
    password = request.form['password']
    access_right = request.form['access_right']
    user_role = session['access_right']

    allowed_roles = ['administrator', 'operator', 'guest'] if user_role == 'owner' else ['operator', 'guest']
    if access_right not in allowed_roles:
        flash('Недопустима роль доступу.', 'error')
        return redirect(url_for('adminpanel'))

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM `keys` WHERE login = %s", [login])
        existing_user = cur.fetchone()
        if existing_user:
            flash('Користувач з таким логіном вже існує.', 'error')
            return redirect(url_for('adminpanel'))

        cur.execute("INSERT INTO `keys` (login, password, access_right) VALUES (%s, %s, %s)",
                    (login, password, access_right))
        conn.commit()
        cur.close()
        conn.close()

        flash('Користувача успішно додано.', 'info')
        return redirect(url_for('adminpanel'))

    except Exception as e:
        print("Error:", e)
        flash('Сталася помилка при додаванні користувача', 'error')
        return redirect(url_for('adminpanel'))

@app.route('/update_user/<string:user_id>', methods=['POST'])
def update_user(user_id):
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        access_right = request.form['access_right']

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            if password:
                cur.execute("""
                    UPDATE `keys`
                    SET login=%s, password=%s, access_right=%s
                    WHERE id=%s
                """, (login, password, access_right, user_id))
            else:
                cur.execute("""
                    UPDATE `keys`
                    SET login=%s, access_right=%s
                    WHERE id=%s
                """, (login, access_right, user_id))

            conn.commit()
            cur.close()
            conn.close()

            flash("Користувача оновлено", 'info')
            return redirect(url_for('adminpanel'))

        except Exception as e:
            print("Error:", e)
            flash('Сталася помилка при оновленні користувача', 'error')
            return redirect(url_for('adminpanel'))

@app.route('/delete_user/<string:user_id>', methods=['GET'])
def delete_user(user_id):
    flash("Користувач успішно видалений", 'info')

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM `keys` WHERE id=%s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('adminpanel'))
    except Exception as e:
        print("Error:", e)
        flash('Сталася помилка при видаленні користувача', 'error')
        return redirect(url_for('adminpanel'))

@app.route('/delete_contestant/<string:contestant_id>', methods=['GET'])
def delete_contestant(contestant_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Contestant WHERE contestant_id=%s", (contestant_id,))
        conn.commit()
        cur.close()
        conn.close()
        flash("Конкурсанта успішно вилучено", "info")
    except pymysql.IntegrityError as e:
        if 'foreign key constraint fails' in str(e):
            flash("Цього конкурсанта не можливо видалити", 'error')
        else:
            flash("An error occurred while deleting the contestant.", "error")
    except Exception as e:
        print("Error:", e)
        flash("An unexpected error occurred while deleting the contestant.", "error")

    return redirect(url_for('contestants'))

@app.route('/delete_song/<string:song_id>', methods=['GET'])
def delete_song(song_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Song WHERE song_id=%s", (song_id,))
        conn.commit()
        cur.close()
        conn.close()
        flash("Song has been deleted successfully", "info")
    except pymysql.IntegrityError as e:
        if 'foreign key constraint fails' in str(e):
            flash("This song cannot be deleted because it is associated with a contestant.", 'error')
        else:
            flash("An error occurred while deleting the song.", "error")
    except Exception as e:
        print("Error:", e)
        flash("An unexpected error occurred while deleting the song.", "error")

    return redirect(url_for('songs'))

@app.route('/delete_broadcast/<string:broadcast_id>', methods=['GET'])
def delete_broadcast(broadcast_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Broadcast WHERE broadcast_id=%s", (broadcast_id,))
        conn.commit()
        cur.close()
        conn.close()
        flash("Broadcast has been deleted successfully", "info")
    except pymysql.IntegrityError as e:
        if 'foreign key constraint fails' in str(e):
            flash("This broadcast cannot be deleted because it is associated with another entity.", "error")
        else:
            flash("An error occurred while deleting the broadcast.", "error")
    except pymysql.Error as e:
        flash("An unexpected error occurred while deleting the broadcast.", "error")

    return redirect(url_for('broadcasts'))

@app.route('/delete_sms/<string:sms_id>', methods=['GET'])
def delete_sms(sms_id):
    flash("SMS has been deleted successfully", 'info')

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM `smses` WHERE sms_id=%s", (sms_id,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('smses'))
    except Exception as e:
        print("Error:", e)
        flash('Сталася помилка при видаленні SMS', 'error')
        return redirect(url_for('smses'))

@app.route('/delete_call/<string:call_id>', methods=['GET'])
def delete_call(call_id):
    flash("Call has been deleted successfully", "info")

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM `calls` WHERE call_id=%s", (call_id,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('calls'))
    except Exception as e:
        print("Error:", e)
        flash('Сталася помилка при видаленні дзвінка', 'error')
        return redirect(url_for('calls'))

@app.route('/delete_performance/<string:performance_id>', methods=['GET'])
def delete_performance(performance_id):
    flash("Виступ успішно вилучено", "info")

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM `performance` WHERE performance_id=%s", (performance_id,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('performances'))
    except Exception as e:
        print("Error:", e)
        flash('Сталася помилка при видаленні виступу', 'error')
        return redirect(url_for('performances'))

@app.route('/delete_jury_vote/<string:vote_id>', methods=['GET'])
def delete_jury_vote(vote_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM `juryvoting` WHERE vote_id=%s", (vote_id,))
        conn.commit()
        cur.close()
        conn.close()
        flash("Голос журі успішно вилучено", "info")
    except pymysql.IntegrityError as e:
        if 'foreign key constraint fails' in str(e):
            flash("Цей голос не можна вилучити, оскільки він пов'язаний з іншими даними.", "error")
        else:
            flash("Сталася помилка під час вилучення голосу.", "error")
    except pymysql.Error as e:
        flash("Сталася неочікувана помилка під час вилучення голосу.", "error")

    return redirect(url_for('juryVoting'))

@app.route('/delete_jury/<string:jury_id>', methods=['GET'])
def delete_jury(jury_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Jury WHERE jury_id=%s", (jury_id,))
        conn.commit()
        cur.close()
        conn.close()
        flash("Jury member has been deleted successfully", "info")
    except pymysql.IntegrityError as e:
        if 'foreign key constraint fails' in str(e):
            flash("This jury member cannot be deleted because they are referenced in another table (e.g., jury votes).", 'error')
        else:
            flash("An error occurred while deleting the jury member.", "error")
    except pymysql.Error as e:
        flash("An unexpected error occurred while deleting the jury member.", "error")

    return redirect(url_for('juries'))

@app.route('/insert_contestant', methods=['POST'])
def insert_contestant():
    if request.method == "POST":
        contestant_name = request.form['contestant_name']
        contestant_surname = request.form['contestant_surname']
        city = request.form['city']
        age = request.form['age']

        if not contestant_name or not contestant_surname or not city or not age:
            flash('Всі поля повинні бути заповнені.', category='error')
            return redirect(url_for('contestants'))

        if not age.isdigit() or int(age) <= 0:
            flash('Вік повинен бути дійсним числом більше 0.', category='error')
            return redirect(url_for('contestants'))

        if len(contestant_name) > 50 or len(contestant_surname) > 50 or len(city) > 50:
            flash('Ім\'я, прізвище та місто не повинні перевищувати 50 символів.', category='error')
            return redirect(url_for('contestants'))

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO Contestant (name, surname, city, age) VALUES (%s, %s, %s, %s)",
                        (contestant_name, contestant_surname, city, age))
            conn.commit()
            flash('Конкурсанта добавлено', category="info")
        except Exception as e:
            conn.rollback()
            flash(f'Сталася помилка: {str(e)}', category='error')
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('contestants'))

@app.route('/insert_song', methods=['POST'])
def insert_song():
    if request.method == "POST":
        song_title = request.form['song_title']
        contestant_id = request.form['contestant_id']

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT * FROM contestant WHERE contestant_id = %s", [contestant_id])
            contestant = cur.fetchone()

            if contestant is None:
                flash('Конкурсант з ID {} не знайдений. Спробуйте ще раз.'.format(contestant_id), category="error")
                return redirect(url_for('songs'))

            cur.execute("SELECT * FROM song WHERE title = %s AND contestant_id = %s", (song_title, contestant_id))
            existing_song = cur.fetchone()

            if existing_song:
                flash('Пісня з назвою "{}" вже існує для цього конкурсанта.'.format(song_title), category="error")
                return redirect(url_for('songs'))

            cur.execute("INSERT INTO song (title, contestant_id) VALUES (%s, %s)", (song_title, contestant_id))
            conn.commit()
            flash('Пісню успішно додано', category="info")
        except Exception as e:
            conn.rollback()
            flash(f'Сталася помилка: {str(e)}', category="error")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('songs'))

@app.route('/insert_broadcast', methods=['POST'])
def insert_broadcast():
    if request.method == "POST":
        description = request.form['description']
        broadcast_date = request.form['broadcast_date']
        broadcast_time = request.form['broadcast_time']

        new_broadcast_datetime = datetime.strptime(f"{broadcast_date} {broadcast_time}", "%Y-%m-%d %H:%M")

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute(
                "SELECT broadcast_date, broadcast_time FROM broadcast ORDER BY broadcast_date DESC, broadcast_time DESC LIMIT 1")
            latest_broadcast = cur.fetchone()

            if latest_broadcast:
                latest_broadcast_time = latest_broadcast['broadcast_time']
                if isinstance(latest_broadcast_time, timedelta):
                    hours, remainder = divmod(latest_broadcast_time.seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    latest_broadcast_time = time(hours, minutes, seconds)

                latest_broadcast_datetime = datetime.combine(latest_broadcast['broadcast_date'], latest_broadcast_time)

                if new_broadcast_datetime <= latest_broadcast_datetime:
                    flash("Новий ефір повинен бути пізніше за останній ефір.", category="error")
                    return redirect(url_for('broadcasts'))

            cur.execute(
                "INSERT INTO broadcast (description, broadcast_date, broadcast_time) VALUES (%s, %s, %s)",
                (description, broadcast_date, broadcast_time))
            conn.commit()
            flash('Трансляцію успішно додано', category="info")
        except Exception as e:
            conn.rollback()
            flash(f'Сталася помилка: {str(e)}', category="error")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('broadcasts'))

@app.route('/get_songs/<contestant_id>', methods=['GET'])
def get_songs(contestant_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT song_id, title FROM song WHERE contestant_id = %s", [contestant_id])
        songs = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(songs)
    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/insert_performance', methods=['POST'])
def insert_performance():
    if request.method == "POST":
        broadcast_id = request.form['broadcast_id']
        contestant_id = request.form['contestant_id']
        song_id = request.form['song_id']
        sequence_number = request.form['sequence_number']

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT * FROM broadcast WHERE broadcast_id = %s", [broadcast_id])
            broadcast = cur.fetchone()
            if broadcast is None:
                flash('Трансляцію з ID {} не знайдено. Спробуйте ще раз.'.format(broadcast_id), category="error")
                return redirect(url_for('performances'))

            cur.execute("SELECT * FROM contestant WHERE contestant_id = %s", [contestant_id])
            contestant = cur.fetchone()
            if contestant is None:
                flash('Конкурсанта з ID {} не знайдено. Спробуйте ще раз.'.format(contestant_id), category="error")
                return redirect(url_for('performances'))

            cur.execute("SELECT * FROM song WHERE song_id = %s AND contestant_id = %s", (song_id, contestant_id))
            song = cur.fetchone()
            if song is None:
                flash('Пісня з ID {} не належить конкурсанту з ID {}. Спробуйте ще раз.'.format(song_id, contestant_id),
                      category="error")
                return redirect(url_for('performances'))

            cur.execute("SELECT * FROM performance WHERE broadcast_id = %s AND sequence_number = %s",
                        (broadcast_id, sequence_number))
            existing_performance = cur.fetchone()
            if existing_performance:
                flash('Виступ з порядковим номером {} вже існує в трансляції з ID {}. Виберіть інший номер.'.format(
                    sequence_number, broadcast_id), category="error")
                return redirect(url_for('performances'))

            cur.execute("SELECT * FROM performance WHERE broadcast_id = %s AND contestant_id = %s",
                        (broadcast_id, contestant_id))
            contestant_performance = cur.fetchone()
            if contestant_performance:
                flash(
                    'Конкурсант з ID {} вже має виступ у трансляції з ID {}. Додавання повторного виступу неможливе.'.format(
                        contestant_id, broadcast_id), category="error")
                return redirect(url_for('performances'))

            cur.execute(
                "INSERT INTO performance (broadcast_id, contestant_id, song_id, sequence_number) VALUES (%s, %s, %s, %s)",
                (broadcast_id, contestant_id, song_id, sequence_number))
            conn.commit()
            flash('Виступ успішно додано', category="info")
        except Exception as e:
            conn.rollback()
            flash(f'Сталася помилка: {str(e)}', category="error")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('performances'))

@app.route('/insert_sms', methods=['POST'])
def insert_sms():
    if request.method == "POST":
        phone_number = request.form['phone_number']
        broadcast_id = request.form['broadcast_id']
        contestant_id = request.form['contestant_id']

        phone_pattern = re.compile(r'^\+?\d{10,15}$')
        if not phone_pattern.match(phone_number):
            flash('Невірний формат номера телефону. Введіть номер у форматі +380XXXXXXXXX.', category="error")
            return redirect(url_for('smses'))

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) FROM Broadcast WHERE broadcast_id = %s", (broadcast_id,))
            if cur.fetchone()['COUNT(*)'] == 0:
                flash('Ефіру з вказаним ID не існує.', category="error")
                return redirect(url_for('smses'))

            cur.execute("SELECT COUNT(*) FROM Contestant WHERE contestant_id = %s", (contestant_id,))
            if cur.fetchone()['COUNT(*)'] == 0:
                flash('Конкурсанта з вказаним ID не існує.', category="error")
                return redirect(url_for('smses'))

            cur.execute(
                "INSERT INTO SMSes (phone_number, broadcast_id, contestant_id) VALUES (%s, %s, %s)",
                (phone_number, broadcast_id, contestant_id))
            conn.commit()
            flash('SMS успішно додано', category="info")
        except Exception as e:
            conn.rollback()
            flash(f'Сталася помилка: {str(e)}', category="error")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('smses'))

@app.route('/insert_call', methods=['POST'])
def insert_call():
    if request.method == "POST":
        phone_number = request.form['phone_number']
        broadcast_id = request.form['broadcast_id']
        contestant_id = request.form['contestant_id']

        phone_pattern = re.compile(r'^\+?\d{10,15}$')
        if not phone_pattern.match(phone_number):
            flash('Невірний формат номера телефону. Введіть номер у форматі +380XXXXXXXXX.', category="error")
            return redirect(url_for('calls'))

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) FROM Broadcast WHERE broadcast_id = %s", (broadcast_id,))
            if cur.fetchone()['COUNT(*)'] == 0:
                flash('Ефіру з вказаним ID не існує.', category="error")
                return redirect(url_for('calls'))

            cur.execute("SELECT COUNT(*) FROM Contestant WHERE contestant_id = %s", (contestant_id,))
            if cur.fetchone()['COUNT(*)'] == 0:
                flash('Конкурсанта з вказаним ID не існує.', category="error")
                return redirect(url_for('calls'))

            cur.execute(
                "INSERT INTO calls (phone_number, broadcast_id, contestant_id) VALUES (%s, %s, %s)",
                (phone_number, broadcast_id, contestant_id))
            conn.commit()
            flash('Дзвінок успішно додано', category="info")
        except Exception as e:
            conn.rollback()
            flash(f'Сталася помилка: {str(e)}', category="error")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('calls'))

@app.route('/insert_jury', methods=['POST'])
def insert_jury():
    if request.method == "POST":
        jury_name = request.form['jury_name']
        jury_surname = request.form['jury_surname']
        position = request.form['position']

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO Jury (name, surname, position) VALUES (%s, %s, %s)",
                (jury_name, jury_surname, position))
            conn.commit()
            flash('Член журі успішно доданий', category="info")
        except Exception as e:
            conn.rollback()
            flash(f'Сталася помилка: {str(e)}', category="error")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('juries'))

@app.route('/insert_juryVote', methods=['POST'])
def insert_juryVote():
    if request.method == "POST":
        contestant_id = request.form['contestant_id']
        jury_id = request.form['jury_id']
        broadcast_id = request.form['broadcast_id']
        score = request.form['score']

        if not contestant_id.isdigit() or not jury_id.isdigit() or not broadcast_id.isdigit() or not score.isdigit():
            flash('Усі значення повинні бути числовими', category='error')
            return redirect(url_for('juryVoting'))

        score = int(score)
        if score < 0 or score > 10:
            flash('Оцінка має бути в межах від 0 до 10', category='error')
            return redirect(url_for('juryVoting'))

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT 1 FROM Contestant WHERE contestant_id = %s", (contestant_id,))
            if not cur.fetchone():
                flash('Конкурсанта з таким ID не існує', category='error')
                return redirect(url_for('juryVoting'))

            cur.execute("SELECT 1 FROM Jury WHERE jury_id = %s", (jury_id,))
            if not cur.fetchone():
                flash('Журі з таким ID не існує', category='error')
                return redirect(url_for('juryVoting'))

            cur.execute("SELECT 1 FROM Broadcast WHERE broadcast_id = %s", (broadcast_id,))
            if not cur.fetchone():
                flash('Ефіру з таким ID не існує', category='error')
                return redirect(url_for('juryVoting'))

            cur.execute(
                "SELECT 1 FROM JuryVoting WHERE contestant_id = %s AND jury_id = %s AND broadcast_id = %s",
                (contestant_id, jury_id, broadcast_id))
            if cur.fetchone():
                flash('Голос від цього журі за цього конкурсанта в цьому ефірі вже існує', category='error')
                return redirect(url_for('juryVoting'))

            cur.execute(
                "INSERT INTO JuryVoting (contestant_id, jury_id, broadcast_id, score) VALUES (%s, %s, %s, %s)",
                (contestant_id, jury_id, broadcast_id, score))
            conn.commit()
            flash('Голос журі успішно додано', category="info")
        except Exception as e:
            conn.rollback()
            flash(f'Сталася помилка: {str(e)}', category="error")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('juryVoting'))

@app.route('/update_broadcast', methods=['POST'])
def update_broadcast():
    if request.method == 'POST':
        broadcast_id = request.form['broadcast_id']
        description = request.form['description']
        broadcast_date = request.form['broadcast_date']
        broadcast_time = request.form['broadcast_time']

        if len(broadcast_time) == 5:
            broadcast_time += ":00"

        new_broadcast_datetime = datetime.strptime(f"{broadcast_date} {broadcast_time}", "%Y-%m-%d %H:%M:%S")

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute(
                "SELECT broadcast_date, broadcast_time FROM broadcast ORDER BY broadcast_date DESC, broadcast_time DESC LIMIT 1")
            latest_broadcast = cur.fetchone()

            if latest_broadcast:
                latest_broadcast_time = latest_broadcast['broadcast_time']
                if isinstance(latest_broadcast_time, timedelta):
                    hours, remainder = divmod(latest_broadcast_time.seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    latest_broadcast_time = time(hours, minutes, seconds)

                latest_broadcast_datetime = datetime.combine(latest_broadcast['broadcast_date'], latest_broadcast_time)

                if new_broadcast_datetime <= latest_broadcast_datetime:
                    flash("Новий ефір повинен бути пізніше за останній ефір.", category="error")
                    return redirect(url_for('broadcasts'))

            cur.execute("""
                UPDATE broadcast
                SET description=%s, broadcast_date=%s, broadcast_time=%s
                WHERE broadcast_id=%s
            """, (description, broadcast_date, broadcast_time, broadcast_id))

            conn.commit()
            flash("Трансляцію успішно оновлено", category="info")
        except Exception as e:
            conn.rollback()
            flash(f'Сталася помилка: {str(e)}', category="error")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('broadcasts'))

@app.route('/update_performance', methods=['POST'])
def update_performance():
    if request.method == 'POST':
        performance_id = request.form['performance_id']
        broadcast_id = request.form['broadcast_id']
        contestant_id = request.form['contestant_id']
        song_id = request.form['song_id']
        sequence_number = request.form['sequence_number']

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT * FROM broadcast WHERE broadcast_id = %s", [broadcast_id])
            broadcast = cur.fetchone()
            if broadcast is None:
                flash('Трансляцію з ID {} не знайдено. Спробуйте ще раз.'.format(broadcast_id), category="error")
                return redirect(url_for('performances'))

            cur.execute("SELECT * FROM contestant WHERE contestant_id = %s", [contestant_id])
            contestant = cur.fetchone()
            if contestant is None:
                flash('Конкурсанта з ID {} не знайдено. Спробуйте ще раз.'.format(contestant_id), category="error")
                return redirect(url_for('performances'))

            cur.execute("SELECT * FROM song WHERE song_id = %s AND contestant_id = %s", (song_id, contestant_id))
            song = cur.fetchone()
            if song is None:
                flash('Пісня з ID {} не належить конкурсанту з ID {}. Спробуйте ще раз.'.format(song_id, contestant_id),
                      category="error")
                return redirect(url_for('performances'))

            cur.execute(
                "SELECT * FROM performance WHERE broadcast_id = %s AND sequence_number = %s AND performance_id != %s",
                (broadcast_id, sequence_number, performance_id))
            existing_performance = cur.fetchone()
            if existing_performance:
                flash('Виступ з порядковим номером {} вже існує в трансляції з ID {}. Виберіть інший номер.'.format(
                    sequence_number, broadcast_id), category="error")
                return redirect(url_for('performances'))

            cur.execute("SELECT * FROM performance WHERE broadcast_id = %s AND contestant_id = %s AND performance_id != %s",
                        (broadcast_id, contestant_id, performance_id))
            contestant_performance = cur.fetchone()
            if contestant_performance:
                flash('Конкурсант з ID {} вже має виступ у трансляції з ID {}. Оновлення неможливе.'.format(contestant_id,
                                                                                                        broadcast_id),
                      category="error")
                return redirect(url_for('performances'))

            cur.execute("""
                UPDATE performance
                SET broadcast_id=%s, contestant_id=%s, song_id=%s, sequence_number=%s
                WHERE performance_id=%s
            """, (broadcast_id, contestant_id, song_id, sequence_number, performance_id))

            conn.commit()
            flash("Виступ оновлено успішно", category="info")
        except Exception as e:
            conn.rollback()
            flash(f'Сталася помилка: {str(e)}', category="error")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('performances'))

@app.route('/update_sms', methods=['POST'])
def update_sms():
    if request.method == "POST":
        sms_id = request.form['sms_id']
        phone_number = request.form['phone_number']
        broadcast_id = request.form['broadcast_id']
        contestant_id = request.form['contestant_id']

        phone_pattern = re.compile(r'^\+?\d{10,15}$')
        if not phone_pattern.match(phone_number):
            flash('Невірний формат номера телефону. Введіть номер у форматі +380XXXXXXXXX.', category="error")
            return redirect(url_for('smses'))

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) FROM Broadcast WHERE broadcast_id = %s", (broadcast_id,))
            if cur.fetchone()['COUNT(*)'] == 0:
                flash('Ефіру з вказаним ID не існує.', category="error")
                return redirect(url_for('smses'))

            cur.execute("SELECT COUNT(*) FROM Contestant WHERE contestant_id = %s", (contestant_id,))
            if cur.fetchone()['COUNT(*)'] == 0:
                flash('Конкурсанта з вказаним ID не існує.', category="error")
                return redirect(url_for('smses'))

            cur.execute(
                "UPDATE SMSes SET phone_number = %s, broadcast_id = %s, contestant_id = %s WHERE sms_id = %s",
                (phone_number, broadcast_id, contestant_id, sms_id))
            conn.commit()
            flash('SMS успішно оновлено', category="info")
        except Exception as e:
            conn.rollback()
            flash(f'Сталася помилка: {str(e)}', category="error")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('smses'))

@app.route('/update_call', methods=['POST'])
def update_call():
    if request.method == "POST":
        call_id = request.form['call_id']
        phone_number = request.form['phone_number']
        broadcast_id = request.form['broadcast_id']
        contestant_id = request.form['contestant_id']

        phone_pattern = re.compile(r'^\+?\d{10,15}$')
        if not phone_pattern.match(phone_number):
            flash('Невірний формат номера телефону. Введіть номер у форматі +380XXXXXXXXX.', category="error")
            return redirect(url_for('calls'))

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) FROM Broadcast WHERE broadcast_id = %s", (broadcast_id,))
            if cur.fetchone()['COUNT(*)'] == 0:
                flash('Ефіру з вказаним ID не існує.', category="error")
                return redirect(url_for('calls'))

            cur.execute("SELECT COUNT(*) FROM Contestant WHERE contestant_id = %s", (contestant_id,))
            if cur.fetchone()['COUNT(*)'] == 0:
                flash('Конкурсанта з вказаним ID не існує.', category="error")
                return redirect(url_for('calls'))

            cur.execute(
                "UPDATE calls SET phone_number = %s, broadcast_id = %s, contestant_id = %s WHERE call_id = %s",
                (phone_number, broadcast_id, contestant_id, call_id))
            conn.commit()
            flash('Дзвінок успішно оновлено', category="info")
        except Exception as e:
            conn.rollback()
            flash(f'Сталася помилка: {str(e)}', category="error")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('calls'))

@app.route('/update_jury', methods=['POST'])
def update_jury():
    if request.method == "POST":
        jury_id = request.form['jury_id']
        jury_name = request.form['jury_name']
        jury_surname = request.form['jury_surname']
        position = request.form['position']

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute(
                "UPDATE Jury SET name = %s, surname = %s, position = %s WHERE jury_id = %s",
                (jury_name, jury_surname, position, jury_id))
            conn.commit()
            flash('Дані члена журі успішно оновлено', category="info")
        except Exception as e:
            conn.rollback()
            flash(f'Сталася помилка: {str(e)}', category="error")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('juries'))

@app.route('/update_juryVote', methods=['POST'])
def update_juryVote():
    if request.method == "POST":
        vote_id = request.form['vote_id']
        contestant_id = request.form['contestant_id']
        jury_id = request.form['jury_id']
        broadcast_id = request.form['broadcast_id']
        score = request.form['score']

        if not vote_id.isdigit() or not contestant_id.isdigit() or not jury_id.isdigit() or not broadcast_id.isdigit() or not score.isdigit():
            flash('Усі значення повинні бути числовими', category='error')
            return redirect(url_for('juryVoting'))

        score = int(score)
        if score < 0 or score > 10:
            flash('Оцінка має бути в межах від 0 до 10', category='error')
            return redirect(url_for('juryVoting'))

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT 1 FROM JuryVoting WHERE vote_id = %s", (vote_id,))
            if not cur.fetchone():
                flash('Голос з таким ID не існує', category='error')
                return redirect(url_for('juryVoting'))

            cur.execute("SELECT 1 FROM Contestant WHERE contestant_id = %s", (contestant_id,))
            if not cur.fetchone():
                flash('Конкурсанта з таким ID не існує', category='error')
                return redirect(url_for('juryVoting'))

            cur.execute("SELECT 1 FROM Jury WHERE jury_id = %s", (jury_id,))
            if not cur.fetchone():
                flash('Журі з таким ID не існує', category='error')
                return redirect(url_for('juryVoting'))

            cur.execute("SELECT 1 FROM Broadcast WHERE broadcast_id = %s", (broadcast_id,))
            if not cur.fetchone():
                flash('Ефіру з таким ID не існує', category='error')
                return redirect(url_for('juryVoting'))

            cur.execute(
                "SELECT 1 FROM JuryVoting WHERE contestant_id = %s AND jury_id = %s AND broadcast_id = %s AND vote_id != %s",
                (contestant_id, jury_id, broadcast_id, vote_id))
            if cur.fetchone():
                flash('Голос від цього журі за цього конкурсанта в цьому ефірі вже існує', category='error')
                return redirect(url_for('juryVoting'))

            cur.execute(
                "UPDATE JuryVoting SET contestant_id = %s, jury_id = %s, broadcast_id = %s, score = %s WHERE vote_id = %s",
                (contestant_id, jury_id, broadcast_id, score, vote_id))
            conn.commit()
            flash('Дані голосу журі успішно оновлено', category="info")
        except Exception as e:
            conn.rollback()
            flash(f'Сталася помилка: {str(e)}', category="error")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('juryVoting'))

@app.route('/update_сontestant', methods=['POST'])
def update_сontestant():
    if request.method == 'POST':
        worker_id = request.form['contestant_id']
        name = request.form['name']
        surname = request.form['surname']
        city = request.form['city']
        age = request.form['age']

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE contestant
                SET name=%s, surname=%s, city=%s, age=%s
                WHERE contestant_id=%s
            """, (name, surname, city, age, worker_id))
            conn.commit()
            flash("Конкурсанта успішно оновлено", 'info')
        except Exception as e:
            conn.rollback()
            flash(f'Сталася помилка: {str(e)}', category="error")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('contestants'))

@app.route('/update_song', methods=['POST'])
def update_song():
    if request.method == 'POST':
        song_id = request.form['song_id']
        song_title = request.form['song_title']
        contestant_id = request.form['contestant_id']

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT * FROM contestant WHERE contestant_id = %s", [contestant_id])
            contestant = cur.fetchone()
            if contestant is None:
                flash('Конкурсант з ID {} не знайдений. Спробуйте ще раз.'.format(contestant_id), category="error")
                return redirect(url_for('songs'))

            cur.execute("""
                SELECT * FROM song
                WHERE title = %s AND contestant_id = %s AND song_id != %s
            """, (song_title, contestant_id, song_id))
            existing_song = cur.fetchone()

            if existing_song:
                flash('Пісня з назвою "{}" вже існує для цього конкурсанта.'.format(song_title), category="error")
                return redirect(url_for('songs'))

            cur.execute("""
                UPDATE song
                SET title=%s, contestant_id=%s
                WHERE song_id=%s
            """, (song_title, contestant_id, song_id))
            conn.commit()
            flash("Пісня успішно оновлена", category="info")
        except Exception as e:
            conn.rollback()
            flash(f'Сталася помилка: {str(e)}', category="error")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('songs'))

@app.route('/queries', methods=['GET', 'POST'])
def queries():
    if 'access_right' not in session:
        return redirect(url_for('login'))

    access_right = session['access_right']
    return render_template('queries.html', role=access_right)

@app.route('/execute_query', methods=['POST'])
def execute_query():
    query_id = request.json.get('query_id')
    params = request.json.get('params', {})

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if query_id == 'query_2':
            broadcast_id = params.get('broadcast_id')
            cur.execute("""
                SELECT
                    c.contestant_id,
                    c.name,
                    c.surname,
                    s.title AS song_title
                FROM
                    Performance p
                    INNER JOIN Contestant c ON p.contestant_id = c.contestant_id
                    INNER JOIN Song s ON p.song_id = s.song_id
                    INNER JOIN Broadcast b ON p.broadcast_id = b.broadcast_id
                WHERE
                    b.broadcast_id = %s
            """, (broadcast_id,))
            results = cur.fetchall()

        elif query_id == 'query_3':
            broadcast_id = params.get('broadcast_id')
            cur.execute("""
                SELECT
                    p.performance_id,
                    c.name AS contestant_name,
                    c.surname AS contestant_surname,
                    s.title AS song_title,
                    p.sequence_number
                FROM Performance p
                JOIN Contestant c ON p.contestant_id = c.contestant_id
                JOIN Song s ON p.song_id = s.song_id
                WHERE p.broadcast_id = %s
                ORDER BY p.sequence_number
            """, (broadcast_id,))
            results = cur.fetchall()

        elif query_id == 'query_4':
            song_title = params.get('song_title')
            cur.execute("""
                SELECT DISTINCT
                    c.contestant_id,
                    c.name,
                    c.surname,
                    c.city,
                    s.title AS song_title
                FROM
                    Performance p
                    INNER JOIN Contestant c ON p.contestant_id = c.contestant_id
                    INNER JOIN Song s ON p.song_id = s.song_id
                WHERE
                    s.title LIKE CONCAT('%%', %s, '%%')
            """, (song_title,))
            results = cur.fetchall()

        elif query_id == 'query_6':
            city_partial = params.get('city_name')
            cur.execute("""
                SELECT DISTINCT
                    c.contestant_id,
                    c.name,
                    c.surname,
                    c.city
                FROM
                    Performance p
                    INNER JOIN Contestant c ON p.contestant_id = c.contestant_id
                WHERE
                    c.city LIKE CONCAT('%%', %s, '%%')
            """, (city_partial,))
            results = cur.fetchall()

        elif query_id == 'query_10':
            cur.execute("""
                SELECT
                    broadcast_id,
                    COUNT(*) AS sms_count
                FROM SMSes
                GROUP BY broadcast_id
                ORDER BY broadcast_id;
            """)
            results = cur.fetchall()

        elif query_id == 'query_11':
            broadcast_id = params.get('broadcast_id')
            cur.execute("""
                SELECT
                    phone_number,
                    COUNT(*) AS call_count
                FROM Calls
                WHERE broadcast_id = %s
                GROUP BY phone_number
                ORDER BY call_count DESC;
            """, (broadcast_id,))
            results = cur.fetchall()

        elif query_id == 'query_7':
            cur.execute("""
                WITH SmsVotes AS (
                    SELECT
                        contestant_id,
                        COUNT(*) AS sms_count
                    FROM SMSes
                    GROUP BY contestant_id
                )
                SELECT
                    c.contestant_id,
                    c.name,
                    c.surname,
                    sv.sms_count
                FROM Contestant c
                JOIN SmsVotes sv ON c.contestant_id = sv.contestant_id
                WHERE sv.sms_count = (SELECT MAX(sms_count) FROM SmsVotes);
            """)
            results = cur.fetchall()

        elif query_id == 'query_12':
            cur.execute("""
                WITH FirstBroadcast AS (
                    SELECT broadcast_id
                    FROM Broadcast
                    ORDER BY broadcast_date, broadcast_time
                    LIMIT 1
                ),
                SmsVotes AS (
                    SELECT
                        sms.contestant_id,
                        COUNT(*) AS sms_count
                    FROM SMSes sms
                    JOIN FirstBroadcast fb ON sms.broadcast_id = fb.broadcast_id
                    GROUP BY sms.contestant_id
                ),
                CallVotes AS (
                    SELECT
                        `call`.contestant_id,
                        COUNT(*) AS call_count
                    FROM Calls `call`
                    JOIN FirstBroadcast fb ON `call`.broadcast_id = fb.broadcast_id
                    GROUP BY `call`.contestant_id
                ),
                JuryVotes AS (
                    SELECT
                        jv.contestant_id,
                        SUM(jv.score) AS jury_score
                    FROM JuryVoting jv
                    JOIN FirstBroadcast fb ON jv.broadcast_id = fb.broadcast_id
                    GROUP BY jv.contestant_id
                )
                SELECT
                    c.contestant_id,
                    c.name,
                    c.surname,
                    COALESCE(sms.sms_count, 0) + COALESCE(call.call_count, 0) + COALESCE(jv.jury_score, 0) AS total_votes
                FROM Contestant c
                JOIN Performance p ON c.contestant_id = p.contestant_id
                JOIN FirstBroadcast fb ON p.broadcast_id = fb.broadcast_id
                LEFT JOIN SmsVotes sms ON c.contestant_id = sms.contestant_id
                LEFT JOIN CallVotes `call` ON c.contestant_id = `call`.contestant_id
                LEFT JOIN JuryVotes jv ON c.contestant_id = jv.contestant_id
                ORDER BY total_votes DESC;
            """)
            results = cur.fetchall()

        elif query_id == 'query_13':
            cur.execute("""
                WITH TotalVotes AS (
                    SELECT
                        c.contestant_id,
                        c.name,
                        c.surname,
                        COALESCE(SUM(sms_count), 0) + COALESCE(SUM(call_count), 0) + COALESCE(SUM(jury_score), 0) AS total_votes
                    FROM Contestant c
                    LEFT JOIN (
                        SELECT
                            contestant_id,
                            COUNT(*) AS sms_count
                        FROM SMSes
                        GROUP BY contestant_id
                    ) sms_votes ON c.contestant_id = sms_votes.contestant_id
                    LEFT JOIN (
                        SELECT
                            contestant_id,
                            COUNT(*) AS call_count
                        FROM Calls
                        GROUP BY contestant_id
                    ) call_votes ON c.contestant_id = call_votes.contestant_id
                    LEFT JOIN (
                        SELECT
                            contestant_id,
                            SUM(score) AS jury_score
                        FROM JuryVoting
                        GROUP BY contestant_id
                    ) jury_votes ON c.contestant_id = jury_votes.contestant_id
                    GROUP BY c.contestant_id, c.name, c.surname
                )
                SELECT
                    contestant_id,
                    name,
                    surname,
                    total_votes
                FROM TotalVotes
                WHERE total_votes < 70;
            """)
            results = cur.fetchall()

        elif query_id == 'query_14':
            cur.execute("""
                WITH SongPerformances AS (
                    SELECT
                        c.contestant_id,
                        c.name AS contestant_name,
                        c.surname AS contestant_surname,
                        s.title AS song_title,
                        COUNT(*) AS performance_count
                    FROM Contestant c
                    JOIN Performance p ON c.contestant_id = p.contestant_id
                    JOIN Song s ON p.song_id = s.song_id
                    GROUP BY c.contestant_id, c.name, c.surname, s.title
                )
                SELECT
                    contestant_id,
                    contestant_name,
                    contestant_surname,
                    song_title,
                    performance_count
                FROM SongPerformances
                ORDER BY contestant_id, song_title;
            """)
            results = cur.fetchall()

        elif query_id == 'query_15':
            cur.execute("""
                SELECT
                    broadcast_id,
                    COALESCE(description, 'No Description') AS description,
                    COALESCE(broadcast_date, '0000-00-00') AS broadcast_date,
                    COALESCE(broadcast_time, '00:00:00') AS broadcast_time
                FROM Broadcast
                ORDER BY broadcast_date, broadcast_time;
            """)
            results = cur.fetchall()

        elif query_id == 'query_16':
            cur.execute("""
                WITH TotalVotes AS (
                    SELECT
                        c.contestant_id,
                        c.name,
                        c.surname,
                        COALESCE(jv.total_jury_score, 0) AS total_jury_score,
                        COALESCE(sms.total_sms_votes, 0) AS total_sms_votes,
                        COALESCE(calls.total_calls, 0) AS total_calls,
                        (COALESCE(jv.total_jury_score, 0) +
                        COALESCE(sms.total_sms_votes, 0) +
                        COALESCE(calls.total_calls, 0)) AS total_score
                    FROM Contestant c
                    LEFT JOIN (
                        SELECT
                            contestant_id,
                            SUM(score) AS total_jury_score
                        FROM JuryVoting
                        GROUP BY contestant_id
                    ) jv ON c.contestant_id = jv.contestant_id
                    LEFT JOIN (
                        SELECT
                            contestant_id,
                            COUNT(*) AS total_sms_votes
                        FROM SMSes
                        GROUP BY contestant_id
                    ) sms ON c.contestant_id = sms.contestant_id
                    LEFT JOIN (
                        SELECT
                            contestant_id,
                            COUNT(*) AS total_calls
                        FROM Calls
                        GROUP BY contestant_id
                    ) calls ON c.contestant_id = calls.contestant_id
                ),
                RankedContestants AS (
                    SELECT
                        contestant_id,
                        name,
                        surname,
                        total_score,
                        RANK() OVER (ORDER BY total_score DESC) AS contestant_rank
                    FROM TotalVotes
                )
                SELECT
                    contestant_id,
                    name,
                    surname,
                    total_score,
                    contestant_rank
                FROM RankedContestants
                WHERE contestant_rank <= 3
                ORDER BY contestant_rank;
            """)
            results = cur.fetchall()

        cur.close()
        conn.close()

        return jsonify(results)

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
