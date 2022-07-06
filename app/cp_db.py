from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

app = Flask(__name__)
db = SQLAlchemy(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_BINDS'] = {
    'organization': 'sqlite:///organizations.db',
    'timecard': 'sqlite:///timecards.db'
}
app.config['SECRET_KEY'] = 'thisisasecretkey'

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
    
    def __init__(self, fname, lname, email, username, password, workId, pronouns, phone,
    etype, pay, payInt, pImgURL="None"):
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
        
db.create_all()
db.session.commit()
        
class Org(db.Model, UserMixin):
    __bind_key__ = 'organization'
    id = db.Column(db.Integer, primary_key=True)
    orgName = db.Column(db.String(80), nullable=False)
    phoneorg = db.Column(db.String(80), nullable=False)
    des = db.Column(db.String(80), nullable=False, unique=True)
    orgAddress = db.Column(db.String(20), nullable=False, unique=True) 
    logoURL = db.Column(db.String(120), nullable=False)
    bannerURL = db.Column(db.String(120), nullable=False)
    checkTimecard = db.Column(db.Boolean, nullable=False)
    checkMask = db.Column(db.Boolean, nullable=False)
    checkSymptom = db.Column(db.Boolean, nullable=False)
    

    def __init__(self, orgName, phoneorg, des, orgAddress, logoURL, bannerURL, checkTimecard, checkMask, checkSymptom):
        self.orgName = orgName
        self.phoneorg = phoneorg
        self.des = des
        self.orgAddress = orgAddress
        self.logoURL = logoURL
        self.bannerURL = bannerURL
        self.checkTimecard = checkTimecard
        self.checkMask = checkMask
        self.checkSymptom = checkSymptom
        
db.create_all()
db.session.commit()
        
#class Time(db.Model, UserMixin):
    # __bind_key__ = 'timecard'

    
    

    # def __init__(self, fname, lname, email, username, password, workId, pronouns, phone,
    # etype, pay, payInt):
    #     self.fname = fname
    #     self.lname = lname
    #     self.email = email
    #     self.username = username
    #     self.password = password
    #     self.workId = workId
    #     self.pronouns = pronouns
    #     self.phone = phone
    #     self.etype = etype
    #     self.pay = pay
    #     self.payInt = payInt
#db.create_all()
#db.session.commit()

if __name__ == '__main__':
    db.drop_all()
    app.run(debug=True)

def get_org(_id):
    org = Org.query.filter_by(id=_id).first()
    return org