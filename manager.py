import argparse
import getpass
import json
import multiprocessing
import uuid
from datetime import date, datetime, timedelta
from io import StringIO

import bcrypt
import dash
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
from dash import dcc, html
from dash.dependencies import Input, Output
from rich import print


class CustomHelpFormatter(argparse.HelpFormatter):
    """Custom help formatter to improve readability."""


    def _fill_text(self, text, width, indent):
        return "".join([indent + line for line in text.splitlines(keepends=True)])



def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")



# Create main parser
parser = argparse.ArgumentParser(description="Manage administrative tasks", formatter_class=CustomHelpFormatter)


# Create subparsers for each command
subparsers = parser.add_subparsers(dest="command", help="Command to execute")


# --- Admin Management ---
admin_parser = subparsers.add_parser("create-user",help="Create a new administrator account",formatter_class=CustomHelpFormatter,)


admin_parser.add_argument("--username", required=True, help="Username for the administrator account")
admin_parser.add_argument("--password", required=True, help="Password for the administrator account")
admin_parser.add_argument("--is_active",type=str2bool,nargs="?",const=True,default=True,help="Activate the administrator account",)
admin_parser.add_argument("--email", help="Email address for the administrator (Optional)")


# --- Project Management ---
project_parser = subparsers.add_parser("create-project", help="Create a new project", formatter_class=CustomHelpFormatter)


project_parser.add_argument("--title", required=True, help="Project Title")
project_parser.add_argument("--start_date", required=True, help="Project Start Date (dd/mm/yyyy)")


# --- Purge Data ---
project_parser = subparsers.add_parser("purge-data", help="Purge all data")


# --- Task Management ---
task_parser = subparsers.add_parser("add-task", help="Add a new task", formatter_class=CustomHelpFormatter)


