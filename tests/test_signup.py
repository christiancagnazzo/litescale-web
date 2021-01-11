from tests.BaseCase import BaseCase, EMAIL_TEST, PASSWORD_TEST
import json

class TestUserSignUp(BaseCase):
    
    def test_successful_signup(self):
        payload = json.dumps({
            "email": EMAIL_TEST,
            "password": PASSWORD_TEST
        })

        response = self.app.post('/litescale/api/users', headers={"Content-Type": "application/json"}, data=payload)
        
        self.assertEqual('True', response.json['result'])
        self.assertEqual(200, response.status_code)
        
    def test_creating_already_existing_user(self):
        payload = json.dumps({
            "email": EMAIL_TEST,
            "password": PASSWORD_TEST
        })

        response = self.app.post('/litescale/api/users', headers={"Content-Type": "application/json"}, data=payload)
        response = self.app.post('/litescale/api/users', headers={"Content-Type": "application/json"}, data=payload)

        self.assertEqual('User with given email address already exists', response.json['message'])
        self.assertEqual(400, response.status_code)
                
    
    def test_signup_without_email(self):
        payload = json.dumps({
            "password": PASSWORD_TEST,
        })

        response = self.app.post('/litescale/api/users', headers={"Content-Type": "application/json"}, data=payload)

        self.assertEqual(400, response.status_code)


    def test_signup_without_password(self):
        payload = json.dumps({
            "email": EMAIL_TEST,
        })

        response = self.app.post('/litescale/api/users', headers={"Content-Type": "application/json"}, data=payload)

        self.assertEqual(400, response.status_code)

