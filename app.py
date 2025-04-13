from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import difflib

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Home page
@app.route('/')
def home():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    return redirect(url_for('login'))

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Username already exists. <a href='/register'>Try again</a>"

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_input = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password_input):
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return "Invalid credentials. <a href='/login'>Try again</a>"

    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Couple Matching Result
@app.route('/result', methods=['POST'])
def result():
    data = request.form.to_dict()
    compatibility_score = calculate_compatibility(data)
    duration_prediction = predict_relationship_duration(compatibility_score)
    return render_template('result.html', score=compatibility_score, duration=duration_prediction)

# Show Registered Users
@app.route('/users')
def users_list():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    all_users = User.query.all()
    return render_template('users.html', users=all_users)

# Matching logic
def calculate_compatibility(data):
    score = 0

    # Age
    age_diff = abs(int(data['your_age']) - int(data['partner_age']))
    if age_diff <= 2:
        score += 20
    elif age_diff <= 5:
        score += 10
    elif age_diff <= 10:
        score += 5
    else:
        score -= 5

    # Zodiac
    zodiac_compat = {
        'aries': ['leo', 'sagittarius', 'gemini'],
        'taurus': ['virgo', 'capricorn', 'cancer'],
        'gemini': ['libra', 'aquarius', 'aries'],
        'cancer': ['scorpio', 'pisces', 'taurus'],
        'leo': ['aries', 'sagittarius', 'libra'],
        'virgo': ['taurus', 'capricorn', 'scorpio'],
        'libra': ['gemini', 'aquarius', 'leo'],
        'scorpio': ['cancer', 'pisces', 'virgo'],
        'sagittarius': ['aries', 'leo', 'aquarius'],
        'capricorn': ['taurus', 'virgo', 'pisces'],
        'aquarius': ['gemini', 'libra', 'sagittarius'],
        'pisces': ['cancer', 'scorpio', 'capricorn']
    }

    your_zodiac = data['your_zodiac'].lower().strip()
    partner_zodiac = data['partner_zodiac'].lower().strip()
    if partner_zodiac in zodiac_compat.get(your_zodiac, []):
        score += 15
    elif your_zodiac == partner_zodiac:
        score += 10

    # Hobbies
    your_hobbies = set(x.strip().lower() for x in data['your_hobbies'].split(','))
    partner_hobbies = set(x.strip().lower() for x in data['partner_hobbies'].split(','))
    score += len(your_hobbies & partner_hobbies) * 5

    # Interests
    your_interests = set(x.strip().lower() for x in data['your_interests'].split(','))
    partner_interests = set(x.strip().lower() for x in data['partner_interests'].split(','))
    score += len(your_interests & partner_interests) * 5

    # Name similarity
    name_similarity = difflib.SequenceMatcher(None, data['your_name'].lower(), data['partner_name'].lower()).ratio()
    if name_similarity > 0.7:
        score += 5

    return min(round(score), 100)

# Prediction
def predict_relationship_duration(score):
    if score > 85:
        return "You're soulmates! Expect a lifetime together!"
    elif score > 70:
        return "Very strong match. You could last a long time!"
    elif score > 50:
        return "There's potential here, but needs effort."
    elif score > 30:
        return "Some common ground, but might be tough."
    else:
        return "Not very compatible. Short-term likely."

# Run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
