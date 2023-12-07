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
from forms import (CommentForm, CreateHabitat, HabitForm, LoginForm,
                   RegisterForm, ProfileForm)
from flask_mail import Message
from flask_login import LoginManager, current_user

from forms import SearchForm


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


login_manager = LoginManager(app)
login_manager.login_view = 'login'


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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/home1')
def home1():
    form = ProfileForm()

    if request.method == 'POST' and form.validate_on_submit():
        profile_picture = form.profile_picture.data
        user = db.session.query(User).get(session.get('user_id'))
        if profile_picture:
            pic_filename = secure_filename(profile_picture.filename)
            pic_name = str(uuid.uuid1()) + "_" + pic_filename
            subfolder = 'images/profile_uploads'

            try:
                os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], subfolder), exist_ok=True)
                profile_picture.save(os.path.join(app.config['UPLOAD_FOLDER'], subfolder, pic_name))
                user.profile_picture = pic_name
            except Exception as e:
                print(f"Error saving profile picture: {e}")
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error committing changes to the database: {e}")
        finally:
            db.session.close()
    user = db.session.query(User).get(session.get('user_id'))
    return render_template('home1.html', user=user, form=form)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    

@app.route('/search', methods=["POST"])
def search():
    form = CreateHabitat()
    habitat_query = Habitat.query
    habitats = habitat_query.filter_by(title=form.title.data).order_by(Habitat.title).all()

    return render_template("search.html", form=form, habitat=habitats)




@app.route('/profile', methods=['GET', 'POST'])
def profile():
    form = ProfileForm()

    if request.method == 'POST' and form.validate_on_submit():
        # Process the form data and update the user profile
        profile_picture = form.profile_picture.data
        bio = form.bio.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        user = db.session.query(User).get(session.get('user_id'))

        # Update the bio
        user.bio = bio

        # Update the profile picture if a new one is provided
        if profile_picture:
            pic_filename = secure_filename(profile_picture.filename)
            pic_name = str(uuid.uuid1()) + "_" + pic_filename
            subfolder = 'images/profile_uploads'

            try:
                os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], subfolder), exist_ok=True)
                profile_picture.save(os.path.join(app.config['UPLOAD_FOLDER'], subfolder, pic_name))
                user.profile_picture = pic_name
            except Exception as e:
                # Handle the exception, log the error, or provide feedback to the user
                print(f"Error saving profile picture: {e}")
                # Redirect or render the page with an error message if needed

        # Commit changes to the database
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error committing changes to the database: {e}")
            # Handle the error, provide feedback to the user, etc.
        finally:
            db.session.close()

    # Retrieve the user again to get the updated information
    user = db.session.query(User).get(session.get('user_id'))
    form.bio.data = user.bio


    return render_template('profile.html', user=user, form=form)

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
        profile_picture = " "
        bio = " "
        # create user model
        #new_user = User(first_name, last_name, request.form['email'], h_password)
        new_user = User(first_name, last_name, email, h_password, profile_picture, bio)
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
    
    # Update 'done' value for each habit
    for habit in my_habits:
        if habit.latestDone != str(datetime.date.today()):
            habit.done = False
            if habit.latestDone != str(datetime.date.today() - datetime.timedelta(days=1)):
                habit.streak = 0
        else:
            habit.done = True
        

    # Commit changes to the database
    db.session.commit()
    user = db.session.query(User).get(session.get('user_id'))

    return render_template('habits.html', habits=my_habits, form=form, user=user)

