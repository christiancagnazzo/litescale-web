from tests.BaseCase import BaseCase, EMAIL_TEST, PASSWORD_TEST
import json
from io import BytesIO

class TestProjectInfo(BaseCase):
    
    def test_succesful_project_list(self):
        payload = json.dumps({
            "email": EMAIL_TEST,
            "password": PASSWORD_TEST
        })
        
        response = self.app.post('/litescale/api/users', headers={"Content-Type": "application/json"}, data=payload)
        response = self.app.post('/litescale/api/login', headers={"Content-Type": "application/json"}, data=payload)
        access_token = response.json['AccessToken']
        
        payload = {'project_name': "P1",
                    'phenomenon': "Phenomenon",
                    'tuple_size': 4,
                    'replication': 4 }
       
        data = { 'file': (BytesIO(b'1\tDasher\n2\tDancer\n3\tPrancer\n4\tVixem\n5\tDonner'), 'example.tsv'), 
                 'json': json.dumps(payload),}
          
        response = self.app.post('/litescale/api/projects',
                                headers={"Authorization": f"Bearer {access_token}"},
                                data=data)
        
        payload['project_name'] = "P2"
        
        data = { 'file': (BytesIO(b'1\tDasher\n2\tDancer\n3\tPrancer\n4\tVixem\n5\tDonner'), 'example.tsv'), 
                 'json': json.dumps(payload),}
        
        response = self.app.post('/litescale/api/projects',
                                headers={"Authorization": f"Bearer {access_token}"},
                                data=data)
        
        payload['project_name'] = "P3"
        
        data = { 'file': (BytesIO(b'1\tDasher\n2\tDancer\n3\tPrancer\n4\tVixem\n5\tDonner'), 'example.tsv'), 
                 'json': json.dumps(payload),}
        
        response = self.app.post('/litescale/api/projects',
                                headers={"Authorization": f"Bearer {access_token}"},
                                data=data)
        
        data = { 'type': 'owner'}
        
        response = self.app.get('/litescale/api/projectList',
                                headers={"Authorization": f"Bearer {access_token}"},
                                query_string=data)
        
        project_list = response.json
        self.assertEqual(200, response.status_code)
        self.assertEqual(3, len(project_list))
        self.assertEqual('P1', project_list[0]['projectName'])
        self.assertEqual('P2', project_list[1]['projectName'])
        self.assertEqual('P3', project_list[2]['projectName'])
        
        
def test_error_type(self):
        payload = json.dumps({
            "email": EMAIL_TEST,
            "password": PASSWORD_TEST
        })
        
        response = self.app.post('/litescale/api/users', headers={"Content-Type": "application/json"}, data=payload)
        response = self.app.post('/litescale/api/login', headers={"Content-Type": "application/json"}, data=payload)
        access_token = response.json['AccessToken']
        
        data = { 'type': 'ownery'}
        
        response = self.app.get('/litescale/api/projectList',
                                headers={"Authorization": f"Bearer {access_token}"},
                                query_string=data)
        
        self.assertEqual(400, response.status_code)
        self.assertEqual('Invalid type list. Indicate \'owner\' or \'authorized\'', response.json['message'])
        
        
        
def test_miss_type(self):
        payload = json.dumps({
            "email": EMAIL_TEST,
            "password": PASSWORD_TEST
        })
        
        response = self.app.post('/litescale/api/users', headers={"Content-Type": "application/json"}, data=payload)
        response = self.app.post('/litescale/api/login', headers={"Content-Type": "application/json"}, data=payload)
        access_token = response.json['AccessToken']
        
        response = self.app.get('/litescale/api/projectList',
                                headers={"Authorization": f"Bearer {access_token}"},)
        
        self.assertEqual(400, response.status_code)
        
        
def test_empty_list(self):
        payload = json.dumps({
            "email": EMAIL_TEST,
            "password": PASSWORD_TEST
        })
        
        response = self.app.post('/litescale/api/users', headers={"Content-Type": "application/json"}, data=payload)
        response = self.app.post('/litescale/api/login', headers={"Content-Type": "application/json"}, data=payload)
        access_token = response.json['AccessToken']
        
        data = { 'type': 'owner'}
        
        response = self.app.get('/litescale/api/projectList',
                                headers={"Authorization": f"Bearer {access_token}"},
                                query_string=data)
        
        project_list = response.json
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(project_list))
        self.assertEqual('There are no projects', response.json['Error'])
        