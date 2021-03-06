from audioop import add
from enum import unique
from turtle import width
from typing import Any
from cp_db import User, Org, Time, Clock, Verify, app, db, get_verify, get_org, get_time, get_user, get_clock_in, update_time, update_org, get_employee_submitted_timecards
import bcrypt
from flask import render_template, url_for, redirect, abort, flash, request, session, Response
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFError
from werkzeug.datastructures import MultiDict
from flask_navigation import Navigation
from platformdirs import user_runtime_path
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, FloatField
from wtforms.validators import InputRequired, Length, ValidationError, EqualTo, NumberRange, AnyOf
from flask_bcrypt import Bcrypt
import phonenumbers
from datetime import datetime, timedelta, timezone
import cv2


##################################################  CAMERA   #####################################################

from keras.models import load_model
from PIL import Image, ImageOps
import numpy as np
import pickle
from keras import backend as K
from tensorflow import Graph, Session

def join(source_dir, dest_file, read_size):
    # Create a new destination file
    output_file = open(dest_file, 'wb')

    # Get a list of the file parts
    parts = ['final_model1', 'final_model2', 'final_model3']

    # Go through each portion one by one
    for file in parts:

        # Assemble the full path to the file
        path = file

        # Open the part
        input_file = open(path, 'rb')

        while True:
            # Read all bytes of the part
            bytes = input_file.read(read_size)

            # Break out of loop if we are at end of file
            if not bytes:
                break

            # Write the bytes to the output file
            output_file.write(bytes)

        # Close the input file
        input_file.close()

    # Close the output file
    output_file.close()


join(source_dir='', dest_file="Combined_Model.p", read_size=50000000)


classifier=cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
size = 4
labels_dict={0:'mask',1:'no mask'}
color_dict={0:(0,255,0),1:(0,0,255)}
global loaded_model
graph1 = Graph()
with graph1.as_default():
	session1 = Session(graph=graph1)
	with session1.as_default():
		loaded_model = pickle.load(open('Combined_Model.p', 'rb'))

