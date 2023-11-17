# ///// IMPORTS /////
from __future__ import print_function

import datetime
import json
import os
import sqlite3
import sys
import uuid as uuid
from os.path import dirname, join, realpath

import bcrypt
import flask
import flask_socketio
import httplib2
from database import db
from flask import (Flask, Response, flash, jsonify, redirect, render_template,
                   request, session, url_for)
from flask_socketio import SocketIO, join_room
from flask_sqlalchemy import SQLAlchemy
from forms import (CommentForm, CreateHabitat, HabitForm,
                   LoginForm, RegisterForm)
#from models import Task as Task
#from models import Project as Project
#//// Potential Import Guidelines (Will substitute Note to Habit for example) ////#
from models import Comment as Comment
from models import Habit as Habit
from models import Habitat as Habitat
from models import Note as Note
from models import User as User
from werkzeug.utils import secure_filename

#*/

# ///// APP CREATION /////
app = Flask(__name__)  # create an app
socketio = SocketIO(app)

# ///// DATABASE CONFIG /////
# Configure database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask_habit_app.db'
# Disables a feature that signals the application every time a change is about to be made in the database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'SE4150'

UPLOAD_FOLDER = join(dirname(realpath(__file__)), 'static/images/..')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#  Binds SQLAlchemy db object to this Flask app
db.init_app(app)

# Setup models
with app.app_context():
    db.create_all()  # Run under the app context

# ///// ROUTES /////
# - Home -
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/home1')
def home1():
    return render_template('home1.html')

def generate_user_id():
    return str(uuid.uuid4())

# ---------- User - Account ----------
# - User Registration -
@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()

    if request.method == 'POST' and form.validate_on_submit():
        # salt and hash password
        h_password = bcrypt.hashpw(
            request.form['password'].encode('utf-8'), bcrypt.gensalt())
        # get entered user data
        first_name = request.form['firstname']
        last_name = request.form['lastname']
        email = request.form['email']
        # create user model
        #new_user = User(first_name, last_name, request.form['email'], h_password)
        new_user = User(first_name, last_name, email, h_password)
        # add user to database and commit
        db.session.add(new_user)
        db.session.commit()
        # save the user's name to the session
        session['user'] = first_name
        session['user_id'] = new_user.id  # access id value from user model of this newly added user
        # show user dashboard view
        return redirect(url_for('login'))

    # something went wrong - display register view
    return render_template('register.html', form=form)


# - User Login -
@app.route('/login', methods=['POST', 'GET'])
def login():
    login_form = LoginForm()
    # validate_on_submit only validates using POST
    if login_form.validate_on_submit():
        # we know user exists. We can use one()
        the_user = db.session.query(User).filter_by(email=request.form['email']).one()
        # user exists check password entered matches stored password
        if bcrypt.checkpw(request.form['password'].encode('utf-8'), the_user.password):
            # password match add user info to session
            session['user'] = the_user.first_name
            session['user_id'] = the_user.id
            # render view
            return redirect(url_for('createhabits'))

        # password check failed
        # set error message to alert user
        login_form.password.errors = ["Incorrect username or password."]
        return render_template("login.html", form=login_form)
    else:
        # form did not validate or GET request
        return render_template("login.html", form=login_form)


# - User Logout -
@app.route('/logout')
def logout():
    # check if a user is saved in session
    if session.get('user'):
        session.clear()

    return render_template('home.html')


@app.route('/aboutUs')
def aboutUs():
    return render_template('aboutUs.html')

@app.route('/overview')
def overview():
    if session.get('user'):
        my_habits = db.session.query(Habit).filter_by(user_id=session['user_id']).all()

        return render_template('overview.html', habit=my_habits, user=session['user'])
    else:
        return redirect(url_for('login'))
    
@app.route('/habits', methods =['POST', 'GET'])
def createhabits():

    form = HabitForm()
    my_habits = db.session.query(Habit).filter_by(user_id=session.get('user_id')).all()

    if request.method=='POST' and form.validate_on_submit():
        
        title = request.form['title']
        user_id = session.get('user_id')
        description = ""
        created = datetime.date.today()  # Get the current date
        habit = Habit(user_id, title, description, created)
        habit.streak = 0
        habit.done = False
        db.session.add(habit)
        db.session.commit()
        return redirect('/habits')
        
    return render_template('habits.html', habits=my_habits, form=form)

@app.route('/SlowAdd', methods =['POST', 'GET'])
def createhabitsslow():

    form = HabitForm()
    my_habits = db.session.query(Habit).filter_by(user_id=session.get('user_id')).all()

    if request.method=='POST' and form.validate_on_submit():
        
        title = request.form['title']
        user_id = session.get('user_id')
        description = request.form['description']
        created = datetime.date.today()  # Get the current date
        habit = Habit(user_id, title, description, created)
        # habit = Habit(title, user_id, created)
        habit.streak = 0
        habit.done = False
        db.session.add(habit)
        db.session.commit()
        return redirect('/habits')
        
    return render_template('habits.html', habits=my_habits, form=form)


