from tests.BaseCase import BaseCase, EMAIL_TEST, PASSWORD_TEST
import json

class TestUserLogin(BaseCase):
    
    def test_succesful_login(self):
        payload = json.dumps({
            "email": EMAIL_TEST,
            "password": PASSWORD_TEST
        })
        
        response = self.app.post('/litescale/api/users', headers={"Content-Type": "application/json"}, data=payload)
        
        response = self.app.post('/litescale/api/login', headers={"Content-Type": "application/json"}, data=payload)
        
        self.assertEqual(str, type(response.json['AccessToken']))
        self.assertEqual(str, type(response.json['RefreshToken']))
        self.assertEqual(200, response.status_code)
        
    def test_login_with_invalid_email(self):
        payload = {
            "email": EMAIL_TEST,
            "password": PASSWORD_TEST
        }
        
        response = self.app.post('/litescale/api/users', headers={"Content-Type": "application/json"}, data=json.dumps(payload))
        
        payload['email'] = "wrong@mail.com"
        response = self.app.post('/litescale/api/login', headers={"Content-Type": "application/json"}, data=json.dumps(payload))
        
        self.assertEqual("Invalid username or password", response.json['message'])
        self.assertEqual(401, response.status_code)
                
    def test_login_with_invalid_pw(self):
        payload = {
            "email": EMAIL_TEST,
            "password": PASSWORD_TEST
        }
        
        response = self.app.post('/litescale/api/users', headers={"Content-Type": "application/json"}, data=json.dumps(payload))
        
        payload['password'] = "wrongPassword"
        response = self.app.post('/litescale/api/login', headers={"Content-Type": "application/json"}, data=json.dumps(payload))
        
        self.assertEqual("Invalid username or password", response.json['message'])
        self.assertEqual(401, response.status_code)