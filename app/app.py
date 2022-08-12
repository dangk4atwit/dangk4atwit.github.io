from audioop import add
from enum import unique
from turtle import width
from typing import Any
from cp_db import User, Org, Time, Clock, Verify, app, db, get_verify, get_org, get_time, get_user,get_clock_in, update_time, update_org, get_employee_submitted_timecards, update_verify, update_clock
import bcrypt
from flask import render_template, url_for, redirect, abort, flash, request, session, Response
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from flask_navigation import Navigation
from platformdirs import user_runtime_path
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, FloatField
from wtforms.validators import InputRequired, Length, ValidationError, EqualTo, NumberRange
from flask_bcrypt import Bcrypt
import phonenumbers
from datetime import datetime, timedelta, timezone
import cv2


##################################################  CAMERA   #####################################################

import tensorflow.python.keras
from PIL import Image, ImageOps
import numpy as np
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

results = {}

#getting/reading the labels 
def gen_labels():
        labels = {}
        with open("app/labels.txt", "r") as label:
            text = label.read()
            lines = text.split("\n")
            for line in lines[0:-1]:
                    hold = line.split(" ", 1)
                    labels[hold[0]] = hold[1]
        return labels

# http://stackoverflow.com/questions/46036477/drawing-fancy-rectangle-around-face
def draw_border(img, pt1, pt2, color, thickness, r, d):
    x1,y1 = pt1
    x2,y2 = pt2
    # Top left
    img = cv2.line(img, (x1 + r, y1), (x1 + r + d, y1), color, thickness)
    img = cv2.line(img, (x1, y1 + r), (x1, y1 + r + d), color, thickness)
    img = cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness)
    # Top right
    img = cv2.line(img, (x2 - r, y1), (x2 - r - d, y1), color, thickness)
    img = cv2.line(img, (x2, y1 + r), (x2, y1 + r + d), color, thickness)
    img = cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness)
    # Bottom left
    img = cv2.line(img, (x1 + r, y2), (x1 + r + d, y2), color, thickness)
    img = cv2.line(img, (x1, y2 - r), (x1, y2 - r - d), color, thickness)
    img = cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, thickness)
    # Bottom right
    img = cv2.line(img, (x2 - r, y2), (x2 - r - d, y2), color, thickness)
    img = cv2.line(img, (x2, y2 - r), (x2, y2 - r - d), color, thickness)
    img = cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, thickness)
    return img

