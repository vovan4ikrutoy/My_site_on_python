import sqlalchemy as sa
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase
from flask_login import UserMixin
from sqlalchemy.util.preloaded import orm


class Talon(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'talons'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))
    number = sa.Column(sa.String)
    desc = sa.Column(sa.String)
    actuality = sa.Column(sa.Date)

    user_name = orm.relationship('User')
