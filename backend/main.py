from flask import Flask
from flask_sqlalchemy import SQLAlchemy 
from datetime import datetime
from models import db, User, Post, Follow
from flask_bcrypt import Bcrypt  
from flask import request,jsonify,json
from flask_cors import CORS
from flask_jwt_extended import JWTManager,create_access_token,jwt_required,get_jwt_identity
import os


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@localhost:5432/twitter_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.urandom(24)
jwt= JWTManager(app)
db.init_app(app)
bcrypt = Bcrypt(app)
CORS(app)




@app.route('/register',methods = ['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if len(password)<6:
        return jsonify({'message':'Password must be at least 6 chareacters long!'}),400

    
    if User.query.filter_by(username=username).first():
        return jsonify({'message' : 'Username already registered!'}),400
    
    new_user = User(username=username)
    new_user.set_password(password)
    
    db.session.add(new_user)
    db.session.commit()

    return jsonify({ 'message': 'Registration succesful! '}),201


@app.route('/login',methods= ['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user and bcrypt.check_password_hash(user.password,password):
        access_token = create_access_token(identity= user.id) 
            
        return jsonify(access_token=access_token, message="Login successful"), 200
    else:
        return jsonify({'message':'Username or password incorrect'}),401
    


@app.route('/posts',methods= ['POST'])
@jwt_required()
def create_post():
    try:
        current_user_id = get_jwt_identity()
    except Exception as e:
        return jsonify({'message':'Token is missing or invalid'})   
    
    data = request.get_json()
    content = data.get('content')
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'message' : 'User not found'}),404
    
    new_post = Post(user_id = current_user_id,content=content)
    try:
        db.session.add(new_post)
        db.session.commit()
        return jsonify({'message' : 'Post has been shared!'}),201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message':'Failed to create post','error': str(e)}),500
   
    
@app.route('/posts',methods = ['GET'])
def get_posts():
    posts = Post.query.all()
    post_list = [{'id': post.id,'content':post.content,'user_id':post.user_id} for post in posts]
    return jsonify(post_list),200  

@app.route('/posts/<int:user_id>',methods = ['GET'])
def get_user_posts(user_id):
    posts = Post.query.filter_by(user_id=user_id).all()
    post_list = [{'id':post.id,'content':post.content,'user_id':post.user_id} for post in posts ]
    return jsonify(post_list)




@app.route('/users',methods = ['GET'])
def get_users():
    users = User.query.all()
    user_list = [{'id':user.id,'username':user.username} for user in users]
    return jsonify(user_list),200

@app.route('/follow',methods = ['POST'])
@jwt_required()
def follow():
    data = request.get_json()
    follower_id = data.get('follower_id')
    followed_id = data.get('followed_id')

    current_user_id = get_jwt_identity()
    if current_user_id != follower_id:
        return jsonify({'message':'Unauthorized'}),403

    follower = User.query.get(follower_id)
    followed = User.query.get(followed_id)

    if not follower or not followed :
        return jsonify({'message':'User not found!!'}),404
    
    if Follow.query.filter_by(follower_id=follower_id,followed_id=followed_id).first():
        return ({'message':'You are already following this user'}),400
    
    new_follow = Follow(follower_id=follower_id,followed_id=followed_id)
    db.session.add(new_follow)
    db.session.commit() 


    return jsonify({'message':'You are now following this user'}),201

@app.route('/unfollow',methods = ['POST'])
@jwt_required()
def unfollow():
    data = request.get_json()
    follower_id = data.get('follower_id')
    followed_id = data.get('followed_id')

    current_user_id = get_jwt_identity()
    if (current_user_id != follower_id):
        return jsonify({'message':'Unouthorized'}),403

    follower = User.query.get(follower_id)
    followed = User.query.get(followed_id)

    if not follower or not followed:
        return jsonify({'message' : 'User not found'}),404
    
    follow =  Follow.query.filter_by(follower_id=follower_id,followed_id=followed_id).first()

    if not follow:
        return jsonify({'message':'You are not following user!'}),400
    
    db.session.delete(follow)
    db.session.commit()
    return jsonify({'message':'You have unfollowed this user!'}),200
        
@app.route('/followers/<int:user_id>',methods = ['GET'])
def get_followers(user_id):
    user = User.query.get(user_id)
    
    if not user:
        return ({'message' : 'User not found'}),404
    
    followers = Follow.query.filter_by(followed_id=user_id).all()

    if not followers:
        return jsonify({'message' : 'No followers found'})
    
    follower_list = [{'id':follower.follower.id,'username':follower.follower.username} for follower in followers]

    return jsonify(follower_list)


@app.route('/following/<int:user_id>',methods=['GET'])
def get_following(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({'message':'User not found!'}),404


    following = Follow.query.filter_by(follower_id = user_id).all()
    if not following:
        return jsonify({'message':'No following user found'})

    
    following_list = [{'id': follow.followed.id, 'username': follow.followed.username} for follow in following]


    return jsonify(following_list),200
    
@app.route('/posts/<int:post_id>',methods = ['GET'])
def get_post(post_id):
    post = Post.query.get(post_id)

    if not post:
        return jsonify({'message':'Post not found'}),404
    
    post_data = {
        'id' : post.id,
        'content' : post.content,
        'user_id' : post.user_id
    }
    return jsonify(post_data)

@app.route('/posts/<int:post_id>',methods=['DELETE'])
def delete_post(post_id):

    post = Post.query.get(post_id)
    if not post:
        return jsonify({'message':'Post not found!'}),404
    
    db.session.delete(post)
    db.session.commit()

    return jsonify({'message':'Post has been deleted succesfully!'}),200

@app.route('/posts/<int:post_id>',methods=['PUT'])
def update_post(post_id):
    post = Post.query.get(post_id)

    if not post:
        return jsonify({'message':'Post not found!'}),404
    
    data = request.get_json()
    content = data.get('content')
    
    if content :
        post.content = content
        db.session.commit()
        return jsonify({'message':'Post uptaded succesfully!'}),200
    
    return jsonify({'message':'Content is required to update the post'})


@app.route('/posts/followed/<int:user_id>')
def get_followed_posts(user_id):

    following = Follow.query.filter_by(follower_id=user_id).all()

    if not following:
        return jsonify([]),200

    followed_ids = []
    for follow in following:
        followed_ids.append(follow.followed_id)

    posts = Post.query.filter(Post.user_id.in_(followed_ids)).all()
    post_list = [{'id': post.id, 'content': post.content, 'user_id': post.user_id} for post in posts]

    return jsonify(post_list), 200



@app.route('/')
def home():
    return 'Hello Flask'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        
        test_user2 = {'username': 'test_user2', 'password': 'test_password'}
        response = app.test_client().post('/login', data=json.dumps(test_user2), content_type='application/json')
        print(response.get_json()) 
    

    app.run(debug=True)



