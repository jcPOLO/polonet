from wtforms import SubmitField, PasswordField, StringField
from wtforms.validators import Email, DataRequired
from app.forms import BaseForm


# Define the login form (WTForms) for /login and /singup
class LoginForm(BaseForm):
    email = StringField(
        "Email Address",
        validators=[Email(), DataRequired(message="Forgot your email address?")],
    )
    password = PasswordField(
        "Password", validators=[DataRequired(message="Must provide a password.")]
    )
    submit = SubmitField("Submit")


class SingupForm(BaseForm):
    email = StringField(
        "Email Address",
        validators=[Email(), DataRequired(message="Forgot your email address?")],
    )
    first_name = StringField("First name")
    password1 = PasswordField(
        "Password", validators=[DataRequired(message="Must provide a password.")]
    )
    password2 = PasswordField(
        "Confirm password",
        validators=[DataRequired(message="Must provide a password.")],
    )
    submit = SubmitField("Submit")
