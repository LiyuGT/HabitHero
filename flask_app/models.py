# ///// IMPORTS /////
import datetime
import uuid
# from datetime import datetime
from flask_login import UserMixin
from database import db

habit_habitat_association = db.Table(
    'habit_habitat_association',
    db.Column('habit_id', db.Integer, db.ForeignKey('habits.id')),
    db.Column('habitat_id', db.Integer, db.ForeignKey('habitats.id'))
)
# ///// MODELS /////
# - Users -
class User(db.Model, UserMixin):
    id = db.Column("id", db.Integer, primary_key=True)
    first_name = db.Column("first_name", db.String(100))
    last_name = db.Column("last_name", db.String(100))
    email = db.Column("email", db.String(100))
    password = db.Column(db.String(255), nullable=False)
    registered_on = db.Column(db.DateTime, nullable=False)
    profile_picture = db.Column(db.String(200))
    bio = db.Column("bio", db.String(200))
    score =db.Column("score", db.Integer, default=0)
    notes = db.relationship("Note", backref="user", lazy=True)
    comments = db.relationship("Comment", backref="user", lazy=True)
    habits = db.relationship("Habit", backref="user", cascade="all, delete", lazy=True)
    habitats = db.relationship("Habitat", backref="user", lazy=True)
    
    def __init__(self, first_name, last_name, email, password, profile_picture, bio):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.registered_on = datetime.date.today()
        self.profile_picture = 'profile_default.jpeg'
        self.bio = bio


    def __repr__(self):
        return f'<User {self.id}>'


# - User / Notes -
class Note(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    title = db.Column("title", db.String(200))
    text = db.Column("text", db.String(100))
    descrip = db.Column("descrip", db.String(100))
    date = db.Column("date", db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __init__(self, title, text, date, user_id):
        self.title = title
        self.text = text
        self.date = date
        self.user_id = user_id


# - User / Comments -
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, nullable=False)
    content = db.Column(db.VARCHAR, nullable=False)
    note_id = db.Column(db.Integer, db.ForeignKey("note.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # comments = db.relationship("Comment",backref ="note",cascade="all,delete-orphan",lazy=True) //ask tomorrow
    def __init__(self, content, note_id, user_id):
        self.date_posted = datetime.date.today()
        self.content = content
        self.note_id = note_id
        self.user_id = user_id

# - User / Projects -

class Habit(db.Model):
    __tablename__ = "habits"

    id = db.Column("id", db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), autoincrement=True)
    title = db.Column("title", db.String(200))
    description = db.Column("description", db.String(500))
    created = db.Column("created", db.String(50), nullable=False)
    streak = db.Column("streak", db.Integer)
    done = db.Column("done", db.Boolean)
    habitat_id = db.Column(db.Integer, db.ForeignKey('habitats.id'))
    latestDone = db.Column(db.String(50))
    saveLastDone = db.Column(db.String(50))
    orderList = db.Column("orderList", db.Integer, nullable=False, default=0)
    #tasks = db.relationship("Task", backref="projects", cascade="all, delete", lazy=True)


    def __init__(self, user_id, title, description, created): 
    # def __init__(self, title, user_id, created): 
        self.user_id = user_id
        self.title = title
        self.description = description
        self.created = created

    def delete_habit(self):
        db.session.delete(self)
        db.session.commit()

    def markAsDone(self):
        user = User.query.get(self.user_id)
        # Check if the habit is not already marked as done today
        if not self.done and self.latestDone != datetime.date.today():
            # Update the habit's state
            self.done = True
            self.streak += 1

            # if self.streak == 7:
            #     self.user_id.score += 5
            
            user.score += 1
            self.saveLastDone = self.latestDone
            self.latestDone = datetime.date.today() 
        elif self.done:
            # Unmark the habit and adjust the streak
            self.done = False
            self.latestDone = self.saveLastDone
            self.streak = max(0, self.streak - 1)
            user.score = max(0, self.streak - 1)

        db.session.commit()

    # def markAsDone(self):
    #     today = date.today()

    #     if not self.done:

    #         self.done = True
    #         self.streak += 1
    #         self.saveLastDone = self.latestDone
    #         self.latestDone = datetime.now()
    #     else:

    #         self.done = False

    #         latest_done_date = self.latestDone.date() if self.latestDone else None
    #         if latest_done_date != today:
    #             self.latestDone = self.saveLastDone
    #             self.streak = max(0, self.streak - 1)

    #     db.session.commit()

class Habitat(db.Model):
    __tablename__ = "habitats"

    id = db.Column("id", db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), autoincrement=True)
    description = db.Text()
    icon_image = db.Column(db.String(255))
    title = db.Column("title", db.String(200))
    is_public =  db.Column("is_public", db.Boolean, nullable=False, default=False)
    # members = db.relationship("User", backref="habitat", lazy=True)
    habits = db.relationship("Habit", backref="habitat")
    # streak = db.Column("streak", db.Integer)
    # done = db.Column("done", db.Boolean)
    
    def __init__(self, title, user_id, description, icon_image, is_public):
        self.title = title
        self.description = description
        self.icon_image = icon_image
        self.user_id = user_id
        self.is_public = is_public

    # def markHabitatAsDone(self):

    #     self.done = not self.done

    #     if self.done:
    #         self.streak += 1
    #     else:
    #         self.streak -= 1 if self.streak > 0 else 0

    #     db.session.commit()

# - User / Project / Tasks -
# class Task(db.Model):
#     __tablename__ = "tasks"

#     id = db.Column("id", db.Integer, primary_key=True)
#     habit_id = db.Column(db.Integer, db.ForeignKey("habits.id"), nullable=False)
#     title = db.Column("title", db.String(200), nullable=False)
#     description = db.Column("description", db.String(200), nullable=False)
#     created = db.Column("created", db.String(50), nullable=False)

#     def __init__(self, title, desc, created, habit_id):
#         self.title = title
#         self.description = desc
#         self.created = created
#         self.habit_id = habit_id
