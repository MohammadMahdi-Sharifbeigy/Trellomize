import unittest
import os
import json
import bcrypt
from datetime import date, timedelta
from manager import UserManager, ProjectManager, TaskManager, DataManager

class TestUserManager(unittest.TestCase):
    def setUp(self):
        self.user_file = "test_users.json"
        self.data_file = "test_data.json"
        self.user_manager = UserManager(user_filename=self.user_file, data_filename=self.data_file)
        self.user_manager.user_data = {"users": []}
        self.user_manager._save_data(self.user_manager.user_data, self.user_file)

    def tearDown(self):
        if os.path.exists(self.user_file):
            os.remove(self.user_file)
        if os.path.exists(self.data_file):
            os.remove(self.data_file)

    def test_create_user(self):
        self.user_manager.create_user("testuser", "password", True, "test@example.com")
        user = self.user_manager.get_user("testuser")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "testuser")
        self.assertTrue(bcrypt.checkpw("password".encode("utf-8"), user["password"].encode("utf-8")))
        self.assertEqual(user["email"], "test@example.com")
        self.assertTrue(user["is_active"])

    def test_create_user_duplicate(self):
        self.user_manager.create_user("testuser", "password", True, "test@example.com")
        with self.assertRaises(ValueError):
            self.user_manager.create_user("testuser", "password", True, "test2@example.com")

    def test_get_members(self):
        self.user_manager.create_user("adminuser", "password", True, "admin@example.com", is_admin=True)
        self.user_manager.create_user("memberuser", "password", True, "member@example.com", is_admin=False)
        members = self.user_manager.get_members()
        self.assertEqual(members, ["memberuser"])


class TestProjectManager(unittest.TestCase):
    def setUp(self):
        self.user_file = "test_users.json"
        self.data_file = "test_data.json"
        self.user_manager = UserManager(user_filename=self.user_file, data_filename=self.data_file)
        self.project_manager = ProjectManager(user_filename=self.user_file, data_filename=self.data_file)
        self.project_manager.data = {"projects": []}
        self.project_manager._save_data(self.project_manager.data, self.data_file)
        self.user_manager.create_user("owner", "password", True, "owner@example.com")

    def tearDown(self):
        if os.path.exists(self.user_file):
            os.remove(self.user_file)
        if os.path.exists(self.data_file):
            os.remove(self.data_file)

    def test_create_project(self):
        project = self.project_manager.create_project("Test Project", "01/01/2023", "owner")
        self.assertEqual(project["title"], "Test Project")
        self.assertEqual(project["start_date"], "2023-01-01")
        self.assertEqual(project["owner"], "owner")
        self.assertIn({"owner": "owner"}, project["members"])

    def test_create_project_duplicate(self):
        self.project_manager.create_project("Test Project", "01/01/2023", "owner")
        with self.assertRaises(ValueError):
            self.project_manager.create_project("Test Project", "01/01/2023", "owner")

    def test_add_member(self):
        self.project_manager.create_project("Test Project", "01/01/2023", "owner")
        self.user_manager.create_user("newmember", "password", True, "newmember@example.com")
        self.project_manager.add_member("Test Project", "newmember", "member", self.project_manager)
        project = self.project_manager.get_project("Test Project")
        self.assertIn({"newmember": "member"}, project["members"])

    def test_remove_member(self):
        self.project_manager.create_project("Test Project", "01/01/2023", "owner")
        self.user_manager.create_user("newmember", "password", True, "newmember@example.com")
        self.project_manager.add_member("Test Project", "newmember", "member", self.project_manager)
        self.project_manager.remove_member_from_project("Test Project", "newmember")
        project = self.project_manager.get_project("Test Project")
        self.assertNotIn({"newmember": "member"}, project["members"])

    def test_get_projects_for_user(self):
        self.project_manager.create_project("Project1", "01/01/2023", "owner")
        self.project_manager.create_project("Project2", "01/01/2023", "owner")
        self.user_manager.create_user("member", "password", True, "member@example.com")
        self.project_manager.add_member("Project1", "member", "member", self.project_manager)
        projects = self.project_manager.get_projects_for_user("member")
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["title"], "Project1")