def maskverify(_id):
    # Disable scientific notation for clarity
    np.set_printoptions(suppress=True)
    # Loading the model
    model = tensorflow.keras.models.load_model('app/keras_model.h5', compile=False)
    global results
    result = 0
    """
    Create the array of the right shape to feed into the keras model
    The 'length' or number of images you can put into the array is
    determined by the first position in the shape tuple, in this case 1."""
    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    # A dict that stores the labels
    labels = gen_labels()
    try:
        #turning on ther camera
        camera = cv2.VideoCapture(0)
        while True:
            success, frame=camera.read()
            if not success:
                break
            else:
    
                # Draw a rectangle, in the frame
                if result == 1:
                    color = (0,255,0)
                else:
                    color = (0,0,255)
                
                # Draw rectangle in which the image to labelled is to be shown.
                frame2 = frame[160:480, 80:370]
                
                                
                # resize the image to a 224x224
                # resizing the image to be at least 224x224 and then cropping from the center
                frame2 = cv2.resize(frame2, (224, 224))
                # turn the image into a numpy array
                image_array = np.asarray(frame2)
                # Normalize the image
                
                #frame = cv2.rectangle(frame, (60, 40), (580, 450), color, 3)
                frame = draw_border(frame, (160, 80), (480, 370), color, 3, 15, 50)

                normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1
                # Load the image into the array
                data[0] = normalized_image_array
                #getting the prediction of the image and outputting the results
                pred = model.predict(data, verbose = 0)
                result = np.argmax(pred[0])
                
                results[_id] = result
                
                #outputting the image
                ret, frame=cv2.imencode('.jpg',frame)
                frame=frame.tobytes()
                yield(b'--frame\r\n'
                         b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    finally:
        camera.release()



def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')



##################################################  CAMERA   #####################################################

#Initialize flask navigator and encrypters for application
nav = Navigation(app)   
bcrypt = Bcrypt(app)

#Initialize flask login manager and settings
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

#Initialize current timezone
LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo

#Determine what type of user is trying to login (Organization vs employee)
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
        
        
#Check if user has admin priviledges 
def isAdmin():
    if session.get("uType", "") == "user":
        if current_user != None:
            if "69" in str(current_user.workId)[0:2]:
                return True
    return False

#Function that gets name of current user's supervisor/manager
def get_super_name():
    if current_user.super_id == 1000000:
        return ""
    s = get_user(current_user.super_id)
    if s == None:
        return ""
    return " ".join([s.fname,s.lname])

#Adapts navigation for page depending on organization settings and user information
def adaptNav():
    navItems = []
    navItems.append(nav.Item('Dashboard', 'dashboard'))
    uType = session.get("uType", "")
    
    #Generate navigation for users/employees
    if uType == "user":
        navItems.append(nav.Item('Profile', 'profile'))
        org = get_org(current_user.orga_id)
        if org == None:
            return
        
        #Only put timecard if organization allows and if employees is paid by the hour
        if org.checkTimecard:
            pay_interval = str(current_user.payInt)
            if "weekly" in pay_interval.lower():
                navItems.append(nav.Item('Timecard', 'timecard'))
                
        #Only add verify to navigation if organization has symptom check or mask verify enabled.
        if org.checkSymptom or org.checkMask:
            subItems = []
            if org.checkSymptom:
                subItems.append(nav.Item('Symptom Check', 'symptom_check'))
            if org.checkMask:
                subItems.append(nav.Item('Mask Verify', 'mask_verify'))
            navItems.append(nav.Item('Verify', '', items=subItems))
            
        #Only add management to navigation if user is a manager/admin
        if isAdmin():
            navItems.append(nav.Item('Management', 'management'))
            
    #Generate navigation for organizations
    elif uType == "org":
        navItems.append(nav.Item('Management', 'org_management'))
    nav.Bar('top', navItems)

#Gets the amount of weeks a user has in their timecard
def getWeeks(user):
    week_count = 0
    pay_interval = str(user.payInt)
    
    if "weekly" in pay_interval.lower():
        week_count = 1
        if "bi" in pay_interval.lower():
            week_count += 1
    return week_count

#Gets the users most recently passed sunday
def getLastSunday():
    today = datetime.now(LOCAL_TIMEZONE)
    idx = (today.weekday() + 1) % 7
    sun = today - timedelta(idx)
    sun = sun.replace(hour=0, minute=0, second=0, microsecond=1)
    return sun

#Gets users sunday before the most recently passed sunday
def getSundayBefore():
    sun = getLastSunday()
    return sun - timedelta(days=7)

#Gets list of day dates for the requested days from the requested sunday.
def getListOfDayVals(days, sunday):
    dayNums = []
    for i in range(days):
        dayNums.append((sunday + timedelta(days=i)).day)
    return dayNums

#Gets list of full dates for the requested days from the requested sunday.
def getListOfDayDates(days, sunday):
    dayNums = []
    for i in range(days):
        newDay = (sunday + timedelta(days=i))
        dayNums.append("/".join([str(newDay.month), str(newDay.day), str(newDay.year)]))
    return dayNums

#Gets the hours stored in the database for a user's current timecard
def getTimecardHours(_id, startDate, timecardDays):
    #Gets time object from database
    time = get_time(_id, startDate.strftime('%m/%d/%Y'))
    
    #If no timecard was found, create new timecard.
    if time == None:
        generateEmptyTimecard(_id, startDate)
        time = get_time(_id, startDate.strftime('%m/%d/%Y'))
    
    #Fills timecard with prexisting timecard times.
    fillCurrTime(time, True)
    
    #If user is paid bi-weekly, fill second week with preexisting timecard times.
    if len(timecardDays) > 7:
        nextDate = startDate + timedelta(days=7)
        nextTime = get_time(_id, nextDate.strftime('%m/%d/%Y'))
        #If no second week is found, generate empty timecard week.
        if nextTime == None:
            generateEmptyTimecard(_id, nextDate)
            nextTime = get_time(_id, nextDate.strftime('%m/%d/%Y'))
        fillCurrTime(nextTime, False) 

#Generates new timecard with hour values of all 0's.
#_id represents user id for timecard
#startDate represents the sunday that the timecard starts on.
def generateEmptyTimecard(_id, startDate):
    #Generates new timecard object
    newTime = Time(_id, startDate.strftime('%m/%d/%Y'), "0", "0", "0", "0", "0", "0", "0", "0", "none")
    
    #Submits object to database
    db.session.add(newTime)
    db.session.commit()
    
#Fills current session held timecard with values from the database.
def fillCurrTime(time, reset):
    curr_timecard_hours = session.get("curr_timecard_hours", None)
    
    #Create new empty timecard list if no timecard was found in session.
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

#Sets given hours to currently selected day in timecard
def setTimecardHour(hours):
    curr_timecard_hours = session.get("curr_timecard_hours", None)
    curr_timecard_index = session.get("curr_timecard_index", None)

    #If session was found to not have either a timecard or an index selected, do nothing.
    if curr_timecard_hours == None or curr_timecard_index == None:
        return
    curr_timecard_hours[curr_timecard_index] = hours
    session["curr_timecard_hours"] = curr_timecard_hours

#Adds given hours to selected day index in timecard
def addTimecardHour(hour):
    curr_timecard_hours = session.get("curr_timecard_hours", None)
    curr_timecard_index = session.get("curr_timecard_index", None)
    #If session was found to not have either a timecard or an index selected, do nothing.
    if curr_timecard_hours == None or curr_timecard_index == None:
        return
    #set rather than add if current day index in timecard has a value of "0".
    if curr_timecard_hours[curr_timecard_index] == "0":
        setTimecardHour(hour)
        return
    #Dont do anything if given hours to add is 0
    if hour == "0":
        return
    #split given hours into hours and minutes.
    current_time = curr_timecard_hours[curr_timecard_index].split(":")
    current_hour = hour.split(":")
    #add given hours to previously stored hours.
    total_minute = int(current_time[1]) + int(current_hour[1])
    total_hour = int(current_time[0]) + int(current_hour[0]) + int(int(total_minute)/60)
    total_minute = total_minute % 60
    
    #If totals are found to go over 24 hours, limit hours to only setting to 24 hours in a day.
    if total_hour >= 24:
        setTimecardHour("24:00")
    else:
        #Format totals into a "HH#MM" format.
        if total_minute < 10:
            total_hours = ":".join([str(total_hour), "0" + str(total_minute)])
        else:
            total_hours = ":".join([str(total_hour), str(total_minute)])
        setTimecardHour(total_hours)

#Determine the start date of a current biweekly timecard
def determineBiweeklyStart():
    sun = getLastSunday()
    referenceDate = datetime(2017, 1, 1, hour=0,minute=0,second=0,microsecond=1,tzinfo=LOCAL_TIMEZONE)
    currentHalf = ((referenceDate - sun).days/7)%2
    if currentHalf == 0:
        return sun
    return getSundayBefore()

#caluclate the total hours worked in the current session's timecard.
def calculateTotalHours():
    curr_timecard_hours = session.get("curr_timecard_hours", None)
    #return 0 if timecard is not in session
    if curr_timecard_hours == None:
        return "0"
    totalHours = 0
    totalMinutes = 0
    #Goes thoughn timecards and adds hours and minutes together
    for t in curr_timecard_hours:
        if t != "0":
            HM = t.split(":")
            totalHours += int(HM[0])
            totalMinutes += int(HM[1])
            
    #Converts all excess minutes into hours
    totalHours += int(totalMinutes/60)
    totalMinutes = totalMinutes % 60
    
    #Convert total into a "HH:MM" format
    if totalMinutes < 10:
        return ":".join([str(totalHours),"0" + str(totalMinutes)])
    return ":".join([str(totalHours),str(totalMinutes)])
        
#Save the users current timecard in session into the database
def saveTimecard(_id, startDate, status):
    curr_timecard_hours = session.get("curr_timecard_hours", None)
    
    #Do nothing if timecard was not loaded into session previously
    if curr_timecard_hours == None:
        return
    #Do nothing if timecard is found to have no days.
    if curr_timecard_hours == []:
        return
    
    #Deposits current session's timecard into database
    newTime = Time(_id, startDate.strftime('%m/%d/%Y'), curr_timecard_hours[0], 
    curr_timecard_hours[1], curr_timecard_hours[2], curr_timecard_hours[3], curr_timecard_hours[4], curr_timecard_hours[5], 
    curr_timecard_hours[6], calculateTotalHours(), status)
    update_time(newTime)
    #Deposits current session's second week timecard into database.
    if len(curr_timecard_hours) > 7:
        nextDate = startDate + timedelta(days=7)
        nextNewTime = Time(_id, nextDate.strftime('%m/%d/%Y'), curr_timecard_hours[7], 
        curr_timecard_hours[8], curr_timecard_hours[9], curr_timecard_hours[10], curr_timecard_hours[11], curr_timecard_hours[12], 
        curr_timecard_hours[13], calculateTotalHours(), status)
        update_time(nextNewTime)

#Clocks in the current user
def clock_in():
    now = datetime.now(LOCAL_TIMEZONE)
    newC = Clock(current_user.workId, now.strftime('%m/%d/%Y|%H:%M'), False)
    update_clock(newC)

#Converts a total amount of seconds into a "HH:MM" format
def seconds_to_hours_string(seconds):
    #Converts seconds into hours and minutes
    hours = int(seconds/(3600))
    minutes = int((seconds - (hours*3600))/60)
    
    #If no hours or minutes were found do nothing
    if hours == 0 and minutes == 0:
        return "0"
    #convert hours and minutes into a "HH:MM" format
    if minutes < 10:
        return ":".join([str(hours), "0" + str(minutes)])
    else:
        return ":".join([str(hours), str(minutes)])

#Clocks the current user out and adds total hours to timecard.
def clock_out(sunday):
    c = get_clock_in(current_user.workId)
    inTime = datetime.strptime(c.clock_in, '%m/%d/%Y|%H:%M')
    inTime = inTime.astimezone(LOCAL_TIMEZONE)
    now = datetime.now(LOCAL_TIMEZONE)

    #Clock out user but dont add hours to timecard if clock in date was found to be before current timecard
    if "bi" in current_user.payInt.lower():
        if (now - sunday).days > 14:
            newC = Clock(current_user.workId, c.clock_in, True)
            update_clock(newC)
            return
    else:
        if (now - sunday).days > 7:
            newC = Clock(current_user.workId, c.clock_in, True)
            update_clock(newC)
            return
    
    #Clock out user but dont add hours to timecard if clock in date was found to be after current timecard
    if sunday > inTime:
        newC = Clock(current_user.workId, c.clock_in, True)
        update_clock(newC)
        return
    
    #calculates total differerence in days between clockin and clockout dates
    nextDate = inTime - timedelta(hours=inTime.hour, minutes=inTime.minute)
    daysDifference = (now - inTime).days
    #Fill in total worked hours into proper dates if clockin vs clockout time was found to span to a different date.
    if daysDifference > 0:
        for i in range(daysDifference+1):
            nextDate = nextDate + timedelta(days=1)
            #Calculates and adds hours remaining to initial clockin date
            if i == 0:
                session["curr_timecard_index"] = (inTime - sunday).days
                inputHours = seconds_to_hours_string((nextDate - inTime).total_seconds())
                addTimecardHour(inputHours)
            #Calculates and adds hours worked in current clock out date
            elif i == daysDifference:
                #Weird fix for bug that skipped 1 day when adding hours worked
                if (not i - 1 == 0):
                    session["curr_timecard_index"] = (nextDate - sunday).days
                    setTimecardHour("24:00")

                session["curr_timecard_index"] = (now - sunday).days
                inputHours = seconds_to_hours_string((now - nextDate).total_seconds())
                addTimecardHour(inputHours)
            else:
                #Set any day that is not the last or first day in between clockin and clockout as working 24hours.
                session["curr_timecard_index"] = (nextDate - sunday).days
                setTimecardHour("24:00")
    #Simply add total worked time to current clocked in hours to current date in timecard.
    else:
        session["curr_timecard_index"] = (inTime - sunday).days
        inputHours = seconds_to_hours_string((now - inTime).total_seconds())
        addTimecardHour(inputHours)
    session.pop("curr_timecard_index")
    newC = Clock(current_user.workId, c.clock_in, True)
    update_clock(newC)

#Check if user is clocked-in
def isClockedIn():
    c = get_clock_in(current_user.workId)
    if c == None:
        return False
    elif c.clocked_out:
        return False
    return True

#Create new empty verification database entry current user.
def newVerify(_id):
    verify = get_verify(_id)
    if verify == None:
        newV = Verify(_id, False, "None", False, "None")
        update_verify(newV)
    
#Submit user's status for symptoms to their verify database entry.
def submitSymptom(_id, hasSymp):
    now = datetime.now(LOCAL_TIMEZONE)
    newSympTime = now.strftime('%m/%d/%Y|%H:%M')
    old_verify = get_verify(_id)
    
    #Generate new verify entry if no verify entry found in database.
    if old_verify == None:
        newVerify(_id)
        old_verify = get_verify(_id)
    
    #Dont update date of latest status update if status matches previous status.
    if hasSymp and hasSymp == old_verify.symptomVerify:
        newSympTime = old_verify.symptomTime
    new_verify = Verify(_id, old_verify.maskVerify, old_verify.maskTime, not hasSymp, newSympTime)
    update_verify(new_verify)
    
#Submits user's mask verification status to their verify database entry.
def submitMask(_id, hasMask):
    now = datetime.now(LOCAL_TIMEZONE)
    newMaskTime = now.strftime('%m/%d/%Y|%H:%M')
    old_verify = get_verify(_id)
    #Generate new verify entry if no entry was found in database.
    if old_verify == None:
        newVerify(_id)
        old_verify = get_verify(_id)
        
     #Dont update date of latest status update if status matches previous status.
    if not hasMask and hasMask == old_verify.maskVerify:
        newMaskTime = old_verify.maskTime
    new_verify = Verify(_id, hasMask, newMaskTime, old_verify.symptomVerify, old_verify.symptomTime)
    update_verify(new_verify)
    
#Gets symptom verification status of a given user
def checkSymptomVerified(_id):
    verify = get_verify(_id)
    #generates new verify entry in database if none was found for requested user.
    if verify == None:
        newVerify(_id)
        return False
    
    #Get last verification date and time if user was found to be previously verified
    if verify.symptomVerify:
        if verify.symptomTime == "None":
            return False
        symptomTime = datetime.strptime(verify.symptomTime, '%m/%d/%Y|%H:%M')
        symptomTime = symptomTime.astimezone(LOCAL_TIMEZONE)
        now = datetime.now(LOCAL_TIMEZONE)
        #Checks if last verified date is not over a day old.
        if now - timedelta(days=1) > symptomTime:
            submitSymptom(_id, True)
            return False
        return True
    return False

#Gets mask verification status of a given user
def checkMaskVerified(_id):
    verify = get_verify(_id)
    
    #generates new verify entry in database if none was found for requested user.
    if verify == None:
        newVerify(_id)
        return False
    
    #Get last verification date and time if user was found to be previously verified
    if verify.maskVerify:
        if verify.maskTime == "None":
            return False
        maskTime = datetime.strptime(verify.maskTime, '%m/%d/%Y|%H:%M')
        maskTime = maskTime.astimezone(LOCAL_TIMEZONE)
        now = datetime.now(LOCAL_TIMEZONE)
        
        #Checks if last verified date is not over a day old.
        if now - timedelta(days=1) > maskTime:
            submitMask(_id, False)
            return False
        return True
    return False

#Checks total verification status of requested user
def checkVerified(_id):
    verify = get_verify(_id)
    
    #Generate empty verification if verify database entry is not found
    if verify == None:
        newVerify(_id)
        return False
    curr_org = get_org(current_user.orga_id)
    
    #If current organization is not found, do nothing
    if curr_org == None:
        return False
    verifiedArr = []
    
    #Only check mask verification if organization has it enabled
    if curr_org.checkMask:
        verifiedArr.append(checkMaskVerified(_id))
        
    #Only check symptom verification if organization has it enabled
    if curr_org.checkSymptom:
        verifiedArr.append(checkSymptomVerified(_id))
    
    #Return all verification statuses
    return all(x for x in verifiedArr)
    
    
####################################################            FORMS & PAGES              #################################################################################


#Form for user registration
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

    #Validates that given username does not exist in database
    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            print("username")
            raise ValidationError("That user is already registered.")
    
    #Validates that given workId does not exist in database
    def validate_workId(self, workId):
        existing_workId_username = User.query.filter_by(workId=workId.data).first()
        if existing_workId_username:
            print("workID")
            raise ValidationError("That id is already registered.")
    
    #Validates that given phone number is a real phone number
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




# form for organization registration
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

    #Validates that given phone number is a real phone number
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

#Registration page for users
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    #If passed validations, register user into database
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(fname=form.fname.data, lname=form.lname.data, email=form.email.data,
                        username=form.username.data, password=hashed_password, workId=form.workId.data,
                        pronouns=form.pronouns.data, phone=form.phone.data, etype=form.etype.data,
                        pay=int(round(form.pay.data, 2)*100), payInt=form.payInt.data, 
                        super_id=form.super_id.data, orga_id=form.orga_id.data, pImgURL=form.profileImgUrl.data)
        db.session.add(new_user)
        db.session.commit()
        #Redirect user to login screen.
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

#Registration page for organizations
@app.route('/org_register', methods=['GET', 'POST'])
def org_register():
    form = OrgRegisterForm()
    
    #If passed validations, register organization into database
    if form.validate_on_submit():
        hashed_orgpassword = bcrypt.generate_password_hash(form.orgPass.data)
        new_org = Org(orgUname=form.orgUname.data, orgPass= hashed_orgpassword, orgName=form.orgName.data, 
                    phoneorg=form.phoneorg.data, des=form.des.data, ceo=form.ceo.data, orgAddress=form.orgAddress.data, 
                    orgid = form.orgid.data, logoURL=form.logoURL.data, bannerURL=form.bannerURL.data, checkTimecard=form.checkTimecard.data, 
                    checkMask=form.checkMask.data, checkSymptom=form.checkSymptom.data)
        db.session.add(new_org)
        db.session.commit()
        
        #Redirect user to login screen.
        return redirect(url_for('org_login'))
    
    return render_template('register_org.html', form=form)

#Organization login page.
@app.route('/org_login', methods=['GET', 'POST'])
def org_login():
    form = LoginForm()
    
    #Validates information given and flashes error for wrong username or password.
    #If no errors, login organization.
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

#Form for user login
class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=25)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=25)], render_kw={"placeholder": "Password"})
    remember = BooleanField(false_values=(False, 'false', 0, '0'))
    submit = SubmitField("Login")

