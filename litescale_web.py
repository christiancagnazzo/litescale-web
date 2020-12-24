from flask import Flask, render_template, request, session, redirect, url_for, make_response
import json
import requests
import os 

# User default: root / 1234

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'litescale'  # Session key


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

        query = {"email": user, "password": password}
        response = requests.post(
            "http://localhost:5000/litescale/api/login", json=query)
        response_json = response.json()

        if not response or response.status_code > 399:
            return render_template('login.html', error=True, msg=response_json['message'])

        # -> redirect to HOME MENU'
        session['user'] = user
        session['token'] = response_json['AccessToken']
        return redirect(url_for('home', user=user))

    # GET
    else:
        return render_template('login.html')

# ---------------------------------------------------------------------------------------------------- #


# ----------------------------------- LOGOUT --------------------------------------------------------- #


@app.route('/<user>/logout')
def logout(user):
    session.pop('user', None)
    session.pop('token', None)
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
            query = {"email": details['email'],
                     "password": details['password']}

            response = requests.post(
                "http://localhost:5000/litescale/api/users", json=query)
            response_json = response.json()

            if not response or response.status_code > 399:
                return render_template('registration.html', error=True, msg=response_json['message'])

            session['user'] = user
            session['token'] = response_json['AccessToken']
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

                query = {'project_name': project_name,
                         'phenomenon': phenomenon,
                         'tuple_size': tuple_size,
                         'replication': replication }
                
                files = {
                    'json': (None, json.dumps(query), 'application/json'),
                    'file': (os.path.basename('tmp.tsv'), open('tmp.tsv', 'rb'), 'application/octet-stream')
                }
                
                headers = {'Authorization': 'Bearer {}'.format(
                    session.get('token'))}
                response = requests.post(
                    'http://localhost:5000/litescale/api/projects', json=query, headers=headers, files=files)
                response_json = response.json()

                try:
                    os.remove('tmp.tsv')
                except:
                    pass

                if not response or response.status_code > 399:
                    return render_template('new.html',  user=user, rep=True, msg=response_json['message'])

                if 'result' in response_json and response_json['result'] == 'True':
                    # -> PROJECT CREATED
                    return render_template('new.html',  user=user, rep=True, msg="Project created")

            else:  # empty fileds
                return render_template('new.html',  user=user, rep=True, msg='Complete all fields')
        # GET
        return render_template('new.html', user=user)
    else:
        return redirect('/')

# ---------------------------------------------------------------------------------------------------- #


# ------------------------------ START/CONTINUE ANNOTATION ------------------------------------------- #


@app.route('/<user>/start', methods=['GET', 'POST'])
def start(user):
    if session.get('user') == user:

        headers = {'Authorization': 'Bearer {}'.format(
            session.get('token'))}

        type_list = {"type": "authorized"}
        response = requests.get(
            "http://localhost:5000/litescale/api/projectList", headers=headers, params=type_list)
        project_list = response.json()

        if not response or response.status_code > 399:
            return render_template('projects.html', user=user, action='start', rep=True, msg=project_list['message'])
        
        if 'Error' in project_list:
            return render_template('projects.html', user=user, action='start', rep=True, msg=project_list['Error'])

        # POST -> save annotation into db
        if request.method == 'POST' and 'tup_id' in request.form:
            project_id = request.form['project_id']
            
            # save annotation
            details = request.form
            tup_id = details['tup_id']
            answer_best = details['best']
            answer_worst = details['worst']

            # annotate
            query = {"project_id": project_id,
                     "tup_id": tup_id,
                     "answer_best": answer_best,
                     "answer_worst": answer_worst}

            requests.post(
                "http://localhost:5000/litescale/api/annotations", headers=headers, json=query)

        # POST -> start annotation
        if request.method == 'POST':
            project_id = request.form['project_id']
            params = {"project_id": project_id}
            

            response = requests.get(
                "http://localhost:5000/litescale/api/projects", headers=headers, params=params)
            project_dict = response.json()

            if not response or response.status_code > 399:
                return render_template('projects.html', user=user, action='start', project_list=project_list, rep=True, msg=response_json['message'])

            response = requests.get(
                "http://localhost:5000/litescale/api/tuples", headers=headers, params=params)
            tuples = response.json()

            if not response or response.status_code > 399:
                return render_template('projects.html', user=user, action='start', project_list=project_list, rep=True, msg=response_json['message'])

            if 'Error' in tuples:  # no tuple
                return render_template('projects.html', user=user, action='start', project_list=project_list, rep=True, msg=tuples['Error'])

            # progress
            response = requests.get(
                "http://localhost:5000/litescale/api/progress", headers=headers, params=params)
            progress = response.json()

            if not response or response.status_code > 399:
                return render_template('projects.html', user=user, action='start', project_list=project_list, rep=True, msg=progress['message'])

            done = progress['done']
            total = progress['total']
            progress_string = 'progress: {0}/{1} {2:.1f}%'.format(
                done, total, 100.0*(done/total))

            # tuple
            return render_template('annotation.html', project_id=project_id, phenomenon=project_dict['phenomenon'], user=user, tup_id=tuples['tup_id'], tup=tuples['tup'], progress=progress_string)

        # GET -> project list
        return render_template('projects.html', user=user, action='start', project_list=project_list)
    else:
        return redirect('/')

# ---------------------------------------------------------------------------------------------------- #


# ----------------------------------- GENERATE GOLD FILE --------------------------------------------- #


