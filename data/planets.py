import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Planets(SqlAlchemyBase):
    __tablename__ = 'planets'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True, unique=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    fabrics = sqlalchemy.Column(sqlalchemy.Integer, default=2)
    ships = sqlalchemy.Column(sqlalchemy.Integer, default=2)
    available_ships = sqlalchemy.Column(sqlalchemy.Integer, default=2)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relationship('Users')
