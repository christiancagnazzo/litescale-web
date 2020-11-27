from math import floor, gcd
from db import *

ERROR = 0
NOT_ERROR = 1

# TODO
# check autorization first function


def project_list(user):
    db = Dbconnect()
    query = "SELECT P.ProjectId, P.ProjectName, P.ProjectOwner \
            FROM Project P JOIN Authorization A ON P.ProjectId=A.Project \
            WHERE A.Authorized = %s"
    project_list = db.select_advanced(query, ("A.Authorized", user))
    db.close()
    return project_list
    # Returns the list of projects which the user is authorized to access


def insert_user(user, password):
    db = Dbconnect()
    result = db.insert('_User', False, user, password)
    db.close()
    if (isinstance(result, int)):
        return NOT_ERROR, "User entered correctly"
    else:
        return ERROR, "User not entered: " + result.msg
    # Insert a new user into the database


def delete_user(user):
    db = Dbconnect()
    condition = 'Email = %s'
    result = db.delete('_User', condition, user)
    db.close()
    if (isinstance(result, int)):
        return NOT_ERROR, "User deleted correctly"
    else:
        return ERROR, "User not deleted: " + result.msg
    # Delete user


def delete_project(project_id):
    db = Dbconnect()
    condition = 'ProjectId = %s'
    result = db.delete('Project', condition, project_id)
    db.close()
    if (isinstance(result, int)):
        return NOT_ERROR, "Project deleted correctly"
    else:
        return ERROR, "Projct not deleted: " + result.msg
    # Delete user


def get_authorization(project_id, user):
    db = Dbconnect()
    result = db.insert('Authorization', False, project_id, user)
    if (isinstance(result, int)):
        return NOT_ERROR, "Authorization given correctly"
    else:
        return ERROR, "Authorization not given correctly: " + result.msg
    # Get authorization


def check_authorization(project_id, user):
    db = Dbconnect()
    query = "SELECT * FROM Authorization A WHERE A.Project = %s AND A.Authorized = %s"
    result = db.select_advanced(
        query, ("A.Project", project_id), ("A.Authorized", user))

    if (not result):
        return ERROR, "User not authorized"
    else:
        return NOT_ERROR, "User authorized"
    # Check authorization


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
                           False,
                           ProjectName=project_name,
                           Phenomenon=phenomenon,
                           TupleSize=tuple_size,
                           ReplicateInstances=replication,
                           ProjectOwner=user)
    if (not isinstance(project_id, int)):
        return ERROR, "Project not create: " + result.msg

    # Owner authorization
    get_authorization(project_id, user)

    # Insert instance into the db (!!!! instance file !!!)
    instances = []
    with open(instance_file) as f:
        for line in f:
            id, text = line.strip().split("\t")
            instances.append({"id": id, "text": text})
            # True = INSERT IGNORE
            db.insert('Instance', True, id, text, project_id)

    # Make tuples
    tuples = make_tuples(instances, tuple_size, replication)

    # Insert tuples in the database
    for tup_id, tup in tuples.items():
        db.insert('Tuple', True, tup_id, project_id)  # True = INSERT IGNORE
        for instance in tup:
            # Unique instances in each project
            query = "SELECT InstanceId FROM Instance WHERE InstanceDescription = %s AND Project = %s"
            instance_id = db.select_advanced(query,
                                             ('InstanceDescription',
                                              instance["text"]),
                                             ('Project', project_id))
            db.insert('InstanceTuple', True,
                      instance_id[0], tup_id, project_id)  # True = INSERT IGNORE

    db.close()
    return NOT_ERROR, "Project create correctly"
    # Create a new project
