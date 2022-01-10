"""Example flask app that stores passwords hashed with Bcrypt. Yay!"""

from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.exceptions import Unauthorized 
from models import connect_db, db, User,Feedback
from forms import RegisterForm, LoginForm, DeleteForm, FeedbackForm

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:metal@localhost:5432/feedb"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"

connect_db(app)
db.create_all()

toolbar = DebugToolbarExtension(app)


@app.route("/")
def homepage():
    """Show homepage with links to site areas."""
    if 'username' in session:
      user=session['username']
    else:
        user="No user logged in"  
    return render_template("index.html",user=user)



@app.route("/user/register", methods=["GET", "POST"])
def register():
    """Register user: produce form & handle form submission."""

    if "username" in session:
        return redirect(f"/user/{session['username']}")

    form = RegisterForm()

    if form.validate_on_submit():
        name = form.username.data
        pwd = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        
        user = User.register(name, pwd)
        user_data = User(username= name,password=user.password,email = email, first_name = first_name,
        last_name = last_name)
        db.session.add(user_data)
        db.session.commit()

        session["username"] = user_data.username
        

        # on successful login, redirect to user data page
        return redirect(f"/user/{user_data.username}")

    else:
        return render_template("user/register.html", form=form)
#End-Register

@app.route("/user/login", methods=["GET", "POST"])
def login():
    """Produce login form or handle login."""
    if "username" in session:
        return redirect(f"/user/{session['username']}")
    
    form = LoginForm()

    if form.validate_on_submit():
        name = form.username.data
        pwd = form.password.data

        # authenticate will return a user or False
        user = User.authenticate(name, pwd)

        if user:
            session["username"] = user.username  # keep logged in
            return redirect(f"/user/{name}")

        else:
            form.username.errors = ["Bad name/password"]

    return render_template("/user/login.html", form=form)
# end-login

# Direct a loged in user to a list of his feedbaks
@app.route("/user/<username>")
def data_user(username):
    """Example hidden page for logged-in users only."""
    
    if "username" not in session or username != session['username']:
        flash("You must be logged in to view!")
        return redirect("/")

        # alternatively, can return HTTP Unauthorized status:
        #
        # from werkzeug.exceptions import Unauthorized
        # raise Unauthorized()

    else:
        user=User.query.get(username)
        form = DeleteForm()
        return render_template("/user/userfeedback.html",user=user,form=form)



@app.route("/user/logout")
def logout():
    """Logs user out and redirects to homepage."""

    session.pop("username")
    
    return redirect("/user/login")
# end-logout

@app.route('/user')
def list_users():
    """List user data."""
    
    if "username" in session:
        username=session["username"]
        user=User.query.get(username)
    return render_template('/user/user.html', user=user)
    

@app.route("/user/<username>/delete", methods=["POST"])
def remove_user(username):
    """Remove user nad redirect to login."""

    if "username" not in session or username != session['username']:
        raise Unauthorized()

    user = User.query.get(username)
    db.session.delete(user)
    db.session.commit()
    session.pop("username")

    return redirect("/user/login")

# *********** User's feedback ************


@app.route("/user/<username>/feedback/new", methods=["GET", "POST"])
def new_feedback(username):
    """Show add-feedback form and process it."""

    if "username" not in session or username != session['username']:
        raise Unauthorized()

    form = FeedbackForm()

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        feedback = Feedback(
            title=title,
            content=content,
            username=username,
        )

        db.session.add(feedback)
        db.session.commit()

        return redirect(f"/user/{feedback.username}")

    else:
        return render_template("feedback/newfeedback.html", form=form)
# end- new feedback


@app.route("/feedback/<int:feedback_id>/update", methods=["GET", "POST"])
def update_feedback(feedback_id):
    """Show update-feedback form and process it."""

    feedback = Feedback.query.get(feedback_id)

    if "username" not in session or feedback.username != session['username']:
        raise Unauthorized()

    form = FeedbackForm(obj=feedback)

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data

        db.session.commit()

        return redirect(f"/user/{feedback.username}")

    return render_template("/feedback/editfeedback.html", form=form, feedback=feedback)
# end- update feedback

@app.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
def delete_feedback(feedback_id):
    """Delete feedback."""

    feedback = Feedback.query.get(feedback_id)
    if "username" not in session or feedback.username != session['username']:
        raise Unauthorized()

    form = DeleteForm()

    if form.validate_on_submit():
        db.session.delete(feedback)
        db.session.commit()

    return redirect(f"/user/{feedback.username}")
# end- delete feedback

