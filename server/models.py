#!/usr/bin/env python3
# server/models.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, UniqueConstraint
from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin
from flask_bcrypt import Bcrypt

# Naming convention for foreign keys to ensure migrations work smoothly
metadata = MetaData(naming_convention={
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
})

db = SQLAlchemy(metadata=metadata)
bcrypt = Bcrypt()

class Game(db.Model, SerializerMixin):
    __tablename__ = 'games'

    # Rules: Include reviews, but don't let reviews include the game again (recursion)
    serialize_rules = ('-reviews.game',)

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True)
    genre = db.Column(db.String)
    platform = db.Column(db.String)
    price = db.Column(db.Integer)

    reviews = db.relationship('Review', backref='game')

class Review(db.Model, SerializerMixin):
    __tablename__ = 'reviews'

    # Rule: Include the user's name and game title in the review JSON
    serialize_rules = ('-game.reviews', '-user.reviews', 'user.name', 'game.title')
    
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer)
    comment = db.Column(db.String)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Constraint: One review per user per game
    __table_args__ = (UniqueConstraint('user_id', 'game_id', name='uq_user_game'),)

    @validates('score')
    def validate_score(self, key, score):
        if not (0 <= score <= 10):
            raise ValueError("Score must be between 0 and 10.")
        return score

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    serialize_rules = ('-reviews.user', '-_password_hash')

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    _password_hash = db.Column(db.String)

    reviews = db.relationship('Review', backref='user')

    @hybrid_property
    def password_hash(self):
        return self._password_hash

    @password_hash.setter
    def password_hash(self, password):
        hash_obj = bcrypt.generate_password_hash(password.encode('utf-8'))
        self._password_hash = hash_obj.decode('utf-8')

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password.encode('utf-8'))