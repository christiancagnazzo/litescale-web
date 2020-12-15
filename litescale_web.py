from flask import Flask, render_template, request, session, redirect, url_for
from litescale import *
from werkzeug.security import generate_password_hash, check_password_hash

# TO-DO
# file input error ?
# check authorization every

# User default
# email: root - password: 1234

app = Flask(__name__, static_url_path='/static')

# Sessione key
app.secret_key = 'litescale'


@app.route('/')
def main():
    return redirect('login')


# --------------------------------------------- LOGIN -------------------------------------------- #


@app.route('/login', methods=['GET', 'POST'])
def login():
    # POST
    if (request.method == 'POST'):
        details = request.form
        user = details['email']
        password = details['password']

        if (not user or not password):  # empty fields
            return render_template('login.html', error=True, msg='Complete all fields')

        result, user = search_user(user)
        if not result:  # user not found in the db
            return render_template('login.html', error=True, msg=user)

        if check_password_hash(user[0][1], password):  # check password
            session['user'] = user[0][0]
            # -> redirect to HOME MENU'
            return redirect(url_for('home', user=user[0][0]))

        else:  # incorrect password
            return render_template('login.html', error=True, msg='Incorrect Email or Password')
    # GET
    else:
        return render_template('login.html')

# ---------------------------------------------------------------------------------------------------- #


# ----------------------------------- LOGOUT --------------------------------------------------------- #


@app.route('/<user>/logout')
def logout(user):
    session.pop('user', None)
    return redirect('/')

# ---------------------------------------------------------------------------------------------------- #


# ----------------------------------- REGISTRATION --------------------------------------------------- #


@app.route('/signUp', methods=['GET', 'POST'])
def signUp():
    # POST (registration)
    if request.method == 'POST':
        details = request.form
        user = details['email']
        password = details['password']

        if user and password:
            password = generate_password_hash(details['password'])
            result, msg = insert_user(user, password)

            if not result:  # existing user
                return render_template('registration.html', error=True, msg='User not valid')

            session['user'] = user
            # -> redirect to HOME MENU'
            return redirect(url_for('home', user=user))

        else:  # empty fields
            return render_template('registration.html', error=True, msg='Complete all fields')
    # GET
    return render_template('registration.html')

# ---------------------------------------------------------------------------------------------------- #


# ---------------------------------------- HOME MENU' ------------------------------------------------ #


@app.route('/<user>/home')
def home(user):
    if session.get('user') == user:
        return render_template('home.html', user=user)
    else:
        return redirect('/')

# ---------------------------------------------------------------------------------------------------- #


# ----------------------------- CREATE NEW PROJECT --------------------------------------------------- #


@app.route('/<user>/new', methods=['GET', 'POST'])
def new(user):
    if session.get('user') == user:
        # POST (new project)
        if request.method == 'POST':
            try:
                os.remove('tmp.tsv')
            except:
                pass
            details = request.form
            project_name = details['project_name']
            phenomenon = details['phenomenon']
            tuple_size = eval(details['tuple_size'])
            replication = eval(details['replication'])
            request.files.get('instance_file').save('tmp.tsv')
            # new project
            if (project_name and phenomenon and request.files.get('instance_file')):
                rst, msg = new_project(
                    user,
                    project_name,
                    phenomenon,
                    tuple_size,
                    replication,
                    'tmp.tsv'
                )
                try:
                    os.remove('tmp.tsv')
                except:
                    pass

                if (not rst):  # project not created (db error)
                    return render_template('new.html',  user=user, rep=True, msg=msg)

                else:
                    # -> PROJECT CREATED
                    return render_template('new.html',  user=user, rep=True, msg=msg)
                
            else:  # empty fileds
                return render_template('new.html',  user=user, rep=True, msg='Complete all fields')
        # GET
        return render_template('new.html', user=user)
    else:
        return redirect('/')

# ---------------------------------------------------------------------------------------------------- #


# ------------------------------ START/CONTINUE ANNOTATION ------------------------------------------- #


