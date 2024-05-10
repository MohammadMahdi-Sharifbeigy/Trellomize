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

# from utils import display_project_board, get_user_input

theme = Theme(
    {
        "info": "bold blue",
        "warning": "bold yellow",
        "danger": "bold red",
        "success": "bold green",
    }
)
console = Console(theme=theme)
user_manager = UserManager()
project_manager = ProjectManager()


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
        if choice == "1":
            display_project_list()
        elif choice == "2":
            title = Prompt.ask("Enter the title of the new project")
            start_date = Prompt.ask(
                "Enter the start date of the project (dd/mm/yyyy)"
            )
            project = project_manager.create_project(title, start_date)
            console.print(
                f"[green]New project created successfully with ID: {project['id']}[/]"
            )
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
            project_id = Prompt.ask("Enter the project ID")
            display_project_board(project_id)
        elif choice == "5" and is_admin:
            # Function for admin settings
            console.print("Accessing Admin Settings...")
        elif choice == "0":
            console.print("Logging Out...", style="bold red")
            break
        else:
            console.print("Invalid option, please try again.", style="bold red")

# def get_user_input(prompt, allowed_chars=None):
#     while True:
#         user_input = input(f"{prompt} ").strip()

#         if allowed_chars and user_input.upper() not in allowed_chars:
#             console.print(
#                 f"[bold red]Invalid input. Please enter one of: {', '.join(allowed_chars)}[/]"
#             )
#         else:
#             return user_input

def display_project_list():
    projects = project_manager.list_projects()
    if projects:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim")
        table.add_column("Title")
        table.add_column("Start Date", justify="right")
        for project in projects:
            table.add_row(project["id"], project["title"], project["start_date"])
        console.print(table)
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

def display_project_board(project_id):
    project_manager = ProjectManager()
    task_manager = TaskManager()
    project = project_manager.get_project(project_id)

    if not project:
        console.print(f"[bold red]Project with ID '{project_id}' not found![/]")
        return

    console.print(f"[bold blue]Project Board: {project['title']}[/]")

    # Create a table for each task status
    task_tables = {}
    for status in ["TODO", "DOING", "DONE", "ARCHIVED"]:
        task_table = Table(title=status.upper(), style="bold magenta")
        task_table.add_column("ID", style="dim")
        task_table.add_column("Title", style="italic")
        task_table.add_column("Assignee", justify="right")
        task_table.add_column("Priority", justify="center", style="bold")
        task_table.add_column("Due Date", justify="right")
        task_tables[status] = task_table

    # Add tasks to their respective tables
    for status, tasks in project["tasks"].items():
        for task_id, task in enumerate(tasks):
            if task["status"] == status:
                due_date = datetime.strptime(
                    task["end_date"], "%Y-%m-%d").strftime("%d/%m/%Y")
                assignees = ", ".join(task.get("assignees", []))
                task_tables[status].add_row(str(task_id), task["title"], assignees, task["priority"], due_date)


    # Print the task tables
    for status, table in task_tables.items():
        console.print(table)
        console.print("")  # Add a space between tables

    # Provide options for interacting with the board
    while True:
        user_input = Prompt.ask("Choose an action: (a)dd task, (m)ove task, (d)elete task, (b)ack",choices=["a", "m", "d", "b"],)

        if user_input == "a":
            add_task_to_board(project_id)
        elif user_input == "m":
            move_task_on_board(project_id)
        elif user_input == "d":
            delete_task_from_board(project_id)
        elif user_input == "b":
            break


def add_task_to_board(project_id):
    # Collect task details from the user
    title = Prompt.ask("Enter task title:")
    description = input("Enter task description (optional):")
    duration = int(input("Enter task duration (days):"))
    priority = Prompt.ask("Enter task priority (CRITICAL, HIGH, MEDIUM, LOW):",choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"],)
    status = "TODO"  # Default status for new tasks

    # Create and add the task using the task manager
    task_manager.add_task(
        project_id, title, description, duration, priority, status
    )

    # Update the project board display
    display_project_board(project_id)


def move_task_on_board(project_id):
    # Display task IDs and titles for selection
    task_table = Table(title="Available Tasks", style="bold magenta")
    task_table.add_column("ID", style="dim")
    task_table.add_column("Title", style="italic")
    console.print(task_table)
    console.print("")

    for status, tasks in project_manager.get_project(project_id)["tasks"].items():
        for task_id, task in enumerate(tasks):
            task_table.add_row(str(task_id), task["title"])
    console.print(task_table)
    console.print("")

    # Get task ID and new status from the user
    task_id = Prompt.ask("Enter task ID to move:")
    new_status = Prompt.ask("Enter new status (TODO, DOING, DONE, ARCHIVED):",choices=["TODO", "DOING", "DONE", "ARCHIVED"],)

    # Move the task using the task manager
    task_manager.move_task(project_id, task_id, new_status)

    # Update the project board display
    display_project_board(project_id)


def delete_task_from_board(project_id):
    # Display task IDs and titles for selection
    task_table = Table(title="Available Tasks", style="bold magenta")
    task_table.add_column("ID", style="dim")
    task_table.add_column("Title", style="italic")
    console.print(task_table)
    console.print("")

    for task_id, task in project_manager.get_project(project_id)["tasks"].items():
        task_table.add_row(task_id, task["title"])
    console.print(task_table)
    console.print("")

    task_id = Prompt.ask("Enter task ID to delete:")
    try:
        task_manager.delete_task(project_id, task_id)
    except ValueError as e:
        console.print(f"[bold red]{e}[/]")
    else:
        # Update the project board display
        display_project_board(project_id)

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


if __name__ == "__main__":
    user_manager = UserManager()
    project_manager = ProjectManager()
    task_manager = TaskManager()
    main()
