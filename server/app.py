#!/usr/bin/env python3
# server/app.py
from flask import Flask, request, make_response, session
from flask_migrate import Migrate
from sqlalchemy import desc, asc
from sqlalchemy.exc import IntegrityError
from models import db, User, Review, Game

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = b'\x17\x01\x19\xda\x0e\x02\x04\x08' 
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)

# --- AUTHENTICATION ROUTES ---

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(name=data.get('name')).first()
    if user and user.authenticate(data.get('password')):
        session['user_id'] = user.id
        return make_response(user.to_dict(), 200)
    return make_response({"error": "Invalid name or password"}, 401)

@app.route('/logout', methods=['DELETE'])
def logout():
    session.pop('user_id', None)
    return make_response({}, 204)

@app.route('/check_session', methods=['GET'])
def check_session():
    user = User.query.filter_by(id=session.get('user_id')).first()
    if user:
        return make_response(user.to_dict(), 200)
    return make_response({"error": "Not logged in"}, 401)

# --- REVIEW ROUTES ---

@app.route('/reviews', methods=['GET', 'POST'])
def reviews():
    if request.method == 'GET':
        query = Review.query
        
        # Filtering & Search
        if request.args.get('game_id'):
            query = query.filter_by(game_id=request.args.get('game_id', type=int))
        if request.args.get('search'):
            query = query.filter(Review.comment.ilike(f"%{request.args.get('search')}%"))
        
        # Sorting
        sort = request.args.get('sort', 'created_at')
        order = desc if request.args.get('order') == 'desc' else asc
        query = query.order_by(order(getattr(Review, sort)))

        # Pagination
        page = request.args.get('page', 1, type=int)
        paginated = query.paginate(page=page, per_page=10, error_out=False)
        
        return make_response({
            "reviews": [r.to_dict() for r in paginated.items],
            "total_pages": paginated.pages
        }, 200)

    elif request.method == 'POST':
        user_id = session.get('user_id')
        if not user_id:
            return make_response({"error": "Login required"}, 401)
        
        try:
            data = request.get_json()
            new_review = Review(
                score=data.get('score'),
                comment=data.get('comment'),
                game_id=data.get('game_id'),
                user_id=user_id
            )
            db.session.add(new_review)
            db.session.commit()
            return make_response(new_review.to_dict(), 201)
        except (ValueError, IntegrityError) as e:
            db.session.rollback()
            return make_response({"errors": [str(e)]}, 400)

@app.route('/reviews/<int:id>', methods=['PATCH', 'DELETE'])
def review_by_id(id):
    review = Review.query.get(id)
    if not review:
        return make_response({"error": "Not found"}, 404)
    
    # Ownership Check
    if review.user_id != session.get('user_id'):
        return make_response({"error": "Unauthorized"}, 403)

    if request.method == 'PATCH':
        try:
            data = request.get_json()
            for attr in data:
                setattr(review, attr, data[attr])
            db.session.commit()
            return make_response(review.to_dict(), 200)
        except ValueError as e:
            return make_response({"errors": [str(e)]}, 400)

    elif request.method == 'DELETE':
        db.session.delete(review)
        db.session.commit()
        return make_response({}, 204)

if __name__ == '__main__':
    app.run(port=5555, debug=True)