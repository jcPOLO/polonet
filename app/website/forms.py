
from flask import flash
from flask_wtf import FlaskForm
from wtforms import SubmitField, PasswordField, StringField
from wtforms.validators import Email, DataRequired

class BaseForm(FlaskForm):

    __abstract__ = True
    
    def flash_errors(self):
        """Flashes form errors"""
        for field, errors in self.errors.items():
            for error in errors:
                flash(u"Error in the %s field - %s" % (
                    getattr(self, field).label.text,
                    error
                ), 'error')

# Define the login form (WTForms) for /login and /singup
class LoginForm(BaseForm):
    email = StringField('Email Address',
    validators=[
        Email(),
        DataRequired(message='Forgot your email address?')
    ])
    password = PasswordField('Password',
    validators=[
        DataRequired(message='Must provide a password.')
    ])
    submit = SubmitField("Submit")


class SingupForm(BaseForm):
    email = StringField('Email Address',
    validators=[
        Email(),
        DataRequired(message='Forgot your email address?')
    ])
    first_name = StringField('First name')
    password1 = PasswordField('Password',
    validators=[
        DataRequired(message='Must provide a password.')
    ])
    password2 = PasswordField('Confirm password',
    validators=[
        DataRequired(message='Must provide a password.')
    ])
    submit = SubmitField("Submit")