task_parser.add_argument("--project_title", required=True, help="Project Title")
task_parser.add_argument("--title", required=True, help="Task Title")
task_parser.add_argument("--description", help="Description (Optional)")
task_parser.add_argument("--duration", default=1, type=int, help="Duration in days (Optional)")
task_parser.add_argument("--priority",choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"],default="LOW",help="Task priority (Optional)",)
task_parser.add_argument("--status",choices=["TODO", "DOING", "DONE", "ARCHIVED"],default="TODO",help="Task status (Optional)",)


task_parser = subparsers.add_parser("move-task",help="Move a task to a different status",formatter_class=CustomHelpFormatter,)
task_parser.add_argument("--project_title", required=True, help="Project Title")
task_parser.add_argument("--task_title", required=True, help="Task Title")
task_parser.add_argument("--new_status",required=True,choices=["TODO", "DOING", "DONE", "ARCHIVED"],help="New task status",)


task_parser = subparsers.add_parser("delete-task", help="Delete a task", formatter_class=CustomHelpFormatter)
task_parser.add_argument("--project_title", required=True, help="Project Title")
task_parser.add_argument("--task_title", required=True, help="Task Title")


task_parser = subparsers.add_parser("assign-member", help="Assign a user to a task", formatter_class=CustomHelpFormatter)
task_parser.add_argument("--project_title", required=True, help="Project Title")
task_parser.add_argument("--task_title", required=True, help="Task Title")
task_parser.add_argument("--username", required=True, help="Username of the member to assign")


# --- Member Management ---
member_parser = subparsers.add_parser("add-member", help="Add a user to a project", formatter_class=CustomHelpFormatter)
member_parser.add_argument("--project_title", required=True, help="Project Title")
member_parser.add_argument("--username", required=True, help="Username")


member_parser = subparsers.add_parser("remove-member-from-project",help="Remove a user from a project",formatter_class=CustomHelpFormatter,)
member_parser.add_argument("--project_title", required=True, help="Project Title")
member_parser.add_argument("--username", required=True, help="Username")


task_parser = subparsers.add_parser("remove_assignee_from_task",help="Remove a user from a task",formatter_class=CustomHelpFormatter,)
task_parser.add_argument("--project_title", required=True, help="Project Title")
task_parser.add_argument("--task_title", required=True, help="Task Title")



class DataManager:
    """
    A class for managing project and user data.
    """

    def __init__(self, user_filename="users.json", data_filename="data.json"):
        self.user_filename = user_filename
        self.data_filename = data_filename
        self.reload_data()

    def reload_data(self):
        """
        Reload data from the JSON files.
        """
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
            self.reload_data()
        except FileNotFoundError:
            print("[bold red]Warning: No data to purge![/]")


class UserManager(DataManager):
    """
    A class for managing user data.
    """

    def create_user(self, username, password, is_active=True, email=None, is_admin=False):
        """
        Creates a new user account.
        """
        self.reload_data()
        users = self.user_data.get("users", [])

        for user in users:
            if user["username"] == username:
                raise ValueError(f"User with username '{username}' already exists!")

        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        user = {
            "username": username,
            "password": hashed_password.decode("utf-8"),
            "email": email,
            "is_active": is_active,
            "is_admin": is_admin,
        }
        users.append(user)
        self.user_data["users"] = users
        self._save_data(self.user_data, self.user_filename)
        if email and is_active is not None:
            print(f"[blue italic]User account created: username='{username}', password='{password}', Email='{email}', Is_active='{is_active}'[/]")
        elif email:
            print(f"[blue italic]User account created: username='{username}', password='{password}', Email='{email}'[/]")
        else:
            print(f"[blue italic]User account created: username='{username}', password='{password}', No email provided[/]")
        return user

    def get_user(self, username):
        """
        Retrieve user data by username.
        """
        self.reload_data()
        for user in self.user_data.get("users", []):
            if user["username"] == username:
                return user
        return None

    def update_user(self, username, updates):
        """
        Update user data.
        """
        self.reload_data()
        users = self.user_data.get("users", [])
        for user in users:
            if user["username"] == username:
                user.update(updates)
                break
        else:
            raise ValueError("User not found")

        self._save_data(self.user_data, self.user_filename)
    
    def get_members(self):
        """
        Retrieve all members.
        """
        self.reload_data()
        users = self.user_data.get("users", [])
        members = [user["username"] for user in users if not user.get("is_admin")]
        return members


class ProjectManager(DataManager):
    """
    A class for managing project data.
    """

    def create_project(self, title, start_date, owner):
        """
        Creates a new project.
        """
        self.reload_data()
        project_id = str(uuid.uuid4())
        projects = self.data.get("projects", [])
        for existing_project in projects:
            if existing_project["title"] == title:
                raise ValueError(f"Project with title '{title}' already exists!")

        project = {
            "id": project_id,
            "title": title,
            "start_date": datetime.strptime(start_date, "%d/%m/%Y").strftime("%Y-%m-%d"),
            "owner": owner,
            "members": [owner],
            "tasks": {"TODO": [], "DOING": [], "DONE": [], "ARCHIVED": []},
        }
        self.data.setdefault("projects", []).append(project)
        self._save_data(self.data, self.data_filename)
        print(f"[green]Project created with title: {title}[/]")
        return project

    def is_project_owner(self, project_title, username):
        """
        Checks if the given user is the owner of the project.
        """
        project = self.get_project(project_title)
        if not project:
            raise ValueError("Project not found!")

        return project["owner"] == username

    def get_project(self, title):
        """
        Retrieves a project by its title.
        """
        self.reload_data()
        for project in self.data.get("projects", []):
            if project["title"] == title:
                return project
        return None

    def get_projects_for_user(self, username):
        """
        Retrieves a list of projects for a given user.
        """
        self.reload_data()
        projects = self.data.get("projects", [])
        user_projects = []
        for project in projects:
            if username in project.get("members", []):
                user_projects.append(project)
        return user_projects

    def list_projects(self):
        """
        Retrieves and returns a list of all projects.
        """
        self.reload_data()
        projects = self.data.get("projects", [])
        if not projects:
            print("[bold magenta]No projects found![/]")
            return []
        return projects

    def add_member(self, project_title, username, project_manager):
        """
        Adds a user to a project.
        """
        self.reload_data()
        project = project_manager.get_project(project_title)
        if not project:
            raise ValueError(f"Project with Title'{project_title}' not found!")

        if username in project.get("members", []):
            print(f"[bold red]Error: User '{username}' is already a member of the project![/]")
            return
        project["members"].append(username)
        self._save_data(self.data, self.data_filename)

    def remove_member_from_project(self, project_title, username):
        """
        Removes a user from a project.
        """
        self.reload_data()
        project = self.get_project(project_title)
        if not project:
            raise ValueError("Project not found!")

        if username not in project["members"]:
            raise ValueError("User is not a member of the project!")

        project["members"].remove(username)
        self._save_data(self.data, self.data_filename)
    
    def delete_project(self, project_title):
        """
        Deletes a project.
        """
        self.reload_data()
        project = self.get_project(project_title)
        if not project:
            raise ValueError(f"Project with title '{project_title}' not found!")

        self.data["projects"].remove(project)
        self._save_data(self.data, self.data_filename)


class TaskManager(DataManager):
    def get_project(self, project_title):
        self.reload_data()
        for project in self.data.get("projects", []):
            if project["title"] == project_title:
                return project
        return None

    def add_task(self, project_title, task_title, description, duration, priority, status="TODO"):
        self.reload_data()
        project = self.get_project(project_title)
        if not project:
            raise ValueError(f"Project with title '{project_title}' not found!")

        task = {
            "title": task_title,
            "description": description,
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=duration)).isoformat(),
            "priority": priority,
            "status": status,
            "comments": [],
            "assignees": [],
        }

        if "tasks" not in project or not isinstance(project["tasks"], dict):
            project["tasks"] = {"TODO": [], "DOING": [], "DONE": [], "ARCHIVED": []}

        project["tasks"][status].append(task)
        self._save_data(self.data, self.data_filename)
        return task
    
    def edit_task(self, project_title, task_title, new_title, new_description, new_duration, new_priority):
        self.reload_data()
        project = self.get_project(project_title)
        if not project:
            raise ValueError(f"Project with title '{project_title}' not found!")

        for status, task_list in project["tasks"].items():
            for task in task_list:
                if task["title"] == task_title:
                    task["title"] = new_title if new_title else task["title"]
                    task["description"] = new_description if new_description else task["description"]
                    task["end_date"] = (task["start_date"] + timedelta(days=new_duration)).isoformat() if new_duration else task["end_date"]
                    task["priority"] = new_priority if new_priority else task["priority"]
                    self._save_data(self.data, self.data_filename)
                    return
        raise ValueError(f"Task with title '{task_title}' not found in project '{project_title}'.")

    def delete_task(self, project_title, task_title):
        self.reload_data()
        project = self.get_project(project_title)
        if not project:
            raise ValueError(f"Project with title '{project_title}' not found!")

        for task_list in project["tasks"].values():
            for task in task_list:
                if task["title"] == task_title:
                    task_list.remove(task)
                    self._save_data(self.data, self.data_filename)
                    return
        raise ValueError(f"Task with title '{task_title}' not found in project '{project_title}'.")

    def move_task(self, project_title, task_title, new_status):
        self.reload_data()
        project = self.get_project(project_title)
        if not project:
            raise ValueError(f"Project with title '{project_title}' not found!")

        for status, task_list in project["tasks"].items():
            for task in task_list:
                if task["title"] == task_title:
                    task["status"] = new_status
                    task_list.remove(task)
                    project["tasks"].setdefault(new_status, []).append(task)
                    self._save_data(self.data, self.data_filename)
                    return

        raise ValueError(f"Task with title '{task_title}' not found in project '{project_title}'.")

    def assign_member(self, project_title, task_title, username):
        self.reload_data()
        project = self.get_project(project_title)
        if not project:
            raise ValueError("Project not found!")

        task_found = False
        for task_list in project["tasks"].values():
            for task in task_list:
                if task["title"] == task_title:
                    task_found = True
                    if username in task["assignees"]:
                        raise ValueError("User already assigned to this task!")
                    task["assignees"].append(username)
                    self._save_data(self.data, self.data_filename)
                    return

        if not task_found:
            raise ValueError("Task not found in project!")

    def remove_assignee_from_task(self, project_title, task_title, username):
        self.reload_data()
        project = self.get_project(project_title)
        if not project:
            raise ValueError("Project not found!")

        for task_list in project["tasks"].values():
            for task in task_list:
                if task["title"] == task_title:
                    if username not in task["assignees"]:
                        raise ValueError("User is not assigned to this task!")
                    task["assignees"].remove(username)
                    self._save_data(self.data, self.data_filename)
                    return

        raise ValueError("Task not found in project!")

    def get_tasks_for_project(self, project_title):
        self.reload_data()
        project = self.get_project(project_title)
        if not project:
            raise ValueError(f"Project with title '{project_title}' not found!")

        tasks = []
        for task_list in project["tasks"].values():
            tasks.extend(task_list)
        return tasks

    def get_task(self, project_title, task_title):
        self.reload_data()
        project = self.get_project(project_title)
        if not project:
            raise ValueError(f"Project with title '{project_title}' not found!")

        for task_list in project["tasks"].values():
            for task in task_list:
                if task["title"] == task_title:
                    return task
        return None