#allows the users rank order to stay when the page is refreshed and adds the rank to the db
@app.route('/update_habit_order', methods=['POST'])
def update_habit_order():
    data = request.get_json()
    new_order = data.get('habit_order', [])

    try:
        for index, habit_id in enumerate(new_order, start=1):
            habit = Habit.query.get(habit_id)
            habit.orderList = index

        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        print(f"Error updating habit order: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})
    
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
    
    user = db.session.query(User).get(session.get('user_id'))
        
    return render_template('habits.html', habits=my_habits, form=form, user=user)



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

#----- Habitat Routes ----#

@app.route('/habitats/<habitat_id>', methods=['GET', 'POST'])
def open_habitat(habitat_id):
    print(habitat_id)
    # Redirect to the '/habitats' route with the habitat_id as a query parameter
    return redirect(url_for('open_habitats', habitat_id=habitat_id))

@app.route('/habitats', methods=['GET', 'POST'])
def open_habitats():
    my_habitats = db.session.query(Habitat).filter_by(user_id=session.get('user_id')).all()
    my_habits = db.session.query(Habit).filter_by(user_id=session['user_id']).all()

    for h in my_habitats:
        habit_query_result = db.session.query(Habit).filter_by(user_id=session['user_id'], habitat_id=h.id).first()

        if habit_query_result:
            h.users_habit = habit_query_result.title

    form = CreateHabitat()
    form.habit.choices = [(habit.id, habit.title) for habit in my_habits]

    habitat_id = request.args.get('habitat_id')

    selected_habitat = None
    members_habits = None

    if habitat_id:
        # Fetch the selected habitat if habitat_id is present
        print(f"habitat_id: {habitat_id}")
        selected_habitat = db.session.query(Habitat).get(habitat_id)
        members_habits = db.session.query(Habit).filter_by(habitat_id=habitat_id).all()

        for habit in members_habits:
            user = db.session.query(User).filter_by(id=habit.user_id).first()
            habit.member = user


    if request.method == "POST" and form.validate_on_submit():
        # Handle form submission for creating a new habitat
        title = request.form['title']
        description = request.form['description']
        is_public = form.is_public.data
        user_id = session.get('user_id')
        icon_image = request.files['icon_image']

        pic_filename = secure_filename(icon_image.filename)
        pic_name = str(uuid.uuid1()) + "_" + pic_filename

        saver = request.files['icon_image']

        icon_image = pic_name

        subfolder = 'images/user_uploads'
        saver.save(os.path.join(app.config['UPLOAD_FOLDER'], subfolder, pic_name))

        # Retrieve the selected habit from the form
        selected_habit_id = form.habit.data
        selected_habit = db.session.query(Habit).get(selected_habit_id)

        # Add code to link habitat with selected habit here?

        habitat = Habitat(title, user_id, description, icon_image, is_public)
        db.session.add(habitat)
        db.session.commit()

        # Set the habitat_id for the selected habit
        selected_habit.habitat_id = habitat.id
        db.session.commit()

        return redirect('/habitats')

    user = db.session.query(User).get(session.get('user_id'))

    return render_template('habitats.html', user=user, form=form, habitats=my_habitats, habitat=selected_habitat, membersHabits = members_habits)

    
    # my_habitats = db.session.query(Habitat).filter_by(user_id=session.get('user_id')).all()
    # my_habits = db.session.query(Habit).filter_by(user_id=session['user_id']).all()

    # for h in my_habitats:
    #     habit_query_result = db.session.query(Habit).filter_by(user_id=session['user_id'], habitat_id=h.id).first()

    #     if habit_query_result:
    #         h.users_habit = habit_query_result.title

    # form = CreateHabitat()

    # # Populate the dropdown choices with the user's habits
    # form.habit.choices = [(habit.id, habit.title) for habit in my_habits]

    # if request.method == "POST" and form.validate_on_submit():
    #     title = request.form['title']
    #     description = request.form['description']
    #     user_id = session.get('user_id')
    #     icon_image = request.files['icon_image']

    #     pic_filename = secure_filename(icon_image.filename)
    #     pic_name = str(uuid.uuid1())+"_"+pic_filename

    #     saver = request.files['icon_image']

    #     icon_image = pic_name

    #     subfolder = 'images/user_uploads'
    #     saver.save(os.path.join(app.config['UPLOAD_FOLDER'], subfolder, pic_name))

    #     # Retrieve the selected habit from the form
    #     selected_habit_id = form.habit.data
    #     selected_habit = db.session.query(Habit).get(selected_habit_id)

    #     # Add code to link habitat with selected habit here?

    #     habitat = Habitat(title, user_id, description, icon_image)
    #     db.session.add(habitat)
    #     db.session.commit()

    #     # Set the habitat_id for the selected habit
    #     selected_habit.habitat_id = habitat.id
    #     db.session.commit()

    #     return redirect('/habitats')

    # #     form = ProfileForm()

    # # if request.method == 'POST' and form.validate_on_submit():
    # #     profile_picture = form.profile_picture.data
    # #     user = db.session.query(User).get(session.get('user_id'))
    # #     if profile_picture:
    # #         pic_filename = secure_filename(profile_picture.filename)
    # #         pic_name = str(uuid.uuid1()) + "_" + pic_filename
    # #         subfolder = 'images/profile_uploads'

    # #         try:
    # #             os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], subfolder), exist_ok=True)
    # #             profile_picture.save(os.path.join(app.config['UPLOAD_FOLDER'], subfolder, pic_name))
    # #             user.profile_picture = pic_name
    # #         except Exception as e:
    # #             print(f"Error saving profile picture: {e}")
    # #     try:
    # #         db.session.commit()
    # #     except Exception as e:
    # #         db.session.rollback()
    # #         print(f"Error committing changes to the database: {e}")
    # #     finally:
    # #         db.session.close()
    # user = db.session.query(User).get(session.get('user_id'))

    # return render_template('habitats.html',  user=user, form=form, habitats=my_habitats)

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
@app.route('/chatroom/<habitat_id>')
def chatroom(habitat_id):
    # username = request.args.get('username')
    # room = request.args.get('room')
    user = db.session.query(User).get(session.get('user_id'))
    habitat = db.session.query(Habitat).get(habitat_id)
    
    return render_template('chatroom.html', user=user, habitat=habitat)



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
    return render_template('habitats.html', user_id=session.get('user_id'))

@app.route('/get_habitat_details/<int:habitat_id>')
def get_habitat_details(habitat_id):
    habitat = db.session.query(Habitat).get(habitat_id)

    if habitat:
        habitat_details = {
            'title': habitat.title,
            'icon_image': url_for('static', filename=f'images/user_uploads/{habitat.icon_image}'),
            'members': [
                {'first_name': habit.user.first_name, 'last_name': habit.user.last_name, 'streak': habit.streak}
                for habit in habitat.habits
            ]
        }
        return jsonify(habitat_details)
    else:
        return jsonify({'error': 'Habitat not found'}), 404
'''

@app.route('/habitats/<int:habitat_id>/send_invitations', methods=['POST'])
def send_invitations(habitat_id):
    if request.method == 'POST':
        email = request.form.get('email')

        flash(f'Invitation sent to {email} successfully!', 'success')
        return redirect(url_for('open_habitat', habitat_id=habitat_id))

'''
from flask_mail import Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Replace with your SMTP server address
app.config['MAIL_PORT'] = 587  # The default port for TLS
app.config['MAIL_USE_TLS'] = True  # Use TLS (True for most servers)
app.config['MAIL_USE_SSL'] = False  # Use SSL (True for some servers, but usually TLS is preferred)
app.config['MAIL_USERNAME'] = '****@gmail.com'  # Replace with your email username
app.config['MAIL_PASSWORD'] = '******'  # Replace with your email password
app.config['MAIL_DEFAULT_SENDER'] = '****@gmail.com'  # Replace with your email address

mail = Mail(app) 
@app.route('/habitats/<int:habitat_id>/send_invitations', methods=['POST'])
def send_invitations(habitat_id):
    if request.method == 'POST':
        email = request.form.get('email')

        # Send the email
        send_invitation_email(email, habitat_id)

        flash(f'Invitation sent to {email} successfully!', 'success')
        return redirect(url_for('open_habitat', habitat_id=habitat_id))



def send_invitation_email(email, habitat_id):
    # Create the email message
    subject = 'Invitation to Habit Hero'
    body = f'You have been invited to join Habit Hero! Click the following link to join: {url_for("habitats", _external=True)}'
    sender = '***@gmail.com'  # Replace with your email

    msg = Message(subject, sender=sender, recipients=[email])
    msg.body = body

    # Send the email
    mail.send(msg)




# ///// HOST & PORT CONFIG /////
if __name__ == '__main__':
    # socketio.run(app, debug=True)
    socketio.run(app, host=os.getenv('IP', '127.0.0.1'), port=int(os.getenv('PORT', 5000)), debug=True)

# To see the web page in your web browser, go to the url,
#   http://127.0.0.1:5000