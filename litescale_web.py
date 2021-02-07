from flask import Flask, render_template, request, session, redirect, url_for
import json
import requests
import os 

# User default: root / 1234

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'litescale'  # Session key

@app.route('/')
def main():
    return redirect('home')


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

        try:
            params = {'email': user, 'password': password}
            response = requests.post(make_url('Login'), json=params)
            responsej = response.json()
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            return render_template('error.html', msg="Could not connect to server")
        except:
            if response.status_code == 500:
                return render_template('error.html', msg="Internal server error")
            return render_template('login.html', error=True, msg=responsej['message'])
           
         # -> redirect to HOME MENU'
        session['user'] = user
        session['AccessToken'] = responsej['AccessToken']
        session['RefreshToken'] = responsej['RefreshToken']
        if 'current_location' in session:
            return redirect(session['current_location'])
        return redirect('home')

    # GET
    else:
        return render_template('login.html')

# ---------------------------------------------------------------------------------------------------- #


# ----------------------------------- LOGOUT --------------------------------------------------------- #


@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('current_location', None)
    session.pop('AccessToken', None)
    session.pop('RefreshToken', None)
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
            params = {'email': details['email'],
                     'password': details['password']}

            try:
                response = requests.post(make_url('Users'), json=params)
                responsej = response.json()
                response.raise_for_status()
            except requests.exceptions.ConnectionError:
                return render_template('error.html', msg="Could not connect to server")
            except:
                if response.status_code == 500:
                    return render_template('error.html', msg="Internal server error")
                return render_template('registration.html', error=True, msg=responsej['message'])

            if 'result' in responsej and responsej['result'] == 'True':
                try:
                    params = {'email': user, 'password': password}
                    response = requests.post(make_url('Login'), json=params)
                    responsej = response.json()
                    response.raise_for_status()
                except requests.exceptions.ConnectionError:
                    return render_template('error.html', msg="Could not connect to server")
                except:
                    if response.status_code == 500:
                        return render_template('error.html', msg="Internal server error")
                    return render_template('login.html', error=True, msg=responsej['message'])
           
            # -> redirect to HOME MENU'
            session['user'] = user
            session['AccessToken'] = responsej['AccessToken']
            session['RefreshToken'] = responsej['RefreshToken']
            return redirect('home')
                
        else:  # empty fields
            return render_template('registration.html', error=True, msg='Complete all fields')
    # GET
    return render_template('registration.html')

# ---------------------------------------------------------------------------------------------------- #


# ---------------------------------------- HOME MENU' ------------------------------------------------ #


@app.route('/home')
def home():
    if 'user' in session:
        return render_template('home.html', user=session.get('user'))
    else:
        return render_template('home.html')

# ---------------------------------------------------------------------------------------------------- #


# ----------------------------- CREATE NEW PROJECT --------------------------------------------------- #


@app.route('/new', methods=['GET', 'POST'])
def new():
    if 'user' in session: 
        user = session.get('user')
            
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

                params = {'project_name': project_name,
                         'phenomenon': phenomenon,
                         'tuple_size': tuple_size,
                         'replication': replication }
                
                files = {
                    'json': (None, json.dumps(params), 'application/json'),
                    'file': (os.path.basename(instance_file.filename), open(instance_file.filename, 'rb'), 'application/octet-stream')
                }
                
                try:
                    response = requests.post(make_url('Projects'), headers=make_header(), files=files, json=params)
                    responsej = response.json()
                    response.raise_for_status()
                except requests.exceptions.ConnectionError:
                    return render_template('error.html', msg="Could not connect to server")
                except:
                    if response.status_code == 500:
                        return render_template('error.html', msg="Internal server error")
                    if response.status_code == 401:
                        session['current_location'] = request.path
                        return render_template('login.html', error=True, msg='Session expired. Re-login, please') # need new fresh token
                    return render_template('new.html',  user=user, rep=True, msg=responsej['message'])
                
                try:
                    os.remove(instance_file.filename)
                except:
                    pass

                if 'result' in responsej and responsej['result'] == 'True':
                    # -> PROJECT CREATED
                    return redirect('start')
                    #return render_template('new.html',  user=user, rep=True, msg='Project created')

            else:  # empty fileds
                return render_template('new.html',  user=user, rep=True, msg='Complete all fields')
        # GET
        return render_template('new.html', user=user)
    else:
        return redirect('login')

