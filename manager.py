import sys
import bcrypt
import argparse
from rich import print
from datetime import datetime, timedelta, date
import uuid
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import multiprocessing
import getpass

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

# Define task status list for clarity
TASK_STATUSES = ['BACKLOG', 'TODO', 'DOING', 'DONE', 'ARCHIVED']

DATA_FILE = "data.json"

parser = argparse.ArgumentParser(description='Manage administrative tasks')

subparsers = parser.add_subparsers(dest='command')

# --- Admin Management ---
admin_parser = subparsers.add_parser('create-admin')
admin_parser.add_argument('--username', help='Username for the administrator account', required=True)
admin_parser.add_argument('--password', help='Password for the administrator account', required=True)
admin_parser.add_argument('--is_active', type=str2bool, nargs='?', const=True, default=True, help="Activate the administrator account")
admin_parser.add_argument('--email', help="Email address for admin (Optional)", required=False)

# --- Project Management ---
project_parser = subparsers.add_parser('create-project')
project_parser.add_argument('--project_id', help='Project ID', required=True)
project_parser.add_argument('--title', help='Project Title', required=True)
project_parser.add_argument('--start_date', help='Project Start Date (dd/mm/yyyy)', required=True)

project_parser = subparsers.add_parser('purge-data')

# --- Task Management ---
task_parser = subparsers.add_parser('add-task')
task_parser.add_argument('--project_id', help='Project ID', required=True)
task_parser.add_argument('--task_id', help='Task ID', required=True)
task_parser.add_argument('--title', help='Task Title', required=True)
task_parser.add_argument('--description', help='Description (Optional)', required=False)
task_parser.add_argument('--duration', help='Duration in days (Optional)', default=1, type=int)
task_parser.add_argument('--priority', help='Task priority (Optional)', choices=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'], default='LOW')
task_parser.add_argument('--status', help='Task status (Optional)', choices=TASK_STATUSES, default='TODO')

task_parser = subparsers.add_parser('move-task')
task_parser.add_argument('--project_id', help='Project ID', required=True)
task_parser.add_argument('--task_id', help='Task ID', required=True)
task_parser.add_argument('--new_status', help='New task status', choices=TASK_STATUSES)

task_parser = subparsers.add_parser('delete-task')
task_parser.add_argument('--project_id', help='Project ID', required=True)
task_parser.add_argument('--task_id', help='Task ID', required=True)

task_parser = subparsers.add_parser('assign-member')
task_parser.add_argument('--project_id', help='Project ID', required=True)
task_parser.add_argument('--task_id', help='Task ID', required=True)
task_parser.add_argument('--username', help='Username of the member to assign', required=True)

# --- Member Management ---
member_parser = subparsers.add_parser('add-member')
member_parser.add_argument('--project_id', help='Project ID', required=True)
member_parser.add_argument('--username', help='Username', required=True)

member_parser = subparsers.add_parser('remove-member-from-project')
member_parser.add_argument('--project_id', help='Project ID', required=True)
member_parser.add_argument('--username', help='Username', required=True)

task_parser = subparsers.add_parser('remove-member-from-task')
task_parser.add_argument('--project_id', help='Project ID', required=True)
task_parser.add_argument('--task_id', help='Task ID', required=True)
task_parser.add_argument('--username', help='Username', required=True)


# --- Data Handling ---
def _save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def _load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Create an empty file if it doesn't exist
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
        return {}

def create_admin(username, password, is_active=True, email=None):
    try:
        with open("data.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
        with open("data.json", "w") as f:
            json.dump(data, f)
        print("[bold red]Warning: Data file not found! Creating a new one.[/]")

    if 'users' not in data:
        data['users'] = []

    if any(user["username"] == username for user in data["users"]):
        print("[bold red]Error: User with this username already exists![/]")
        return

    if any(user["email"] == email for user in data["users"]):
        print("[bold red]Error: User with this email already exists! Please use a different email.[/]")
        return

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    user = {
        "username": username,
        "password": hashed_password.decode('utf-8'), 
        "email": email,
        "is_active": is_active
    }

    data["users"].append(user)

    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)

    if email and is_active is not None:
        print(f"[blue italic]User account created: username='{username}', password='{password}', Email='{email}', Is_active='{is_active}'[/]")
    elif email:
        print(f"[blue italic]User account created: username='{username}', password='{password}', Email='{email}'[/]")
    else:
        print(f"[blue italic]User account created: username='{username}', password='{password}', No email provided[/]")

def purge_data(confirm):
    if confirm.lower() == "y":
        try:
            with open("data.json", "w") as f:
                json.dump({"users":[],"projects":[],"tasks":[]}, f)
            print("[yellow]All data has been purged![/]")  
        except FileNotFoundError:
            print("[bold red]Warning: No data to purge![/]")

def create_project(project_id, title, start_date):
    if get_project(project_id):
        print(f"[bold red]Error: Project '{project_id}' is already taken![/]")
        return None
    
    project = {
        "id": project_id,
        "title": title,
        "start_date": datetime.strptime(start_date, '%d/%m/%Y').strftime('%Y-%m-%d'),
        "members": [],
        "tasks": []
    }
    
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    
    if 'projects' not in data:
        data['projects'] = []
    
    data["projects"].append(project)
    print(f"[green]Project '{title}' successfully created![/]")
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
    return project

def get_project(project_id):
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return None
    
    if 'projects' not in data:
        return None
    
    for project in data["projects"]:
        if project["id"] == project_id:
            return project
    return None

def get_user(username):
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return None
    
    for user in data["users"]:
        if user["username"] == username:
            return user
    return None

def add_member(project_id, username):
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("[bold red]Error: Data file not found![/]")
        return None

    project = None
    for p in data["projects"]:
        if p["id"] == project_id:
            project = p
            break

    if not project:
        print(f"[bold red]Error: Project '{project_id}' not found![/]")
        return None

    user = get_user(username)
    if not user:
        print(f"[bold red]Error: User '{username}' not found![/]")
        return None

    if username in project["members"]:
        print(f"[bold red]Error: User '{username}' is already a member of the project![/]")
        return None

    project["members"].append(username)

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"[green]User '{username}' successfully added to the project![/]")


