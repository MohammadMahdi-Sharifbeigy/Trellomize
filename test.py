import unittest
import json
import os
import datetime
import importlib.util
import shutil
import bcrypt
import sys
import tempfile

class ProjectManagementTest(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = self.temp_dir.name
        data_path = os.path.join(self.cwd, "data.json")
        test_data_path = os.path.join(self.data_dir, "data.json")
        shutil.copy(data_path, test_data_path)
        main_path = os.path.join(self.cwd, "main.py")
        test_main_path = os.path.join(self.data_dir, "main.py")
        shutil.copy(main_path, test_main_path)
        sys.path.append(self.data_dir)
        spec = importlib.util.spec_from_file_location("main", os.path.join(self.data_dir, "main.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.main = module
        self.user_manager = self.main.UserManager()
        self.project_manager = self.main.ProjectManager()
        self.task_manager = self.main.TaskManager()
        self.users_json = test_data_path

    def tearDown(self):
        self.temp_dir.cleanup()
        sys.path.remove(self.data_dir)

    def test_login(self):
        self.assertTrue(self.main.login("yasin", "test123"))
        self.assertFalse(self.main.login("yasin", "wrong_password"))
        self.assertFalse(self.main.login("unknown_user", "test123"))

    def test_create_new_project(self):
        try:
            self.project_manager.create_project("Test Project", "12/06/2024", "yasin")
        except ValueError:
            pass
        with self.assertRaises(ValueError):
            self.project_manager.create_project("Test Project", "12/06/2024", "yasin")

    def test_add_task_to_board(self):
        self.task_manager.add_task("Test Project", "Test Task", "This is a test task", 3, "HIGH", "TODO")
        with self.assertRaises(ValueError):
            self.task_manager.add_task("Test Project", "Test Task", "This is a test task", 3, "HIGH", "TODO")

    def test_move_task_on_board(self):
        self.task_manager.move_task("Test Project", "Test Task", "DOING")
        with self.assertRaises(ValueError):
            self.task_manager.move_task("Test Project", "Non-existent Task", "DOING")
        with self.assertRaises(ValueError):
            self.task_manager.move_task("Test Project", "Test Task", "Invalid Status")

    def test_delete_task_from_board(self):
        self.task_manager.delete_task("Test Project", "Test Task")
        with self.assertRaises(ValueError):
            self.task_manager.delete_task("Test Project", "Non-existent Task")

    def test_edit_task_on_board(self):
        self.task_manager.edit_task("Test Project", "Test Task", "Edited Task", "Edited Description", 5, "CRITICAL")
        task = self.task_manager.get_task("Test Project", "Edited Task")
        self.assertEqual(task["title"], "Edited Task")
        self.assertEqual(task["description"], "Edited Description")
        self.assertEqual(task["priority"], "CRITICAL")
        start_date = datetime.fromisoformat(task["start_date"])
        expected_end_date = (start_date + timedelta(days=5))
        self.assertEqual(task["end_date"], expected_end_date)

    def test_add_member_to_project(self):
        self.project_manager.add_member("Test Project", "mmd", "admin", self.project_manager)
        with self.assertRaises(Exception):
            self.project_manager.add_member("Test Project", "mmd", "admin")
        with self.assertRaises(Exception):
            self.project_manager.add_member("Test Project", "unknown_user", "member")

    def test_remove_member_from_project(self):
        self.project_manager.remove_member_from_project("Test Project", "mmd")
        with self.assertRaises(Exception):
            self.project_manager.remove_member_from_project("Test Project", "unknown_user")

    def test_assign_member_to_task(self):
        self.task_manager.assign_member("Test Project", "Test Task", "mmd")
        with self.assertRaises(ValueError):
            self.task_manager.assign_member("Test Project", "Test Task", "mmd")
        with self.assertRaises(ValueError):
            self.task_manager.assign_member("Test Project", "Test Task", "unknown_user")

    def test_remove_assignee_from_task(self):
        self.task_manager.assign_member("Test Project", "Test Task", "mmd")
        self.task_manager.remove_assignee_from_task("Test Project", "Test Task", "mmd")
        with self.assertRaises(ValueError):
            self.task_manager.remove_assignee_from_task("Test Project", "Test Task", "unknown_user")

    def test_add_comment_to_task(self):
        self.task_manager.add_comment("Test Project", "Test Task", "This is a test comment", "yasin")
        self.assertTrue(True)
        with self.assertRaises(ValueError):
            self.task_manager.add_comment("Test Project", "Test Task", "This is a duplicate comment", "yasin")

    def test_edit_comment_on_task(self):
        self.task_manager.add_comment("Test Project", "Test Task", "This is a test comment", "yasin")
        self.task_manager.edit_comment("Test Project", "Test Task", 0, "Edited Comment")
        with self.assertRaises(Exception):
            self.task_manager.edit_comment("Test Project", "Test Task", 10, "Edited Comment")
        with self.assertRaises(Exception):
            self.task_manager.edit_comment("Test Project", "Test Task", 5, "Edited Comment")

    def test_delete_comment_from_task(self):
        self.task_manager.add_comment("Test Project", "Test Task", "This is a test comment", "yasin")
        self.task_manager.delete_comment("Test Project", "Test Task", 0)
        with self.assertRaises(ValueError):
            self.task_manager.delete_comment("Test Project", "Test Task", 1)

    def test_update_project_board(self):
        self.task_manager.move_task("Test Project", "Test Task", "DONE")
        projects = self.project_manager.list_projects()
        board = projects[0]["tasks"]
        self.assertEqual(len(board["TODO"]), 1)
        self.assertEqual(len(board["DONE"]), 1)

    def test_update_user_profile(self):
        self.user_manager.update_user("yasin", {"email": "new_email@example.com"})
        with open(self.users_json) as f:
            users = json.load(f)
        self.assertEqual(users[0]["email"], "new_email@example.com")

    def test_load_users_from_json(self):
        users = self.user_manager.get_members()
        self.assertEqual(len(users), 0)
        self.assertIn("yasin", users)
        self.assertIn("mmd", users)

if __name__ == "__main__":
    unittest.main()
