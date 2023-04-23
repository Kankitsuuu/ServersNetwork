from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField(validators=[DataRequired()], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[DataRequired(), Length(min=6, max=64)],
                             render_kw={"placeholder": "Password"})
    remember = BooleanField('Save me', default=False)

