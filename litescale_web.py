from flask import Flask, render_template, request, session, redirect, url_for
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
        response = make_request('Login','post',query)
        response_json = response.json()

        if not response or response.status_code > 399:
            return render_template('login.html', error=True, msg=response_json['message'])

        # -> redirect to HOME MENU'
        session['user'] = user
        session['AccessToken'] = response_json['AccessToken']
        session['RefreshToken'] = response_json['RefreshToken']
        return redirect(url_for('home', user=user))

    # GET
    else:
        return render_template('login.html')

# ---------------------------------------------------------------------------------------------------- #


# ----------------------------------- LOGOUT --------------------------------------------------------- #


@app.route('/<user>/logout')
def logout(user):
    session.pop('user', None)
    session.pop('AccessToken', None)
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

            response = make_request('Users','post',query)
            response_json = response.json()

            if not response or response.status_code > 399:
                return render_template('registration.html', error=True, msg=response_json['message'])

            session['user'] = user
            session['AccessToken'] = response_json['AccessToken']
            session['RefreshToken'] = response_json['RefreshToken']
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
            instance_file = request.files.get('instance_file')
    
            # new project
            if (project_name and phenomenon and instance_file):
                instance_file.save(instance_file.filename)

                query = {'project_name': project_name,
                         'phenomenon': phenomenon,
                         'tuple_size': tuple_size,
                         'replication': replication }
                
                files = {
                    'json': (None, json.dumps(query), 'application/json'),
                    'file': (os.path.basename(instance_file.filename), open(instance_file.filename, 'rb'), 'application/octet-stream')
                }

                response = make_request('Projects','post',query,files)
                
                try:
                    os.remove(instance_file.filename)
                except:
                    pass

                if response.status_code == 401:
                    if not refresh_token():
                        return redirect("/")
                    else:
                        return redirect(request.url)
                
                response_json = response.json()

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

        type_list = {"type": "authorized"}
        response = make_request('ProjectList', 'get', type_list)
        
        if response.status_code == 401:
            if not refresh_token():
                return redirect("/")
            else:
                return redirect(request.url)
        
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

            response = make_request('Annotations', 'post', query)
            
            if response.status_code == 401:
                if not refresh_token():
                    return redirect("/")
                else:
                    return redirect(request.url)

        # POST -> start annotation
        if request.method == 'POST':
            project_id = request.form['project_id']
            params = {"project_id": project_id}
            
            response = make_request('Projects','get',params)
            
            if response.status_code == 401:
                if not refresh_token():
                    return redirect("/")
                else:
                    return redirect(request.url)
                
            project_dict = response.json()

            if not response or response.status_code > 399:
                return render_template('projects.html', user=user, action='start', project_list=project_list, rep=True, msg=response_json['message'])

            response = make_request('Tuples','get',params)
            
            if response.status_code == 401:
                if not refresh_token():
                    return redirect("/")
                else:
                    return redirect(request.url)
                
            tuples = response.json()

            if not response or response.status_code > 399:
                return render_template('projects.html', user=user, action='start', project_list=project_list, rep=True, msg=response_json['message'])

            if 'Error' in tuples:  # no tuple
                return render_template('projects.html', user=user, action='start', project_list=project_list, rep=True, msg=tuples['Error'])

            # progress
            response = make_request('Progress','get',params)
            
            if response.status_code == 401:
                if not refresh_token():
                    return redirect("/")
                else:
                    return redirect(request.url)
                
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
        
        type_list = {"type": "authorized"}
        response = make_request('ProjectList','get', type_list)
        
        if response.status_code == 401:
            if not refresh_token():
                return redirect("/")
            else:
                return redirect(request.url)
        
        project_list = response.json()
        
        if not response or response.status_code > 399:
            return render_template('projects.html', user=user, action='gold', rep=True, msg=response['message'])
        
        if 'Error' in project_list:
            return render_template('projects.html', user=user, action='gold', rep=True, msg=project_list['Error'])


        # POST
        if request.method == 'POST':
            project_id = request.form['project_id']

            params = {'project_id': project_id}
            response = make_request('Gold','get',params)
            
            if response.status_code == 401:
                if not refresh_token():
                    return redirect("/")
                else:
                    return redirect(request.url)

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
        
        type_list = {"type": "owner"}
        response = make_request('ProjectList','get',type_list)
        
        if response.status_code == 401:
            if not refresh_token():
                return redirect("/")
            else:
                return redirect(request.url)
        
        project_list = response.json()
        
        if not response or response.status_code > 399:
            return render_template('projects.html', user=user, action='delete', rep=True, msg=response['message'])
        
        if 'Error' in project_list:
            return render_template('projects.html', user=user, action='delete', rep=True, msg=project_list['Error'])


        # POST
        if request.method == 'POST':
            project_id = request.form['project_id']

            params = {"project_id": project_id}
            
            response = make_request('Projects','delete',params)
        
            if response.status_code == 401:
                if not refresh_token():
                    return redirect("/")
                else:
                    return redirect(request.url)
            
            response_json = response.json()

            if not response or response.status_code > 399:
                return render_template('projects.html', user=user, action='delete', project_list=project_list, rep=True, msg=response_json['message'])

            # -> PROJECT DELETED
            if 'result' in response_json and response_json['result'] == 'True':
                response = make_request('ProjectList','get',type_list)
                
                if response.status_code == 401:
                    if not refresh_token():
                        return redirect("/")
                    else:
                        return redirect(request.url)
                
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
        
        type_list = {"type": "owner"}
        
        response = make_request('ProjectList','get',type_list)
        
        if response.status_code == 401:
            if not refresh_token():
                return redirect("/")
            else:
                return redirect(request.url)
        
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
            response = make_request('Authorizations','post',query)
        
            if response.status_code == 401:
                if not refresh_token():
                    return redirect("/")
                else:
                    return redirect(request.url)
            
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

