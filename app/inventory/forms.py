from wtforms import SubmitField, StringField
from wtforms.validators import Email, DataRequired
from app.forms import BaseForm


# Define the login form (WTForms) for /login and /singup
class LoginForm(BaseForm):
    email = StringField('Email Address',
    validators=[
        Email(),
        DataRequired(message='Forgot your email address?')
    ])
    submit = SubmitField("Submit")
