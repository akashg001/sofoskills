from flask import Flask,redirect, url_for,session
from flask_login import LoginManager,UserMixin
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.mongoengine import *
from flask_mongoengine import MongoEngine
import os
app = Flask(__name__)
mongo = os.getenv('mongo')
app.config['SECRET_KEY'] = os.getenv('secure_key')
app.config['MONGODB_SETTINGS'] = {
    'db': os.getenv('db'),
    'host': mongo,
    'port': 5000
}
app.config['UPLOAD_FOLDER'] = '/path/to/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

db = MongoEngine(app)
login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    return User.objects(id=user_id).first()

class User(UserMixin, db.Document):
    name = db.StringField()
    email = db.EmailField(unique=True)
    password = db.StringField()
    last_attempt = db.IntField()


class results(db.Document):
    user = db.ReferenceField(User)
    q1_time = db.IntField()
    q1_attempts = db.IntField(default=0)
    q2_time = db.IntField()
    q2_attempts = db.IntField(default=0)
    q3_time = db.IntField()
    q3_attempts = db.IntField(default=0)
    q4_time = db.IntField()
    q4_attempts = db.IntField(default=0)
    q5_time = db.IntField()
    q5_attempts = db.IntField(default=0)
    total = db.IntField(default=0)
    avg = db.IntField(default=0)
    
class questions(db.Document):
    qstn_id = db.IntField()
    qstn = db.StringField()
    qstn_attach = db.FileField()
    qstn_answer = db.StringField()
    hints = db.StringField()

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        # check if the user is authenticated
        return session.get('admin_email') == 'admin@gmail.com'

    def inaccessible_callback(self, name, **kwargs):
        # redirect to the login page if the user is not authenticated
        return redirect(url_for('admin_login'))
    
admin = Admin(
    app,
    name='Admin  Dashboard',
    index_view=MyAdminIndexView(url='/admin'),
    url='/admin',
    template_mode='bootstrap3'
)

class UserView(ModelView):
    column_list = ('name', 'email')

class ResultsView(ModelView):
    column_list = '__all__'

class QuestionsView(ModelView):
    column_list = '__all__'
