from audioop import add
from enum import unique
import this
from cp_db import User, Org, app, db, Time, get_org, get_time
import bcrypt
from flask import render_template, url_for, redirect, abort, flash, request
# from flask_modals import Modal, render_template_modal
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from flask_navigation import Navigation
from platformdirs import user_runtime_path
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, FloatField
from wtforms.validators import InputRequired, Length, ValidationError, EqualTo, NumberRange
from flask_bcrypt import Bcrypt
import phonenumbers
from datetime import datetime, timedelta, date

nav = Navigation(app)   
bcrypt = Bcrypt(app)
# modal = Modal(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

curr_timecard_index = -1
curr_timecard_hours = []

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
    if current_user != None:
        if str(current_user.workId)[0:2] == "69":
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


def getWeeks():
    pay_interval = ""
    week_count = 0
    if current_user != None:
        pay_interval = str(current_user.payInt)
    
    if "weekly" in pay_interval:
        week_count = 1
        if "bi" in pay_interval:
            week_count += 1
    return week_count

def getLastSunday():
    today = date.today()
    idx = (today.weekday() + 1) % 7
    sun = today - timedelta(idx)
    return sun

def getSundayBefore():
    sun = getLastSunday()
    return sun - timedelta(days=7)

def getListOfDayVals(days, sunday):
    dayNums = []
    for i in range(days):
        dayNums.append((sunday + timedelta(days=i)).day)
    return dayNums

def getListOfDayDates(days, sunday):
    dayNums = []
    for i in range(days):
        newDay = (sunday + timedelta(days=i))
        dayNums.append("/".join([str(newDay.month), str(newDay.day), str(newDay.year)]))
    return dayNums

def getTimecardHours(startDate, timecardDays):
    
    time = get_time(current_user.workId, "/".join([str(startDate.month), str(startDate.day), str(startDate.year)]))
    
    if time == None:
        generateEmptyTimecard(startDate)
        time = get_time(current_user.workId, "/".join([str(startDate.month), str(startDate.day), str(startDate.year)]))
    fillCurrTime(time, True)
    if len(timecardDays) > 7:
        nextDate = startDate + timedelta(days=7)
        nextTime = get_time(current_user.workId, "/".join([str(nextDate.month), str(nextDate.day), str(nextDate.year)]))
        if nextTime == None:
            generateEmptyTimecard(nextDate)
            nextTime = get_time(current_user.workId, "/".join([str(nextDate.month), str(nextDate.day), str(nextDate.year)]))
        fillCurrTime(nextTime, False) 

def generateEmptyTimecard(startDate):
    newTime = Time(current_user.workId, "/".join([str(startDate.month), str(startDate.day), str(startDate.year)]), "0", "0", "0", "0", "0", "0", "0", "0", "none")
    db.session.add(newTime)
    db.session.commit()
    

def fillCurrTime(time, reset):
    global curr_timecard_hours
    if reset:
        curr_timecard_hours = []
    curr_timecard_hours.append(time.sunday)
    curr_timecard_hours.append(time.monday)
    curr_timecard_hours.append(time.tuesday)
    curr_timecard_hours.append(time.wednesday)
    curr_timecard_hours.append(time.thursday)
    curr_timecard_hours.append(time.friday)
    curr_timecard_hours.append(time.saturday)

def setTimecardHour(hours):
    global curr_timecard_hours
    global curr_timecard_index

    curr_timecard_hours[curr_timecard_index] = hours

def determineBiweeklyStart():
    sun = getLastSunday()
    referenceDate = date(2017, 1, 1)
    currentHalf = ((referenceDate - sun).days/7)%2
    if currentHalf == 0:
        return sun
    return getSundayBefore()

def calculateTotalHours():
    global curr_timecard_hours
    totalHours = 0
    totalMinutes = 0
    for t in curr_timecard_hours:
        if t != "0":
            HM = t.split(":")
            totalHours += int(HM[0])
            totalMinutes += int(HM[1])
    totalHours += int(totalMinutes/60)
    totalMinutes = totalMinutes % 60
    return ":".join([str(totalHours),str(totalMinutes)])
        

