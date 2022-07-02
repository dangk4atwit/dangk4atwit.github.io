from audioop import add
from enum import unique
import bcrypt
from flask import Flask, render_template, url_for, redirect, abort, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from flask_navigation import Navigation
from platformdirs import user_runtime_path
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import InputRequired, Length, ValidationError, EqualTo
from flask_bcrypt import Bcrypt

app = Flask(__name__)
nav = Navigation(app)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

nav.Bar('top', [
    nav.Item('Dashboard', 'dashboard'),
    nav.Item('Profile', 'profile'),
    nav.Item('Timecard', 'timecard'),
    nav.Item('Verify', 'verify'),
])

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user is None:
        flash('You have been automatically logged out')
    return user

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), nullable=False, unique=True)
    username = db.Column(db.String(20), nullable=False, unique=True) # 20 characters
    password = db.Column(db.String(80), nullable=False)  # 80 characters

    def __init__(self, name, email, username, password):
        self.name = name
        self.email = email
        self.username = username
        self.password = password

db.create_all()
db.session.commit()

class RegisterForm(FlaskForm):
    name = StringField(validators=[InputRequired(), Length(min=5, max=25)], render_kw={"placeholder": "Name"})
    email = StringField(validators=[InputRequired(), Length(min=5, max=25)], render_kw={"placeholder": "Email"})
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
    firstName = "Test"
    lastName = "Name"
    title = "Test Title"
    isAdmin = False
    
class TimecardForm(FlaskForm):
    firstName = "Test"
    lastName = "Name"
    title = "Test Title"
    isAdmin = False
    
class VerifyForm(FlaskForm):
    firstName = "Test"
    lastName = "Name"
    title = "Test Title"
    isAdmin = False
    
class ProfileForm(FlaskForm):
    firstName = "Admin"
    lastName = "Admin"
    pronouns="(He/Him)"
    title = "Administrator"
    employmentEmail = "admin@checkpointmail.com"
    employeeID = "0000000001";
    employmentType = "Tenure"
    payRate = 420
    payInterval = "century"
    superior = "Mr. Boss"
    orgName = "Wentworth Institute of Technology"
    orgAddress="550 Huntington Ave, Boston, MA 02115"
    orgLeader="Mark A. Thompson"
    isAdmin = True
    
class ManagementForm(FlaskForm):
    firstName = "Admin"
    lastName = "Admin"
    title = "Administrator"
    isAdmin = False

def adaptAdmin():
    nav.Bar('top', [
            nav.Item('Dashboard', 'dashboard'),
            nav.Item('Profile', 'profile'),
            nav.Item('Timecard', 'timecard'),
            nav.Item('Verify', 'verify'),
            nav.Item('Management', 'management'),])
    
def adaptRegular():
    nav.Bar('top', [
    nav.Item('Dashboard', 'dashboard'),
    nav.Item('Profile', 'profile'),
    nav.Item('Timecard', 'timecard'),
    nav.Item('Verify', 'verify'),])

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.isAdmin:
        adaptAdmin()
    else:
        adaptRegular()
    return render_template('profile.html', form=form)

@app.route('/management', methods=['GET', 'POST'])
@login_required
def management():
    form = ManagementForm()
    if form.isAdmin:
        adaptAdmin()
    else:
        adaptRegular()
    return render_template('management.html', form=form)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = DashboardForm()
    if form.isAdmin:
        adaptAdmin()
    else:
        adaptRegular()
    return render_template('dashboard.html', form=form)

@app.route('/timecard', methods=['GET', 'POST'])
@login_required
def timecard():
    form = TimecardForm()
    if form.isAdmin:
        adaptAdmin()
    else:
        adaptRegular()
    return render_template('timecard.html', form=form)

@app.route('/verify', methods=['GET', 'POST'])
@login_required
def verify():
    form = VerifyForm()
    if form.isAdmin:
        adaptAdmin()
    else:
        adaptRegular()
    return render_template('verify.html', form=form)

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

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(name=form.name.data, email=form.email.data, username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/')
@login_required
def home():
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)