# ---------------------------------------------------------------------------------------------------- #


# ------------------------------ START/CONTINUE ANNOTATION ------------------------------------------- #


@app.route('/start', methods=['GET', 'POST'])
def start():
    if 'user' in session: 
        user = session.get('user')
        params = {'type': 'authorized'}
        
        rst, project_list, progress_list = get_project_list(params)
        
        if rst is None: 
            session['current_location'] = request.path
            return render_template('login.html', error=True, msg='Session expired. Re-login, please')
        elif not rst:
            return render_template('projects.html', user=user, action='start', rep=True, msg=project_list['message'])
        elif 'Error' in project_list:
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
            params = {'project_id': project_id,
                     'tup_id': tup_id,
                     'answer_best': answer_best,
                     'answer_worst': answer_worst}

            try:
                response = requests.post(make_url('Annotations'), headers=make_header(), json=params)
                response.raise_for_status()
            except requests.exceptions.ConnectionError:
                return render_template('error.html', msg="Could not connect to server")
            except:
                if response.status_code == 500:
                    return render_template('error.html', msg="Internal server error")
                # need new fresh token 
                session['current_location'] = request.path
                return render_template('login.html', error=True, msg='Session expired. Re-login, please')
            
        # POST -> start annotation
        if request.method == 'POST':
            project_id = request.form['project_id']
            params = {'project_id': project_id}
            
            try:
                response = requests.get(make_url('Projects'), params=params, headers=make_header())
                rspj = project_dict = response.json()
                response.raise_for_status()
                
                response = requests.get(make_url('Tuples'), params=params, headers=make_header())
                rspj = tuples = response.json()
                response.raise_for_status()
                
                if 'Error' in tuples:  # no tuple
                    progress_list[int(project_id)] = '100.0'
                    return render_template('projects.html', user=user, action='start', project_list=project_list, progress_list=progress_list ,rep=True, msg=tuples['Error'])
                
                response = requests.get(make_url('Progress'), params=params, headers=make_header())
                rspj = progress = response.json()
                response.raise_for_status()
                
            except requests.exceptions.ConnectionError:
                return render_template('error.html', msg="Could not connect to server")
            except:
                if response.status_code == 500:
                    return render_template('error.html', msg="Internal server error")
                if response.status_code == 401:
                    if 'message' in project_list and 'sub_status' in project_list['message']:
                        status_code = project_list['message']['sub_status']
                        if status_code == 40: # token expired
                            result = refresh_token()
                            if result:
                                return redirect(request.url, code=307)
                            else:
                                session['current_location'] = request.path
                                return render_template('login.html', error=True, msg='Session expired. Re-login, please')
                    session['current_location'] = request.path
                    return render_template('login.html', error=True, msg='Session expired. Re-login, please')
                return render_template('projects.html', user=user, action='start', project_list=project_list, progress_list=progress_list, rep=True, msg=rspj['Error'])
            

            done = progress['done']
            total = progress['total']
            progress_string = 'Progress: {0}/{1} {2:.1f}%'.format(
                done, total, 100.0*(done/total))

            # tuple
            return render_template('annotation.html', project_id=project_id, phenomenon=project_dict['phenomenon'], user=user, tup_id=tuples['tup_id'], tup=tuples['tup'], progress=progress_string)
        
        # GET -> project list
        return render_template('projects.html', user=user, action='start', project_list=project_list, progress_list=progress_list)
        
    else:
        return redirect('login')

# ---------------------------------------------------------------------------------------------------- #


# ----------------------------------- GENERATE GOLD FILE --------------------------------------------- #


