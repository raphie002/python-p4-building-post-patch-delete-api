#!/usr/bin/env python3
# server/seed.py
from random import randint, choice as rc
from faker import Faker
from app import app
from models import db, Game, Review, User

fake = Faker()

with app.app_context():
    print("Clearing database...")
    Review.query.delete()
    User.query.delete()
    Game.query.delete()

    print("Seeding users...")
    users = []
    # Create a test user we know the password for
    test_user = User(name="Raphie")
    test_user.password_hash = "password123"
    users.append(test_user)

    for i in range(10):
        u = User(name=fake.name())
        # All fake users get the same password for easy testing
        u.password_hash = "password123"
        users.append(u)
    db.session.add_all(users)

    print("Seeding games...")
    games = []
    for i in range(20):
        g = Game(
            title=fake.unique.sentence(nb_words=3),
            genre=rc(["RPG", "Action", "Indie", "Strategy"]),
            platform=rc(["PC", "PS5", "Switch"]),
            price=randint(10, 60)
        )
        games.append(g)
    db.session.add_all(games)

    print("Seeding reviews...")
    for u in users:
        # Give each user 1-3 random reviews
        for i in range(randint(1, 3)):
            r = Review(
                score=randint(1, 10),
                comment=fake.sentence(),
                user=u,
                game=rc(games)
            )
            # Use try/except because our unique constraint might 
            # prevent duplicate user/game reviews during random seeding
            try:
                db.session.add(r)
                db.session.commit()
            except:
                db.session.rollback()

    print("Done seeding!")