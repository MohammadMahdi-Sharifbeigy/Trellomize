import json
import bcrypt
import uuid
from rich import print
from datetime import datetime, timedelta, date
from io import StringIO
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import multiprocessing
import getpass
import argparse


class CustomHelpFormatter(argparse.HelpFormatter):
    """Custom help formatter to improve readability."""
    def _fill_text(self, text, width, indent):
        return ''.join([indent + line for line in text.splitlines(keepends=True)])

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

# Create main parser
parser = argparse.ArgumentParser(description='Manage administrative tasks', formatter_class=CustomHelpFormatter)

# Create subparsers for each command
subparsers = parser.add_subparsers(dest='command', help='Command to execute')

# --- Admin Management ---
admin_parser = subparsers.add_parser('create-user', help='Create a new administrator account', formatter_class=CustomHelpFormatter)

admin_parser.add_argument('--username', required=True, help='Username for the administrator account')
admin_parser.add_argument('--password', required=True, help='Password for the administrator account')
admin_parser.add_argument('--is_active', type=str2bool, nargs='?', const=True, default=True, help="Activate the administrator account")
admin_parser.add_argument('--email', help='Email address for the administrator (Optional)')

# --- Project Management ---
project_parser = subparsers.add_parser('create-project', help='Create a new project', formatter_class=CustomHelpFormatter)

project_parser.add_argument('--title', required=True, help='Project Title')
project_parser.add_argument('--start_date', required=True, help='Project Start Date (dd/mm/yyyy)')

# --- Purge Data ---
project_parser = subparsers.add_parser('purge-data', help='Purge all data')

# --- Task Management ---
task_parser = subparsers.add_parser('add-task', help='Add a new task', formatter_class=CustomHelpFormatter)