#User/employee login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    #Validates information given and flashes error for wrong username or password.
    #If no errors, login user.
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



#Form for user dashboard
class UserDashboardForm(FlaskForm):
    toMask = SubmitField("Mask Check")
    toSymptom = SubmitField("Symptom Check")
    refresh = SubmitField("Refresh")
    clockIn = SubmitField("Clock In")
    clockOut = SubmitField("Clock Out")
    def __init__(self, amount, sunday, *args, **kwargs):
        super(UserDashboardForm, self).__init__(*args, **kwargs)
        self.dayVals = getListOfDayVals(amount, sunday)
        c = get_clock_in(current_user.workId)
        if c is not None:
            self.lastClockIn = c.clock_in
        else:
            self.lastClockIn = "None"

#Form for organization dashboard
class OrgDashboardForm(FlaskForm):
    pass

#Dashboard page for both organizations and users
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    #Check user login type (Organization vs employee)
    uType = session.get("uType",None)
    
    #Generates user widgets if a user has been detected to have logged in.
    if uType == "user":
        #Sets current timecard for current user
        if "bi" in current_user.payInt.lower():
            startDate = determineBiweeklyStart()
            form = UserDashboardForm(amount=getWeeks(current_user)*7, sunday=startDate)
        else:
            startDate = getLastSunday()
            form = UserDashboardForm(amount=getWeeks(current_user)*7, sunday=getLastSunday())
        curr_timecard_hours = session.get("curr_timecard_hours", None)
        if curr_timecard_hours == None:
            getTimecardHours(current_user.workId, startDate, form.dayVals)
            curr_timecard_hours = session.get("curr_timecard_hours", None)
        if curr_timecard_hours == []:
            getTimecardHours(current_user.workId, startDate, form.dayVals)
            curr_timecard_hours = session.get("curr_timecard_hours", None)
        
        #Gets current date and time
        now = datetime.now(LOCAL_TIMEZONE)
        nowString = now.strftime('%m/%d/%Y|%H:%M').split("|")
        nowDate = nowString[0]
        nowTime = nowString[1]
        
        #Check user's verification status
        verified = checkVerified(current_user.workId)
        verify = get_verify(current_user.workId)
        
        #Get user's current organization
        curr_org = get_org(current_user.orga_id)
        
        #Checks what buttons have been pressed on dashboard
        if form.validate_on_submit():
            #Clockin widget check
            if form.clockIn.data:
                #Clock in user
                clock_in()
            elif form.clockOut.data:
                #Clockout user and save timecard
                clock_out(startDate)
                saveTimecard(current_user.workId, startDate, "none")
            #Verification widget buttons
            elif form.toMask.data:
                #Redirect user to mask verify page
                session.pop("curr_timecard_hours")
                return redirect(url_for('mask_verify'))
            elif form.toSymptom.data:
                #Redirect user to symptom report page
                session.pop("curr_timecard_hours")
                return redirect(url_for('symptom_check'))
            
            #Remove currently selected timecard from session before page unloads.
            session.pop("curr_timecard_hours")
            return redirect(url_for('dashboard'))
        adaptNav()
        return render_template('dashboard.html', form=form, uType=uType, clocked = isClockedIn(), verified=verified, verify=verify, curr_org=curr_org, nowDate=nowDate, nowTime=nowTime)
    else:
        #Generates organization dashboard
        form = OrgDashboardForm()
        adaptNav()
        return render_template('dashboard.html', form=form, uType=uType)



