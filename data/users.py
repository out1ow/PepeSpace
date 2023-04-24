import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Users(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    chat_id = sqlalchemy.Column(sqlalchemy.Integer, unique=True)
    name = sqlalchemy.Column(sqlalchemy.String, unique=True,
                             nullable=True)
    tg_name = sqlalchemy.Column(sqlalchemy.String, unique=True,
                                nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    credits = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    resources = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    exp = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    level = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    planets = orm.relationship("Planets", back_populates='user')
