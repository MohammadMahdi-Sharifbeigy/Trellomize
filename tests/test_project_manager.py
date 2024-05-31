import unittest
from unittest.mock import patch, mock_open
import json

from manager import ProjectManager

class TestProjectManager(unittest.TestCase):

    @patch('manager.open', new_callable=mock_open, read_data='{"projects": []}')
    def setUp(self, mock_file):
        self.project_manager = ProjectManager()

    @patch('manager.open', new_callable=mock_open, read_data='{"projects": []}')
    def test_create_project(self, mock_file):
        project = self.project_manager.create_project("test_project", "01/01/2024", "owner_user")
        self.assertTrue(self.project_manager.get_project("test_project"))
        self.assertEqual(project["title"], "test_project")

    @patch('manager.open', new_callable=mock_open, read_data='{"projects": []}')
    def test_get_project(self, mock_file):
        self.project_manager.create_project("test_project", "01/01/2024", "owner_user")
        project = self.project_manager.get_project("test_project")
        self.assertEqual(project["title"], "test_project")

    @patch('manager.open', new_callable=mock_open, read_data='{"projects": []}')
    def test_get_projects_for_user(self, mock_file):
        self.project_manager.create_project("test_project", "01/01/2024", "owner_user")
        projects = self.project_manager.get_projects_for_user("owner_user")
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["title"], "test_project")

    @patch('manager.open', new_callable=mock_open, read_data='{"projects": []}')
    def test_add_member(self, mock_file):
        self.project_manager.create_project("test_project", "01/01/2024", "owner_user")
        self.project_manager.add_member("test_project", "new_member", "member", self.project_manager)
        project = self.project_manager.get_project("test_project")
        self.assertIn({"new_member": "member"}, project["members"])

    @patch('manager.open', new_callable=mock_open, read_data='{"projects": []}')
    def test_remove_member_from_project(self, mock_file):
        self.project_manager.create_project("test_project", "01/01/2024", "owner_user")
        self.project_manager.add_member("test_project", "new_member", "member", self.project_manager)
        self.project_manager.remove_member_from_project("test_project", "new_member")
        project = self.project_manager.get_project("test_project")
        self.assertNotIn({"new_member": "member"}, project["members"])

    @patch('manager.open', new_callable=mock_open, read_data='{"projects": []}')
    def test_delete_project(self, mock_file):
        self.project_manager.create_project("test_project", "01/01/2024", "owner_user")
        self.project_manager.delete_project("test_project")
        project = self.project_manager.get_project("test_project")
        self.assertIsNone(project)

if __name__ == '__main__':
    unittest.main()