# --- Task Functions ---
def add_task(project_id, task_id, title, description, duration, priority, status="TODO"):
    project = None
    for p in data["projects"]:
        if p["id"] == project_id:
            project = p
            break

    if not project:
        print(f"[bold red]Error: Project '{project_id}' not found![/]")
        return None

    task = {
        "task_id": task_id,
        "title": title,
        "description": description,
        "start_date": date.today().isoformat(), # Set start date
        "end_date": (date.today() + timedelta(days=duration)).isoformat(), # Set estimated end date
        "priority": priority, 
        "status": status, 
        "comments": [],
        "assignees": []
    }

    # Add the task to the appropriate list in the project
    project["tasks"] = {status: [] for status in TASK_STATUSES}
    project["tasks"][status].append(task)
    print(f"[green]Task '{title}' successfully added to the project![/]")
    _save_data(data)
    return task


def delete_task(project_id, task_id):
    project = None
    for p in data["projects"]:
        if p["id"] == project_id:
            project = p
            break

    if not project:
        print(f"[bold red]Error: Project '{project_id}' not found![/]")
        return None

    for task_list in project["tasks"].values():
        for task in task_list:
            if task["task_id"] == task_id:
                task_list.remove(task)
                print(f"[green]Task '{task['title']}' deleted successfully![/]")
                _save_data(data)
                return

    print(f"[bold red]Error: Task with ID '{task_id}' not found in project '{project_id}'.[/]")

def move_task(project_id, task_id, new_status):
    project = None
    for p in data["projects"]:
        if p["id"] == project_id:
            project = p
            break

    if not project:
        print(f"[bold red]Error: Project '{project_id}' not found![/]")
        return None

    for task_list in project["tasks"].values():
        for task in task_list:
            if task["task_id"] == task_id:
                # Remove from the current list
                task_list.remove(task)
                # Add to the new status list
                project["tasks"][new_status].append(task)
                print(f"[green]Task '{task['title']}' moved to '{new_status}' successfully![/]")
                _save_data(data)
                return
    print(f"[bold red]Error: Task with ID '{task_id}' not found in project '{project_id}'.[/]")


def assign_member(project_id, task_id, username):
    project = None
    for p in data["projects"]:
        if p["id"] == project_id:
            project = p
            break

    if not project:
        print(f"[bold red]Error: Project '{project_id}' not found![/]")
        return None

    task_found = False
    for task_list in project["tasks"].values():
        for task in task_list:
            if task["task_id"] == task_id:
                task_found = True
                if username in task["assignees"]:
                    print(f"[bold red]Error: User '{username}' is already assigned to this task![/]")
                    return None
                else:
                    task["assignees"].append(username)
                    print(f"[green]User '{username}' successfully assigned to task '{task['title']}![/]")
                    _save_data(data)
                    return

    if not task_found:
        print(f"[bold red]Error: Task with ID '{task_id}' not found in project '{project_id}'.[/]")

def remove_member_from_project(project_id, username):
    project = None
    for p in data["projects"]:
        if p["id"] == project_id:
            project = p
            break

    if not project:
        print(f"[bold red]Error: Project '{project_id}' not found![/]")
        return None

    if username not in project["members"]:
        print(f"[bold red]Error: User '{username}' is not a member of the project![/]")
        return None

    project["members"].remove(username)
    print(f"[green]User '{username}' successfully removed from the project![/]")
    _save_data(data)

def remove_member_from_task(project_id, task_id, username):
    project = None
    for p in data["projects"]:
        if p["id"] == project_id:
            project = p
            break

    if not project:
        print(f"[bold red]Error: Project '{project_id}' not found![/]")
        return None

    for task_list in project["tasks"].values():
        for task in task_list:
            if task["task_id"] == task_id:
                if username not in task["assignees"]:
                    print(f"[bold red]Error: User '{username}' is not assigned to this task![/]")
                    return None
                task["assignees"].remove(username)
                print(f"[green]User '{username}' successfully removed from task '{task['title']}![/]")
                _save_data(data)
                return

    print(f"[bold red]Error: Task with ID '{task_id}' not found in project '{project_id}'.[/]")

if __name__ == "__main__":
    # Load data from the JSON file
    data = _load_data()

    args = parser.parse_args()

    if args.command == 'create-admin':
        create_admin(args.username, args.password, args.is_active, args.email)
    elif args.command == 'purge-data':
        purge_data(input("[bold red]Are you sure you want to erase all data? (y/n): "))
    elif args.command == 'create-project':
        create_project(args.project_id, args.title, args.start_date)
    elif args.command == 'add-member':
        add_member(args.project_id, args.username)
    elif args.command == 'remove-member-from-project':
        remove_member_from_project(args.project_id, args.username)
    elif args.command == 'remove-member-from-task':
        remove_member_from_task(args.project_id, args.task_id, args.username)
    elif args.command == 'add-task':
        add_task(args.project_id, args.task_id, args.title, args.description, args.duration, args.priority, args.status)
    elif args.command == 'delete-task':
        delete_task(args.project_id, args.task_id)
    elif args.command == 'move-task':
        move_task(args.project_id, args.task_id, args.new_status)
    elif args.command == 'assign-member':
        assign_member(args.project_id, args.task_id, args.username)
    else:
        print("[red]Invalid command![/]")