def saveTimecard(startDate, status):
    global curr_timecard_hours
    if curr_timecard_hours == []:
        return
    time = get_time(current_user.workId, "/".join([str(startDate.month), str(startDate.day), str(startDate.year)]))
    db.session.delete(time)
    db.session.commit()
    newTime = Time(current_user.workId, "/".join([str(startDate.month), str(startDate.day), str(startDate.year)]), curr_timecard_hours[0], 
    curr_timecard_hours[1], curr_timecard_hours[2], curr_timecard_hours[3], curr_timecard_hours[4], curr_timecard_hours[5], 
    curr_timecard_hours[6], calculateTotalHours(), status)
    db.session.add(newTime)
    db.session.commit()
    if len(curr_timecard_hours) > 7:
        nextDate = startDate + timedelta(days=7)
        nextTime = get_time(current_user.workId, "/".join([str(nextDate.month), str(nextDate.day), str(nextDate.year)]))
        db.session.delete(nextTime)
        db.session.commit()
        nextNewTime = Time(current_user.workId, "/".join([str(nextDate.month), str(nextDate.day), str(nextDate.year)]), curr_timecard_hours[7], 
        curr_timecard_hours[8], curr_timecard_hours[9], curr_timecard_hours[10], curr_timecard_hours[11], curr_timecard_hours[12], 
        curr_timecard_hours[13], calculateTotalHours(), status)
        db.session.add(nextNewTime)
        db.session.commit()


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
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=25), EqualTo('confirm', message='Passwords must match')], 
    render_kw={"placeholder": "Password"})
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
                        pay=int(round(form.pay.data, 2)*100), payInt=form.payInt.data, pImgURL=form.profileImgUrl.data,
                        super_id=form.super_id.data, orga_id=form.orga_id.data)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)



class OrgRegisterForm(FlaskForm):
    orgName = StringField(validators=[InputRequired(), Length(min=2, max=25)], render_kw={"placeholder": "Organization Name"})
    phoneorg = StringField(validators=[InputRequired(), Length(min=2, max=25)], render_kw={"placeholder": "Phone Number"})
    des = StringField(validators=[InputRequired(), Length(min=5, max=25)], render_kw={"placeholder": "Description"})
    orgAddress = StringField(validators=[InputRequired(), Length(min=4, max=25)], render_kw={"placeholder": "Organization Address"})
    logoURL = StringField(validators=[InputRequired(), Length(min=4, max=25)], render_kw={"placeholder": "Logo URL"})
    bannerURL = StringField(validators=[InputRequired(), Length(min=4, max=25)], render_kw={"placeholder": "Banner URL"})
    checkTimecard = BooleanField(validators=[InputRequired()], false_values=(False, 'false', 0, '0'))
    checkMask = BooleanField(validators=[InputRequired()], false_values=(False, 'false', 0, '0'))
    checkSymptom = BooleanField(validators=[InputRequired()], false_values=(False, 'false', 0, '0'))
    submit = SubmitField("Register")

    def validate_phone(self, phoneorg):
        try:
            p = phonenumbers.parse(phoneorg.data, None)
            if not phonenumbers.is_valid_number(p):
                print("Phone Number valid number")
                raise ValueError()
        except (phonenumbers.phonenumberutil.NumberParseException, ValueError) as e:
            print(phoneorg.data)
            print("Phone Number format")
            print(e)
            raise ValidationError('Invalid phone number')

@app.route('/org_register', methods=['GET', 'POST'])
def org_register():
    form = OrgRegisterForm()
    
    if form.validate_on_submit():
        new_org = Org(orgName=form.orgName.data, phoneorg=form.phoneorg.data, des=form.des.data, orgAddress=form.orgAddress.data,
                    logoURL=form.logoURL.data, bannerURL=form.bannerURL.data, checkTimecard=form.checkTimecard.data, checkMask=form.checkMask.data, 
                    checkSymptom=form.checkSymptom.data)
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
    saveDraft = SubmitField("Save Draft")
    submit = SubmitField("Submit Timecard")
    def __init__(self, amount, sunday, *args, **kwargs):
        super(TimecardForm, self).__init__(*args, **kwargs)
        self.dayVals = getListOfDayVals(amount, sunday)
    

