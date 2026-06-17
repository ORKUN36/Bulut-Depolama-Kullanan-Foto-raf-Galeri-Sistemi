from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime


import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import os

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)

print("CLOUD_NAME =", os.getenv("CLOUD_NAME"))
print("API_KEY =", os.getenv("API_KEY"))
print("API_SECRET =", os.getenv("API_SECRET"))

app = Flask(__name__)

app.secret_key = "gizli_anahtar"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)

class User(UserMixin, db.Model):
    
    id = db.Column(db.Integer, primary_key=True)

    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))

    email = db.Column(db.String(150), unique=True)

    phone = db.Column(db.String(20))

    username = db.Column(db.String(100), unique=True)

    password = db.Column(db.String(100))

class Photo(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(100))

    image_url = db.Column(db.String(300))
    
    created_at = db.Column(
    db.DateTime,
    default=datetime.now
)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    
    is_deleted = db.Column(
    db.Boolean,
    default=False
)
    
    is_favorite = db.Column(
    db.Boolean,
    default=False
)

@app.route("/")
@login_required
def index():

    q = request.args.get("q")

    sort = request.args.get("sort")

    if q:

        photos_query = Photo.query.filter(

            Photo.title.contains(q),

            Photo.user_id == current_user.id,

            Photo.is_deleted == False

        )

    else:

        photos_query = Photo.query.filter_by(

            user_id=current_user.id,

            is_deleted=False

        )

    if sort == "old":

        photos_query = photos_query.order_by(
            Photo.created_at.asc()
        )

    else:

        photos_query = photos_query.order_by(
            Photo.created_at.desc()
        )

    photos = photos_query.all()

    return render_template(
        "index.html",
        photos=photos
    )

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():

    if request.method == "POST":

        title = request.form["title"]
        photo = request.files["photo"]

        result = cloudinary.uploader.upload(photo)

        image_url = result["secure_url"]
        
        print("FOTO URL =", image_url)

        new_photo = Photo(
    title=title,
    image_url=image_url,
    user_id=current_user.id
)

        db.session.add(new_photo)
        db.session.commit()

        return redirect("/")

    return render_template("upload.html")

@app.route("/delete/<int:id>")
def delete(id):

    photo = Photo.query.get(id)

    photo.is_deleted = True
    db.session.commit()

    return redirect("/")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    photo = Photo.query.get(id)

    if request.method == "POST":

        photo.title = request.form["title"]

        db.session.commit()

        return redirect("/")

    return render_template("edit.html", photo=photo)

@app.route("/test")
def test():
    return "TEST CALISTI"

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        first_name = request.form["first_name"]
        last_name = request.form["last_name"]

        email = request.form["email"]

        phone = request.form["phone"]

        username = request.form["username"]

        password = request.form["password"]

        new_user = User(

            first_name=first_name,
            last_name=last_name,

            email=email,

            phone=phone,

            username=username,

            password=password
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect("/login?success=1")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(
            username=username,
            password=password
        ).first()

        if user:
            login_user(user)
            return redirect("/")

    return render_template("login.html")

@app.route("/users")
def users():

    all_users = User.query.all()

    text = ""

    for user in all_users:
        text += user.username + "<br>"

    return text

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect("/")

@app.route("/profile")
@login_required
def profile():

    return render_template(
        "profile.html"
    )
    
@app.route("/trash")
@login_required
def trash():

    photos = Photo.query.filter_by(
        user_id=current_user.id,
        is_deleted=True
    ).all()

    return render_template(
        "trash.html",
        photos=photos
    )

@app.route("/restore/<int:id>")
@login_required
def restore(id):

    photo = Photo.query.get(id)

    photo.is_deleted = False

    db.session.commit()

    return redirect("/trash")

@app.route("/favorite/<int:id>")
@login_required
def favorite(id):

    photo = Photo.query.get(id)

    photo.is_favorite = not photo.is_favorite

    db.session.commit()

    return redirect("/")

@app.route("/favorites")
@login_required
def favorites():

    photos = Photo.query.filter_by(
        user_id=current_user.id,
        is_favorite=True,
        is_deleted=False
    ).all()

    return render_template(
        "favorites.html",
        photos=photos
    )
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        username = request.form["username"]

        email = request.form["email"]

        new_password = request.form["new_password"]

        confirm_password = request.form["confirm_password"]

        user = User.query.filter_by(
            username=username,
            email=email
        ).first()

        if user:

            if new_password == confirm_password:

                user.password = new_password

                db.session.commit()

                return redirect("/login")

    return render_template("forgot_password.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)