task_parser.add_argument('--project_id', required=True, help='Project ID')
task_parser.add_argument('--title', required=True, help='Task Title')
task_parser.add_argument('--description', help='Description (Optional)')
task_parser.add_argument('--duration', default=1, type=int, help='Duration in days (Optional)')
task_parser.add_argument('--priority', choices=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'], default='LOW', help='Task priority (Optional)')
task_parser.add_argument('--status', choices=['TODO', 'DOING', 'DONE', 'ARCHIVED'], default='TODO', help='Task status (Optional)')

task_parser = subparsers.add_parser('move-task', help='Move a task to a different status', formatter_class=CustomHelpFormatter)
task_parser.add_argument('--project_id', required=True, help='Project ID')
task_parser.add_argument('--task_id', required=True, help='Task ID')
task_parser.add_argument('--new_status', required=True, choices=['TODO', 'DOING', 'DONE', 'ARCHIVED'], help='New task status')

task_parser = subparsers.add_parser('delete-task', help='Delete a task', formatter_class=CustomHelpFormatter)
task_parser.add_argument('--project_id', required=True, help='Project ID')
task_parser.add_argument('--task_id', required=True, help='Task ID')

task_parser = subparsers.add_parser('assign-member', help='Assign a user to a task', formatter_class=CustomHelpFormatter)
task_parser.add_argument('--project_id', required=True, help='Project ID')
task_parser.add_argument('--task_id', required=True, help='Task ID')
task_parser.add_argument('--username', required=True, help='Username of the member to assign')

# --- Member Management ---
member_parser = subparsers.add_parser('add-member', help='Add a user to a project', formatter_class=CustomHelpFormatter)
member_parser.add_argument('--project_id', required=True, help='Project ID')
member_parser.add_argument('--username', required=True, help='Username')

member_parser = subparsers.add_parser('remove-member-from-project', help='Remove a user from a project', formatter_class=CustomHelpFormatter)
member_parser.add_argument('--project_id', required=True, help='Project ID')
member_parser.add_argument('--username', required=True, help='Username')

task_parser = subparsers.add_parser('remove_assignee_from_task', help='Remove a user from a task', formatter_class=CustomHelpFormatter)
task_parser.add_argument('--project_id', required=True, help='Project ID')
task_parser.add_argument('--task_id', required=True, help='Username')

class DataManager:
    """
    A class for managing project and user data.
    """

    def __init__(self, user_filename="users.json", data_filename="data.json"):
        self.user_filename = user_filename
        self.data_filename = data_filename
        self.user_data = self._load_data(self.user_filename)
        self.data = self._load_data(self.data_filename)

    def _load_data(self, filename):
        try:
            with open(filename, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def _save_data(self, data, filename):
        if "tasks" in data and not data["tasks"]:
            del data["tasks"]
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
    def purge_data(self):
        """
        Deletes all user and project data.
        """
        try:
            with open(self.user_filename, "w") as f:
                json.dump({"users": []}, f)
            with open(self.data_filename, "w") as f:
                json.dump({"projects": [], "tasks": []}, f)
            print("[yellow]All data has been purged![/]")
        except FileNotFoundError:
            print("[bold red]Warning: No data to purge![/]")

class UserManager(DataManager):
    """
    A class for managing user data.
    """

    def __init__(self, user_filename="users.json"):
        self.user_filename = user_filename
        self._load_data(self.user_filename)

    def create_user(self, username, password, is_active=True, email=None):
        """
        Creates a new user account.
        """
        data = self._load_data(self.user_filename)
        users = data.get("users", [])
        
        for user in users:
            if user["username"] == username:
                raise ValueError(f"User with username '{username}' already exists!")

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user = {
            "username": username,
            "password": hashed_password.decode('utf-8'),
            "email": email,
            "is_active": is_active
        }
        users.append(user)
        data["users"] = users
        self._save_data(data, self.user_filename)
        if email and is_active is not None:
            print(f"[blue italic]User account created: username='{username}', password='{password}', Email='{email}', Is_active='{is_active}'[/]")
        elif email:
            print(f"[blue italic]User account created: username='{username}', password='{password}', Email='{email}'[/]")
        else:
            print(f"[blue italic]User account created: username='{username}', password='{password}', No email provided[/]")
        return user

class ProjectManager(DataManager):
    """
    A class for managing project data.
    """

    def create_project(self, title, start_date):
        """
        Creates a new project.
        """
        project_id = str(uuid.uuid4())
        hashed_project_id = bcrypt.hashpw(project_id.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        if hashed_project_id in [project.get("id") for project in self.data.get("projects", [])]:
            raise ValueError(f"Project with ID '{hashed_project_id}' already exists!")
        
        project = {
            "id": hashed_project_id,
            "title": title,
            "start_date": datetime.strptime(start_date, '%d/%m/%Y').strftime('%Y-%m-%d'),
            "members": [],
            "tasks": []
        }
        self.data.setdefault("projects", []).append(project)
        self._save_data(self.data, self.data_filename)
        print(f"[green]Project created with ID:{hashed_project_id}[/]")
        return project

    def get_project_by_hashed_id(self, hashed_project_id):
        for project in self.data.get("projects", []):
            if project["id"] == hashed_project_id:
                return project
        return None
    
    def get_project(self, project_id):
        """
        Retrieves a project by its ID.
        """
        for project in self.data.get("projects", []):
            if project["id"] == project_id:
                return project
        return None
    
    def add_member(self,project_id, username):

        """
        Adds a user to a project.

        Args:
            project_id: The ID of the project to add the member to.
            username: The username of the member to add.

        Raises:
            ValueError: If the project or user is not found.
        """

        project = project_manager.get_project_by_hashed_id(project_id)
        if not project:
            raise ValueError(f"Project with ID '{project_id}' not found!")

        # Check if the user already exists in the project
        if username in project.get("members", []):
            print(f"[bold red]Error: User '{username}' is already a member of the project![/]")
            return

        # Add the user to the project's members list
        project["members"].append(username)

        # Save the updated project data
        self._save_data(self.data, self.data_filename)

        print(f"[green]User '{username}' successfully added to the project![/]") 
    
    def remove_member_from_project(self, project_id, username):
        """
        Removes a user from a project.
        """
        project = self.get_project_by_hashed_id(project_id)
        if not project:
            raise ValueError("Project not found!")

        if username not in project["members"]:
            raise ValueError("User is not a member of the project!")

        project["members"].remove(username)
        print(f"[green]User '{username}' successfully removed from the project![/]")
        self._save_data(self.data, self.data_filename)

class TaskManager(DataManager):
    """
    A class for managing task data.
    """
    def get_project_by_hashed_id(self, hashed_project_id):
        for project in self.data.get("projects", []):
            if project["id"] == hashed_project_id:
                return project
        return None
    
    def add_task(self, project_id, title, description, duration, priority, status="TODO"):
        """
        Adds a new task to a project.
        """
        project = self.get_project_by_hashed_id(project_id)
        if not project:
            raise ValueError(f"Project with hashed ID '{project_id}' not found!")
        task_id = str(uuid.uuid4())
        hashed_task_id = bcrypt.hashpw(task_id.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        task = {
            "task_id": hashed_task_id,
            "title": title,
            "description": description,
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=duration)).isoformat(),
            "priority": priority,
            "status": status,
            "comments": [],
            "assignees": []
        }

        # Ensure the tasks dictionary is initialized
        if "tasks" not in project or not isinstance(project["tasks"], dict):
            project["tasks"] = {"TODO": [], "DOING": [], "DONE": [], "ARCHIVED": []}

        # Add the task to the appropriate status list
        project["tasks"][status].append(task)
        self._save_data(self.data, self.data_filename)
        print(f"Task created with ID: {hashed_task_id}")
        return task

    def delete_task(self, project_id, task_id):
        """
        Deletes a task from a project.
        """
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project with ID '{project_id}' not found!")

        for task_list in project["tasks"].values():
            for task in task_list:
                if task["task_id"] == task_id:
                    task_list.remove(task)
                    self._save_data()
                    return
        raise ValueError(f"Task with ID '{task_id}' not found in project '{project_id}'.")

    def move_task(self, project_id, task_id, new_status):
        """
        Moves a task to a different status within a project.
        """
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project with ID '{project_id}' not found!")

        for task_list in project["tasks"].values():
            for task in task_list:
                if task["task_id"] == task_id:
                    task_list.remove(task)
                    project["tasks"].setdefault(new_status, []).append(task)
                    self._save_data()
                    return
        raise ValueError(f"Task with ID '{task_id}' not found in project '{project_id}'.")

    def assign_member(self, project_id, task_id, username):
        """
        Assigns a user to a task.
        """
        project = self.get_project_by_hashed_id(project_id)
        if not project:
            raise ValueError("Project not found!")

        task_found = False
        for task_list in project["tasks"].values():
            for task in task_list:
                if task["task_id"] == task_id:
                    task_found = True
                    if username in task["assignees"]:
                        raise ValueError("User already assigned to this task!")
                    task["assignees"].append(username)
                    self._save_data(self.data, self.data_filename)
                    print(f"[green]User '{username}' successfully assigned to task '{task['title']}![/]")
                    return

        if not task_found:
            raise ValueError("Task not found in project!")

    def remove_assignee_from_task(self, project_id, task_id, username):
        """
        Removes a user from a task.
        """
        project = self.get_project_by_hashed_id(project_id)
        if not project:
            raise ValueError("Project not found!")

        for task_list in project["tasks"].values():
            for task in task_list:
                if task["task_id"] == task_id:
                    if username not in task["assignees"]:
                        raise ValueError("User is not assigned to this task!")
                    task["assignees"].remove(username)
                    print(f"[green]User '{username}' successfully removed from task '{task['title']}![/]")
                    self._save_data(self.data, self.data_filename)
                    return

        raise ValueError("Task not found in project!")

if __name__ == "__main__":
    # Create instances of the classes
    data_manager = DataManager()
    user_manager = UserManager()
    project_manager = ProjectManager()
    task_manager = TaskManager()

    args = parser.parse_args()

    if args.command == 'create-user':
        user_manager.create_user(args.username, args.password, args.is_active, args.email)
    elif args.command == 'purge-data':
        data_manager.purge_data(input("[bold red]Are you sure you want to erase all data? (y/n): "))
    elif args.command == 'create-project':
        project_manager.create_project(args.title, args.start_date)
    elif args.command == 'add-member':
        project_manager.add_member(args.project_id, args.username)
    elif args.command == 'remove-member-from-project':
        project_manager.remove_member_from_project(args.project_id, args.username)
    elif args.command == 'add-task':
        task_manager.add_task(args.project_id, args.title, args.description, args.duration, args.priority, args.status)
    elif args.command == 'move-task':
        task_manager.move_task(args.project_id, args.task_id, args.new_status)
    elif args.command == 'assign-member':
        task_manager.assign_member(args.project_id, args.task_id, args.username)    
    elif args.command == 'remove_assignee_from_task':
        task_manager.remove_assignee_from_task(args.project_id, args.task_id, args.username)
    elif args.command == 'delete-task':
        task_manager.delete_task(args.project_id, args.task_id)
    else:
        print("[red]Invalid command![/]")