# test_task_manager.py
import unittest
from unittest.mock import patch, mock_open
import json

from manager import TaskManager

class TestTaskManager(unittest.TestCase):

    @patch('manager.open', new_callable=mock_open, read_data='{"projects": []}')
    def setUp(self, mock_file):
        self.task_manager = TaskManager()
        self.task_manager.create_project("test_project", "01/01/2024", "owner_user")

    @patch('manager.open', new_callable=mock_open, read_data='{"projects": []}')
    def test_add_task(self, mock_file):
        task = self.task_manager.add_task("test_project", "test_task", "test_description", 5, "MEDIUM")
        self.assertIn(task, self.task_manager.get_project("test_project")["tasks"]["TODO"])

    @patch('manager.open', new_callable=mock_open, read_data='{"projects": []}')
    def test_edit_task(self, mock_file):
        self.task_manager.add_task("test_project", "test_task", "test_description", 5, "MEDIUM")
        self.task_manager.edit_task("test_project", "test_task", "new_title", "new_description", 10, "HIGH")
        task = self.task_manager.get_task("test_project", "new_title")
        self.assertEqual(task["title"], "new_title")
        self.assertEqual(task["description"], "new_description")
        self.assertEqual(task["priority"], "HIGH")

    @patch('manager.open', new_callable=mock_open, read_data='{"projects": []}')
    def test_delete_task(self, mock_file):
        self.task_manager.add_task("test_project", "test_task", "test_description", 5, "MEDIUM")
        self.task_manager.delete_task("test_project", "test_task")
        task = self.task_manager.get_task("test_project", "test_task")
        self.assertIsNone(task)

    @patch('manager.open', new_callable=mock_open, read_data='{"projects": []}')
    def test_move_task(self, mock_file):
        self.task_manager.add_task("test_project", "test_task", "test_description", 5, "MEDIUM")
        self.task_manager.move_task("test_project", "test_task", "DOING")
        task = self.task_manager.get_task("test_project", "test_task")
        self.assertEqual(task["status"], "DOING")

    @patch('manager.open', new_callable=mock_open, read_data='{"projects": []}')
    def test_assign_member(self, mock_file):
        self.task_manager.add_task("test_project", "test_task", "test_description", 5, "MEDIUM")
        self.task_manager.assign_member("test_project", "test_task", "new_member")
        task = self.task_manager.get_task("test_project", "test_task")
        self.assertIn("new_member", task["assignees"])

    @patch('manager.open', new_callable=mock_open, read_data='{"projects": []}')
    def test_remove_assignee_from_task(self, mock_file):
        self.task_manager.add_task("test_project", "test_task", "test_description", 5, "MEDIUM")
        self.task_manager.assign_member("test_project", "test_task", "new_member")
        self.task_manager.remove_assignee_from_task("test_project", "test_task", "new_member")
        task = self.task_manager.get_task("test_project", "test_task")
        self.assertNotIn("new_member", task["assignees"])

    @patch('manager.open', new_callable=mock_open, read_data='{"projects": []}')
    def test_add_comment(self, mock_file):
        self.task_manager.add_task("test_project", "test_task", "test_description", 5, "MEDIUM")
        self.task_manager.add_comment("test_project", "test_task", "new_comment", "author_user")
        task = self.task_manager.get_task("test_project", "test_task")
        self.assertIn({"comment": "new_comment", "author": "author_user", "timestamp": task["comments"][0]["timestamp"]}, task["comments"])

    @patch('manager.open', new_callable=mock_open, read_data='{"projects": []}')
    def test_edit_comment(self, mock_file):
        self.task_manager.add_task("test_project", "test_task", "test_description", 5, "MEDIUM")
        self.task_manager.add_comment("test_project", "test_task", "new_comment", "author_user")
        self.task_manager.edit_comment("test_project", "test_task", 0, "edited_comment")
        task = self.task_manager.get_task("test_project", "test_task")
        self.assertEqual(task["comments"][0]["comment"], "edited_comment")

    @patch('manager.open', new_callable=mock_open, read_data='{"projects": []}')
    def test_delete_comment(self, mock_file):
        self.task_manager.add_task("test_project", "test_task", "test_description", 5, "MEDIUM")
        self.task_manager.add_comment("test_project", "test_task", "new_comment", "author_user")
        self.task_manager.delete_comment("test_project", "test_task", 0)
        task = self.task_manager.get_task("test_project", "test_task")
        self.assertEqual(len(task["comments"]), 0)

if __name__ == '__main__':
    unittest.main()
