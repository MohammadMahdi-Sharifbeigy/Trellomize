import argparse
import json
import os
from datetime import date, datetime, timedelta

import bcrypt
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.theme import Theme

from manager import ProjectManager, TaskManager, UserManager

theme = Theme({
    "info": "bold blue",
    "warning": "bold yellow",
    "danger": "bold red",
    "success": "bold green",
})

console = Console(theme=theme)

def clear_screen():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

def login(username, password):
    with open("users.json") as f:
        users = json.load(f)["users"]
    user = next((user for user in users if user["username"] == username), None)
    if not user["is_active"]:
        return False, False

    password = bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8"))
    if user["username"] == username and password:
        return True, user
    else:
        return False, False

def display_project_list(project_manager, current_user):
    user = user_manager.get_user(current_user)
    if user["is_admin"]:
        projects = project_manager.list_projects()
    else:
        projects = project_manager.get_projects_for_user(current_user)
        
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
                    project_manager.add_member(project_title, username, project_manager)
                    console.print(f"User '{username}' successfully added to the project!", style="green")
                except Exception as e:
                    console.print(f"Error adding member: {e}", style="danger")
                    continue
            elif user_choice == "r":
                project_title = Prompt.ask("Enter the project title:")
                # project = project_manager.get_project(project_title)
                username = Prompt.ask("Enter the username of the member to remove:")
                try:
                    project_manager.remove_member_from_project(project_title, username)
                    console.print(f"User '{username}' successfully removed from the project!", style="success")
                except Exception as e:
                    console.print(f"Error removing member: {e}", style="danger")
                    continue
            elif user_choice == "b":
                break

    else:
        console.print("No projects available!", style="warning")

def create_new_project():
    project_title = Prompt.ask("Enter the title of the new project")
    start_date = Prompt.ask("Enter the start date of the project (dd/mm/yyyy)")
    try:
        project = project_manager.create_project(project_title, start_date)
        console.print(f"New project created successfully with ID: {project['id']}", style="success")
    except Exception as e:
        console.print(f"Error creating project: {e}", style="danger")

def profile_settings(username):
    user = user_manager.get_user(username)
    if not user:
        console.print("User not found!", style="danger")
        return

    console.print("Edit your profile", style="info")
    fields = {"1": "password", "2": "email"}
    choices = {key: f"Edit {value}" for key, value in fields.items()}
    choices["3"] = "Go back"

    while True:
        for key, value in choices.items():
            console.print(f"[{key}] {value}")

        choice = Prompt.ask("Select an option", choices=list(choices.keys()))
        if choice == "3":
            clear_screen()
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
            console.print(f"Error updating user: {e}", style="danger")
            continue

        console.print(f"{field} updated successfully!", style="success")

