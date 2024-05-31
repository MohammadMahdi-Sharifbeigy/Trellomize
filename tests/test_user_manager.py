import unittest
from unittest.mock import patch, mock_open
import bcrypt
import json

from manager import UserManager

class TestUserManager(unittest.TestCase):

    @patch('manager.open', new_callable=mock_open, read_data='{"users": []}')
    def setUp(self, mock_file):
        self.user_manager = UserManager()

    @patch('manager.open', new_callable=mock_open, read_data='{"users": []}')
    def test_create_user(self, mock_file):
        self.user_manager.create_user("test_user", "test_password")
        self.assertTrue(self.user_manager.get_user("test_user"))

    @patch('manager.open', new_callable=mock_open, read_data='{"users": []}')
    def test_get_user(self, mock_file):
        self.user_manager.create_user("test_user", "test_password")
        user = self.user_manager.get_user("test_user")
        self.assertEqual(user["username"], "test_user")

    @patch('manager.open', new_callable=mock_open, read_data='{"users": []}')
    def test_update_user(self, mock_file):
        self.user_manager.create_user("test_user", "test_password")
        self.user_manager.update_user("test_user", {"email": "new_email@test.com"})
        user = self.user_manager.get_user("test_user")
        self.assertEqual(user["email"], "new_email@test.com")

    @patch('manager.open', new_callable=mock_open, read_data='{"users": []}')
    def test_get_members(self, mock_file):
        self.user_manager.create_user("admin_user", "admin_password", is_admin=True)
        self.user_manager.create_user("member_user", "member_password")
        members = self.user_manager.get_members()
        self.assertEqual(len(members), 1)
        self.assertIn("member_user", members)

if __name__ == '__main__':
    unittest.main()
