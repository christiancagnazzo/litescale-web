from math import floor, gcd
from db import *
import csv

ERROR = 0
NOT_ERROR = 1
INSERT = 0
INSERT_IGNORE = 1


def all_project_list(user):
    db = Dbconnect()
    query = "SELECT P.ProjectId, P.ProjectName, P.ProjectOwner, \
                    P.Phenomenon, P.TupleSize, P.ReplicateInstances \
            FROM Project P JOIN Authorization A ON P.ProjectId=A.Project \
            WHERE A.Authorized = %s"
    project_list = db.select_advanced(query, ("A.Authorized", user))
    db.close()
    return project_list
    # Returns the list of projects which the user is authorized to access


def own_project_list(user):
    db = Dbconnect()
    condition = "ProjectOwner = %s"
    project_list = db.select('Project', condition, 'ProjectId', 'ProjectName', 'ProjectOwner', 
                             'Phenomenon', 'TupleSize', 'ReplicateInstances', ProjectOwner=user)
    db.close()
    return project_list
    # Returns the list of projects which the user is owner


def insert_user(user, password):
    db = Dbconnect()
    result = db.insert('_User', INSERT, user, password)
    db.close()
    if (isinstance(result, int)):
        return NOT_ERROR, "User entered correctly"
    else:
        return ERROR, "User not entered"
    # Insert a new user into the database


def search_user(user):
    db = Dbconnect()
    condition = "Email = %s"
    result = db.select('_User', condition, 'Email', 'Password', Email=user)
    db.close()
    if not result:
        return ERROR, "User not found"
    return NOT_ERROR, result
    # Check login


def delete_user(user):
    db = Dbconnect()
    condition = 'Email = %s'
    result = db.delete('_User', condition, user)
    db.close()
    if (isinstance(result, int)):
        return NOT_ERROR, "User deleted correctly"
    else:
        return ERROR, "User not deleted"
    # Delete user


def delete_project(project_id):
    db = Dbconnect()
    condition = 'ProjectId = %s'
    result = db.delete('Project', condition, project_id)
    db.close()
    if (isinstance(result, int) and result):
        return NOT_ERROR, "Project deleted correctly"
    else:
        return ERROR, "Project does not exist"
    # Delete project


def get_authorization(project_id, user):
    db = Dbconnect()
    result = db.insert('Authorization', INSERT, project_id, user)
    db.close()
    if (isinstance(result, int)):
        return NOT_ERROR, "Authorization given correctly"
    else:
        return ERROR, "Authorization not given correctly"
    # Get authorization


def remove_authorization(project_id, user):
    db = Dbconnect()
    condition = 'Project = %s && Authorized = %s'
    result = db.delete('Authorization', condition, project_id, user)
    db.close()
    if (isinstance(result, int) and result > 0):
        return NOT_ERROR, "Authorization removed correctly"
    else:
        return ERROR, "Authorization not removed correctly"
    # Remove authorization


def check_authorization(project_id, user):
    db = Dbconnect()
    query = "SELECT * FROM Authorization A WHERE A.Project = %s AND A.Authorized = %s"
    result = db.select_advanced(
        query, ("A.Project", project_id), ("A.Authorized", user))

    if (not result):
        return ERROR, "User not authorized"
    else:
        return NOT_ERROR, "User authorized"
    # Check project authorization


def check_owner(project_id, user):
    db = Dbconnect()
    query = "SELECT * FROM Project P WHERE P.ProjectId = %s AND P.ProjectOwner = %s"
    result = db.select_advanced(
        query, ("P.ProjectId", project_id), ("P.ProjectOwner", user))

    if (not result):
        return ERROR, "User not authorized"
    else:
        return NOT_ERROR, "User authorized"
    # Check project owner


def make_tuples(instances, k, p):
    n = len(instances)

    while gcd(n, k) != 1:
        instances = instances[:-1]
        n = len(instances)

    tuples = dict()
    tuple_id = 0
    for j in range(p):
        for x in range(int(floor(n/k))):
            t = [(x*(k**(j+1)) + (i*(k**j))) % n for i in range(k)]
            tuples[tuple_id] = [instances[x] for x in t]
            tuple_id += 1
    return tuples
    # Create tuples of a project


def new_project(user, project_name, phenomenon, tuple_size, replication, instance_file):
    # Insert project into db
    db = Dbconnect()
    
    project_id = db.insert('Project',
                           INSERT,
                           ProjectName=project_name,
                           Phenomenon=phenomenon,
                           TupleSize=tuple_size,
                           ReplicateInstances=replication,
                           ProjectOwner=user)
    if (not isinstance(project_id, int)):
        return ERROR, "Project not create: " + project_id.msg

    # Owner authorization
    get_authorization(project_id, user)

    # Insert instance into the db
    instances = []
    with open(instance_file, encoding='utf-8') as f:
        tsv_file = csv.reader(f,delimiter="\t")
        try:
            for row in tsv_file:
                id, text = row[0], row[1]
                instances.append({"id": id, "text": text})
                res = db.insert('Instance', INSERT, id, text, project_id)
                if not isinstance(res,int):
                    raise
        except:
            condition = 'ProjectId = %s'
            db.delete('Project', condition, project_id)
            return ERROR, "Wrong instance file format"
    
    if (len(instances) <= tuple_size):        
        condition = 'ProjectId = %s'
        db.delete('Project', condition, project_id)
        return ERROR, "Wrong instance file format"

    # Make tuples
    tuples = make_tuples(instances, tuple_size, replication)

    # Insert tuples in the database
    for tup_id, tup in tuples.items():
        db.insert('Tuple', INSERT_IGNORE, tup_id, project_id)
        for instance in tup:
            db.insert('InstanceTuple', INSERT,
                      instance['id'], tup_id, project_id)

    db.close()
    return project_id, "Project create correctly"
    # Create a new project


