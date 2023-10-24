# ///// IMPORTS /////
from __future__ import print_function
import os, sys, json, flask, flask_socketio, httplib2, uuid, bcrypt, sqlite3
from flask import Flask, Response, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from database import db
from flask_socketio import SocketIO, join_room

#//// Potential Import Guidelines (Will substitute Note to Habit for example) ////#
from models import User as User
from models import Note as Note
from models import Comment as Comment
from models import Habit as Habit
from models import Project as Project
from models import Task as Task
from forms import RegisterForm, LoginForm, CommentForm
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

#  Binds SQLAlchemy db object to this Flask app
db.init_app(app)

# Setup models
with app.app_context():
    db.create_all()  # Run under the app context

app = Flask(__name__)

# ///// ROUTES /////
# - Home -
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/register', methods=['POST'])
def registerpage():
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def loginpage():
    return render_template('login.html')

@app.route('/overview')
def overview():
    # # Create a Habit object
    # new_habit = Habit(title="Habit Title")

    # # Add the habit to the database
    # db.session.add(new_habit)
    # db.session.commit()

    return render_template('habits.html')

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
        # create user model
        new_user = User(first_name, last_name, request.form['email'], h_password)
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
            return redirect(url_for('overview'))

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

    return redirect(url_for('home'))


# ///// HOST & PORT CONFIG /////
if __name__ == '__main__':
    # socketio.run(app, debug=True)
    socketio.run(app, host=os.getenv('IP', '127.0.0.1'), port=int(os.getenv('PORT', 5000)), debug=True)

# To see the web page in your web browser, go to the url,
#   http://127.0.0.1:5000