@app.route('/timecard', methods=['GET', 'POST'])
@login_required
def timecard():
    global curr_timecard_hours
    
    if "bi" in current_user.payInt.lower():
        startDate = determineBiweeklyStart()
        form = TimecardForm(amount=getWeeks()*7, sunday=startDate)
    else:
        startDate = getLastSunday()
        form = TimecardForm(amount=getWeeks()*7, sunday=getLastSunday())
    
    if curr_timecard_hours == []:
        getTimecardHours(startDate, form.dayVals)
    
    if form.validate_on_submit():
        if form.saveDraft.data:
            print("Saving Draft")
            saveTimecard(startDate, "none")

        else:
            print("Submitting")
            saveTimecard(startDate, "submitted")
            
        curr_timecard_hours = []
        return redirect(url_for('dashboard'))
    adaptAdmin()
    return render_template('timecard.html', form=form, weeks = getWeeks(), today=date.today().day, curr_timecard_hours=curr_timecard_hours)





@app.route('/load_timecard_modal', methods=['GET', 'POST'])
@login_required
def loadModal():
    if request.method == "POST":
        id = request.form["id"]
        global curr_timecard_index
        curr_timecard_index = int(id)
        return redirect(url_for("timecard_modal"))





class Timecard_ModalForm(FlaskForm):

    hours = StringField(validators=[InputRequired(), Length(min=1, max=5)], render_kw={"placeholder": "Hours"})
    submit = SubmitField("Submit Hours")
    
    def validate_hours(self, hours):
        h = str(hours.data)
        try: 
            if ":" in h:
                HM = h.split(":")
                if (int(HM[0]) == 0 and int(HM[1]) == 0) or (int(HM[0]) > 24) or ((int(HM[1]) > 59)) or (int(HM[0]) < 0) or (int(HM[1]) < 0):
                    print("invalid hours")
                    raise ValidationError('Please enter valid hours')
                if int(HM[0]) == 24 and int(HM[1]) > 0:
                    print("invalid hours")
                    raise ValidationError('Please enter valid hours')
            else:
                if len(h) > 4:
                    print("Too many characters")
                    raise ValidationError('Please enter valid hours')
                else:
                    if len(h) > 2:
                        if int(h[: len(h)-2]) > 24 or int(h[: len(h)-2]) < 0:
                            print("Hours too large")
                            raise ValidationError('Please enter valid hours')
                        elif int(h[len(h)-2:]) > 59 or int(h[len(h)-2:]) < 0:
                            print("minutes too large")
                            raise ValidationError('Please enter valid hours')
                        elif int(h[: len(h)-2]) == 24 and int(h[len(h)-2:]) > 0:
                            print("Above max time")
                            raise ValidationError('Please enter valid hours')
                    else:
                        if int(h) < 0 or int(h) > 24:
                            print("value error")
                            raise ValidationError('Please enter valid hours')
        except Exception as e:
            raise ValidationError('Please enter valid hours')



@app.route('/timecard_modal', methods=['GET', 'POST'])
@login_required
def timecard_modal():
    global curr_timecard_index
    if curr_timecard_index == -1:
        return redirect(url_for('timecard'))
    form = Timecard_ModalForm()
    adaptAdmin()
    if "bi" in current_user.payInt.lower():
        dayVals = getListOfDayVals(getWeeks()*7, determineBiweeklyStart())
    else:
        dayVals = getListOfDayVals(getWeeks()*7, getLastSunday())
    global curr_timecard_hours
    if form.validate_on_submit():
        h = str(form.hours.data)
        if ":" not in h:
            print("inputing : inbetween")
            if len(h) > 2:
                print("inputing : inbetween")
                h = ":".join([h[: len(h)-2],h [len(h)-2:]])
            else:
                print("extending with : ")
                h = ":".join([h,"00"])
                
        #Put hours into database
        setTimecardHour(h)
        curr_timecard_index = -1
        return redirect(url_for('timecard'))
        
    return render_template('tc-modal.html', form=form, weeks = getWeeks(), today=date.today().day, dayVals = dayVals, curr_timecard_hours=curr_timecard_hours)
    



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
    def __init__(self):
        if "week" in str(current_user.payInt).lower():
            self.payInt = "hour"
        else:
            self.payInt = "year"
    
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    curr_org = get_org(1)
    adaptAdmin()

    return render_template('profile.html', form=form, curr_org=curr_org)    

    
    
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