@app.route('/<user>/start', methods=['GET','POST'])
def start(user):
    if session.get('user') == user:
        
        # POST -> save annotation into db
        if request.method=='POST' and 'tup_id' in request.form:
            id = request.form['project_id']
            
            # save annotation
            details = request.form
            tup_id = details['tup_id']
            answer_best = details['best']
            answer_worst = details['worst']

            # annotate into the db
            annotate(id, user, tup_id, answer_best, answer_worst)
    
        
        # POST -> start annotation
        if request.method=='POST':
            id = request.form['project_id']
            
            tup_id, tup = next_tuple(id, user)
            project_dict = get_project(id)

            if tup is None:  # no tuple
                return render_template('projects.html', user=user, action='start', project_list=all_project_list(user), rep=True, msg='No tuple to annotate')

            # tuple
            done, total = progress(id, user)
            progress_string = 'progress: {0}/{1} {2:.1f}%'.format(
                done, total, 100.0*(done/total))
            return render_template('annotation.html', project_id=id, phenomenon=project_dict['phenomenon'], user=user, tup_id=tup_id, tup=tup, progress=progress_string)

        
        # GET -> project list
        return render_template('projects.html', user=user, action='start', project_list=all_project_list(user))
    else:
        return redirect('/')

# ---------------------------------------------------------------------------------------------------- #


# ----------------------------------- GENERATE GOLD FILE --------------------------------------------- #


@app.route('/<user>/gold', methods=['GET','POST'])
def gold(user):
    if session.get('user') == user:

        # POST 
        if request.method=='POST':
            id = request.form['project_id']
        
            # generate gold
            rst, msg = generate_gold(id)

            if (rst):
                return redirect(url_for('static', filename='gold.tsv'))
            else:
                return render_template('projects.html', user=user, action='gold', project_list=all_project_list(user), rep=True, msg=msg)

        # GET
        return render_template('projects.html', user=user, action='gold', project_list=all_project_list(user))
    else:
        return redirect('/')

# ---------------------------------------------------------------------------------------------------- #


# ------------------------------------ DELETE PROJECT ------------------------------------------------ #


@app.route('/<user>/delete', methods=['GET', 'POST'])
def delete(user):
    if session.get('user') == user:

        # POST 
        if request.method=='POST':
            id = request.form['project_id']
            
            # delete project
            rst, msg = delete_project(id)

            if (not rst):  # error db
                return render_template('projects.html', user=user, action='delete', project_list=own_project_list(user), rep=True, msg=msg)

            # -> PROJECT DELETED
            return render_template('projects.html', user=user, action='delete', project_list=own_project_list(user), rep=True, msg=msg)

        # project list
        return render_template('projects.html', user=user, action='delete', project_list=own_project_list(user))
    else:
        return redirect('/')

# ---------------------------------------------------------------------------------------------------- #


# ------------------------------------ GET AUTHORIZATION PROJECT ------------------------------------- #


@app.route('/<user>/authorization', methods=['GET', 'POST'])
def authorization(user):
    if session.get('user') == user:
        
        # POST
        if request.method == 'POST':
            details = request.form
            project_id = details['project_id']
            user_to = details['user'] 
            
            if (not project_id or not user_to): # empty fields
                return render_template('authorization.html', user=user, action='authorization', rep=True, msg='Complete all fields', project_list=own_project_list(user))
            
            """rst, msg = check_authorization(project_id,user)
            if (not rst): # user not authorized
                return render_template('authorization.html', user=user, action='authorization', rep=True, msg=msg, project_list=own_project_list(user))"""
            
            rst, msg = get_authorization(project_id, user_to)  
            return render_template('authorization.html', user=user, action='authorization', rep=True, msg=msg, project_list=own_project_list(user))  
               
        
        # GET
        return render_template('authorization.html', user=user, action='authorization', project_list=own_project_list(user))
    else:
        return redirect('/')

# ---------------------------------------------------------------------------------------------------- #


# --------------------------------------- DELETE ACCOUNT --------------------------------------------- #

@app.route('/<user>/delete_account')
def delete_account(user):
    if session.get('user') == user:
        # delete account
        delete_user(user)
        return redirect('/')
    else:
        return redirect('/')

# ---------------------------------------------------------------------------------------------------- #


if __name__ == '__main__':
    app.run(debug=True)
