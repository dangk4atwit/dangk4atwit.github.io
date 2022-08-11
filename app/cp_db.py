from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import null

app = Flask(__name__)
db = SQLAlchemy(app)

#creating the databse for SQL to work
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

#setting the binds to allow for use of multiple databases
app.config['SQLALCHEMY_BINDS'] = {
    'organization': 'sqlite:///organizations.db',
    'timecard': 'sqlite:///timecards.db',
    'clock' : 'sqlite:///clocks.db',
    'verify' : 'sqlite:///verify.db'
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'thisisasecretkey'


#databse used to store information of the users such as the admin/supervisor/employees
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(80), nullable=False)
    lname = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), nullable=False, unique=True)
    username = db.Column(db.String(20), nullable=False, unique=True) # 20 characters
    password = db.Column(db.String(80), nullable=False)  # 80 characters
    workId = db.Column(db.Integer, nullable=False)
    pronouns = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(80), nullable=False)
    etype = db.Column(db.String(80), nullable=False)
    pay = db.Column(db.Integer, nullable=False)
    payInt = db.Column(db.String(80), nullable=False)
    pImgURL = db.Column(db.String(120), nullable=False)
    super_id = db.Column(db.Integer, nullable=False)
    orga_id = db.Column(db.Integer, nullable=False)
    
    def __init__(self, fname, lname, email, username, password, workId, pronouns, phone,
    etype, pay, payInt, super_id, orga_id, pImgURL="None"):
        self.fname = fname
        self.lname = lname
        self.email = email
        self.username = username    
        self.password = password
        self.workId = workId
        self.pronouns = pronouns
        self.phone = phone
        self.etype = etype
        self.pay = pay
        self.payInt = payInt
        self.pImgURL = pImgURL
        self.super_id = super_id
        self.orga_id = orga_id
        
db.create_all() #create the database with the following columns
db.session.commit() #commiting the information into the table
        
        
#databse used to store information of the organizations
class Org(db.Model, UserMixin):
    __bind_key__ = 'organization'
    id = db.Column(db.Integer, primary_key=True)
    orgUname = db.Column(db.String(80), nullable=False)
    orgPass = db.Column(db.String(80), nullable=False)
    orgName = db.Column(db.String(80), nullable=False)
    orgid = db.Column(db.Integer, nullable=False)
    ceo = db.Column(db.String(80), nullable=False)
    phoneorg = db.Column(db.String(80), nullable=False)
    des = db.Column(db.String(200), nullable=False, unique=True)
    orgAddress = db.Column(db.String(20), nullable=False, unique=True) 
    logoURL = db.Column(db.String(120), nullable=True)
    bannerURL = db.Column(db.String(120), nullable=True)
    checkTimecard = db.Column(db.Boolean, nullable=False)
    checkMask = db.Column(db.Boolean, nullable=False)
    checkSymptom = db.Column(db.Boolean, nullable=False)
    info={'bind_key':'organization'}
    

    def __init__(self, orgUname, orgPass, orgName, phoneorg, des, ceo, orgAddress, logoURL, bannerURL, orgid, checkTimecard, checkMask, checkSymptom):
        self.orgUname = orgUname
        self.orgPass = orgPass
        self.orgName = orgName
        self.phoneorg = phoneorg
        self.des = des
        self.ceo = ceo
        self.orgAddress = orgAddress
        self.logoURL = logoURL
        self.bannerURL = bannerURL
        self.orgid = orgid
        self.checkTimecard = checkTimecard
        self.checkMask = checkMask
        self.checkSymptom = checkSymptom
        

db.create_all(bind=['organization'])
db.session.commit()
        
