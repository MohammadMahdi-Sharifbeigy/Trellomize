import json
import os

import bcrypt
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.theme import Theme

from manager import ProjectManager, UserManager

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

    while True:
        for key, value in menu_options.items():
            console.print(f"[{key}] {value}")

        choice = Prompt.ask("Select an option", choices=menu_options.keys())

        clear_screen()

        if choice == "1":
            display_project_list()
        elif choice == "2":
            create_new_project()
        elif choice == "3":
            profile_settings(current_user)
        elif choice == "4":
            # Function to display the board with all tasks
            console.print("Displaying Board...")
        elif choice == "5" and is_admin:
            # Function for admin settings
            console.print("Accessing Admin Settings...")
        elif choice == "0":
            console.print("Logging Out...", style="bold red")
            break
        else:
            console.print("Invalid option, please try again.", style="bold red")


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


def main():
    console.print("Welcome to the Trellomize app!", style="bold green")

    while True:
        user_choice = Prompt.ask(
            "Choose an option", choices=["login", "register", "exit"], default="login"
        )

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
    main()