def get_project(project_id):
    db = Dbconnect()
    condition = "ProjectId = %s"
    result = db.select('Project', condition,
                       'ProjectName',
                       'Phenomenon',
                       'TupleSize',
                       'ReplicateInstances',
                       'ProjectOwner',
                       ProjectId=project_id)

    if result == []:
        return ERROR, "Project not found"

    project_dict = {
        "project_name": result[0][0],
        "phenomenon": result[0][1],
        "tuple_size": result[0][2],
        "replication": result[0][3],
        "owner": result[0][4],
        "tuples": []
    }

    tuples = dict()
    instance = []

    sql = "SELECT COUNT(*) FROM Tuple WHERE Project = %s"
    num_tuples = db.select_advanced(sql, ('Project', project_id))

    for i in range(num_tuples[0]):

        # Get n instances of each tuples
        query = "SELECT I.InstanceId, I.InstanceDescription \
                FROM InstanceTuple IT JOIN Instance I ON (IT.Instance=I.InstanceId AND IT.Project=I.Project) \
                WHERE IT.Tuple = %s AND IT.Project = %s"
        tuples_instances = db.select_advanced(
            query, ('IT.Tuple', i), ('IT.Project', project_id))

        # Reconstruction tuple
        for t in range(project_dict["tuple_size"]):
            instance.append(
                {"id": tuples_instances[t][0], "text": tuples_instances[t][1]}
            )
        tuples[i] = instance
        instance = []

    db.close()
    project_dict["tuples"] = tuples
    return NOT_ERROR, project_dict
    # Get project dictionary


def get_annotations(project_id, user):
    db = Dbconnect()

    query = "SELECT Tuple, Best, Worst FROM Annotation WHERE Annotator=%s AND Project=%s"
    result = db.select_advanced(
        query, ('Annotator', user), ('Project', project_id))

    annotations = dict()
    for r in result:
        annotations[r[0]] = {"best": r[1], "worst": r[2]}

    db.close()
    return annotations
    # Returns the annotations made by a user in a project


def next_tuple(project_id, user):
    rst, project_dict = get_project(project_id)

    if not rst:
        return None, None

    annotations = get_annotations(project_id, user)

    for tup_id, tup in project_dict["tuples"].items():
        if tup_id in annotations:
            continue
        return tup_id, tup
    return None, None
    # Return the next tuple to annotate


def progress(project_id, user):
    rst, project_dict = get_project(project_id)

    if not rst:
        return None, None

    annotations = get_annotations(project_id, user)
    return len(annotations), len(project_dict["tuples"])
    # Progress of annotations


def empty_annotations(project_id):
    db = Dbconnect()

    condition = "Project = %s"
    result = db.select('Annotation', condition,
                       'AnnotationId', Project=project_id)

    db.close()

    if not result:
        return True

    return False
    # Check if exist annotations


def annotate(project_id, user, tup_id, answer_best, answer_worst):
    annotations = get_annotations(project_id, user)

    annotations[tup_id] = {
        "best": answer_best,
        "worst": answer_worst
    }

    db = Dbconnect()

    db.insert('Annotation',
              INSERT,
              Best=answer_best,
              Worst=answer_worst,
              Tuple=tup_id,
              Annotator=user,
              Project=project_id)

    db.close()
    return progress(project_id, user)
    # Insert annotation into the db


def generate_gold(project_id):
    if (empty_annotations(project_id)):
        return ERROR, "Empty annotations. Start to annotate"

    rst, project_dict = get_project(project_id)

    if not rst:
        return ERROR, "Project not found"

    ids = set()
    texts = dict()
    for tup_id, tup in project_dict["tuples"].items():
        for item in tup:
            ids.add(item["id"])
            texts[item["id"]] = item["text"]
    count_best = {id: 0 for id in ids}
    count_worst = {id: 0 for id in ids}

    db = Dbconnect()

    query = "SELECT Annotation.Best, COUNT(*) \
            FROM Annotation \
            WHERE Annotation.Project = %s \
            GROUP BY Annotation.Best"

    result = db.select_advanced(query, ('Annotation.Project', project_id))

    for r in result:
        count_best[r[0]] = r[1]

    query = "SELECT Annotation.Worst, COUNT(*) \
            FROM Annotation \
            WHERE Annotation.Project = %s \
            GROUP BY Annotation.Worst"

    result = db.select_advanced(query, ('Annotation.Project', project_id))

    for r in result:
        count_worst[r[0]] = r[1]

    db.close()

    # Calculation score
    scores = {id: count_best[id]-count_worst[id] for id in ids}
    max_score = max(list(scores.values()))
    min_score = min(list(scores.values()))
    scores_normalized = {id: (s-min_score)/(max_score-min_score)
                         for id, s in scores.items()}

    result = ""
    for id in ids:
        result += "{0}\t{1}\t{2}\n".format(
            id, texts[id], scores_normalized[id])

    return NOT_ERROR, result
