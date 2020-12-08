from flask import Flask, render_template, request, session, redirect, url_for, flash
from litescale import *
from werkzeug.security import generate_password_hash, check_password_hash

# TO-DO
# security password
# handle entered text file error
# authorization project

# User default
# email: root - password: 1234

app = Flask(__name__)

# Sessione key
app.secret_key = 'litescale'


@app.route('/')
def main():
    session['user'] = None
    return redirect("login")

# --------------------------------------------- LOGIN -------------------------------------------- #


@app.route('/login', methods=["GET", "POST"])
def login():
    # POST
    if (request.method == "POST"):
        details = request.form
        user = details['email']
        password = details['password']

        if (not user or not password):  # empty fields
            return render_template("login.html", error=True, msg="Complete all fields")

        result, user = search_user(user)
        if not result:  # user not found in the db
            return render_template("login.html", error=True, msg=user)

        if check_password_hash(user[0][1], password):  # check password
            session['user'] = user[0][0]
            # -> redirect to HOME MENU'
            return redirect(url_for("home", user=user[0][0]))

        else:  # incorrect password
            return render_template("login.html", error=True, msg="Incorrect Email or Password")
    # GET
    else:
        return render_template("login.html")
# ---------------------------------------------------------------------------------------------------- #


# ----------------------------------- LOGOUT --------------------------------------------------------- #


@app.route('/<user>/logout')
def logout(user):
    session.pop('user', None)
    return redirect('/')
# ---------------------------------------------------------------------------------------------------- #


# ----------------------------------- REGISTRATION --------------------------------------------------- #


@app.route('/signUp', methods=["GET", "POST"])
def signUp():
    # POST (registration)
    if request.method == "POST":
        details = request.form
        user = details['email']
        password = details['password']

        if user and password:
            password = generate_password_hash(details['password'])
            result, msg = insert_user(user, password)

            if not result:  # existing user
                return render_template("registration.html", error=True, msg="User not valid")

            session['user'] = user
            # -> redirect to HOME MENU'
            return redirect(url_for("home", user=user))

        else:  # empty fields
            return render_template("registration.html", error=True, msg="Complete all fields")
    # GET
    return render_template("registration.html")

# ---------------------------------------------------------------------------------------------------- #


# ---------------------------------------- HOME MENU' ------------------------------------------------ #


@app.route('/<user>/home')
def home(user):
    if session.get('user'):
        return render_template("home.html", user=user)
    else:
        return redirect("/")

# ---------------------------------------------------------------------------------------------------- #


# ----------------------------- CREATE NEW PROJECT --------------------------------------------------- #


@app.route('/<user>/new', methods=["GET", "POST"])
def new(user):
    if session.get('user'):
        # POST (new project)
        if request.method == "POST":
            try:
                os.remove("tmp.tsv")
            except:
                pass
            details = request.form
            project_name = details['project_name']
            phenomenon = details['phenomenon']
            tuple_size = eval(details['tuple_size'])
            replication = eval(details['replication'])
            request.files.get('instance_file').save("tmp.tsv")
            # new project
            if (project_name and phenomenon and request.files.get('instance_file')):
                rst, msg = new_project(
                    user,
                    project_name,
                    phenomenon,
                    tuple_size,
                    replication,
                    "tmp.tsv"
                )
                try:
                    os.remove("tmp.tsv")
                except:
                    pass
                
                if (not rst): # project not created (db error)
                    return render_template("new.html", error=True, msg=msg)
                
                else:
                    return redirect(url_for("home", user=user)) # -> redirect to HOME MENU'
            
            else: # empty fileds
                return render_template("new.html", error=True, msg="Complete all fields")
        # GET
        return render_template("new.html", user=user)
    else:
        return redirect("/")

# ---------------------------------------------------------------------------------------------------- #


@app.route('/<user>/start')
def start(user):
    if session.get('user'):
        return render_template("projects.html", user=user, action="start", project_list=project_list(user))
    else:
        return redirect("/")


@app.route('/<user>/gold')
def gold(user):
    if session.get('user'):
        return render_template("projects.html", user=user, action="gold", project_list=project_list(user))
    else:
        return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
