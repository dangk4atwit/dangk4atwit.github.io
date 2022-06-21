from enum import unique
from tokenize import String
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, user_accessed 
from flask_wtf import FlaskFroms, wtforms
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError

app = Flask(__name__)
db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), nullable = False, unique = True) # 20 characters
    password = db.Column(db.String(80), nullable = False)  # 80 characters

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=5, max=25)], render_kw={"placeholder": "Username"})
    password = StringField(validators=[InputRequired(), Length(min=5, max=25)], render_kw={"placeholder": "Password"})

    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError("That user")

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
  
    