#databse used to store information of the user's timecard (hours, days, weeks)
class Time(db.Model, UserMixin):
    __bind_key__ = 'timecard'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    start_week= db.Column(db.String(10), nullable=False)
    sunday = db.Column(db.String(5), nullable=False)
    monday = db.Column(db.String(5), nullable=False)
    tuesday = db.Column(db.String(5), nullable=False)
    wednesday = db.Column(db.String(5), nullable=False)
    thursday = db.Column(db.String(5), nullable=False)
    friday = db.Column(db.String(5), nullable=False)
    saturday = db.Column(db.String(5), nullable=False)
    total = db.Column(db.String(5), nullable=False)
    state = db.Column(db.String(20), nullable=False)
    info={'bind_key':'timecard'}
    
    def __init__(self, user_id, start_week, sunday, monday, tuesday, wednesday, thursday, friday,
    saturday, total, state):
        self.user_id = user_id
        self.start_week = start_week
        self.sunday = sunday
        self.monday = monday
        self.tuesday = tuesday
        self.wednesday = wednesday
        self.thursday = thursday
        self.friday = friday
        self.saturday = saturday
        self.total = total
        self.state = state


db.create_all(bind=['timecard'])
db.session.commit()

#databse used to store information of the users clock in/out
class Clock(db.Model, UserMixin):
    __bind_key__ = 'clock'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    clock_in = db.Column(db.String(10), nullable=False)
    clocked_out = db.Column(db.Boolean, nullable=False)
    info={'bind_key':'clock'}
    
    def __init__(self, user_id, clock_in, clocked_out):
        self.user_id = user_id
        self.clock_in = clock_in
        self.clocked_out = clocked_out


db.create_all(bind=['clock'])
db.session.commit()

#databse used to store information of the users verifcatins - mask will not store users images/face
class Verify(db.Model, UserMixin):
    __bind_key__ = 'verify'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    maskVerify = db.Column(db.Boolean, nullable=False)
    maskTime = db.Column(db.String(20), nullable=False)
    symptomVerify = db.Column(db.Boolean, nullable=False)
    symptomTime = db.Column(db.String(20), nullable=False)
    info={'bind_key':'verify'}
    
    def __init__(self, user_id, maskVerify, maskTime, symptomVerify, symptomTime):
        self.user_id = user_id
        self.maskVerify = maskVerify
        self.maskTime = maskTime
        self.symptomVerify = symptomVerify
        self.symptomTime = symptomTime


db.create_all(bind=['verify'])
db.session.commit()


#these are all of our global variables used to access the database

def get_verify(_id):
    verify=Verify.query.filter_by(user_id=_id).first()
    return verify

def update_verify(new_verify):
    old_verify = get_verify(new_verify.user_id)
    if old_verify != None:
        db.session.delete(old_verify)
        db.session.commit()
    db.session.add(new_verify)
    db.session.commit()
    
def get_org(_id):
    org = Org.query.filter_by(orgid=_id).first()
    return org

def update_org(new_org):
    old_org = get_org(new_org.orgid)
    if old_org != None:
        db.session.delete(old_org)
        db.session.commit()
    db.session.add(new_org)
    db.session.commit()

def get_time(_id, start_week):
    time = Time.query.filter_by(user_id=_id, start_week=start_week).first()
    return time

def update_time(new_time):
    old_time = get_time(new_time.user_id, new_time.start_week)
    if old_time != None:
        db.session.delete(old_time)
        db.session.commit()
    db.session.add(new_time)
    db.session.commit()

def get_user(_id):
    user = User.query.filter_by(workId=_id).first()
    return user

def get_clock_in(_id):
    clock = Clock.query.filter_by(user_id=_id).first()
    return clock

def update_clock(new_clock):
    old_c = get_clock_in(new_clock.user_id)
    if old_c != None:
        db.session.delete(old_c)
        db.session.commit()
    db.session.add(new_clock)
    db.session.commit()

def get_employees(_id):
    users = User.query.filter_by(super_id=_id).all()
    return users

def get_employee_submitted_timecards(_id):
    users = get_employees(_id)
    times = []
    for u in users:
        times.extend(Time.query.filter_by(user_id=u.workId, state="submitted").all())
    return times
        
    
if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)