@app.route('/gold', methods=['GET', 'POST'])
def gold():
    if 'user' in session: 
        user = session.get('user')
        
        params = {'type': 'authorized'}
        
        rst, project_list, progress_list = get_project_list(params)
        
        if rst is None: 
            session['current_location'] = request.path
            return render_template('login.html', error=True, msg='Session expired. Re-login, please')
        elif not rst:
            return render_template('projects.html', user=user, action='gold', rep=True, msg=project_list['message'])
        elif 'Error' in project_list:
            return render_template('projects.html', user=user, action='gold', rep=True, msg=project_list['Error'])
        
        # POST
        if request.method == 'POST':
            project_id = request.form['project_id']
            params = {'project_id': project_id}
            
            try:
                response = requests.get(make_url('Gold'), params=params, headers=make_header())
                response.raise_for_status()
            except requests.exceptions.ConnectionError:
                return render_template('error.html', msg="Could not connect to server")
            except:
                if response.status_code == 500:
                    return render_template('error.html', msg="Internal server error")
                if response.status_code == 401:
                    session['current_location'] = request.path
                    return render_template('login.html', error=True, msg='Session expired. Re-login, please')
                responsej = response.json()
                return render_template('projects.html', user=user, action='gold', project_list=project_list, progress_list=progress_list, rep=True, msg=responsej['message'])
         
            file = open('static/gold.tsv', 'wb')
            file.write(response.content)
            file.close

            return redirect(url_for('static', filename='gold.tsv'))

        # GET
        return render_template('projects.html', user=user, action='gold', project_list=project_list, progress_list=progress_list)
    else:
        return redirect('login')

# ---------------------------------------------------------------------------------------------------- #


# ------------------------------------ DELETE PROJECT ------------------------------------------------ #


@app.route('/delete', methods=['GET', 'POST'])
def delete():
    if 'user' in session: 
        user = session.get('user')
        
        params = {'type': 'owner'}
        
        rst, project_list, progress_list = get_project_list(params)
        
        if rst is None: 
            session['current_location'] = request.path
            return render_template('login.html', error=True, msg='Session expired. Re-login, please')
        elif not rst:
            return render_template('projects.html', user=user, action='delete', rep=True, msg=project_list['message'])
        elif 'Error' in project_list:
            return render_template('projects.html', user=user, action='delete', rep=True, msg=project_list['Error'])
        
        # POST
        if request.method == 'POST':
            project_id = request.form['project_id']

            params = {'project_id': project_id}
            
            try:
                response = requests.delete(make_url('Projects'), params=params, headers=make_header())
                responsej = response.json()
                response.raise_for_status()
            except requests.exceptions.ConnectionError:
                return render_template('error.html', msg="Could not connect to server")
            except:
                if response.status_code == 500:
                    return render_template('error.html', msg="Internal server error")
                if response.status_code == 401:
                    session['current_location'] = request.path
                    return render_template('login.html', error=True, msg='Session expired. Re-login, please')
                return render_template('projects.html', user=user, action='delete', project_list=project_list, progress_list=progress_list, rep=True, msg=responsej['message'])
     
            # -> PROJECT DELETED
            if 'result' in responsej and responsej['result'] == 'True':
                params = {'type': 'owner'}
                
                rst, project_list, progress_list = get_project_list(params)
        
                if rst is None: 
                    session['current_location'] = request.path
                    return render_template('login.html', error=True, msg='Session expired. Re-login, please')
                elif not rst:
                    return render_template('projects.html', user=user, action='start', rep=True, msg=project_list['message'])
                elif 'Error' in project_list:
                    return render_template('projects.html', user=user, action='delete', rep=True, msg=project_list['Error'])
                
            return render_template('projects.html', user=user, action='delete', project_list=project_list, progress_list=progress_list, rep=True, msg='Project deleted')
        
        # project list
        return render_template('projects.html', user=user, action='delete', project_list=project_list, progress_list=progress_list)
    else:
        return redirect('login')

# ---------------------------------------------------------------------------------------------------- #


# ------------------------------------ GET AUTHORIZATION PROJECT ------------------------------------- #


