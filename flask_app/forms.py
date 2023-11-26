from database import db
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from models import User
from wtforms import (FileField, PasswordField, StringField, SubmitField,
                     TextAreaField, ValidationError, SelectField, BooleanField)
from wtforms.validators import DataRequired, Email, EqualTo, Length


class RegisterForm(FlaskForm):
    class Meta:
        csrf = False

    firstname = StringField('First Name', validators=[Length(1, 10)])

    lastname = StringField('Last Name', validators=[Length(1, 20)])

    email = StringField('Email', [
        Email(message='Not a valid email address.'),
        DataRequired()])

    password = PasswordField('Password', [
        DataRequired(message="Please enter a password."),
        EqualTo('confirmPassword', message='Passwords must match')
    ])

    confirmPassword = PasswordField('Confirm Password', validators=[
        Length(min=6, max=10)
    ])
    submit = SubmitField('Submit')

    def validate_email(self, field):
        if db.session.query(User).filter_by(email=field.data).count() != 0:
            raise ValidationError('Username already in use.')


class LoginForm(FlaskForm):
    class Meta:
        csrf = False

    email = StringField('Email', [
        Email(message='Not a valid email address.'),
        DataRequired()])

    password = PasswordField('Password', [
        DataRequired(message="Please enter a password.")])

    submit = SubmitField('Submit')

    def validate_email(self, field):
        if db.session.query(User).filter_by(email=field.data).count() == 0:
            raise ValidationError('Incorrect username or password.')

class CommentForm(FlaskForm):
    class Meta:
        csrf = False

    comment = TextAreaField('Comment',validators=[Length(min=1)])

    submit = SubmitField('Add Comment')

class HabitForm(FlaskForm):
    class Meta:
        csrf = False

    title = StringField('Habit Name')
    new_title = StringField('Habit Name')
    description = StringField('Description')
    new_description = StringField('Description')
    submit = SubmitField('Create Habit')
    submit = SubmitField('Edit Habit')
    fields = ['title', 'description', 'submit']



class CreateHabitat(FlaskForm):
    class Meta:
        csrf = False
    title = StringField('Habitat Name')
    description = TextAreaField('Description')
    icon_image = FileField("Habitat Image")
    habit = SelectField('Select Habit', coerce=int)
    submit = SubmitField('Create Habitat')
    is_private = BooleanField('Private Habitat', default=False)
    fields = ['title', 'description', 'icon_image', 'habit', 'submit', 'is_private']


class ProfileForm(FlaskForm):
    class Meta:
        csrf = False
    profile_picture = FileField("Profile Picture", validators=[FileAllowed(['jpg', 'png'], 'Images only!')])
    bio = TextAreaField('Bio')
    submit = SubmitField('Update Profile')