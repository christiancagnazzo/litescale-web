from tests.BaseCase import BaseCase, EMAIL_TEST, PASSWORD_TEST
import json
from io import BytesIO

class TestProjectInfo(BaseCase):
    
    def test_succesful_info_project(self):
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
       
        data = { 'file': (BytesIO(b'1\tDasher\n2\tDancer\n3\tPrancer\n4\tVixem\n5\tDonner'), 'example.tsv'), 
                 'json': json.dumps(payload),}
          
        response = self.app.post('/litescale/api/projects',
                                headers={"Authorization": f"Bearer {access_token}"},
                                data=data)
        
        data = { 'project_id': response.json['id']}
        
        response = self.app.get('/litescale/api/projects',
                                headers={"Authorization": f"Bearer {access_token}"},
                                query_string=data)
        
        project_dict = response.json
        self.assertEqual(200, response.status_code)
        self.assertEqual('test@mail.com', project_dict['owner'])
        self.assertEqual('Project', project_dict['project_name'])
        self.assertEqual('Phenomenon', project_dict['phenomenon'])
        self.assertEqual(4, project_dict['replication'])
        self.assertEqual(4, project_dict['tuple_size'])
        self.assertEqual(4, len(project_dict['tuples']))
        
    
    def test_wrong_id_project(self):
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
       
        data = { 'file': (BytesIO(b'1\tDasher\n2\tDancer\n3\tPrancer\n4\tVixem\n5\tDonner'), 'example.tsv'), 
                 'json': json.dumps(payload),}
          
        response = self.app.post('/litescale/api/projects',
                                headers={"Authorization": f"Bearer {access_token}"},
                                data=data)
        
        data = { 'project_id': 999}
        
        response = self.app.get('/litescale/api/projects',
                                headers={"Authorization": f"Bearer {access_token}"},
                                query_string=data)
        
        
        self.assertEqual(404, response.status_code)
        self.assertEqual('Resource not found', response.json['message'])
        
        
        
        