#Form for timecard display page
class TimecardForm(FlaskForm):
    clockIn = SubmitField("Clock In")
    clockOut = SubmitField("Clock Out")
    saveDraft = SubmitField("Save Draft")
    submit = SubmitField("Submit Timecard")
    refresh = SubmitField("Refresh")
    def __init__(self, amount, sunday, *args, **kwargs):
        super(TimecardForm, self).__init__(*args, **kwargs)
        self.dayVals = getListOfDayVals(amount, sunday)
        
        #Get clockin time
        c = get_clock_in(current_user.workId)
        
        #Save last clockin time or none if user has not clocked in yet.
        if c is not None:
            self.lastClockIn = c.clock_in
        else:
            self.lastClockIn = "None"
    
#Timecard display page for hourly employees
@app.route('/timecard', methods=['GET', 'POST'])
@login_required
def timecard():
    #Determine whether the current user is payed weekly or bi-weeky
    #Get timecard for current week.
    if "bi" in current_user.payInt.lower():
        startDate = determineBiweeklyStart()
        form = TimecardForm(amount=getWeeks(current_user)*7, sunday=startDate)
    else:
        startDate = getLastSunday()
        form = TimecardForm(amount=getWeeks(current_user)*7, sunday=getLastSunday())
    
    curr_timecard_hours = session.get("curr_timecard_hours", None)
    #If no timecard has been generated for current date, generate a new timecard.
    if curr_timecard_hours == None:
        getTimecardHours(current_user.workId, startDate, form.dayVals)
        curr_timecard_hours = session.get("curr_timecard_hours", None)
    
    #Calculates total hours workec
    total = calculateTotalHours()
    
    #Gets current state of timecard to make sure if the user has already submitted the timecard or not.
    status = get_time(current_user.workId, startDate.strftime('%m/%d/%Y')).state
    
    #Check if page has been submitted
    if form.validate_on_submit():
        #Save current timecard to database when save button is pressed.
        if form.saveDraft.data:
            saveTimecard(current_user.workId, startDate, "none")
        #Clock in user when clock in is pressed
        elif form.clockIn.data:
            clock_in()
        #Clock out user when clock out is pressed. Save timecard after clockout.
        elif form.clockOut.data:
            clock_out(startDate)
            saveTimecard(current_user.workId, startDate, "none")
        #Only Reload Page
        elif form.refresh.data:
            pass
        #Save Timecard.
        else:
            saveTimecard(current_user.workId, startDate, "submitted")
        
        #Remove selected timecard from session
        session.pop("curr_timecard_hours")
        return redirect(url_for('timecard'))
    adaptNav()
    return render_template('timecard.html', form=form, status=status, clocked = isClockedIn(), weeks = getWeeks(current_user), today=datetime.now().day, curr_timecard_hours=curr_timecard_hours, total=total)