@app.route('/habits/<habit_id>/delete', methods=['POST'])
def delete_habit(habit_id):
    habit = Habit.query.get_or_404(habit_id)
    habit.delete_habit()
    return redirect('/habits')


@app.route('/habits/<habit_id>/update', methods=['POST'])
def markAsDone(habit_id):
    habit = Habit.query.get_or_404(habit_id)
    habit.markAsDone()
    return redirect('/habits')

def markAsDone(habit_id):
    habit = Habit.query.get_or_404(habit_id)
    
    # Toggle the 'done' status
    habit.done = True
    habit.streak += 1

    db.session.commit()

#----- Habitat Routes ----#

@app.route('/habitats', methods=['GET', 'POST'])
def create_habitat():
    
    my_habitats = db.session.query(Habitat).filter_by(user_id=session.get('user_id')).all()
    my_habits = db.session.query(Habit).filter_by(user_id=session['user_id']).all()

    for h in my_habitats:
        habit_query_result = db.session.query(Habit).filter_by(user_id=session['user_id'], habitat_id=h.id).first()

        if habit_query_result:
            h.users_habit = habit_query_result.title
        

    form = CreateHabitat()

    # Populate the dropdown choices with the user's habits
    form.habit.choices = [(habit.id, habit.title) for habit in my_habits]

    if request.method == "POST" and form.validate_on_submit():
        title = request.form['title']
        description = request.form['description']
        user_id = session.get('user_id')
        icon_image = request.files['icon_image']

        pic_filename = secure_filename(icon_image.filename)
        pic_name = str(uuid.uuid1())+"_"+pic_filename

        saver = request.files['icon_image']

        icon_image = pic_name

        subfolder = 'images/user_uploads'
        saver.save(os.path.join(app.config['UPLOAD_FOLDER'], subfolder, pic_name))

        # Retrieve the selected habit from the form
        selected_habit_id = form.habit.data
        selected_habit = db.session.query(Habit).get(selected_habit_id)

        # Add code to link habitat with selected habit here?

        habitat = Habitat(title, user_id, description, icon_image)
        db.session.add(habitat)
        db.session.commit()

        # Set the habitat_id for the selected habit
        selected_habit.habitat_id = habitat.id
        db.session.commit()

        return redirect('/habitats')

    return render_template('habitats.html', form=form, habitats=my_habitats)

# @habitats_bp.route('/<int:habitat_id>')
# def view_habitat(habitat_id):
#     habitat = get_or_404(Habitat, habitat_id)
#     habits = habitat.habits  # Retrieve habits associated with the habitat
#     return render_template('habitats/view_habitat.html', habitat=habitat, habits=habits)

#------------------------------#

# ---------- Chat ----------
@app.route('/chat')
def chat():
    return render_template("chat.html")


# - Chatroom -
@app.route('/chatroom')
def chatroom():
    username = request.args.get('username')
    room = request.args.get('room')

    if username and room:
        return render_template('chatroom.html', username=username, room=room)
    else:
        return redirect(url_for('chat'))


# - Send Message -
@socketio.on('send_message')
def handle_send_message_event(data):
    app.logger.info("{} has sent message to the room {}:{}".format(data['username'], data['room'], data['message']))

    socketio.emit('receive_message', data, room=data['room'])


# - Join Room -
@socketio.on('join_room')
def handle_join_room_event(data):
    app.logger.info("{} has joined the room {}".format(data['username'], data['room']))
    join_room(data['room'])
    socketio.emit('join_room_announcement', data)

# -----------------------------------------------

@app.route('/habits/<int:habit_id>/edithabits', methods=['POST'])
def edit_habit(habit_id):
    form = HabitForm()

    if form.validate_on_submit():
        habit = Habit.query.get_or_404(habit_id)
        #habit.title = form.new_title.data
        #habit.description = form.new_description.data

        if form.new_title.data is not None:
            habit.title = form.new_title.data

        if form.new_description.data is not None:
            habit.description = form.new_description.data

        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False)

# - See Habitats -
@app.route('/habitats')
def habitats():
    return render_template('habitats.html')

# ///// HOST & PORT CONFIG /////
if __name__ == '__main__':
    # socketio.run(app, debug=True)
    socketio.run(app, host=os.getenv('IP', '127.0.0.1'), port=int(os.getenv('PORT', 5000)), debug=True)

# To see the web page in your web browser, go to the url,
#   http://127.0.0.1:5000