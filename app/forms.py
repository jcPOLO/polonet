from flask_wtf import FlaskForm
from flask import flash


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
