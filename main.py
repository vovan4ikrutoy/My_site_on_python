import flask
import flask_login
import requests
import datetime
from flask import render_template, redirect, request, make_response, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import EmailField, PasswordField, BooleanField, SubmitField, StringField, TelField, DateField
from wtforms.validators import DataRequired

from data.db_session import create_session, global_init
import os
from data.users import User
from data.talons import Talon
from data.news import News
from data import universal_api
from PIL import Image

# Инициализация
app = flask.Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
login_manager = LoginManager()
login_manager.init_app(app)


def check_expired_talons():
    cur_date = datetime.datetime.now().date()
    db_sess = create_session()
    for talon in db_sess.query(Talon).all():
        if talon.actuality > cur_date:
            db_sess.delete(talon)
    db_sess.commit()


@login_manager.user_loader
def load_user(user_id):
    db_sess = create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# Формы для отправки
class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_repeat = PasswordField('Повторить пароль', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


class SenderForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    number = TelField('Телефон', validators=[DataRequired()])
    desc = StringField('Описание работы')
    actuality = DateField('Актульно до', validators=[DataRequired()])
    submit = SubmitField('Отправить заявку')


class NewsForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    text = TelField('Текст статьи', validators=[DataRequired()])
    submit = SubmitField('Отправить заявку')


# Обработка ошибок
@app.errorhandler(404)
def not_found(_):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(401)
def unauth(_):
    return redirect('/')


@app.errorhandler(405)
def wrong_method(_):
    return make_response(jsonify({'error': 'something wrong with your request'}), 405)


@app.errorhandler(400)
def bad_request(_):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


@app.errorhandler(500)
def server_error(_):
    return make_response(jsonify({'error': 'Internal server error'}), 500)


# Публичные страницы
@app.route('/')
def index():
    db_sess = create_session()
    users = db_sess.query(User).all()
    count = len([x for x in users])
    return render_template('index.html', count=count)


@app.route('/about')
def about():
    filename = 'map.jpeg'
    x = 37.6156
    y = 55.7522
    params = {'ll': str(x) + ',' + str(y),
              'spn': str(0.008) + ',' + str(0.008),
              'l': 'map',
              'pt': f'{x},{y},pm2rdm'}
    resp = requests.get("https://static-maps.yandex.ru/1.x/", params=params)
    with open('static/img/other/' + filename, "wb") as file:
        file.write(resp.content)
    return render_template('about.html')


@app.route('/exs')
def examps():
    images = os.listdir('static/img/panorama')
    return render_template('examps.html', images=images)


@app.route('/news')
def news():
    db_sess = create_session()
    all_news = db_sess.query(News).all()
    return render_template('news.html', news=all_news)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    errors = []
    goods = []
    if form.validate_on_submit():
        db_sess = create_session()
        temp = db_sess.query(User).filter(User.email == form.email.data)
        is_okay = True
        if len([x for x in temp]) != 0:
            errors.append('Эта почта уже зарегистрирована!')
            is_okay = False
        if form.password.data != form.password_repeat.data:
            errors.append('Пароли не совпадают!')
            is_okay = False
        if len(form.password.data) < 8:
            errors.append('Пароль должен быть больше 8 символов!')
            is_okay = False
        number = False
        for i in form.password.data:
            if i.isnumeric():
                number = True
        if not number:
            errors.append('Пароль должен содержать цифры')
            is_okay = False
        big_letter = False
        for i in form.password.data:
            if i.isupper():
                big_letter = True
        if not big_letter:
            errors.append('Пароль должен содержать большие буквы')
            is_okay = False
        if is_okay:
            db_sess.add(User(
                email=form.email.data,
                name=form.name.data,
                hashed_password=generate_password_hash(form.password.data),
                is_admin=False
            ))
            db_sess.commit()
            goods.append('Пользователь успешно создан!')

    return render_template('reg.html', title='Авторизация', form=form, errors=errors, goods=goods)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and check_password_hash(user.hashed_password, form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               errors=['Неправильный логин или пароль!'],
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


# Страницы требующие авторизации
@app.route('/sender', methods=['GET', 'POST'])
@login_required
def sender():
    form = SenderForm()
    goods = []
    errors = []
    if form.validate_on_submit():
        db_sess = create_session()
        check_expired_talons()
        is_okay = True
        if len([x for x in db_sess.query(Talon).filter(Talon.user_id == flask_login.current_user.id)]) >= 3:
            is_okay = False
            errors.append('Вы уже оставили 3 заявки! Подождите пока мы их обработаем.')
        if is_okay:
            db_sess.add(Talon(
                user_id=flask_login.current_user.id,
                number=form.number.data,
                desc=form.desc.data,
                actuality=form.actuality.data
            ))
            db_sess.commit()
            goods.append('Заявка успешно отправлена!')

    return render_template('sender.html', title='Авторизация', form=form, errors=errors, goods=goods)


# Админские страницы
@app.route('/look_users')
@login_required
def users():
    if flask_login.current_user.is_admin:
        db_sess = create_session()
        useres = db_sess.query(User).all()
        return render_template('look_users.html', users=useres)
    else:
        return redirect("/")


@app.route('/look')
@login_required
def look():
    if flask_login.current_user.is_admin:
        check_expired_talons()
        db_sess = create_session()
        talons = db_sess.query(Talon).all()
        return render_template('look.html', talons=talons)
    else:
        return redirect("/")


@app.route('/write', methods=['GET', 'POST'])
@login_required
def write():
    if flask_login.current_user.is_admin:
        form = NewsForm()
        errors = []
        goods = []
        if form.validate_on_submit():
            db_sess = create_session()
            is_okay = True
            if len([x for x in db_sess.query(News).filter(News.title == form.title.data)]) != 0:
                errors.append('Статья с таким названием уже существует!')
                is_okay = False
            if len(form.text.data) < 30:
                errors.append('Статья слишком короткая!')
                is_okay = False
            if is_okay:
                db_sess.add(News(title=form.title.data, text=form.text.data, user_id=flask_login.current_user.id))
                db_sess.commit()
                goods.append('Статья успешно создана!')
        return render_template('write.html', title='Статья', form=form, errors=errors, goods=goods)
    else:
        return redirect('/')


@app.route('/add_img', methods=['GET', 'POST'])
@login_required
def add_img():
    if flask_login.current_user.is_admin:
        if request.method == 'POST':
            images = os.listdir("static/img/panorama")
            if request.files['file']:
                imagefile = flask.request.files.get('file', '')
                img = Image.open(imagefile)
                img = img.resize((720, 405))
                img = img.convert('RGB')
                img.save(f'static/img/panorama/image{len(images) + 1}.jpg')
        count = len(os.listdir("static/img/panorama"))
        return render_template('load.html', count=count)
    else:
        return redirect("/")


# Запуск сайта
if __name__ == '__main__':
    global_init('db/database.db')
    check_expired_talons()
    db_ses = create_session()
    temp = db_ses.query(User).filter(User.email == 'test@123')
    if len([x for x in temp]) == 0:
        db_ses.add(User(
            email='test@123',
            name='admin',
            hashed_password=generate_password_hash('123'),
            is_admin=True
        ))
    db_ses.commit()
    app.register_blueprint(universal_api.blueprint)
    app.run(host="localhost", port=8080)
