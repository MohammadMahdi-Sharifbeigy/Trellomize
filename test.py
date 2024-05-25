import sys
import os
import unittest
import json
from io import StringIO
from unittest.mock import patch
from manager import UserManager, ProjectManager, TaskManager
  
class TestManager(unittest.TestCase):
    def setUp(self):
        # Reset data file
        data = {"users": [], "projects": [], "tasks": []}
        with open("data.json", "w") as f:
            json.dump(data, f)

    def tearDown(self):
        # Remove data file
        if os.path.exists("data.json"):
            os.remove("data.json")

    def test_create_user_new_user(self):
        user = UserManager.create_user("testuser", "testpass", email="test@example.com")
        with open("data.json", "r") as f:
            data = json.load(f)
        user = data["users"][0]
        self.assertEqual(user["username"], "testuser")
        self.assertEqual(user["email"], "test@example.com")
        self.assertTrue(user["is_active"])
        self.assertTrue(user["password"].startswith("bcrypt:"))

    def test_create_user_existing_user(self):
        UserManager.create_user("testuser", "testpass", email="test@example.com")
        with self.assertRaises(Exception):
            UserManager.create_user("testuser", "testpass", email="test@example.com")

    def test_create_user_invalid_email(self):
        with self.assertRaises(Exception):
            UserManager.create_user("testuser", "testpass")

    def test_purge_data_confirm(self):
        purge_data("y")
        with open("data.json", "r") as f:
            data = json.load(f)
        self.assertEqual(len(data["users"]), 0)
        self.assertEqual(len(data["projects"]), 0)
        self.assertEqual(len(data["tasks"]), 0)

    def test_purge_data_cancel(self):
        with patch('builtins.input', lambda *args: 'n'):
            purge_data("y")
        with open("data.json", "r") as f:
            data = json.load(f)
        self.assertNotEqual(len(data["users"]), 0)
        self.assertNotEqual(len(data["projects"]), 0)
        self.assertNotEqual(len(data["tasks"]), 0)

    def test_get_project_existing_project(self):
        ProjectManager.create_project("testproject", "Test Project", "01/01/2023")
        project = ProjectManager.get_project("testproject")
        self.assertEqual(project["id"], "testproject")
        self.assertEqual(project["title"], "Test Project")
        self.assertEqual(project["start_date"], "2023-01-01")

    def test_get_project_non_existing_project(self):
        project = ProjectManager.get_project("nonexistentproject")
        self.assertIsNone(project)

    def test_create_project_new_project(self):
        ProjectManager.create_project("testproject", "Test Project", "01/01/2023")
        with open("data.json", "r") as f:
            data = json.load(f)
        project = data["projects"][0]
        self.assertEqual(project["id"], "testproject")
        self.assertEqual(project["title"], "Test Project")
        self.assertEqual(project["start_date"], "2023-01-01")

    def test_create_project_existing_project(self):
        ProjectManager.create_project("testproject", "Test Project", "01/01/2023")
        with self.assertRaises(Exception):
            ProjectManager.create_project("testproject", "Test Project", "01/01/2023")

    def test_add_member_new_member(self):
        ProjectManager.create_project("testproject", "Test Project", "01/01/2023")
        ProjectManager.add_member("testproject", "testuser")
        with open("data.json", "r") as f:
            data = json.load(f)
        project = data["projects"][0]
        self.assertEqual(project["members"], ["testuser"])

    def test_add_member_existing_member(self):
        ProjectManager.create_project("testproject", "Test Project", "01/01/2023")
        ProjectManager.add_member("testproject", "testuser")
        with self.assertRaises(Exception):
            add_member("testproject", "testuser")

    def test_remove_member_from_project_existing_member(self):
        ProjectManager.create_project("testproject", "Test Project", "01/01/2023")
        ProjectManager.add_member("testproject", "testuser")
        ProjectManager.remove_member_from_project("testproject", "testuser")
        with open("data.json", "r") as f:
            data = json.load(f)
        project = data["projects"][0]
        self.assertEqual(project["members"], [])

    def test_remove_member_from_project_non_existing_member(self):
        ProjectManager.create_project("testproject", "Test Project", "01/01/2023")
        with self.assertRaises(Exception):
            ProjectManager.remove_member_from_project("testproject", "testuser")
    def test_remove_assignee_from_task_existing_member(self):
        ProjectManager.create_project("testproject", "Test Project", "01/01/2023")
        ProjectManager.add_member("testproject", "testuser")
        TaskManager.add_task("testproject", "task1", "Test Task 1", None, 1, "HIGH", "TODO")
        TaskManager.assign_member("testproject", "task1", "testuser")
        TaskManager.remove_assignee_from_task("testproject", "task1", "testuser")
        with open("data.json", "r") as f:
            data = json.load(f)
        project = data["projects"][0]
        for task in project["tasks"]["TODO"]:
            if task["task_id"] == "task1":
                self.assertEqual(task["assignees"], [])
                break
        else:
            self.fail("Task not found in project!")

    def test_remove_assignee_from_task_non_existing_member(self):
        ProjectManager.create_project("testproject", "Test Project", "01/01/2023")
        ProjectManager.add_member("testproject", "testuser")
        TaskManager.add_task("testproject", "task1", "Test Task 1", None, 1, "HIGH", "TODO")
        with self.assertRaises(ValueError):
            TaskManager.remove_assignee_from_task("testproject", "task1", "nonexistentuser")

    def test_remove_assignee_from_task_not_assigned(self):
        ProjectManager.create_project("testproject", "Test Project", "01/01/2023")
        ProjectManager.add_member("testproject", "testuser")
        TaskManager.add_task("testproject", "task1", "Test Task 1", None, 1, "HIGH", "TODO")
        with self.assertRaises(ValueError):
            TaskManager.remove_assignee_from_task("testproject", "task1", "testuser")

    def test_remove_assignee_from_task_non_existing_task(self):
        ProjectManager.create_project("testproject", "Test Project", "01/01/2023")
        ProjectManager.add_member("testproject", "testuser")
        with self.assertRaises(ValueError):
            TaskManager.remove_assignee_from_task("testproject", "nonexistenttask", "testuser")

if __name__ == '__main__':
    user_manager = UserManager()
    project_manager = ProjectManager()
    task_manager = TaskManager()
    unittest.main()