if __name__ == "__main__":
    data_manager = DataManager()
    user_manager = UserManager()
    project_manager = ProjectManager()
    task_manager = TaskManager()

    args = parser.parse_args()

    if args.command == "create-user":
        user_manager.create_user(args.username, args.password, args.is_active, args.email, True)
    elif args.command == "purge-data":
        data_manager.purge_data(input("[bold red]Are you sure you want to erase all data? (y/n): "))
    elif args.command == "create-project":
        project_manager.create_project(args.title, args.start_date)
    elif args.command == "add-member":
        project_manager.add_member(args.project_title, args.username)
    elif args.command == "remove-member-from-project":
        project_manager.remove_member_from_project(args.project_title, args.username)
    elif args.command == "add-task":
        task_manager.add_task(
            args.project_title,
            args.task_title,
            args.description,
            args.duration,
            args.priority,
            args.status,
        )
    elif args.command == "move-task":
        task_manager.move_task(args.project_title, args.task_title, args.new_status)
    elif args.command == "assign-member":
        task_manager.assign_member(args.project_title, args.task_title, args.username)
    elif args.command == "remove_assignee_from_task":
        task_manager.remove_assignee_from_task(args.project_title, args.task_title, args.username)
    elif args.command == "delete-task":
        task_manager.delete_task(args.project_title, args.task_title)
    else:
        print("[red]Invalid command![/]")