def display_project_board(project_title, project_manager, task_manager):
    clear_screen()
    try:
        while True :
            clear_screen()
            project = project_manager.get_project(project_title)
            if not project:
                console.print(f"Project '{project_title}' not found!", style="danger")
                return

            console.print(f"Project Board: [info]{project_title}[/info]")

            try:
                tasks = task_manager.get_tasks_for_project(project_title)
                if not tasks:
                    console.print("No tasks found for this project.", style="warning")
                else:
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
                            due_date = datetime.strptime(task["end_date"], "%Y-%m-%d").strftime("%d/%m/%Y")
                            assignees = ", ".join(task.get("assignees", []))
                            task_tables[status].add_row(task["title"], assignees, task["priority"], due_date)

                    # Print the task tables
                    for status, table in task_tables.items():
                        console.print(table)
                        console.print("")

            except ValueError as e:
                console.print(f"[danger]{e}[/danger]")
                
            action = Prompt.ask("Choose an action: (a)dd task, (m)ove task, (d)elete task, (as)sign member, (r)emove assignee, (b)ack", choices=["a", "m", "d", "as", "r", "b"])

            if action == "a":
                try:
                    task_title = Prompt.ask("Enter task title")
                    task_description = Prompt.ask("Enter task description (optional)", default="")
                    task_duration = int(Prompt.ask("Enter task duration (days)"))
                    task_priority = Prompt.ask("Enter task priority (CRITICAL, HIGH, MEDIUM, LOW)", choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"], default="MEDIUM")

                    task = {
                        "title": task_title,
                        "description": task_description,
                        "duration": task_duration,
                        "priority": task_priority
                    }

                    task_manager.add_task(project_title, task_title, task_description, task_duration, task_priority)
                    console.print(f"[green]Task '{task_title}' added successfully![/green]")
                except Exception as e:
                    console.print(f"[danger]An error occurred while adding the task: {e}[/danger]")

            elif action == "m":
                try:
                    task_title = Prompt.ask("Enter task title to move")
                    new_status = Prompt.ask("Enter new status (TODO, DOING, DONE, ARCHIVED)", choices=["TODO", "DOING", "DONE", "ARCHIVED"])
                    task_manager.move_task(project_title, task_title, new_status)
                    console.print(f"[green]Task '{task_title}' moved to {new_status} successfully![/green]")
                except Exception as e:
                    console.print(f"[danger]An error occurred while moving the task: {e}[/danger]")

            elif action == "d":
                try:
                    task_title = Prompt.ask("Enter task title to delete")
                    task_manager.delete_task(project_title, task_title)
                    console.print(f"[green]Task '{task_title}' deleted successfully![/green]")
                except Exception as e:
                    console.print(f"[danger]An error occurred while deleting the task: {e}[/danger]")

            elif action == "as":
                try:
                    task_title = Prompt.ask("Enter task title to assign a member")
                    member_name = Prompt.ask("Enter member's name to assign")
                    task_manager.assign_member(project_title, task_title, member_name)
                    console.print(f"[green]Member '{member_name}' assigned to task '{task_title}' successfully![/green]")
                except Exception as e:
                    console.print(f"[danger]An error occurred while assigning the member: {e}[/danger]")

            elif action == "r":
                try:
                    task_title = Prompt.ask("Enter task title to remove assignee")
                    member_name = Prompt.ask("Enter member's name to remove")
                    task_manager.remove_assignee_from_task(project_title, task_title, member_name)
                    console.print(f"[green]Member '{member_name}' removed from task '{task_title}' successfully![/green]")
                except Exception as e:
                    console.print(f"[danger]An error occurred while removing the assignee: {e}[/danger]")

            elif action == "b":
                break

            else:
                console.print("[danger]Invalid option, please try again.[/danger]")
    except Exception as e:
        console.print(f"[danger]An error occurred in the menu: {e}[/danger]")

def add_task_to_board(project_title):
    # Collect task details from the user
    task_title = Prompt.ask("Enter task title:")
    description = input("Enter task description (optional):")
    duration = int(input("Enter task duration (days):"))
    priority = Prompt.ask("Enter task priority (CRITICAL, HIGH, MEDIUM, LOW):",choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"],)
    status = "TODO"  # Default status for new tasks

    # Create and add the task using the task manager
    task_manager.add_task(project_title, task_title, description, duration, priority, status)
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
        console.print(e, style="danger")
    else:
        display_project_board(project_title)

def main():
    console.print("Welcome to the Trellomize app!", style="success")
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
                clear_screen()
                if login_result:
                    console.print(":white_check_mark: Login successful!", style="success")
                    break
                else:
                    console.print(":x: Login failed, please try again.", style="danger")
            elif user_choice == "register":
                username = Prompt.ask("Choose a username")
                password = Prompt.ask("Choose a password", password=True)
                if user_manager.create_user(username=username, password=password):
                    clear_screen()
                    console.print("Registration successful!", style="info")
                    break
                else:
                    clear_screen()
                    console.print("Registration failed, please try again.", style="danger")
            elif user_choice == "exit":
                clear_screen()
                console.print("Exiting the app. Goodbye!", style="bold magenta")
                return
        except Exception as e:
            clear_screen()
            console.print(f"An error occurred: {e}", style="danger")
    main_menu(is_admin, user["username"] if user else None)

def main_menu(is_admin=False, current_user=None):
    while True:
        console.print("Main Menu", style="info")
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
                display_project_list(project_manager, current_user)
            elif choice == "2":
                title = Prompt.ask("Enter the title of the new project")
                start_date = Prompt.ask(
                    "Enter the start date of the project (dd/mm/yyyy)"
                )
                project = project_manager.create_project(title, start_date)
                console.print(f"New project created successfully with Title: {project['title']}", style="success")
            elif choice == "3":
                profile_settings(current_user)
            elif choice == "4":
                project_title = Prompt.ask("Enter the project title")
                project = project_manager.get_project(project_title)
                if not project:
                    console.print(f"Project with title '{project_title}' not found", style="danger")
                    continue
                display_project_board(project_title, project_manager, task_manager)
            elif choice == "5" and is_admin:
                console.print("Accessing Admin Settings...")
            elif choice == "0":
                console.print("Logging Out...", style="danger")
                break
            else:
                console.print("Invalid option, please try again.", style="danger")
        except Exception as e:
            console.print(f"An error occurred in the menu: {e}", style="danger")

if __name__ == "__main__":
    user_manager = UserManager()
    project_manager = ProjectManager()
    task_manager = TaskManager()
    main()