class TestTaskManager(unittest.TestCase):
    def setUp(self):
        self.user_file = "test_users.json"
        self.data_file = "test_data.json"
        self.user_manager = UserManager(user_filename=self.user_file, data_filename=self.data_file)
        self.project_manager = ProjectManager(user_filename=self.user_file, data_filename=self.data_file)
        self.task_manager = TaskManager(user_filename=self.user_file, data_filename=self.data_file)
        self.project_manager.data = {"projects": []}
        self.project_manager._save_data(self.project_manager.data, self.data_file)
        self.user_manager.create_user("owner", "password", True, "owner@example.com")
        self.project_manager.create_project("Test Project", "01/01/2023", "owner")

    def tearDown(self):
        if os.path.exists(self.user_file):
            os.remove(self.user_file)
        if os.path.exists(self.data_file):
            os.remove(self.data_file)

    def test_add_task(self):
        task = self.task_manager.add_task("Test Project", "Test Task", "Description", 2, "HIGH")
        self.assertEqual(task["title"], "Test Task")
        self.assertEqual(task["description"], "Description")
        self.assertEqual(task["priority"], "HIGH")
        self.assertEqual(task["status"], "TODO")

    def test_delete_task(self):
        self.task_manager.add_task("Test Project", "Test Task", "Description", 2, "HIGH")
        self.task_manager.delete_task("Test Project", "Test Task")
        project = self.project_manager.get_project("Test Project")
        self.assertFalse(project["tasks"]["TODO"])

    def test_move_task(self):
        self.task_manager.add_task("Test Project", "Test Task", "Description", 2, "HIGH")
        self.task_manager.move_task("Test Project", "Test Task", "DOING")
        project = self.project_manager.get_project("Test Project")
        self.assertTrue(project["tasks"]["DOING"])
        self.assertFalse(project["tasks"]["TODO"])

    def test_assign_member(self):
        self.user_manager.create_user("member", "password", True, "member@example.com")
        self.task_manager.add_task("Test Project", "Test Task", "Description", 2, "HIGH")
        self.task_manager.assignee_member("Test Project", "Test Task", "member")
        task = self.task_manager.get_task("Test Project", "Test Task")
        self.assertIn("member", task["assignees"])

    def test_remove_assignee(self):
        self.user_manager.create_user("member", "password", True, "member@example.com")
        self.task_manager.add_task("Test Project", "Test Task", "Description", 2, "HIGH")
        self.task_manager.assignee_member("Test Project", "Test Task", "member")
        self.task_manager.remove_assignee("Test Project", "Test Task", "member")
        task = self.task_manager.get_task("Test Project", "Test Task")
        self.assertNotIn("member", task["assignees"])

    def test_add_comment(self):
        self.task_manager.add_task("Test Project", "Test Task", "Description", 2, "HIGH")
        self.task_manager.add_comment("Test Project", "Test Task", "This is a comment.", "owner")
        task = self.task_manager.get_task("Test Project", "Test Task")
        self.assertEqual(len(task["comments"]), 1)
        self.assertEqual(task["comments"][0]["comment"], "This is a comment.")
        self.assertEqual(task["comments"][0]["author"], "owner")

    def test_edit_comment(self):
        self.task_manager.add_task("Test Project", "Test Task", "Description", 2, "HIGH")
        self.task_manager.add_comment("Test Project", "Test Task", "This is a comment.", "owner")
        self.task_manager.edit_comment("Test Project", "Test Task", 0, "This is an edited comment.")
        task = self.task_manager.get_task("Test Project", "Test Task")
        self.assertEqual(task["comments"][0]["comment"], "This is an edited comment.")

    def test_delete_comment(self):
        self.task_manager.add_task("Test Project", "Test Task", "Description", 2, "HIGH")
        self.task_manager.add_comment("Test Project", "Test Task", "This is a comment.", "owner")
        self.task_manager.delete_comment("Test Project", "Test Task", 0)
        task = self.task_manager.get_task("Test Project", "Test Task")
        self.assertFalse(task["comments"])

if __name__ == "__main__":
    unittest.main()