#Middle page to load timecard day selected.
@app.route('/load_timecard_modal', methods=['GET', 'POST'])
@login_required
def loadModal():
    if request.method == "POST":
        #Stores selected timecard day's index in session
        id = request.form["id"]
        session["curr_timecard_index"] = int(id)
        return redirect(url_for("timecard_modal"))




#Form for timecard editing modal
class Timecard_ModalForm(FlaskForm):

    hours = StringField(validators=[InputRequired(), Length(min=1, max=5)], render_kw={"placeholder": "Hours"})
    submit = SubmitField("Submit Hours")
    
    #Validates hours input to make sure they have been typed in a recognizable format.
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


#Modal page for user to edit their timecard
@app.route('/timecard_modal', methods=['GET', 'POST'])
@login_required
def timecard_modal():
    #Load index stored in session
    curr_timecard_index = session.get("curr_timecard_index", None)
    
    #If no index is found, redirect user to timecard page
    if curr_timecard_index == None:
        return redirect(url_for('timecard'))
    if curr_timecard_index == -1:
        return redirect(url_for('timecard'))
    form = Timecard_ModalForm()
    adaptNav()
    
    #Recreates proper timecard sheet in background of modal.
    weeks=getWeeks(current_user)
    if "bi" in current_user.payInt.lower():
        startDate = determineBiweeklyStart()
        dayVals = getListOfDayVals(weeks*7, startDate)
    else:
        startDate = getLastSunday()
        dayVals = getListOfDayVals(weeks*7, startDate)
    selectedDate = (startDate + timedelta(days=curr_timecard_index)).strftime('%m/%d/%Y')
    curr_timecard_hours = session.get("curr_timecard_hours", None)
    
    #Redirect to timecard page if no timecard has been loaded.
    if curr_timecard_hours == None:
        return redirect(url_for('timecard'))
    
    #Submit hours entered into selected day in timecard.
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
        
    return render_template('tc-modal.html', form=form, date=selectedDate, weeks = weeks, today=datetime.now().day, dayVals = dayVals, curr_timecard_hours=curr_timecard_hours)

