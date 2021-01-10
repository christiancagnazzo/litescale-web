import unittest
import json
from LitescaleAPI import app
from litescale import delete_user

EMAIL_TEST = "test@mail.com"
PASSWORD_TEST = "pwd"

class BaseCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True


    def tearDown(self):
        delete_user(EMAIL_TEST)
