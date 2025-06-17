from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

from models import db, User, Goal, Gratitude
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return send_from_directory('.', 'login.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['user_id'] = user.id
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    session['user_id'] = user.id
    return jsonify({'message': 'Registration successful'}), 201

@app.route('/create_profile', methods=['POST'])
def create_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.get_json()
    user = User.query.get(session['user_id'])
    
    user.name = data.get('name')
    user.location = data.get('location')
    user.bio = data.get('bio')
    user.avatar_color = data.get('avatar_color')
    
    db.session.commit()
    return jsonify({'message': 'Profile created successfully'}), 200

@app.route('/profile')
def get_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    user = User.query.get(session['user_id'])
    goals_count = Goal.query.filter_by(user_id=user.id).count()
    gratitudes_count = Gratitude.query.filter_by(user_id=user.id).count()
    
    return jsonify({
        'name': user.name,
        'location': user.location,
        'bio': user.bio,
        'avatar_color': user.avatar_color,
        'avatar_url': user.avatar_url,
        'goals_count': goals_count,
        'gratitudes_count': gratitudes_count,
        'streak': user.streak
    })

@app.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    if 'avatar' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file:
        filename = secure_filename(f"avatar_{session['user_id']}_{int(datetime.utcnow().timestamp())}.jpg")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        user = User.query.get(session['user_id'])
        user.avatar_url = f"/uploads/{filename}"
        db.session.commit()
        
        return jsonify({'avatar_url': user.avatar_url}), 200

@app.route('/add_goal', methods=['POST'])
def add_goal():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.get_json()
    user = User.query.get(session['user_id'])
    
    goal = Goal(
        content=data.get('content'),
        user_id=session['user_id']
    )
    db.session.add(goal)
    
    # Update user's streak
    user.update_streak()
    
    db.session.commit()
    return jsonify({'message': 'Goal added successfully'}), 200

@app.route('/complete_goal/<int:goal_id>', methods=['POST'])
def complete_goal(goal_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    goal = Goal.query.get_or_404(goal_id)
    if goal.user_id != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403

    goal.completed = True
    goal.completed_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': 'Goal marked as completed'}), 200

@app.route('/add_gratitude', methods=['POST'])
def add_gratitude():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.get_json()
    user = User.query.get(session['user_id'])
    
    gratitude = Gratitude(
        content=data.get('content'),
        user_id=session['user_id']
    )
    db.session.add(gratitude)
    
    # Update user's streak
    user.update_streak()
    
    db.session.commit()
    return jsonify({'message': 'Gratitude added successfully'}), 200

@app.route('/like_gratitude/<int:gratitude_id>', methods=['POST'])
def like_gratitude(gratitude_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    gratitude = Gratitude.query.get_or_404(gratitude_id)
    gratitude.likes += 1
    db.session.commit()
    
    return jsonify({'likes': gratitude.likes}), 200

@app.route('/feed')
def get_feed():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    # Get goals and gratitudes from the last 24 hours
    goals = Goal.query.filter(
        Goal.created_at >= datetime.utcnow().date()
    ).order_by(Goal.created_at.desc()).all()
    
    gratitudes = Gratitude.query.filter(
        Gratitude.created_at >= datetime.utcnow().date()
    ).order_by(Gratitude.created_at.desc()).all()

    # Combine and sort posts
    posts = []
    for goal in goals:
        posts.append({
            'type': 'goal',
            'id': goal.id,
            'content': goal.content,
            'created_at': goal.created_at.isoformat(),
            'completed': goal.completed,
            'completed_at': goal.completed_at.isoformat() if goal.completed_at else None,
            'user': {
                'name': goal.user.name,
                'avatar_color': goal.user.avatar_color,
                'avatar_url': goal.user.avatar_url
            }
        })
    
    for gratitude in gratitudes:
        posts.append({
            'type': 'gratitude',
            'id': gratitude.id,
            'content': gratitude.content,
            'created_at': gratitude.created_at.isoformat(),
            'likes': gratitude.likes,
            'user': {
                'name': gratitude.user.name,
                'avatar_color': gratitude.user.avatar_color,
                'avatar_url': gratitude.user.avatar_url
            }
        })

    # Sort by creation date
    posts.sort(key=lambda x: x['created_at'], reverse=True)
    return jsonify(posts)

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
