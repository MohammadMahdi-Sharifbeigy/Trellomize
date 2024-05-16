import json
import os

import bcrypt
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.theme import Theme

from datetime import date, datetime, timedelta

import argparse

from manager import ProjectManager, UserManager, TaskManager

theme = Theme(
    {
        "info": "bold blue",
        "warning": "bold yellow",
        "danger": "bold red",
        "success": "bold green",
    }
)
console = Console(theme=theme)

def clear_screen():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def login(username, password):
    with open("users.json") as f:
        users = json.load(f)["users"]

    for user in users:
        if not user["is_active"]:
            return False, False

        password = bcrypt.checkpw(
            password.encode("utf-8"), user["password"].encode("utf-8")
        )
        if user["username"] == username and password:
            return True, user
        else:
            return False, False

def display_project_list(project_manager):
    projects = project_manager.list_projects()
    if projects:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Title")
        table.add_column("Start Date", justify="right")
        for project in projects:
            table.add_row(project["title"], project["start_date"])
        console.print(table)

        # Add or remove member to project
        while True:
            user_choice = Prompt.ask("Choose an action: (a)dd member, (r)emove member, (b)ack", choices=["a", "r", "b"])
            if user_choice == "a":
                project_title = Prompt.ask("Enter the project title:")
                # project = project_manager.get_project(project_title)
                username = Prompt.ask("Enter the username of the member to add:")
                try:
                    project_manager.add_member(project_title, username)
                    console.print(f"[green]User '{username}' successfully added to the project![/]")  # Correct markup here
                except Exception as e:
                    console.print(f"[red]Error adding member: {e}[/]")
                    continue
            elif user_choice == "r":
                project_title = Prompt.ask("Enter the project title:")
                # project = project_manager.get_project(project_title)
                username = Prompt.ask("Enter the username of the member to remove:")
                try:
                    project_manager.remove_member_from_project(project_title, username)
                    console.print(f"User '{username}' successfully removed from the project![/]")
                except Exception as e:
                    console.print(f"Error removing member: {e}[/]")
                    continue
            elif user_choice == "b":
                break

    else:
        console.print("[bold red]No projects available![/]")


def create_new_project():
    title = Prompt.ask("Enter the title of the new project")
    start_date = Prompt.ask("Enter the start date of the project (dd/mm/yyyy)")
    try:
        project = project_manager.create_project(title, start_date)
        console.print(
            f"[green]New project created successfully with ID: {project['id']}[/]"
        )
    except Exception as e:
        console.print(f"[red]Error creating project: {e}[/]")


