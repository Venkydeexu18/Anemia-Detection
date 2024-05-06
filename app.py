from flask import Flask, render_template, request, redirect, url_for, g, session
import pandas as pd
import pickle
import sqlite3

app = Flask(__name__)
app.secret_key = 'venkydeexu18'

model_path = 'random_forest_model.pkl'
model = pickle.load(open(model_path, 'rb'))

DATABASE = 'users.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS users 
                       (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, password TEXT)''')
        db.commit()

init_db()

def preprocess_data(hemoglobin, gender, mcv):
    gender_mapping = {'Male': 0, 'Female': 1}
    gender = gender_mapping.get(gender, 0)
    data = {'Gender': [gender], 'Hemoglobin': [hemoglobin], 'MCV': [mcv]}
    df = pd.DataFrame(data)
    return df

def predict_anemia(hemoglobin, gender, mcv):
    df = preprocess_data(hemoglobin, gender, mcv)
    prediction = model.predict(df)
    return prediction[0]

def is_logged_in():
    return 'email' in session

@app.route('/')
def index():
    if is_logged_in():
        return redirect(url_for('test'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
            db.commit()
            return redirect(url_for('signin'))
        except sqlite3.IntegrityError:
            error = "Email already exists! Please choose a different email."

    return render_template('signup.html', error=error)

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = cur.fetchone()
        if user:
            session['email'] = email  # Store user's email in session
            return redirect(url_for('test'))
        else:
            error = "Invalid email or password. Please try again."

    return render_template('signin.html', error=error)

@app.route('/test', methods=['GET', 'POST'])
def test():
    if not is_logged_in():
        return redirect(url_for('signin'))  # Redirect to sign-in if not logged in

    if request.method == 'POST':
        hemoglobin = float(request.form['hemoglobin'])
        gender = request.form['gender']
        mcv = float(request.form['mcv'])
        prediction = predict_anemia(hemoglobin, gender, mcv)
        prediction_label = 'Anemic' if prediction == 1 else 'Non Anemic'
        return render_template('result.html', prediction=prediction_label)

    return render_template('test.html')
@app.route('/logout')
def logout():
    session.pop('email', None) 
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