@app.route('/<user>/delete_account')
def delete_account(user):
    if session.get('user') == user:
        # delete account
        response = make_request('Users','delete')
        return redirect('/')
    else:
        return redirect('/')

# ---------------------------------------------------------------------------------------------------- #


# Auxiliar function to make a request and return a response

def make_request(resource, type_request, parameters, files=None):
    if   resource == 'Login': url = "http://localhost:5000/litescale/api/login"
    elif resource == 'Users': url = "http://localhost:5000/litescale/api/users"
    elif resource == 'ProjectList': url = "http://localhost:5000/litescale/api/projectList"
    elif resource == 'Projects': url = "http://localhost:5000/litescale/api/projects"
    elif resource == 'Tuples': url = "http://localhost:5000/litescale/api/tuples"
    elif resource == 'Annotations': url = "http://localhost:5000/litescale/api/annotations"
    elif resource == 'Gold': url = "http://localhost:5000/litescale/api/gold"
    elif resource == 'Progress': url = "http://localhost:5000/litescale/api/progress"
    elif resource == 'Auhtorization': url = "http://localhost:5000/litescale/api/auhtorizations"
        
    if 'AccessToken' in session:
        headers = {'Authorization': 'Bearer {}'.format(session.get('AccessToken'))}
    else:
        headers = ""
        
    if resource == 'Projects' and type_request == 'post':
        return requests.post(url, json=parameters, headers=headers, files=files)
    else:
        if   type_request == 'get': return requests.get(url, headers=headers, params=parameters)
        elif type_request == 'post': return requests.post(url, headers=headers, json=parameters)
        elif type_request == 'delete': return requests.delete(url, headers=headers, params=parameters)


def refresh_token():
    if 'RefreshToken' in session:
        headers_r = {'Authorization': 'Bearer {}'.format(session.get('RefreshToken'))}
        response = requests.post("http://localhost:5000/litescale/api/token", headers=headers_r)
        response_json = response.json()
    
        if response.status_code == 200:
            session['AccessToken'] = response_json['AccessToken']
            return True
    return False
    
    
    
    

if __name__ == '__main__':
    app.run(debug=True, port=5002)