#Form for mask verify page
class MaskVerifyForm(FlaskForm):
    submit = SubmitField("Submit Mask Verification")

#Mask verify page
@app.route('/mask_verify', methods=['GET', 'POST'])
@login_required
def mask_verify():
    form = MaskVerifyForm()
    #Submits results of mask detection to verification database.
    if form.validate_on_submit():
        global results
        result = results.get(current_user.workId, None)
        submitMask(current_user.workId, result == 1)
        results.pop(current_user.workId)
        return redirect(url_for('dashboard'))
    adaptNav()
    return render_template('mask_verify.html', form=form)

#Video Stream page for mask verification
@app.route('/video')
@login_required
def video():
    return Response(maskverify(current_user.workId), mimetype='multipart/x-mixed-replace; boundary=frame')

# Form for symptom check page
class SymptomCheckForm(FlaskForm):
    #List of all symptoms to be made into checkboxes for symptom checker
    symptoms= ["Fever", "Chills", "Cough", "Difficulty Breathing", "Fatigue", "Muscle Aches",
              "Headache", "Loss of Taste or Smell", "Sore Throat", "Congestion or Runny Nose",
              "Nausea or Vomiting", "Diarrhea", "Pain, Swelling or Rash on Toes or Fingers"]
    noSymp = SubmitField("No Symptoms")
    submit = SubmitField("Submit Symptoms")

