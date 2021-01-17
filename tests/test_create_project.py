from tests.BaseCase import BaseCase, EMAIL_TEST, PASSWORD_TEST
import json
from io import BytesIO

class TestProjectCreation(BaseCase):
    
    def test_succesful_create_project(self):
        payload = json.dumps({
            "email": EMAIL_TEST,
            "password": PASSWORD_TEST
        })
        
        response = self.app.post('/litescale/api/users', headers={"Content-Type": "application/json"}, data=payload)
        response = self.app.post('/litescale/api/login', headers={"Content-Type": "application/json"}, data=payload)
        access_token = response.json['AccessToken']
        
        payload = {'project_name': "Project",
                    'phenomenon': "Phenomenon",
                    'tuple_size': 4,
                    'replication': 4 }
       
        data = { 'file': (BytesIO(b'1\tDasher\n2\tDancer\n3\tPrancer\n4\tDonner\n5\tVixem'), 'example.tsv'), 
                 'json': json.dumps(payload),}
          
        response = self.app.post('/litescale/api/projects',
                                headers={"Authorization": f"Bearer {access_token}"},
                                data = data)
        
        
        self.assertEqual("True", response.json['result'])
        self.assertEqual(int, type(response.json['id']))
        self.assertEqual(200, response.status_code)
        
    def test_few_instance_upload(self):
        payload = json.dumps({
            "email": EMAIL_TEST,
            "password": PASSWORD_TEST
        })
        
        response = self.app.post('/litescale/api/users', headers={"Content-Type": "application/json"}, data=payload)
        response = self.app.post('/litescale/api/login', headers={"Content-Type": "application/json"}, data=payload)
        access_token = response.json['AccessToken']
        
        payload = {'project_name': "Project",
                    'phenomenon': "Phenomenon",
                    'tuple_size': 4,
                    'replication': 4 }
       
        data = { 'file': (BytesIO(b'1\tDasher\n2\tDancer\n3\tPrancer'), 'example.tsv'), 
                 'json': json.dumps(payload),}
          
        response = self.app.post('/litescale/api/projects',
                                headers={"Authorization": f"Bearer {access_token}"},
                                data = data)
        
        
        self.assertEqual("Invalid file upload", response.json['message'])
        self.assertEqual(400, response.status_code)
        
        
    def test_missing_info_create_project(self):
        payload = json.dumps({
            "email": EMAIL_TEST,
            "password": PASSWORD_TEST
        })
        
        response = self.app.post('/litescale/api/users', headers={"Content-Type": "application/json"}, data=payload)
        response = self.app.post('/litescale/api/login', headers={"Content-Type": "application/json"}, data=payload)
        access_token = response.json['AccessToken']
        
        payload = {'project_name': "Project",
                    'phenomenon': "Phenomenon",
                    'replication': 4 }
       
        data = { 'file': (BytesIO(b'1\tDasher\n2\tDancer\n3\tPrancer'), 'example.tsv'), 
                 'json': json.dumps(payload),}
          
        response = self.app.post('/litescale/api/projects',
                                headers={"Authorization": f"Bearer {access_token}"},
                                data = data)
        
        
        self.assertEqual("Missing project info", response.json['message'])
        self.assertEqual(400, response.status_code)
        
    def test_missing_file_create_project(self):
        payload = json.dumps({
            "email": EMAIL_TEST,
            "password": PASSWORD_TEST
        })
        
        response = self.app.post('/litescale/api/users', headers={"Content-Type": "application/json"}, data=payload)
        response = self.app.post('/litescale/api/login', headers={"Content-Type": "application/json"}, data=payload)
        access_token = response.json['AccessToken']
        
        payload = {'project_name': "Project",
                    'phenomenon': "Phenomenon",
                    'tuple_size': 4,
                    'replication': 4 }
       
        data = { 'json': json.dumps(payload),}
          
        response = self.app.post('/litescale/api/projects',
                                headers={"Authorization": f"Bearer {access_token}"},
                                data = data)
        
        self.assertEqual("Missing project info", response.json['message'])
        self.assertEqual(400, response.status_code)
        
    def test_wrong_format_file_create_project(self):
        payload = json.dumps({
            "email": EMAIL_TEST,
            "password": PASSWORD_TEST
        })
        
        response = self.app.post('/litescale/api/users', headers={"Content-Type": "application/json"}, data=payload)
        response = self.app.post('/litescale/api/login', headers={"Content-Type": "application/json"}, data=payload)
        access_token = response.json['AccessToken']
        
        payload = {'project_name': "Project",
                    'phenomenon': "Phenomenon",
                    'tuple_size': 4,
                    'replication': 4 }
       
        data = { 'file': (BytesIO(b'1\tDasher\nDancer\n3\tPrancer\nVixen\n4\tBlixem\t5Donner'), 'example.tsv'), 
                 'json': json.dumps(payload),}
          
        response = self.app.post('/litescale/api/projects',
                                headers={"Authorization": f"Bearer {access_token}"},
                                data = data)
        
        self.assertEqual("Invalid file upload", response.json['message'])
        self.assertEqual(400, response.status_code)
        