def profile_settings(username):
    user = user_manager.get_user(username)
    if not user:
        console.print("[red]User not found![/]")
        return

    console.print("[yellow]Edit your profile[/]")
    fields = {"1": "password", "2": "email"}
    choices = {key: f"Edit {value}" for key, value in fields.items()}
    choices["3"] = "Go back"

    while True:
        for key, value in choices.items():
            console.print(f"[{key}] {value}")

        choice = Prompt.ask("Select an option", choices=list(choices.keys()))
        if choice == "3":
            break

        field = fields[choice]
        new_value = Prompt.ask(f"Enter new {field}")

        if field == "password":
            new_value = bcrypt.hashpw(
                new_value.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

        updates = {field: new_value}
        try:
            user_manager.update_user(username, updates)
        except Exception as e:
            console.print(f"[red]Error updating user: {e}[/]")
            continue

        console.print(f"[green]{field} updated successfully![/]")

def display_project_board(project_title):
    project_manager = ProjectManager()
    task_manager = TaskManager()
    project = project_manager.get_project(project_title)

    if not project:
        console.print(f"[bold red]Project with Title '{project_title}' not found![/]")
        return

    console.print(f"[bold blue]Project Board: {project['title']}[/]")

    # Create a table for each task status
    task_tables = {}
    for status in ["TODO", "DOING", "DONE", "ARCHIVED"]:
        task_table = Table(title=status.upper(), style="bold magenta")
        task_table.add_column("Title", style="italic")
        task_table.add_column("Assignee", justify="right")
        task_table.add_column("Priority", justify="center", style="bold")
        task_table.add_column("Due Date", justify="right")
        task_tables[status] = task_table

    # Add tasks to their respective tables
    for status, tasks in project["tasks"].items():
        for task in tasks:
            due_date = datetime.strptime(
                task["end_date"], "%Y-%m-%d").strftime("%d/%m/%Y")
            assignees = ", ".join(task.get("assignees", []))
            task_tables[status].add_row(task["title"], assignees, task["priority"], due_date)


    # Print the task tables
    for status, table in task_tables.items():
        console.print(table)
        console.print("")  # Add a space between tables

    # Provide options for interacting with the board
    while True:
        user_input = Prompt.ask("Choose an action: (a)dd task, (m)ove task, (d)elete task, (as)sign member, (r)emove assignee, (b)ack",choices=["a", "m", "d", "as", "r", "b"],)

        if user_input == "a":
            add_task_to_board(project_title)
        elif user_input == "m":
            move_task_on_board(project_title)
        elif user_input == "d":
            delete_task_from_board(project_title)
        elif user_input == "as":
            if any(project["tasks"].values()) and any(project["members"]):
                task_title = Prompt.ask("Enter task Title to assign member to:")
                username = Prompt.ask("Enter username of member to assign:")
                task_manager.assign_member(project_title, task_title, username)
            else:
                console.print(f"[bold red]User could not assigne to a task![/]")
        elif user_input == "r":
            if any(project["tasks"].values()) and any(project["members"]):
                task_title = Prompt.ask("Enter task Title to remove assignee from:")
                username = Prompt.ask("Enter username of assignee to remove:")
                task_manager.remove_assignee_from_task(project_title, task_title, username)
            else:
                console.print(f"[bold red]User could not remove to from a task![/]")
        elif user_input == "b":
            break

def add_task_to_board(project_title):
    # Collect task details from the user
    title = Prompt.ask("Enter task title:")
    description = input("Enter task description (optional):")
    duration = int(input("Enter task duration (days):"))
    priority = Prompt.ask("Enter task priority (CRITICAL, HIGH, MEDIUM, LOW):",choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"],)
    status = "TODO"  # Default status for new tasks

    # Create and add the task using the task manager
    task_manager.add_task(project_title, title, description, duration, priority, status)
    # Update the project board display
    display_project_board(project_title)


def move_task_on_board(project_title):
    task_table = Table(title="Available Tasks", style="bold magenta")
    task_table.add_column("ID", style="dim")
    task_table.add_column("Title", style="italic")

    for status, tasks in project_manager.get_project(project_title)["tasks"].items():
        for task_title, task in enumerate(tasks):
            task_table.add_row(task["title"])
    console.print(task_table)
    console.print("")

    task_title = Prompt.ask("Enter task Ttile to move:")
    new_status = Prompt.ask("Enter new status (TODO, DOING, DONE, ARCHIVED):",choices=["TODO", "DOING", "DONE", "ARCHIVED"],)

    task_manager.move_task(project_title, task_title, new_status)

    display_project_board(project_title)


def delete_task_from_board(project_title):
    task_table = Table(title="Available Tasks", style="bold magenta")

    for status, tasks in project_manager.get_project(project_title)["tasks"].items():
        for task_title, task in enumerate(tasks):
            task_table.add_row(task["title"])
    console.print(task_table)

    console.print("")

    task_title = Prompt.ask("Enter task Title to delete:")
    try:
        task_manager.delete_task(project_title, task_title)
    except ValueError as e:
        console.print(f"[bold red]{e}[/]")
    else:
        display_project_board(project_title)

def main():
    console.print("Welcome to the Trellomize app!", style="bold green")
    while True:
        user_choice = Prompt.ask("Choose an option", choices=["login", "register", "exit"], default="login")
        is_admin = False
        user = None
        try:
            if user_choice == "login":
                username = Prompt.ask("Enter your username")
                password = Prompt.ask("Enter your password", password=True)
                login_result, user = login(username, password)
                is_admin = user["is_admin"] if user else False
                if login_result:
                    console.print(
                        ":white_check_mark:Login successful!", style="success"
                    )
                    break
                else:
                    console.print(":x:Login failed, please try again.", style="danger")
            elif user_choice == "register":
                username = Prompt.ask("Choose a username")
                password = Prompt.ask("Choose a password", password=True)
                if user_manager.create_user(username=username, password=password):
                    console.print("Registration successful!", style="bold blue")
                    break
                else:
                    console.print(
                        "Registration failed, please try again.", style="bold red"
                    )
            elif user_choice == "exit":
                console.print("Exiting the app. Goodbye!", style="bold magenta")
                return
        except Exception as e:
            console.print(f"An error occurred: {e}", style="bold red")
    main_menu(is_admin, user["username"] if user else None)


def main_menu(is_admin=False, current_user=None):
    while True:
        clear_screen()
        console.print("Main Menu", style="bold blue")
        menu_options = {
            "1": "Project List",
            "2": "Create New Project",
            "3": "Profile Settings",
            "4": "Board",
            "0": "Log Out",
        }
        if is_admin:
            menu_options["5"] = "Admin Settings"
        for key, value in menu_options.items():
            console.print(f"[{key}] {value}")
        choice = Prompt.ask("Select an option", choices=menu_options.keys())
        clear_screen()
        try:
            if choice == "1":
                display_project_list(project_manager)
            elif choice == "2":
                title = Prompt.ask("Enter the title of the new project")
                start_date = Prompt.ask(
                    "Enter the start date of the project (dd/mm/yyyy)"
                )
                project = project_manager.create_project(title, start_date)
                console.print(f"[green]New project created successfully with Title: {project[project_title]}[/]")
            elif choice == "3":
                username = current_user
                user = user_manager.get_user(username)
                if not user:
                    console.print("[red]User not found![/]")
                    continue
                console.print("[yellow]Edit your profile[/]")
                fields = {"1": "password", "2": "email"}
                choices = {key: f"Edit {value}" for key, value in fields.items()}
                choices["3"] = "Go back"
                while True:
                    for key, value in choices.items():
                        console.print(f"[{key}] {value}")
                    choice = Prompt.ask("Select an option", choices=list(choices.keys()))
                    if choice == "3":
                        break
                    field = fields[choice]
                    new_value = Prompt.ask(f"Enter new {field}")
                    if field == "password":
                        new_value = bcrypt.hashpw(
                            new_value.encode("utf-8"), bcrypt.gensalt()
                        ).decode("utf-8")
                    updates = {field: new_value}
                    try:
                        user_manager.update_user(username, updates)
                    except Exception as e:
                        console.print(f"[red]Error updating user: {e}[/]")
                        continue
                    console.print(f"[green]{field} updated successfully![/]")
            elif choice == "4":
                project_title = Prompt.ask("Enter the project title")
                project = project_manager.get_project(project_title)
                if not project:
                    console.print(f"[bold red]Project with title '{project_title}' not found![/]")
                    continue
                display_project_board(project[project_title])
            elif choice == "5" and is_admin:
                console.print("Accessing Admin Settings...")
            elif choice == "0":
                console.print("Logging Out...", style="bold red")
                break
            else:
                console.print("Invalid option, please try again.", style="bold red")
        except Exception as e:
            console.print(
                f"[bold red]An error occurred in the menu: {e}[/]"
            )

if __name__ == "__main__":
    user_manager = UserManager()
    project_manager = ProjectManager()
    task_manager = TaskManager()
    main()