#Symptom Check page
@app.route('/symptom_check', methods=['GET', 'POST'])
@login_required
def symptom_check():
    form = SymptomCheckForm()
    
    if form.validate_on_submit():
        #If a symptom is checked, submit as not verified for current user in database.
        if form.noSymp.data:
            submitSymptom(current_user.workId, False)   
        sympArr = request.form.getlist('symptom')
        if len(sympArr) > 0:
            submitSymptom(current_user.workId, True)
        return redirect(url_for('dashboard'))
    adaptNav()
    return render_template('symptom_check.html', form=form)


#Profile page form
class ProfileForm(FlaskForm):
    def __init__(self):
        #Loads whether the user gets paid hourly or yearly
        if "week" in str(current_user.payInt).lower():
            self.payInt = "hour"
        else:
            self.payInt = "year"
        self.supervisor = get_super_name()


#Profile Page for all users
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    curr_org = get_org(current_user.orga_id)
    adaptNav()

    return render_template('profile.html', form=form, curr_org=curr_org)    

    
# Form for management page.
class ManagementForm(FlaskForm):
    submit = SubmitField("Submit Management")

#Manager Management page
@app.route('/management', methods=['GET', 'POST'])
@login_required
def management():
    form = ManagementForm()
    if form.validate_on_submit():
        return redirect(url_for('dashboard'))
    
    #Load all submitted timecards for employees under current user manager
    timecards = get_employee_submitted_timecards(current_user.workId)
    names=[]
    for tc in timecards:
        u = get_user(tc.user_id)
        names.append(u.fname + " " + u.lname)
    tcLength = len(timecards)
    adaptNav()
    return render_template('management.html', form=form, tcs=timecards, tcl=tcLength, names=names)

