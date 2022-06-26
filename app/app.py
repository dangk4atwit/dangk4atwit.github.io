import bcrypt
from flask import Flask, render_template, url_for, redirect, abort, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from platformdirs import user_runtime_path
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import InputRequired, Length, ValidationError, EqualTo
from flask_bcrypt import Bcrypt

app = Flask(__name__)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True) # 20 characters
    password = db.Column(db.String(80), nullable=False)  # 80 characters

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=5, max=25)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=5, max=25), EqualTo('confirm', message='Passwords must match')], render_kw={"placeholder": "Password"})
    confirm = PasswordField(render_kw={"placeholder": "Repeat Password"})

    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError("That user is already registered.")

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=5, max=25)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=5, max=25)], render_kw={"placeholder": "Password"})
    remember = BooleanField(false_values=(False, 'false', 0, '0'))
    submit = SubmitField("Login")

class DashboardForm(FlaskForm):
    name = "Test Name"
    title = "Test Title"
    isAdmin = False
class ProfileForm(FlaskForm):
    pass

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    return render_template('profile.html', form=form)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = DashboardForm()
    return render_template('dashboard.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('dashboard'))
            else:
                flash('Incorrect Username or Password', 'danger')
        else:
            flash('Incorrect Username or Password', 'danger')
            
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/')
def home():
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)