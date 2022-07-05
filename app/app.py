from audioop import add
from enum import unique
from cp_db import User, Org, app, db
import bcrypt
from flask import render_template, url_for, redirect, abort, flash
# from flask_modals import Modal, render_template_modal
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from flask_navigation import Navigation
from platformdirs import user_runtime_path
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, FloatField
from wtforms.validators import InputRequired, Length, ValidationError, EqualTo, NumberRange
from flask_bcrypt import Bcrypt
import phonenumbers

nav = Navigation(app)   
bcrypt = Bcrypt(app)
# modal = Modal(app)

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
        flash('You have been automatically logged ut')
    return user

def isAdmin():
    if str(current_user.workId)[0:1] == "69":
        return True
    return False

def adaptRegular():
    nav.Bar('top', [
    nav.Item('Dashboard', 'dashboard'),
    nav.Item('Profile', 'profile'),
    nav.Item('Timecard', 'timecard'),
    nav.Item('Verify', 'verify'),])

def adaptAdmin():
    if isAdmin():
        nav.Bar('top', [
            nav.Item('Dashboard', 'dashboard'),
            nav.Item('Profile', 'profile'),
            nav.Item('Timecard', 'timecard'),
            nav.Item('Verify', 'verify'),
            nav.Item('Management', 'management'),])
    else:
        adaptRegular()





####################################################            FORMS & PAGES              #################################################################################


class RegisterForm(FlaskForm):
    fname = StringField(validators=[InputRequired(), Length(min=2, max=25)], render_kw={"placeholder": "First Name"})
    lname = StringField(validators=[InputRequired(), Length(min=2, max=25)], render_kw={"placeholder": "Last Name"})
    email = StringField(validators=[InputRequired(), Length(min=5, max=25)], render_kw={"placeholder": "Email"})
    workId = IntegerField(validators=[InputRequired(), NumberRange(min=10000000, max=99999999)], render_kw={"placeholder": "Id"})
    pronouns = StringField(validators=[InputRequired(), Length(min=5, max=25)], render_kw={"placeholder": "Pronouns"})
    phone = StringField(validators=[InputRequired(), Length(min=10, max=15)], render_kw={"placeholder": "Phone"})
    etype = StringField(validators=[InputRequired(), Length(min=5, max=25)], render_kw={"placeholder": "Employee Type"})
    pay = FloatField(validators=[InputRequired(), NumberRange(min=7.25)], render_kw={"placeholder": "Pay Rate"})
    payInt = StringField(validators=[InputRequired(), Length(min=5, max=25)], render_kw={"placeholder": "Pay Interval"})
    username = StringField(validators=[InputRequired(), Length(min=4, max=25)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=25), EqualTo('confirm', message='Passwords must match')], render_kw={"placeholder": "Password"})
    profileImgUrl = StringField(validators=[Length(max=120)], render_kw={"placeholder": "Profile Image URL"})
    confirm = PasswordField(render_kw={"placeholder": "Repeat Password"})

    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            print("username")
            raise ValidationError("That user is already registered.")
    
    def validate_workId(self, workId):
        existing_workId_username = User.query.filter_by(workId=workId.data).first()
        if existing_workId_username:
            print("workID")
            raise ValidationError("That id is already registered.")
        
    def validate_phone(self, phone):
        try:
            p = phonenumbers.parse(phone.data, None)
            if not phonenumbers.is_valid_number(p):
                print("Phone Number valid number")
                raise ValueError()
        except (phonenumbers.phonenumberutil.NumberParseException, ValueError) as e:
            print(phone.data)
            print("Phone Number format")
            print(e)
            raise ValidationError('Invalid phone number')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(fname=form.fname.data, lname=form.lname.data, email=form.email.data,
                        username=form.username.data, password=hashed_password, workId=form.workId.data,
                        pronouns=form.pronouns.data, phone=form.phone.data, etype=form.etype.data,
                        pay=int(round(form.pay.data, 2)*100), payInt=form.payInt.data, pImgURL=form.profileImgUrl.data)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)



class OrgRegisterForm(FlaskForm):
    orgName = StringField(validators=[InputRequired(), Length(min=2, max=25)], render_kw={"placeholder": "Organization Name"})
    phoneorg = StringField(validators=[InputRequired(), Length(min=2, max=25)], render_kw={"placeholder": "Phone Number"})
    des = StringField(validators=[InputRequired(), Length(min=5, max=25)], render_kw={"placeholder": "Description"})
    orgAddress = StringField(validators=[InputRequired(), Length(min=4, max=25)], render_kw={"placeholder": "Organization Address"})

    submit = SubmitField("Register")

@app.route('/org_register', methods=['GET', 'POST'])
def org_register():
    form = OrgRegisterForm()
    
    if form.validate_on_submit():
        new_org = Org(orgName=form.orgName.data, phoneorg=form.phoneorg.data, des=form.des.data, orgAddress=form.orgAddress.data)
        db.session.add(new_org)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register_org.html', form=form)



class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=25)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=25)], render_kw={"placeholder": "Password"})
    remember = BooleanField(false_values=(False, 'false', 0, '0'))
    submit = SubmitField("Login")

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



class DashboardForm(FlaskForm):
    firstName = "Test"
    lastName = "Name"
    title = "Test Title"
    isAdmin = False
    
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = DashboardForm()
    adaptAdmin()
    return render_template('dashboard.html', form=form)
    
    
    
    
class TimecardForm(FlaskForm):
    firstName = "Test"
    lastName = "Name"
    title = "Test Title"
    isAdmin = False
    
@app.route('/timecard', methods=['GET', 'POST'])
@login_required
def timecard():
    form = TimecardForm()
    adaptAdmin()
    return render_template('timecard.html', form=form)


    
class VerifyForm(FlaskForm):
    firstName = "Test"
    lastName = "Name"
    title = "Test Title"
    isAdmin = False
    
@app.route('/verify', methods=['GET', 'POST'])
@login_required
def verify():
    form = VerifyForm()
    adaptAdmin()
    return render_template('verify.html', form=form)


    
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
    
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    adaptAdmin()
    return render_template('profile.html', form=form)    

    
    
class ManagementForm(FlaskForm):
    firstName = "Admin"
    lastName = "Admin"
    title = "Administrator"
    isAdmin = False

@app.route('/management', methods=['GET', 'POST'])
@login_required
def management():
    form = ManagementForm()
    adaptAdmin()
    return render_template('management.html', form=form)







@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def home():
    return redirect(url_for('dashboard'))










if __name__ == '__main__':
    app.run(debug=True)