#Loading inbetween page to timecard view modal
@app.route('/load_timecard_view_modal', methods=['GET', 'POST'])
@login_required
def loadTCViewModal():
    if request.method == "POST":
        #Get selected timecard information to load into modal.
        timecards = get_employee_submitted_timecards(current_user.workId)
        id = request.form["id"]
        startDate = datetime.strptime(timecards[int(id)].start_week, '%m/%d/%Y')
        startDate = startDate.astimezone(LOCAL_TIMEZONE)
        user = get_user(timecards[int(id)].user_id)
        dayVals = getListOfDayVals(getWeeks(user)*7, startDate)
        getTimecardHours(timecards[int(id)].user_id, startDate, dayVals)
        session["curr_timecard_index"] = int(id)
        return redirect(url_for("timecard_view_modal"))

# For for employee timecard view modal
class Timecard_Modal_View_Form(FlaskForm):
    decline = SubmitField("Decline")
    confirm = SubmitField("Confirm")

# Modal for timecard viewing for managers.
@app.route('/timecard_view_modal', methods=['GET', 'POST'])
@login_required
def timecard_view_modal():
    curr_timecard_index = session.get("curr_timecard_index", None)
    #Redirect to dashboard if this page was accessed in an unusual way
    if curr_timecard_index == None:
        return redirect(url_for('dashboard'))
    if curr_timecard_index == -1:
        return redirect(url_for('dashboard'))
    
    #Get selected timecard and load hours and date data into a timecard display
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


# Web Form for Org Management Page
class OrgManagementForm(FlaskForm):
    checkTimecard = BooleanField(false_values=(False, 'false', 0, '0'))
    checkMask = BooleanField(false_values=(False, 'false', 0, '0'))
    checkSymptom = BooleanField(false_values=(False, 'false', 0, '0'))
    submit = SubmitField("Save Settings")

#Org management flask page
@app.route('/org_management', methods=['GET', 'POST'])
@login_required
def org_management():
    curr_org = get_org(current_user.orgid)
    form = OrgManagementForm()
    # On Page Load, Fill in current status of restriction customizations
    if request.method == 'GET':
        form.checkTimecard.data=curr_org.checkTimecard
        form.checkMask.data=curr_org.checkMask
        form.checkSymptom.data=curr_org.checkSymptom
    # Submit changes on to organization to database.
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



#logging out and redirecting to login page
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('login'))


#redirecting to dashboard
@app.route('/')
@login_required
def home():
    return redirect(url_for('dashboard'))








if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)