from wtforms import SubmitField, StringField, TextAreaField
from flask_wtf.file import FileField
from wtforms.validators import DataRequired
from app.forms import BaseForm


class InventoryForm(BaseForm):
    name = StringField('Inventory name',
    validators=[
        DataRequired(message='Forgot introduce an inventory name?')
    ])
    inventory = TextAreaField('Paste csv formated text inventory.',
    validators=[
        DataRequired(message='Forgot to paste csv formated text inventory?')
    ])
    submit = SubmitField("Add inventory")

class UploadForm(BaseForm):
    file = FileField('Add your inventory',
    validators=[
        DataRequired(message='Forgot to select a valid csv file inventory?')
    ])
    submit = SubmitField("Upload")
