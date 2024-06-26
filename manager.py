import argparse
import getpass
import json
import multiprocessing
import uuid
from datetime import date, datetime, timedelta
from io import StringIO
import bcrypt
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
admin_parser = subparsers.add_parser("create-user",help="Create a new administrator account",formatter_class=CustomHelpFormatter)
admin_parser.add_argument("--username", required=True, help="Username for the administrator account")
admin_parser.add_argument("--password", required=True, help="Password for the administrator account")
admin_parser.add_argument("--is_active", type=str2bool, nargs="?", const=True, default=True, help="Activate the administrator account")
admin_parser.add_argument("--email", required=True, help="Email address for the administrator")

# --- Project Management ---
project_parser = subparsers.add_parser("create-project", help="Create a new project", formatter_class=CustomHelpFormatter)
project_parser.add_argument("--title", required=True, help="Project Title")
project_parser.add_argument("--start_date", required=True, help="Project Start Date (dd/mm/yyyy)")
project_parser.add_argument("--owner", required=True, help="Owner of the project")

# --- Purge Data ---
purge_parser = subparsers.add_parser("purge-data", help="Purge all data")

# --- Task Management ---
task_parser = subparsers.add_parser("add-task", help="Add a new task", formatter_class=CustomHelpFormatter)
task_parser.add_argument("--project_title", required=True, help="Project Title")
task_parser.add_argument("--title", required=True, help="Task Title")
task_parser.add_argument("--description", help="Description (Optional)")
task_parser.add_argument("--duration", default=1, type=int, help="Duration in days (Optional)")
task_parser.add_argument("--priority", choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"], default="MEDIUM", help="Task priority (Optional)")
task_parser.add_argument("--status", choices=["BACKLOG","TODO", "DOING", "DONE", "ARCHIVED"], default="TODO", help="Task status (Optional)")

task_parser = subparsers.add_parser("move-task", help="Move a task to a different status")
task_parser.add_argument("--project_title", required=True, help="Project Title")
task_parser.add_argument("--task_title", required=True, help="Task Title")
task_parser.add_argument("--new_status", required=True, choices=["BACKLOG","TODO", "DOING", "DONE", "ARCHIVED"], help="New task status")

task_parser = subparsers.add_parser("delete-task", help="Delete a task", formatter_class=CustomHelpFormatter)
task_parser.add_argument("--project_title", required=True, help="Project Title")
task_parser.add_argument("--task_title", required=True, help="Task Title")

task_parser = subparsers.add_parser("assign-member", help="Assign a user to a task")
task_parser.add_argument("--project_title", required=True, help="Project Title")
task_parser.add_argument("--task_title", required=True, help="Task Title")
task_parser.add_argument("--username", required=True, help="Username of the member to assign")

task_parser = subparsers.add_parser("remove_assignee", help="Remove a user from a task")
task_parser.add_argument("--project_title", required=True, help="Project Title")
task_parser.add_argument("--task_title", required=True, help="Task Title")
task_parser.add_argument("--username", required=True, help="Username of the member to assign")

# --- Member Management ---
member_parser = subparsers.add_parser("add-member", help="Add a user to a project", formatter_class=CustomHelpFormatter)
member_parser.add_argument("--project_title", required=True, help="Project Title")
member_parser.add_argument("--username", required=True, help="Username")

member_parser = subparsers.add_parser("remove-member", help="Remove a user from a project")
member_parser.add_argument("--project_title", required=True, help="Project Title")
member_parser.add_argument("--username", required=True, help="Username")

# --- Comment Management ---
add_comment_parser = subparsers.add_parser("add-comment", help="Add a comment to a task", formatter_class=CustomHelpFormatter)
add_comment_parser.add_argument("--project_title", required=True, help="Project Title")
add_comment_parser.add_argument("--task_title", required=True, help="Task Title")
add_comment_parser.add_argument("--comment_body", required=True, help="Comment body")
add_comment_parser.add_argument("--author", required=True, help="Author of the comment")

edit_comment_parser = subparsers.add_parser("edit-comment", help="Edit a comment on a task")
edit_comment_parser.add_argument("--project_title", required=True, help="Project Title")
edit_comment_parser.add_argument("--task_title", required=True, help="Task Title")
edit_comment_parser.add_argument("--comment_index", required=True, help="Index of the comment to edit")
edit_comment_parser.add_argument("--new_comment", required=True, help="New comment body")

delete_comment_parser = subparsers.add_parser("delete-comment", help="Delete a comment on a task")
delete_comment_parser.add_argument("--project_title", required=True, help="Project Title")
delete_comment_parser.add_argument("--task_title", required=True, help="Task Title")
delete_comment_parser.add_argument("--comment_index", required=True, help="Index of the comment to delete")

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
            "members": [{owner: "owner"}],
            "tasks": {"BACKLOG": [],"TODO": [], "DOING": [], "DONE": [], "ARCHIVED": []},
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
            members = [list(member.keys())[0] for member in project.get("members", [])]
            if username in members:
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

    def add_member(self, project_title, username, role, project_manager):
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
        if not role:
            role = "member"
        project["members"].append({username: role})
        self._save_data(self.data, self.data_filename)

    def remove_member_from_project(self, project_title, username):
        """
        Removes a user from a project.
        """
        self.reload_data()
        project = self.get_project(project_title)
        if not project:
            raise ValueError("Project not found!")

        usernames = [list(member.keys())[0] for member in project["members"]]
        if username not in usernames:
            raise ValueError("User is not a member of the project!")

        del project["members"][usernames.index(username)]
        
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
        
    def get_member_role(self, project_title, username):
        """
        Retrieves the role of a member in a project.
        """
        self.reload_data()
        project = self.get_project(project_title)
        if not project:
            raise ValueError(f"Project with title '{project_title}' not found!")

        for member in project.get("members", []):
            if username in member:
                return member[username]
        return None


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
            project["tasks"] = {"BACKLOG": [],"TODO": [], "DOING": [], "DONE": [], "ARCHIVED": []}

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

    def assignee_member(self, project_title, task_title, username):
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

    def remove_assignee(self, project_title, task_title, username):
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
    
    def add_comment(self, project_title, task_title, comment, author):
        self.reload_data()
        task = self.get_task(project_title, task_title)
        if not task:
            raise ValueError(f"Task with title '{task_title}' not found in project '{project_title}'.")

        task["comments"].append({"comment": comment, "author": author, "timestamp": datetime.now().isoformat()})
        self._save_data(self.data, self.data_filename)

    def edit_comment(self, project_title, task_title, comment_index, new_comment):
        self.reload_data()
        task = self.get_task(project_title, task_title)
        if not task:
            raise ValueError(f"Task with title '{task_title}' not found in project '{project_title}'.")

        if comment_index >= len(task["comments"]):
            raise ValueError(f"Comment index '{comment_index}' out of range.")

        task["comments"][comment_index]["comment"] = new_comment
        task["comments"][comment_index]["timestamp"] = datetime.now().isoformat()
        self._save_data(self.data, self.data_filename)

    def delete_comment(self, project_title, task_title, comment_index):
        self.reload_data()
        task = self.get_task(project_title, task_title)
        if not task:
            raise ValueError(f"Task with title '{task_title}' not found in project '{project_title}'.")

        if comment_index >= len(task["comments"]):
            raise ValueError(f"Comment index '{comment_index}' out of range.")

        task["comments"].pop(comment_index)
        self._save_data(self.data, self.data_filename)

    def get_comments(self, project_title, task_title):
        self.reload_data()
        task = self.get_task(project_title, task_title)
        if not task:
            raise ValueError(f"Task with title '{task_title}' not found in project '{project_title}'.")

        return task["comments"]

if __name__ == "__main__":
    data_manager = DataManager()
    data_manager.reload_data()
    user_manager = UserManager()
    project_manager = ProjectManager()
    task_manager = TaskManager()

    args = parser.parse_args()

    if args.command == "create-user":
        user_manager.create_user(args.username, args.password, args.is_active, args.email)
    elif args.command == "create-project":
        project_manager.create_project(args.title, args.start_date, args.owner)
    elif args.command == "purge-data":
        data_manager.purge_data()
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
    elif args.command == "delete-task":
        task_manager.delete_task(args.project_title, args.task_title)
    elif args.command == "assign-member":
        task_manager.assignee_member(args.project_title, args.task_title, args.username)
    elif args.command == "remove_assignee":
        task_manager.remove_assignee(args.project_title, args.task_title, args.username)
    elif args.command == "add-member":
        project_manager.add_member(args.project_title, args.username, "member", project_manager)
    elif args.command == "remove-member":
        project_manager.remove_member_from_project(args.project_title, args.username)
    elif args.command == "add-comment":
        task_manager.add_comment(args.project_title, args.task_title, args.comment_body, args.author)
    elif args.command == "edit-comment":
        task_manager.edit_comment(args.project_title, args.task_title, int(args.comment_index), args.new_comment)
    elif args.command == "delete-comment":
        task_manager.delete_comment(args.project_title, args.task_title, int(args.comment_index))
    else:
        parser.print_help()