@app.route('/<user>/gold', methods=['GET', 'POST'])
def gold(user):
    if session.get('user') == user:
        
        headers = {'Authorization': 'Bearer {}'.format(
            session.get('token'))}

        type_list = {"type": "authorized"}
        response = requests.get(
            "http://localhost:5000/litescale/api/projectList", headers=headers, params=type_list)
        project_list = response.json()
        
        if not response or response.status_code > 399:
            return render_template('projects.html', user=user, action='gold', rep=True, msg=response['message'])
        
        if 'Error' in project_list:
            return render_template('projects.html', user=user, action='gold', rep=True, msg=project_list['Error'])


        # POST
        if request.method == 'POST':
            project_id = request.form['project_id']

            params = {'project_id': project_id}
            headers = {'Authorization': 'Bearer {}'.format(
                session.get('token'))}
            response = requests.get(
                'http://localhost:5000/litescale/api/gold', params=params, headers=headers)

            if not response or response.status_code > 399:
                response = response.json()
                return render_template('projects.html', user=user, action='gold', project_list=project_list, rep=True, msg=response['message'])

            file = open("static/gold.tsv", 'wb')
            file.write(response.content)
            file.close

            return redirect(url_for('static', filename='gold.tsv'))

        # GET
        return render_template('projects.html', user=user, action='gold', project_list=project_list)
    else:
        return redirect('/')

# ---------------------------------------------------------------------------------------------------- #


# ------------------------------------ DELETE PROJECT ------------------------------------------------ #


@app.route('/<user>/delete', methods=['GET', 'POST'])
def delete(user):
    if session.get('user') == user:
        
        headers = {'Authorization': 'Bearer {}'.format(
            session.get('token'))}

        type_list = {"type": "owner"}
        response = requests.get(
            "http://localhost:5000/litescale/api/projectList", headers=headers, params=type_list)
        project_list = response.json()
        
        if not response or response.status_code > 399:
            return render_template('projects.html', user=user, action='delete', rep=True, msg=response['message'])
        
        if 'Error' in project_list:
            return render_template('projects.html', user=user, action='delete', rep=True, msg=project_list['Error'])


        # POST
        if request.method == 'POST':
            project_id = request.form['project_id']

            params = {"project_id": project_id}
            headers = {'Authorization': 'Bearer {}'.format(
                session.get('token'))}
            response = requests.delete(
                "http://localhost:5000/litescale/api/projects", params=params, headers=headers)
            response_json = response.json()

            if not response or response.status_code > 399:
                return render_template('projects.html', user=user, action='delete', project_list=project_list, rep=True, msg=response_json['message'])

            # -> PROJECT DELETED
            if 'result' in response_json and response_json['result'] == 'True':
                response = requests.get(
                    "http://localhost:5000/litescale/api/projectList", headers=headers, params=type_list)
                project_list = response.json()
        
                if not response or response.status_code > 399:
                    return render_template('projects.html', user=user, action='delete', rep=True, msg=response['message'])
            
                if 'Error' in project_list:
                    return render_template('projects.html', user=user, action='delete', rep=True, msg=project_list['Error'])

                    return render_template('projects.html', user=user, action='delete', project_list=project_list, rep=True, msg="Project deleted")

        # project list
        return render_template('projects.html', user=user, action='delete', project_list=project_list)
    else:
        return redirect('/')

# ---------------------------------------------------------------------------------------------------- #


# ------------------------------------ GET AUTHORIZATION PROJECT ------------------------------------- #


@app.route('/<user>/authorization', methods=['GET', 'POST'])
def authorization(user):
    if session.get('user') == user:
        
        headers = {'Authorization': 'Bearer {}'.format(
            session.get('token'))}

        type_list = {"type": "owner"}
        response = requests.get(
            "http://localhost:5000/litescale/api/projectList", headers=headers, params=type_list)
        project_list = response.json()
        
        if not response or response.status_code > 399:
            return render_template('projects.html', user=user, action='authorization', rep=True, msg=response['message'])
        
        if 'Error' in project_list:
            return render_template('projects.html', user=user, action='authorization', rep=True, msg=project_list['Error'])

        # POST
        if request.method == 'POST':
            details = request.form
            project_id = details['project_id']
            user_to = details['user']

            if (not project_id or not user_to):  # empty fields
                return render_template('authorization.html', user=user, action='authorization', rep=True, msg='Complete all fields', project_list=project_list)

            query = {"project_id": project_id, "user_to": user_to}
            response = requests.post(
                "http://localhost:5000/litescale/api/auhtorizations", json=query, headers=headers)
            response_json = response.json()

            if not response or response.status_code > 399:
                return render_template('authorization.html', user=user, action='authorization', rep=True, msg=response_json['message'], project_list=project_list)

            if 'result' in response_json and response_json['result'] == 'True':
                return render_template('authorization.html', user=user, action='authorization', rep=True, msg="Authorization given correctly", project_list=project_list)

        # GET
        return render_template('authorization.html', user=user, action='authorization', project_list=project_list)
    else:
        return redirect('/')

# ---------------------------------------------------------------------------------------------------- #


# --------------------------------------- DELETE ACCOUNT --------------------------------------------- #

@app.route('/delete_account')
def delete_account(user):
    if session.get('user') == user:
        # delete account
        headers = {'Authorization': 'Bearer {}'.format(session.get('token'))}
        requests.delete(
            "http://localhost:5000/litescale/api/login", headers=headers)
        return redirect('/')
    else:
        return redirect('/')

# ---------------------------------------------------------------------------------------------------- #


if __name__ == '__main__':
    app.run(debug=True, port=5002)
