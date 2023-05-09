from flask import Flask, render_template, redirect, url_for, flash,request,session
from flask_mongoengine import MongoEngine
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo
from flask_login import login_required
import urllib.request
import base64
import os
from dotenv import load_dotenv

load_dotenv()
global max_time
global min_time
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


class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

@app.route('/')
def dash():
    session['q1count'] = 0
    return render_template('home.html')

@app.route('/result')
def result():
    res = results.objects(user=current_user).first()
    all = results.objects.all().order_by('-total')
    for i, obj in enumerate(all):
        if obj.user.id == current_user.id:
            rank = i
            break
    all = [(i+1, obj) for i, obj in enumerate(all)]
    print(rank,"RRRRRRRRRRRRRRRR")
    all_mean = results.objects.aggregate([{"$group": {"_id": None, "total_sum": {"$avg": "$total"}}}])
    all_mean = next(all_mean, {'total_sum': 0})['total_sum']
    min_time = results.objects.aggregate([{"$group": {"_id": None, "total_sum": {"$min": "$total"}}}])
    min_time = next(min_time, {'total_sum': 0})['total_sum']
    max_time = results.objects.aggregate([{"$group": {"_id": None, "total_sum": {"$max": "$total"}}}])
    max_time = next(max_time, {'total_sum': 0})['total_sum']
    data = {'my':res,'all':all,'total':all_mean,'max':max_time,'min':min_time,"rank":rank+1}
    return render_template('result.html',data=data)

@app.route('/question',methods=['GET', 'POST'])
def question():
    if request.method == "POST":
        if User.last_attempt == 6:
            return redirect(url_for('result'))
        answer = request.form.get('answer')
        if current_user.is_authenticated:
            if results.objects(user=current_user).first():
                res = results.objects(user=current_user).first()
            else:
                res = results(user = current_user)
            user = User.objects.get(id=current_user.id)
            qstn = questions.objects(qstn_id=user.last_attempt).first()
            if current_user.last_attempt==1:
                message = "WOW Correct answer"
                res.q1_time = request.form.get('time')
                res.q1_attempts = session['q1count']
                current_user.last_attempt += 1
            elif answer == qstn.qstn_answer:
                message = "WOW Correct answer"
                if current_user.last_attempt==1:
                    res.q1_time = request.form.get('time')
                elif current_user.last_attempt==2:
                    res.q2_time = request.form.get('time')
                elif current_user.last_attempt==3:
                    res.q3_time = request.form.get('time')
                elif current_user.last_attempt==4:
                    res.q4_time = request.form.get('time')
                elif current_user.last_attempt==5:
                    res.q5_time = request.form.get('time')
                current_user.last_attempt += 1

            else:
                message = f"OOps. wrong answer. want hint? :- {qstn.hints}"
                if current_user.last_attempt==2:
                    res.q2_attempts+=1
                elif current_user.last_attempt==3:
                    res.q3_attempts+=1
                elif current_user.last_attempt==4:
                    res.q4_attempts+=1
                elif current_user.last_attempt==5:
                    res.q5_attempts+=1
            res.save()
            current_user.save()
            flash(message)
            return redirect(url_for('question'))
        else:
            # qstn = questions.objects(qstn_id=1).first()
            message = f"OOps. wrong answer. want hint? :- Do what is required to show presence online"
            session['q1count']+=1
            flash(message)
            return redirect(url_for('question'))
    else:
        if current_user.is_authenticated:
            if current_user.last_attempt == 6:
                res = results.objects(user=current_user).first()
                time = res.q1_time+res.q2_time+res.q3_time+res.q4_time+res.q5_time
                avg = time/5
                res.avg = avg
                res.total = time
                res.save()
                return redirect(url_for('result'))
            user = User.objects.get(id=current_user.id)
            qstn = questions.objects(qstn_id=user.last_attempt).first()
            image = qstn.qstn_attach.read()
            base64_data = base64.b64encode(image).decode('utf-8')
            image_url = f"data:image/png;base64,{base64_data}"
        else:
            qstn = questions.objects(qstn_id=1).first()
            image = qstn.qstn_attach.read()
            base64_data = base64.b64encode(image).decode('utf-8')
            image_url = f"data:image/png;base64,{base64_data}"
            print("Gupta")
        return render_template('question.html',qstns=qstn,images=image_url)
    
@login_required
@app.route('/set',methods=['POST','GET'])
def set():
    if current_user.email=="admin@gmail.com":
        if request.method=="POST":
            id = request.form.get('id')
            qstn = request.form.get('qsth')
            answer = request.form.get('ans')
            hint = request.form.get('hint')
            attach = request.form.get('attach')
            image_data = urllib.request.urlopen(attach).read()
            question = questions(qstn_id=id,qstn=qstn,qstn_answer=answer,hints=hint)
            question.qstn_attach.put(image_data, content_type='image/png')
                # question.qstn_attach.put)
            question.save()
            return redirect(url_for('set'))
    return render_template('set.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(name=form.name.data, email=form.email.data, password=form.password.data, last_attempt=1)
        user.save()
        flash('Account created successfully!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.objects(email=form.email.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            flash('Logged in successfully.')
            if user.email=="admin@gmail.com":
                return redirect(url_for('set'))
            return redirect(url_for('question'))
        else:
            flash('Invalid email or password.')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.')
    return redirect(url_for('question'))