@app.route('/authorization', methods=['GET', 'POST'])
def authorization():
    if 'user' in session: 
        user = session.get('user')
        
        params = {'type': 'owner'}
        
        rst, project_list, progress_list = get_project_list(params)
        
        if rst is None: 
            session['current_location'] = request.path
            return render_template('login.html', error=True, msg='Session expired. Re-login, please')
        elif not rst:
            return render_template('projects.html', user=user, action='authorization', rep=True, msg=project_list['message'])
        elif 'Error' in project_list:
            return render_template('projects.html', user=user, action='authorization', rep=True, msg=project_list['Error'])
        
        # POST
        if request.method == 'POST':
            details = request.form
            project_id = details['project_id']
            user_to = details['user']

            if (not project_id or not user_to):  # empty fields
                return render_template('projects.html', user=user, action='authorization', rep=True, msg='Complete all fields', project_list=project_list, progress_list=progress_list)

            params = {'project_id': project_id, 'user_to': user_to}
            
            try:
                response = requests.post(make_url('Authorization'), json=params, headers=make_header())
                responsej = response.json()
                response.raise_for_status()
            except requests.exceptions.ConnectionError:
                return render_template('error.html', msg="Could not connect to server")
            except:
                if response.status_code == 500:
                    return render_template('error.html', msg="Internal server error")
                if response.status_code == 401:
                    session['current_location'] = request.path
                    return render_template('login.html', error=True, msg='Session expired. Re-login, please')
                return render_template('projects.html', user=user, action='authorization', rep=True, msg=responsej['message'], project_list=project_list, progress_list=progress_list)
            
            if 'result' in responsej and responsej['result'] == 'True':
                return render_template('projects.html', user=user, action='authorization', rep=True, msg='Authorization given correctly', project_list=project_list, progress_list=progress_list)
            else:
                return render_template('projects.html', user=user, action='authorization', rep=True, msg='Authorization not given correctly', project_list=project_list, progress_list=progress_list)
            

        # GET
        return render_template('projects.html', user=user, action='authorization', project_list=project_list, progress_list=progress_list)
    else:
        return redirect('login')

# ---------------------------------------------------------------------------------------------------- #


# --------------------------------------- DELETE ACCOUNT --------------------------------------------- #

@app.route('/delete_account')
def delete_account():
    if 'user' in session: 
        try:
            response = requests.delete(make_url('Users'), headers=make_header())
            response.raise_for_status()
            return redirect('logout')
        except requests.exceptions.ConnectionError:
            return render_template('error.html', msg="Could not connect to server")
        except:
            if response.status_code == 500:
                return render_template('error.html', msg="Internal server error")
            return render_template('login')
    else:
        return redirect('/')

# ---------------------------------------------------------------------------------------------------- #


# Auxiliar functions to make a url and header request

def make_url(resource):
    if   resource == 'Login': url = 'http://localhost:5000/litescale/api/login'
    elif resource == 'Users': url = 'http://localhost:5000/litescale/api/users'
    elif resource == 'ProjectList': url = 'http://localhost:5000/litescale/api/projectList'
    elif resource == 'Projects': url = 'http://localhost:5000/litescale/api/projects'
    elif resource == 'Tuples': url = 'http://localhost:5000/litescale/api/tuples'
    elif resource == 'Annotations': url = 'http://localhost:5000/litescale/api/annotations'
    elif resource == 'Gold': url = 'http://localhost:5000/litescale/api/gold'
    elif resource == 'Progress': url = 'http://localhost:5000/litescale/api/progress'
    elif resource == 'Authorization': url = 'http://localhost:5000/litescale/api/authorizations'

    return url
    

def make_header():
    if 'AccessToken' in session:
        return {'Authorization': 'Bearer {}'.format(session.get('AccessToken'))}
    return None

    
def refresh_token():
    if 'RefreshToken' in session:
        header = {'Authorization': 'Bearer {}'.format(session.get('RefreshToken'))}
        response = requests.post('http://localhost:5000/litescale/api/token', headers=header)
        response_json = response.json()
    
        if response.status_code == 200:
            session['AccessToken'] = response_json['AccessToken']
            return True
    return False


def get_project_list(params):
    try:
        response = requests.get(make_url('ProjectList'), params=params, headers=make_header())
        project_list = response.json()
        response.raise_for_status()
    except:
        if response.status_code == 401:
            if 'message' in project_list and 'sub_status' in project_list['message']:
                status_code = project_list['message']['sub_status']
                if status_code == 40: # token expired
                    result = refresh_token()
                    if result:
                        return get_project_list(params)
                    else:
                        return None, None, None
                return None, None, None
        return False, project_list, None
     
    if 'Error' in project_list:
        return True, project_list, None    
                
    progress_list = {}
    for project in project_list:
        try:
            p_id = project['projectId']
            params = {'project_id': p_id }
            response = requests.get(make_url('Progress'), params=params, headers=make_header())
            progress = response.json()
            response.raise_for_status()
            done = progress['done']
            total = progress['total']
            progress_list.update({p_id : 100.0*(done/total)})
        except:
            return None, None, None
    return True, project_list, progress_list


if __name__ == '__main__':
    app.run(debug=True, port=5002)
