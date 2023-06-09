import re, time
from flask import Blueprint, flash, redirect, render_template, request, url_for
from . import db, views
from .events import socketio
from .models import User, LoggedIn
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    data = request.form
    if request.method == 'POST':
        username = data.get('username')
        password = data.get('psw')

        user = User.query.filter_by(id=username).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect Password. Try Again', category="error")
                return render_template('login.html', username=username)
        else:
            flash('No username found. Sign up?', category="error")
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    print("we reached mars!")

    username = request.args['username']
    the_user = LoggedIn.query.filter(LoggedIn.active_id==username).filter(LoggedIn.date_out.is_(None)).order_by(LoggedIn.date_in.desc()).first()

    
    datetime = time.strftime('%Y-%m-%d %H:%M:%S')
    the_user.date_out = datetime
    db.session.commit()

    active_users = LoggedIn.query.filter(LoggedIn.date_out.is_(None)).order_by(LoggedIn.date_in.desc()).all()
    
    iter = 0;
    list_of_active = []
    while(iter<len(active_users)):
        list_of_active.append(active_users[iter].active_id)
        iter+=1

    socketio.emit("actives", list_of_active)
    print("active user:", len(list_of_active))

    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        #pic = request.files['pic']

        data = request.form
        username = data.get('username')
        password = data.get('password')
        password1 = data.get('password1')
        email = data.get('email')

        regex = '^[a-z0-9]+[\._]?[ a-z0-9]+[@]\w+[. ]\w{2,3}$'
        user = User.query.filter_by(id=username).first()
        check_email = User.query.filter_by(email=email).first()
        if user:
            flash('This username already exists. Please use another.', category='error')
        elif check_email:
            flash('This email already exists. Please use another.', category='error')
            return render_template('register.html', username=username)
        elif not (re.search(regex, email)):
            flash('Not a valid email address.', category='error')
            return render_template('register.html', username=username)
        elif password1 != password:
            flash('Password does not match', category='error')
            return render_template('register.html', username=username, email=email)
        elif len(password)<8:
            flash('Password is below 8 characters', category='error')
            return render_template('register.html', username=username, email=email)
        else:
            new_user = User(id=username, password=generate_password_hash(password, method='sha256'), email=email)
            db.session.add(new_user)
            db.session.commit()

            #recent_user = User.query.filter_by(email=email).first()
            #filename = secure_filename(pic.filename)
            #mimetype = pic.mimetype
            #img = Profile_Image(user_id=recent_user.id, img=pic.read(), mimetype=mimetype, name=filename)
            #db.session.add(img)

            flash('Account created', category='success')
            return redirect(url_for('auth.login'))

    return render_template('register.html')
