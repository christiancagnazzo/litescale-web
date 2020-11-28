from flask import Flask, render_template, request, session, redirect
from litescale import *
from werkzeug.security import generate_password_hash, check_password_hash

# User default
# email: root - password: 1234

app = Flask(__name__)

# Sessione key
# chiave sessione
app.secret_key = 'litescale'


@app.route('/')
def main():
    session['user'] = None
    return redirect("login")


@app.route('/login', methods=["GET", "POST"])
def login():
    # POST
    if (request.method == "POST"):
        details = request.form
        user = details['email']
        password = details['password']
        result, user = search_user(user)
        if not result:
            return render_template("login.html", error=True, msg=user)
        if check_password_hash(user[0][1], password):
            session['user'] = user[0][0]
            return redirect("home")
        else:
            return render_template("login.html", error=True, msg="Incorrect Email or Password")
    # GET
    else:
        return render_template("login.html")


@app.route('/home')
def home():
    if session.get('user'):
        return render_template("home.html")
    else:
        return redirect("login")


@app.route('/signIn', methods=["GET", "POST"])
def signIn():
    # POST
    if request.method == "POST":
        details = request.form
        user = details['email']
        password = details['password']
        if user and password:
            password = generate_password_hash(details['password'])
            result, msg = insert_user(user, password)
            if not result:
                return render_template("registration.html", error=True, msg="User not valid")
            session['user'] = user
            return redirect("home")
        else:
            return render_template("registration.html", error=True, msg="Complete all fields")
    # GET
    return render_template("registration.html")

@app.route('/logout')
def logout():
   session.pop('user',None)
   return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