class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)
    
    def __del__(self):
        self.video.release()
    
    def get_frame(self):
        (rval, im) = self.video.read()
        im = cv2.flip(im, 1, 1)
        mini = cv2.resize(im, (im.shape[1] // size, im.shape[0] // size))
        faces = classifier.detectMultiScale(mini)
        for f in faces:
            (x, y, w, h) = [v * size for v in f] 
            face_img = im[y:y+h, x:x+w]
            resized=cv2.resize(face_img,(300,300))
            normalized=resized/255.0
            reshaped=np.reshape(normalized,(1,300,300,3))
            reshaped = np.vstack([reshaped])
            K.set_session(session1)
            with graph1.as_default():
                results=loaded_model.predict(reshaped)
            if results >.5:
                result = np.array([[1]])
            else:
                result = np.array([[0]])
            label = np.argmax(result)
            cv2.rectangle(im,(x,y),(x+w,y+h),color_dict[result[label][0]],2)
            cv2.rectangle(im,(x,y-40),(x+w,y),color_dict[result[label][0]],-1)
            cv2.putText(im, labels_dict[result[label][0]], (x, y-10),cv2.FONT_HERSHEY_SIMPLEX,0.8,(255,255,255),2)
            
        ret, jpeg = cv2.imencode('.jpg', im)
        return jpeg.tobytes()


def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')



# def gen_frames():
#     try:
#         camera = cv2.VideoCapture(0)
#         while True:
#             success, frame=camera.read()
#             if not success:
#                 break
#             else:
#                 face_detect=cv2.CascadeClassifier('app/Haarcascades/haarcascade_frontalface_default.xml')
#                 eye_detect = cv2.CascadeClassifier('app/Haarcascades/haarcascade_eye.xml')
#                 mouth_detect = cv2.CascadeClassifier('app/Haarcascades/jaarcascade_smile.xml')
#                 faces=face_detect.detectMultiScale(frame,1.3, 7)
#                 gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#                     #drawing the outline box to look for face features
#                 for (x, y, w, h) in faces:
#                     cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 3)
#                     roi_gray = gray[x:x+w, y:y+w]
#                     roi_color = frame[x:x+w, y:y+h]
#                     eyes = eye_detect.detectMultiScale(roi_gray, 1.3, 7)
#                     mouth = mouth_detect.detectMultiScale(frame, 1.3, 7)
#                     for (ex, ey, ew, eh) in eyes:
#                         cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (0, 255, 0), 3)
#                     for (mx, my, mw, mh) in mouth:
#                         #my=int(my-0.15*mh)
#                         cv2.rectangle(roi_color, (mx, my), (mx+mw, my+mh), (0, 255, 0), 3)

#                 ret, buffer=cv2.imencode('.jpg',frame)
#                 frame=buffer.tobytes()
#                 yield(b'--frame\r\n'
#                         b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
#     finally:
#         camera.release()



##################################################  CAMERA   #####################################################

nav = Navigation(app)   
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo

@login_manager.user_loader
def load_user(_id):
    uType = session.get("uType",None)
    if uType == None:
        flash('You have been automatically logged out')
        return uType
    if uType == "user":
        user = User.query.get(int(_id))
        if user is None:
            flash('You have been automatically logged out')
        return user
    else:
        org = Org.query.get(int(_id))
        if org is None:
            flash('You have been automatically logged out')
        return org
        
        

def isAdmin():
    if session.get("uType", "") == "user":
        if current_user != None:
            if "69" in str(current_user.workId)[0:2]:
                return True
    return False

def get_super_name():
    if current_user.super_id == 1000000:
        return ""
    s = get_user(current_user.super_id)
    if s == None:
        return ""
    return " ".join([s.fname,s.lname])

def adaptNav():
    navItems = []
    navItems.append(nav.Item('Dashboard', 'dashboard'))
    uType = session.get("uType", "")
    if uType == "user":
        navItems.append(nav.Item('Profile', 'profile'))
        org = get_org(current_user.orga_id)
        if org == None:
            return
        if org.checkTimecard:
            pay_interval = str(current_user.payInt)
            if "weekly" in pay_interval.lower():
                navItems.append(nav.Item('Timecard', 'timecard'))
        if org.checkSymptom or org.checkMask:
            subItems = []
            if org.checkSymptom:
                subItems.append(nav.Item('Symptom Check', 'symptom_check'))
            if org.checkMask:
                subItems.append(nav.Item('Mask Verify', 'mask_verify'))
            navItems.append(nav.Item('Verify', '', items=subItems))
        if isAdmin():
            navItems.append(nav.Item('Management', 'management'))
    elif uType == "org":
        navItems.append(nav.Item('Management', 'org_management'))
    nav.Bar('top', navItems)


def getWeeks(user):
    week_count = 0
    pay_interval = str(user.payInt)
    
    if "weekly" in pay_interval.lower():
        week_count = 1
        if "bi" in pay_interval.lower():
            week_count += 1
    return week_count

def getLastSunday():
    today = datetime.now(LOCAL_TIMEZONE)
    idx = (today.weekday() + 1) % 7
    sun = today - timedelta(idx)
    sun = sun.replace(hour=0, minute=0, second=0, microsecond=1)
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

def getTimecardHours(_id, startDate, timecardDays):
    
    time = get_time(_id, startDate.strftime('%m/%d/%Y'))
    
    if time == None:
        generateEmptyTimecard(_id, startDate)
        time = get_time(_id, startDate.strftime('%m/%d/%Y'))
    fillCurrTime(time, True)
    if len(timecardDays) > 7:
        nextDate = startDate + timedelta(days=7)
        nextTime = get_time(_id, nextDate.strftime('%m/%d/%Y'))
        if nextTime == None:
            generateEmptyTimecard(_id, nextDate)
            nextTime = get_time(_id, nextDate.strftime('%m/%d/%Y'))
        fillCurrTime(nextTime, False) 

def generateEmptyTimecard(_id, startDate):
    newTime = Time(_id, startDate.strftime('%m/%d/%Y'), "0", "0", "0", "0", "0", "0", "0", "0", "none")
    db.session.add(newTime)
    db.session.commit()
    

def fillCurrTime(time, reset):
    curr_timecard_hours = session.get("curr_timecard_hours", None)
    if reset or curr_timecard_hours == None:
        curr_timecard_hours = []
    curr_timecard_hours.append(time.sunday)
    curr_timecard_hours.append(time.monday)
    curr_timecard_hours.append(time.tuesday)
    curr_timecard_hours.append(time.wednesday)
    curr_timecard_hours.append(time.thursday)
    curr_timecard_hours.append(time.friday)
    curr_timecard_hours.append(time.saturday)
    
    session["curr_timecard_hours"] = curr_timecard_hours

def setTimecardHour(hours):
    curr_timecard_hours = session.get("curr_timecard_hours", None)
    curr_timecard_index = session.get("curr_timecard_index", None)

    if curr_timecard_hours == None or curr_timecard_index == None:
        return
    curr_timecard_hours[curr_timecard_index] = hours
    session["curr_timecard_hours"] = curr_timecard_hours
    
def addTimecardHour(hour):
    curr_timecard_hours = session.get("curr_timecard_hours", None)
    curr_timecard_index = session.get("curr_timecard_index", None)
    if curr_timecard_hours == None or curr_timecard_index == None:
        return
    if curr_timecard_hours[curr_timecard_index] == "0":
        setTimecardHour(hour)
        return
    if hour == "0":
        return
    current_time = curr_timecard_hours[curr_timecard_index].split(":")
    current_hour = hour.split(":")
    total_minute = int(current_time[1]) + int(current_hour[1])
    total_hour = int(current_time[0]) + int(current_hour[0]) + int(int(total_minute)/60)
    total_minute = total_minute % 60
    if total_hour > 24:
        setTimecardHour("24:00")
    else:
        if total_minute < 10:
            total_hours = ":".join([str(total_hour), "0" + str(total_minute)])
        else:
            total_hours = ":".join([str(total_hour), str(total_minute)])
        setTimecardHour(total_hours)

def determineBiweeklyStart():
    sun = getLastSunday()
    referenceDate = datetime(2017, 1, 1, hour=0,minute=0,second=0,microsecond=1,tzinfo=LOCAL_TIMEZONE)
    currentHalf = ((referenceDate - sun).days/7)%2
    if currentHalf == 0:
        return sun
    return getSundayBefore()

def calculateTotalHours():
    curr_timecard_hours = session.get("curr_timecard_hours", None)
    if curr_timecard_hours == None:
        return "0"
    totalHours = 0
    totalMinutes = 0
    for t in curr_timecard_hours:
        if t != "0":
            HM = t.split(":")
            totalHours += int(HM[0])
            totalMinutes += int(HM[1])
    totalHours += int(totalMinutes/60)
    totalMinutes = totalMinutes % 60
    if totalMinutes == 0:
        return ":".join([str(totalHours),"0" + str(totalMinutes)])
    return ":".join([str(totalHours),str(totalMinutes)])
        

def saveTimecard(_id, startDate, status):
    curr_timecard_hours = session.get("curr_timecard_hours", None)
    if curr_timecard_hours == None:
        return
    if curr_timecard_hours == []:
        return
    newTime = Time(_id, startDate.strftime('%m/%d/%Y'), curr_timecard_hours[0], 
    curr_timecard_hours[1], curr_timecard_hours[2], curr_timecard_hours[3], curr_timecard_hours[4], curr_timecard_hours[5], 
    curr_timecard_hours[6], calculateTotalHours(), status)
    update_time(newTime)
    if len(curr_timecard_hours) > 7:
        nextDate = startDate + timedelta(days=7)
        nextNewTime = Time(_id, nextDate.strftime('%m/%d/%Y'), curr_timecard_hours[7], 
        curr_timecard_hours[8], curr_timecard_hours[9], curr_timecard_hours[10], curr_timecard_hours[11], curr_timecard_hours[12], 
        curr_timecard_hours[13], calculateTotalHours(), status)
        update_time(nextNewTime)

def clock_in():
    c = get_clock_in(current_user.workId)
    if c is not None:
        db.session.delete(c)
        db.session.commit()
    now = datetime.now(LOCAL_TIMEZONE)
    newC = Clock(current_user.workId, now.strftime('%m/%d/%Y|%H:%M'), False)
    db.session.add(newC)
    db.session.commit()

def seconds_to_hours_string(seconds):
    hours = int(seconds/(3600))
    minutes = int((seconds - (hours*3600))/60)
    if hours == 0 and minutes == 0:
        return "0"
    if minutes < 10:
        return ":".join([str(hours), "0" + str(minutes)])
    else:
        return ":".join([str(hours), str(minutes)])

def clock_out(sunday):
    c = get_clock_in(current_user.workId)
    if c is not None:
        db.session.delete(c)
        db.session.commit()
    inTime = datetime.strptime(c.clock_in, '%m/%d/%Y|%H:%M')
    inTime = inTime.astimezone(LOCAL_TIMEZONE)
    now = datetime.now(LOCAL_TIMEZONE)
    
    if "bi" in current_user.payInt.lower():
        if (sunday - now).days > 14:
            return
    else:
        if (sunday - now).days > 7:
            return
    
    if sunday > inTime:
        return

    nextDate = inTime
    daysDifference = (inTime - now).days
    if daysDifference > 0:
        for i in range(daysDifference + 1):
            nextDate = nextDate + timedelta(days=1)
            if i == 0:
                session["curr_timecard_index"] = (inTime - sunday).days
                inputHours = seconds_to_hours_string((inTime - nextDate).total_seconds())
                addTimecardHour(inputHours)
                nextDate = nextDate - timedelta(days=1)
            elif i == daysDifference-1:
                session["curr_timecard_index"] = (now - sunday).days
                inputHours = seconds_to_hours_string((nextDate - now).total_seconds())
                addTimecardHour(inputHours)
            else:
                session["curr_timecard_index"] = (nextDate - sunday).days
                setTimecardHour("24:00")
    else:
        session["curr_timecard_index"] = (inTime - sunday).days
        inputHours = seconds_to_hours_string((now - inTime).total_seconds())
        addTimecardHour(inputHours)
    session.pop("curr_timecard_index")
    newC = Clock(current_user.workId, c.clock_in, True)
    db.session.add(newC)
    db.session.commit()
    
def isClockedIn():
    c = get_clock_in(current_user.workId)
    if c == None:
        return False
    elif c.clocked_out:
        return False
    return True
        
####################################################            FORMS & PAGES              #################################################################################



class RegisterForm(FlaskForm):
    fname = StringField(validators=[InputRequired(), Length(min=2, max=25)], render_kw={"placeholder": "First Name"})
    lname = StringField(validators=[InputRequired(), Length(min=2, max=25)], render_kw={"placeholder": "Last Name"})
    email = StringField(validators=[InputRequired(), Length(min=5, max=25)], render_kw={"placeholder": "Email"})
    workId = IntegerField(validators=[InputRequired(), NumberRange(min=10000000, max=99999999)], render_kw={"placeholder": "Id"})
    pronouns = StringField(validators=[InputRequired(), Length(min=5, max=25)], render_kw={"placeholder": "Pronouns"})
    phone = StringField(validators=[InputRequired(), Length(min=10, max=15)], render_kw={"placeholder": "Phone"})
    etype = StringField(validators=[InputRequired(), Length(min=5, max=50)], render_kw={"placeholder": "Employee Type"})
    pay = FloatField(validators=[InputRequired(), NumberRange(min=7.25)], render_kw={"placeholder": "Pay Rate"})
    payInt = StringField(validators=[InputRequired(), Length(min=5, max=25)], render_kw={"placeholder": "Pay Interval"})
    username = StringField(validators=[InputRequired(), Length(min=4, max=25)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=25), EqualTo('confirm', message='Passwords must match')], 
    render_kw={"placeholder": "Password"})
    super_id = IntegerField(validators=[NumberRange(min=10000000, max=99999999)], render_kw={"Supervisor": "Id"})
    orga_id = IntegerField(validators=[InputRequired(), NumberRange(min=10000000, max=99999999)], render_kw={"Organization": "Id"})
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





class OrgRegisterForm(FlaskForm):
    orgUname = StringField(validators=[InputRequired(), Length(min=2, max=25)], render_kw={"placeholder": "Organization Username"})
    orgPass = PasswordField(validators=[InputRequired(), Length(min=4, max=25), EqualTo('confirm', message='Passwords must match')], 
    render_kw={"placeholder": "Organization Password"})
    orgName = StringField(validators=[InputRequired(), Length(min=2, max=25)], render_kw={"placeholder": "Organization Name"})
    phoneorg = StringField(validators=[InputRequired(), Length(min=2, max=25)], render_kw={"placeholder": "Phone Number"})
    des = StringField(validators=[InputRequired(), Length(min=5, max=200)], render_kw={"placeholder": "Description"})
    ceo = StringField(validators=[InputRequired(), Length(min=5, max=25)], render_kw={"placeholder": "CEO"})
    orgAddress = StringField(validators=[InputRequired(), Length(min=4, max=100)], render_kw={"placeholder": "Organization Address"})
    orgid = IntegerField(validators=[InputRequired(), NumberRange(min=10000000, max=99999999)], render_kw={"Organization": "Id"})
    logoURL = StringField(validators=[Length(min=4, max=25)], render_kw={"placeholder": "Logo URL"})
    bannerURL = StringField(validators=[ Length(min=4, max=25)], render_kw={"placeholder": "Banner URL"})
    checkTimecard = BooleanField(false_values=(False, 'false', 0, '0'))
    checkMask = BooleanField(false_values=(False, 'false', 0, '0'))
    checkSymptom = BooleanField(false_values=(False, 'false', 0, '0'))

    confirm = PasswordField(render_kw={"placeholder": "Repeat Password"})
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

@app.route('/register', methods=['GET', 'POST'])
            
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(fname=form.fname.data, lname=form.lname.data, email=form.email.data,
                        username=form.username.data, password=hashed_password, workId=form.workId.data,
                        pronouns=form.pronouns.data, phone=form.phone.data, etype=form.etype.data,
                        pay=int(round(form.pay.data, 2)*100), payInt=form.payInt.data, 
                        super_id=form.super_id.data, orga_id=form.orga_id.data, pImgURL=form.profileImgUrl.data)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/org_register', methods=['GET', 'POST'])
def org_register():
    form = OrgRegisterForm()
    
    if form.validate_on_submit():
        hashed_orgpassword = bcrypt.generate_password_hash(form.orgPass.data)
        new_org = Org(orgUname=form.orgUname.data, orgPass= hashed_orgpassword, orgName=form.orgName.data, 
                    phoneorg=form.phoneorg.data, des=form.des.data, ceo=form.ceo.data, orgAddress=form.orgAddress.data, 
                    orgid = form.orgid.data, logoURL=form.logoURL.data, bannerURL=form.bannerURL.data, checkTimecard=form.checkTimecard.data, 
                    checkMask=form.checkMask.data, checkSymptom=form.checkSymptom.data)
        db.session.add(new_org)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register_org.html', form=form)


@app.route('/org_login', methods=['GET', 'POST'])
def org_login():
    form = LoginForm()
    
    if form.validate_on_submit():
        orgUser = Org.query.filter_by(orgUname=form.username.data).first()
        if orgUser:
            if bcrypt.check_password_hash(orgUser.orgPass, form.password.data):
                session["uType"] = "org"
                login_user(orgUser, remember=form.remember.data)
                return redirect(url_for('dashboard'))
            else:
                flash('Incorrect Username or Password', 'danger')
        else:
            flash('Incorrect Username or Password', 'danger')
            
    return render_template('org_login.html', form=form)


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
                session["uType"] = "user"
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
    adaptNav()
    return render_template('dashboard.html', form=form)




class TimecardForm(FlaskForm):
    clockIn = SubmitField("Clock In")
    clockOut = SubmitField("Clock Out")
    saveDraft = SubmitField("Save Draft")
    submit = SubmitField("Submit Timecard")
    def __init__(self, amount, sunday, *args, **kwargs):
        super(TimecardForm, self).__init__(*args, **kwargs)
        self.dayVals = getListOfDayVals(amount, sunday)
        c = get_clock_in(current_user.workId)
        if c is not None:
            self.lastClockIn = c.clock_in
        else:
            self.lastClockIn = "None"
    

@app.route('/timecard', methods=['GET', 'POST'])
@login_required
def timecard():
    if "bi" in current_user.payInt.lower():
        startDate = determineBiweeklyStart()
        form = TimecardForm(amount=getWeeks(current_user)*7, sunday=startDate)
    else:
        startDate = getLastSunday()
        form = TimecardForm(amount=getWeeks(current_user)*7, sunday=getLastSunday())
    
    curr_timecard_hours = session.get("curr_timecard_hours", None)
    if curr_timecard_hours == None:
        getTimecardHours(current_user.workId, startDate, form.dayVals)
        curr_timecard_hours = session.get("curr_timecard_hours", None)
    if curr_timecard_hours == []:
        getTimecardHours(current_user.workId, startDate, form.dayVals)
        curr_timecard_hours = session.get("curr_timecard_hours", None)
    
    total = calculateTotalHours()
    
    if form.validate_on_submit():
        if form.saveDraft.data:
            saveTimecard(current_user.workId, startDate, "none")
        elif form.clockIn.data:
            clock_in()
        elif form.clockOut.data:
            clock_out(startDate)
            saveTimecard(current_user.workId, startDate, "none")
        else:
            saveTimecard(current_user.workId, startDate, "submitted")
            
        session.pop("curr_timecard_hours")
        return redirect(url_for('timecard'))
    adaptNav()
    return render_template('timecard.html', form=form, clocked = isClockedIn(), weeks = getWeeks(current_user), today=datetime.now().day, curr_timecard_hours=curr_timecard_hours, total=total)





@app.route('/load_timecard_modal', methods=['GET', 'POST'])
@login_required
def loadModal():
    if request.method == "POST":
        id = request.form["id"]
        session["curr_timecard_index"] = int(id)
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
    curr_timecard_index = session.get("curr_timecard_index", None)
    if curr_timecard_index == None:
        return redirect(url_for('timecard'))
    if curr_timecard_index == -1:
        return redirect(url_for('timecard'))
    form = Timecard_ModalForm()
    adaptNav()
    weeks=getWeeks(current_user)
    if "bi" in current_user.payInt.lower():
        dayVals = getListOfDayVals(weeks*7, determineBiweeklyStart())
    else:
        dayVals = getListOfDayVals(weeks*7, getLastSunday())
    curr_timecard_hours = session.get("curr_timecard_hours", None)
    if curr_timecard_hours == None:
        return redirect(url_for('timecard'))
    if form.validate_on_submit():
        h = str(form.hours.data)
        if ":" not in h:
            if len(h) > 2:
                h = ":".join([h[: len(h)-2],h [len(h)-2:]])
            else:
                h = ":".join([h,"00"])
                
        #Put hours into database
        if h == "0:00":
            h = "0"
        setTimecardHour(h)
        session.pop("curr_timecard_index")
        return redirect(url_for('timecard'))
        
    return render_template('tc-modal.html', form=form, weeks = weeks, today=datetime.now().day, dayVals = dayVals, curr_timecard_hours=curr_timecard_hours)
    
class MaskVerifyForm(FlaskForm):
    submit = SubmitField("Submit Mask Verification")
    
@app.route('/mask_verify', methods=['GET', 'POST'])
@login_required
def mask_verify():
    form = MaskVerifyForm()
    if form.validate_on_submit():
        return redirect(url_for('dashboard'))
    adaptNav()
    return render_template('mask_verify.html', form=form)

@app.route('/video')
@login_required
def video():
    return Response(gen(VideoCamera()), mimetype='multipart/x-mixed-replace; boundary=frame')

class SymptomCheckForm(FlaskForm):
    submit = SubmitField("Submit Symptoms")
    
@app.route('/symptom_check', methods=['GET', 'POST'])
@login_required
def symptom_check():
    form = SymptomCheckForm()
    if form.validate_on_submit():
        return redirect(url_for('dashboard'))
    adaptNav()
    return render_template('symptom_check.html', form=form)


    
class ProfileForm(FlaskForm):
    def __init__(self):
        if "week" in str(current_user.payInt).lower():
            self.payInt = "hour"
        else:
            self.payInt = "year"
        self.supervisor = get_super_name()

    
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    curr_org = get_org(current_user.orga_id)
    adaptNav()

    return render_template('profile.html', form=form, curr_org=curr_org)    

    
    
class ManagementForm(FlaskForm):
    submit = SubmitField("Submit Management")

@app.route('/management', methods=['GET', 'POST'])
@login_required
def management():
    form = ManagementForm()
    if form.validate_on_submit():
        return redirect(url_for('dashboard'))
    timecards = get_employee_submitted_timecards(current_user.workId)
    names=[]
    for tc in timecards:
        u = get_user(tc.user_id)
        names.append(u.fname + " " + u.lname)
    tcLength = len(timecards)
    adaptNav()
    return render_template('management.html', form=form, tcs=timecards, tcl=tcLength, names=names)

@app.route('/load_timecard_view_modal', methods=['GET', 'POST'])
@login_required
def loadTCViewModal():
    if request.method == "POST":
        timecards = get_employee_submitted_timecards(current_user.workId)
        id = request.form["id"]
        startDate = datetime.strptime(timecards[int(id)].start_week, '%m/%d/%Y')
        startDate = startDate.astimezone(LOCAL_TIMEZONE)
        user = get_user(timecards[int(id)].user_id)
        dayVals = getListOfDayVals(getWeeks(user)*7, startDate)
        getTimecardHours(timecards[int(id)].user_id, startDate, dayVals)
        session["curr_timecard_index"] = int(id)
        return redirect(url_for("timecard_view_modal"))

class Timecard_Modal_View_Form(FlaskForm):
    decline = SubmitField("Decline")
    confirm = SubmitField("Confirm")

@app.route('/timecard_view_modal', methods=['GET', 'POST'])
@login_required
def timecard_view_modal():
    curr_timecard_index = session.get("curr_timecard_index", None)
    if curr_timecard_index == None:
        return redirect(url_for('dashboard'))
    if curr_timecard_index == -1:
        return redirect(url_for('dashboard'))
    timecards = get_employee_submitted_timecards(current_user.workId)
    startDate = datetime.strptime(timecards[int(curr_timecard_index)].start_week, '%m/%d/%Y')
    startDate = startDate.astimezone(LOCAL_TIMEZONE)
    user = get_user(timecards[int(curr_timecard_index)].user_id)
    weeks=getWeeks(user)
    dayVals = getListOfDayVals(weeks*7, startDate)
    form = Timecard_Modal_View_Form()
    adaptNav()
    curr_timecard_hours = session.get("curr_timecard_hours", None)
    if curr_timecard_hours == None:
        return redirect(url_for('management'))
    if form.validate_on_submit():
        if form.decline.data:
            saveTimecard(timecards[int(curr_timecard_index)].user_id, startDate, "Denied")
        if form.confirm.data:
            saveTimecard(timecards[int(curr_timecard_index)].user_id, startDate, "Confirmed")
        session.pop("curr_timecard_index")
        session.pop("curr_timecard_hours")
        return redirect(url_for('management'))
        
    return render_template('tc-view-modal.html', form=form, weeks=weeks, dayVals = dayVals, curr_timecard_hours=curr_timecard_hours)


class OrgManagementForm(FlaskForm):
    checkTimecard = BooleanField(false_values=(False, 'false', 0, '0'))
    checkMask = BooleanField(false_values=(False, 'false', 0, '0'))
    checkSymptom = BooleanField(false_values=(False, 'false', 0, '0'))
    submit = SubmitField("Save Settings")

@app.route('/org_management', methods=['GET', 'POST'])
@login_required
def org_management():
    curr_org = get_org(current_user.orgid)
    form = OrgManagementForm()
    if request.method == 'GET':
        form.checkTimecard.data=curr_org.checkTimecard
        form.checkMask.data=curr_org.checkMask
        form.checkSymptom.data=curr_org.checkSymptom
    if form.validate_on_submit():
        new_org = Org(curr_org.orgUname, curr_org.orgPass, curr_org.orgName, curr_org.phoneorg,
                    curr_org.des, curr_org.ceo, curr_org.orgAddress, curr_org.logoURL, 
                    curr_org.bannerURL, curr_org.orgid, form.checkTimecard.data, form.checkMask.data, form.checkSymptom.data)
        print(form.checkTimecard.data)
        update_org(new_org)
        return redirect(url_for('dashboard'))
    print(form.errors)
    adaptNav()
    return render_template('org_management.html', form=form, curr_org=curr_org)




@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def home():
    return redirect(url_for('dashboard'))








if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)