import flask
from flask import jsonify, make_response

from .db_session import create_session
from .users import User
from .talons import Talon
from .news import News

blueprint = flask.Blueprint(
    'news_api',
    __name__,
    template_folder='templates'
)


# Большой запрос выдающий всех пользователь и их талоны
@blueprint.route('/api/all')
def get_all():
    db_sess = create_session()
    ans = []
    for i in db_sess.query(User).all():
        ans.append({'email': i.email,
                    'name': i.name,
                    'hashed_password': i.hashed_password,
                    'is_admin': i.is_admin,
                    'talons': [item.to_dict(only=('id', 'number', 'desc', 'actuality')) for item in
                               db_sess.query(Talon).filter(Talon.user_id == i.id)],
                    'news': [item.to_dict(only=('title', 'text')) for item in
                               db_sess.query(News).filter(News.user_id == i.id)]})
    return jsonify(ans)



# API для запросов
@blueprint.route('/api/talons')
def get_talons():
    db_sess = create_session()
    return jsonify({'talons': [item.to_dict() for item in db_sess.query(Talon).all()]})


@blueprint.route('/api/talons/<int:talon_id>', methods=['GET'])
def get_one_talon(talon_id):
    db_sess = create_session()
    talon = db_sess.query(Talon).get(talon_id)
    if not talon:
        return make_response(jsonify({'error': 'Not found'}), 404)
    return jsonify(
        {
            'talon': talon.to_dict()
        }
    )


@blueprint.route('/api/talons/<int:talon_id>', methods=['DELETE'])
def delete_talon(talon_id):
    db_sess = create_session()
    talon = db_sess.query(Talon).get(talon_id)
    if not talon:
        return make_response(jsonify({'error': 'Not found'}), 404)
    db_sess.delete(talon)
    db_sess.commit()
    return jsonify({'success': 'OK'})


# API для пользователей
@blueprint.route('/api/users')
def get_users():
    db_sess = create_session()
    return jsonify({'users': [item.to_dict() for item in db_sess.query(User).all()]})


@blueprint.route('/api/users/<int:user_id>', methods=['GET'])
def get_one_user(user_id):
    db_sess = create_session()
    users = db_sess.query(User).get(user_id)
    if not users:
        return make_response(jsonify({'error': 'Not found'}), 404)
    return jsonify(
        {
            'user': users.to_dict()
        }
    )


@blueprint.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    db_sess = create_session()
    user = db_sess.query(User).get(user_id)
    if not user:
        return make_response(jsonify({'error': 'Not found'}), 404)
    db_sess.delete(user)
    db_sess.commit()
    return jsonify({'success': 'OK'})


# API для новостей
@blueprint.route('/api/news')
def get_news():
    db_sess = create_session()
    return jsonify({'news': [item.to_dict() for item in db_sess.query(News).all()]})


@blueprint.route('/api/news/<int:news_id>', methods=['GET'])
def get_one_news(news_id):
    db_sess = create_session()
    news = db_sess.query(News).get(news_id)
    if not news:
        return make_response(jsonify({'error': 'Not found'}), 404)
    return jsonify(
        {
            'news': news.to_dict()
        }
    )
