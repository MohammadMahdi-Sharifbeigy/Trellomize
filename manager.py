import sys
import bcrypt
import argparse
from rich import print
from datetime import datetime, timedelta
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

DATA_FILE = "data.json"

parser = argparse.ArgumentParser(description='Manage administrative tasks')

subparsers = parser.add_subparsers(dest='command')

admin_parser = subparsers.add_parser('create-admin')
admin_parser.add_argument('--username', help='Username for the administrator account', required=True)
admin_parser.add_argument('--password', help='Password for the administrator account', required=True)
admin_parser.add_argument('--is_active', help="Activate the administrator account", required=False, default=True, type=bool)
admin_parser.add_argument('--email', help="Email address for admin (Optional)", required=False)

project_parser = subparsers.add_parser('create-project')
project_parser.add_argument('--project_id', help='Project ID', required=True)
project_parser.add_argument('--title', help='Project Title', required=True)
project_parser.add_argument('--start_date', help='Project Start Date (dd/mm/yyyy)', required=True)

project_parser = subparsers.add_parser('purge-data')

member_parser = subparsers.add_parser('add-member')
member_parser.add_argument('--project_id', help='Project ID', required=True)
member_parser.add_argument('--username', help='Username of the member to add', required=True)

def create_admin(username, password):
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
 
    if any(user["username"] == "admin" and user["is_admin"] for user in data["users"]):
        print("[bold red]Error: Administrator account already exists![/]")
        return

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    admin_user = {
        "username": args.username,
        "password": hashed_password.decode('utf-8'), 
        "email": args.email,
        "is_active": True,
        "is_admin": True
    }

    data["users"].append(admin_user)

    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"[blue italic]Administrator account created: username='{username}', password='{password}', Email='{email}'[/]")


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

    project = get_project(project_id)
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

if __name__ == "__main__":
    args = parser.parse_args()
    if args.command == 'create-admin':
        if args.password and args.username:
            create_admin(args.username, args.password)
        else:
            print("[red]Username and password must be provided![/]")
    elif args.command == 'purge-data':
        purge_data(input("[bold red]Are you sure you want to erase all data? (y/n): "))
    elif args.command == 'create-project':
        create_project(args.project_id, args.title, args.start_date)
    elif args.command == 'add-member':
        add_member(args.project_id, args.username)
    else:
        print("[red]Invalid command![/]")
