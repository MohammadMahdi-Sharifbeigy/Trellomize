import argparse
import json
import os
import re
from datetime import date, datetime, timedelta

import bcrypt
from loguru import logger
from rich.columns import Columns
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.theme import Theme

from manager import ProjectManager, TaskManager, UserManager

# Set up Loguru configuration
logger.remove()  # Remove the default handler
logger.add("app.log", rotation="1 MB", level="DEBUG", format="{time} {level} {message}")

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
    if not user:
        logger.warning(f"Login failed for {username}: user not found")
        return False, False
    if not user["is_active"]:
        logger.warning(f"Login failed for {username}: user is inactive")
        return False, False

    password_matches = bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8"))
    if user["username"] == username and password_matches:
        logger.info(f"User {username} logged in successfully")
        return True, user
    else:
        logger.warning(f"Login failed for {username}: incorrect password")
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

        project_title = Prompt.ask("Enter the project title, or press enter to go back")
        if project_title == "":
            clear_screen()
            return
        display_project(project_title, project_manager, task_manager, current_user)
        clear_screen()

    else:
        console.print("No projects available!", style="warning")

def create_new_project(current_user):
    title = Prompt.ask("Enter the title of the new project, or press enter to go back")
    if title == "":
        clear_screen()
        return
    start_date = Prompt.ask(
        "Enter the start date of the project (dd/mm/yyyy)"
    )
    while True:
        try:
            datetime.strptime(start_date, "%d/%m/%Y")
            break
        except ValueError:
            start_date = Prompt.ask("Invalid date format. Enter the start date of the project (dd/mm/yyyy)")
    try:
        project = project_manager.create_project(title, start_date, current_user)
        clear_screen()
        console.print(f"New project created successfully with Title: {project['title']}", style="success")
        logger.info(f"Project '{title}' created successfully by {current_user}")
    except Exception as e:
        console.print(f"Error creating project: {e}", style="danger")
        logger.error(f"Error creating project '{title}': {e}")

def profile_settings(username):
    user = user_manager.get_user(username)
    if not user:
        console.print("User not found!", style="danger")
        logger.warning(f"Profile settings: user {username} not found")
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
            logger.info(f"{field.capitalize()} updated successfully for {username}")
        except Exception as e:
            console.print(f"Error updating user: {e}", style="danger")
            logger.error(f"Error updating {field} for {username}: {e}")
            continue

        console.print(f"{field} updated successfully!", style="success")

def display_project(project_title, project_manager, task_manager, current_user):
    clear_screen()
    try:
        while True :
            clear_screen()
            project = project_manager.get_project(project_title)
            if not project:
                console.print(f"Project '{project_title}' not found!", style="danger")
                logger.warning(f"Project '{project_title}' not found")
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

                    # Create a list of the tables to display side by side
                    tables = [task_tables[status] for status in ["TODO", "DOING", "DONE", "ARCHIVED"]]

                    # Print the task tables side by side
                    console.print(Columns(tables))

            except ValueError as e:
                console.print(f"{e}", style="danger")
                logger.error(f"Error retrieving tasks for project '{project_title}': {e}")
                
            member_role = project_manager.get_member_role(project_title, current_user)
            
            menu_options = {
                "1": "Add Task",
                "2": "Edit Task",
                "3": "Move Task",
                "4": "Delete Task",
                "5": "Add Member",
                "6": "Remove Member",
                "7": "Assign Member",
                "8": "Remove Assignee",
                "9": "View Members",
                "11": "Comments",
                "0": "Exit",
            }
            if project_manager.is_project_owner(project_title, current_user):
                menu_options.pop("0")
                menu_options.pop("11")
                menu_options["10"] = "Delete Project"
                menu_options["11"] = "Comments"
                menu_options["0"] = "Exit"
            
            for key, value in menu_options.items():
                console.print(f"[{key}] {value}")
            action = Prompt.ask("Select an option", choices=menu_options.keys())
            if action == "1":
                if member_role == "member":
                    console.print("You do not have permission to add tasks!", style="warning")
                    input("Press any key to continue...")
                    continue
                try:
                    task_title = Prompt.ask("Enter task title, or press enter to go back")
                    if task_title == "":
                        continue
                    while task_manager.get_task(project_title, task_title):
                        console.print(f"Task '{task_title}' already exists! Please enter a different title.", style="warning")
                        task_title = Prompt.ask("Enter task title")
                    while not task_title:
                        console.print("Task title cannot be empty!", style="warning")
                        task_title = Prompt.ask("Enter task title")
                    task_description = Prompt.ask("Enter task description (optional)", default="")
                    task_duration = int(Prompt.ask("Enter task duration (days)", default="1"))
                    while task_duration <= 0:
                        console.print("Duration must be greater than 0!", style="warning")
                        task_duration = int(Prompt.ask("Enter task duration (days)"))
                    task_priority = Prompt.ask("Enter task priority (CRITICAL, HIGH, MEDIUM, LOW)", choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"], default="MEDIUM")

                    task = {
                        "title": task_title,
                        "description": task_description,
                        "duration": task_duration,
                        "priority": task_priority
                    }

                    task_manager.add_task(project_title, task_title, task_description, task_duration, task_priority)
                    console.print(f"Task '{task_title}' added successfully!", style="success")
                    logger.info(f"Task '{task_title}' added to project '{project_title}' by {current_user}")
                except Exception as e:
                    console.print(f"An error occurred while adding the task: {e}", style="danger")
                    logger.error(f"Error adding task '{task_title}' to project '{project_title}': {e}")
            elif action == "2":
                if member_role == "member":
                    console.print("You do not have permission to edit tasks!", style="warning")
                    input("Press any key to continue...")
                    continue
                try:
                    task_title = Prompt.ask("Enter task title to edit, or press enter to go back")
                    if task_title == "":
                        continue
                    new_title = Prompt.ask("Enter new title (optional)")
                    new_description = Prompt.ask("Enter new description (optional)")
                    new_duration = Prompt.ask("Enter new duration (days) (optional)")
                    new_priority = Prompt.ask("Enter new priority (CRITICAL, HIGH, MEDIUM, LOW) (optional)", choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"])
                    task_manager.edit_task(project_title, task_title, new_title, new_description, new_duration, new_priority)
                    console.print(f"Task '{task_title}' updated successfully!", style="success")
                    logger.info(f"Task '{task_title}' updated in project '{project_title}' by {current_user}")
                except Exception as e:
                    console.print(f"An error occurred while updating the task: {e}", style="danger")
                    logger.error(f"Error updating task '{task_title}' in project '{project_title}': {e}")
            elif action == "3":
                if member_role == "member":
                    console.print("You do not have permission to move tasks!", style="warning")
                    input("Press any key to continue...")
                    continue
                try:
                    task_title = Prompt.ask("Enter task title to move, or press enter to go back")
                    if task_title == "":
                        continue
                    new_status = Prompt.ask("Enter new status (TODO, DOING, DONE, ARCHIVED)", choices=["TODO", "DOING", "DONE", "ARCHIVED"])
                    task_manager.move_task(project_title, task_title, new_status)
                    console.print(f"Task '{task_title}' moved to {new_status} successfully!", style="success")
                    logger.info(f"Task '{task_title}' moved to {new_status} in project '{project_title}' by {current_user}")
                except Exception as e:
                    console.print(f"An error occurred while moving the task: {e}", style="danger")
                    logger.error(f"Error moving task '{task_title}' in project '{project_title}': {e}")

            elif action == "4":
                if member_role == "member":
                    console.print("You do not have permission to delete tasks!", style="warning")
                    input("Press any key to continue...")
                    continue
                try:
                    task_title = Prompt.ask("Enter task title to delete, or press enter to go back")
                    if task_title == "":
                        continue
                    task_manager.delete_task(project_title, task_title)
                    console.print(f"Task '{task_title}' deleted successfully!", style="success")
                    logger.info(f"Task '{task_title}' deleted from project '{project_title}' by {current_user}")
                except Exception as e:
                    console.print(f"An error occurred while deleting the task: {e}", style="danger")
                    logger.error(f"Error deleting task '{task_title}' from project '{project_title}': {e}")

            elif action == "5":
                if member_role == "member":
                    console.print("You do not have permission to add members!", style="warning")
                    input("Press any key to continue...")
                    continue
                try:
                    console.print("Available members:")
                    avl_members = set(user_manager.get_members()) - set(list(member.keys())[0] for member in project_manager.get_project(project_title)["members"])
                    if not avl_members:
                        console.print("No members available to add!", style="warning")
                    else:
                        for member in avl_members:
                            console.print(member)
                        member_name = Prompt.ask("Enter member's name to add, or press enter to go back")
                        if member_name == "":
                            continue
                        while member_name not in avl_members and member_name != '0':
                            console.print(f"Member '{member_name}' not found! Enter 0 to exit", style="danger")
                            member_name = Prompt.ask("Enter member's name to add")
                        role_list = ["admin", "manager", "member"]
                        role = Prompt.ask("Enter member's role", choices=role_list)
                        while role not in role_list:
                            role = Prompt.ask("Choose a valid role", choices=role_list)
                        if member_name != '0':
                            project_manager.add_member(project_title, member_name, role, project_manager)
                            console.print(f"Member '{member_name}' added successfully!", style="success")
                            logger.info(f"Member '{member_name}' added to project '{project_title}' with role '{role}' by {current_user}")
                except Exception as e:
                    console.print(f"An error occurred while adding the member: {e}", style="danger")
                    logger.error(f"Error adding member '{member_name}' to project '{project_title}': {e}")

            elif action == "6":
                if member_role == "member":
                    console.print("You do not have permission to remove members!", style="warning")
                    input("Press any key to continue...")
                    continue
                try:
                    project_members_name = list()
                    console.print("Members in the project:")
                    for member in project_manager.get_project(project_title)["members"]:
                        for name, role in member.items():
                            console.print(f"{name} ({role})")
                            project_members_name.append(name)
                    member_name = Prompt.ask("Enter member's name to remove, or press enter to go back")
                    if member_name == "":
                        continue
                    while member_name not in project_members_name and member_name != '0':
                        console.print(f"Member '{member_name}' is not part of the project! Enter 0 to exit", style="danger")
                        member_name = Prompt.ask("Enter member's name to remove")
                    if member_name != '0':
                        project_manager.remove_member_from_project(project_title, member_name)
                        console.print(f"Member '{member_name}' removed successfully!", style="success")
                        logger.info(f"Member '{member_name}' removed from project '{project_title}' by {current_user}")
                except Exception as e:
                    console.print(f"An error occurred while removing the member: {e}", style="danger")
                    logger.error(f"Error removing member '{member_name}' from project '{project_title}': {e}")

            elif action == "7":
                if member_role == "member":
                    console.print("You do not have permission to assign members!", style="warning")
                    input("Press any key to continue...")
                    continue
                try:
                    task_title = Prompt.ask("Enter task title to assign a member, or press enter to go back")
                    if task_title == "":
                        continue
                    console.print("Members in the project:")
                    for member in project_manager.get_project(project_title)["members"]:
                        for name, role in member.items():
                            console.print(f"{name} ({role})")
                    member_name = Prompt.ask("Enter member's name to assign")
                    project_members_name = [list(member.keys())[0] for member in project_manager.get_project(project_title)["members"]]
                    while member_name not in project_members_name and member_name != '0':
                        console.print(f"Member '{member_name}' is not part of the project! Enter 0 to exit", style="danger")
                        member_name = Prompt.ask("Enter member's name to assign")
                    if member_name != '0':
                        task_manager.assign_member(project_title, task_title, member_name)
                        console.print(f"Member '{member_name}' assigned to task '{task_title}' successfully!", style="success")
                        logger.info(f"Member '{member_name}' assigned to task '{task_title}' in project '{project_title}' by {current_user}")
                except Exception as e:
                    console.print(f"An error occurred while assigning the member: {e}", style="danger")
                    logger.error(f"Error assigning member '{member_name}' to task '{task_title}' in project '{project_title}': {e}")

            elif action == "8":
                if member_role == "member":
                    console.print("You do not have permission to remove assignees!", style="warning")
                    input("Press any key to continue...")
                    continue
                try:
                    task_title = Prompt.ask("Enter task title to remove assignee, or press enter to go back")
                    if task_title == "":
                        continue
                    console.print("Assignees in the task:")
                    for assignee in task_manager.get_task(project_title, task_title)["assignees"]:
                        console.print(assignee)
                    member_name = Prompt.ask("Enter member's name to remove")
                    while member_name not in task_manager.get_task(project_title, task_title)["assignees"] and member_name != '0':
                        console.print(f"Member '{member_name}' is not assigned to the task! Enter 0 to exit", style="danger")
                        member_name = Prompt.ask("Enter member's name to remove")
                    if member_name != '0':
                        task_manager.remove_assignee_from_task(project_title, task_title, member_name)
                        console.print(f"Member '{member_name}' removed from task '{task_title}' successfully!", style="success")
                        logger.info(f"Member '{member_name}' removed from task '{task_title}' in project '{project_title}' by {current_user}")
                except Exception as e:
                    console.print(f"An error occurred while removing the assignee: {e}", style="danger")
                    logger.error(f"Error removing assignee '{member_name}' from task '{task_title}' in project '{project_title}': {e}")

            elif action == "9":
                try:
                    console.print("Members in the project:")
                    for member in project_manager.get_project(project_title)["members"]:
                        for name, role in member.items():
                            console.print(f"{name} ({role})")
                except Exception as e:
                    console.print(f"An error occurred while viewing the members: {e}", style="danger")
                    logger.error(f"Error viewing members in project '{project_title}': {e}")
            elif action == "10":
                # no need to write this, but who cares
                if member_role != "owner":
                    console.print("You do not have permission to delete the project!", style="warning")
                    input("Press any key to continue...")
                    continue
                try:
                    sure = Prompt.ask("Are you sure you want to delete the project? (yes/no)")
                    if sure.lower() != "yes":
                        console.print("Project deletion cancelled.", style="warning")
                        break
                    else:
                        sure = Prompt.ask("Are you really sure you want to delete the project? (yes/no)")
                        if sure.lower() == "yes":
                            project_manager.delete_project(project_title)
                            console.print(f"Project '{project_title}' deleted successfully!", style="success")
                            logger.info(f"Project '{project_title}' deleted by {current_user}")
                            input("Press any key to continue...")
                            break
                    console.print("Project deletion cancelled.", style="warning")
                except Exception as e:
                    console.print(f"An error occurred while deleting the project: {e}", style="danger")
                    logger.error(f"Error deleting project '{project_title}': {e}")
            
            elif action == "11":
                all_tasks = task_manager.get_tasks_for_project(project_title)
                if len(all_tasks) == 0:
                    console.print("No tasks found in the project.", style="warning")
                    input("Press any key to continue...")
                    clear_screen()
                    continue
                handle_comments(project_title, task_manager, current_user)
                
            elif action == "0":
                break

            else:
                console.print("Invalid option, please try again.", style="danger")
                logger.warning(f"Invalid menu option selected in project '{project_title}' by {current_user}")

            
            input("Press any key to continue...")
    except Exception as e:
        console.print(f"An error occurred in the menu: {e}")
        logger.error(f"Error in project '{project_title}' menu: {e}")

def handle_comments(project_title, task_manager, current_user):
    task_title = Prompt.ask("Enter the task title to manage comments")
    while True:
        clear_screen()
        console.print(f"Managing comments for task: [bold]{task_title}[/bold] in project: [bold]{project_title}[/bold]")
        comments = task_manager.get_comments(project_title, task_title)
        if comments:
            for index, comment in enumerate(comments):
                console.print(f"[{index}] {comment['comment']} (by {comment['author']} - at {comment['timestamp']})")
        else:
            console.print("No comments found.", style="warning")

        comment_action = Prompt.ask("Choose an option", choices=["add", "edit", "delete", "back"], default="back")
        if comment_action == "add":
            comment = Prompt.ask("Enter your comment")
            task_manager.add_comment(project_title, task_title, comment, current_user)
            console.print(f"Comment added successfully.", style="success")
        elif comment_action == "edit":
            index = int(Prompt.ask("Enter the comment zindex to edit"))
            new_comment = Prompt.ask("Enter your new comment")
            task_manager.edit_comment(project_title, task_title, index, new_comment)
            console.print(f"Comment edited successfully.", style="success")
        elif comment_action == "delete":
            index = int(Prompt.ask("Enter the comment index to delete"))
            task_manager.delete_comment(project_title, task_title, index)
            console.print(f"Comment deleted successfully.", style="success")
        elif comment_action == "back":
            break
        input("Press any key to continue...")

def admin_panel():
    console.print("Admin Panel", style="info")
    while True:
        console.print("[1] List Users")
        console.print("[2] Activate/Deactivate User")
        console.print("[3] Go back")
        choice = Prompt.ask("Select an option", choices=["1", "2", "3"])
        usernames = user_manager.get_members()
        users = [user_manager.get_user(username) for username in usernames]
        if choice == "1":
            clear_screen()
            if not users:
                console.print("No users found!", style="warning")
            else:
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Username")
                table.add_column("Email")
                table.add_column("Is Active", justify="right")
                table.add_column("Is Admin", justify="right")
                for user in users:
                    table.add_row(user["username"], user["email"], str(user["is_active"]), str(user["is_admin"]))
                console.print(table)
                logger.info("Listed all users in admin panel")
        elif choice == "2":
            clear_screen()
            console.print("List of users:")
            for user in users:
                console.print(user["username"])
            username = Prompt.ask("Enter the username to activate/deactivate")
            try:
                user_manager.update_user(username, {"is_active": not user_manager.get_user(username)["is_active"]})
                console.print(f"User '{username}' new status: {user_manager.get_user(username)['is_active']}", style="success")
                logger.info(f"User '{username}' status changed to {user_manager.get_user(username)['is_active']} by admin")
            except Exception as e:
                console.print(f"An error occurred while updating the user: {e}", style="danger")
                logger.error(f"Error changing status of user '{username}': {e}")
        elif choice == "3":
            clear_screen()
            break
        else:
            console.print("Invalid option, please try again.", style="danger")
            logger.warning("Invalid option selected in admin panel")

def display_project_board(username):
    all_projects = project_manager.get_projects_for_user(username)
    all_tasks = []
    for project in all_projects:
        for status, tasks in project["tasks"].items():
            for task in tasks:
                if task["description"] == "":
                    task["description"] = "No description"
                task["project"] = project["title"]
                task["duration"] = str((datetime.strptime(task["end_date"], "%Y-%m-%d") - datetime.strptime(task["start_date"], "%Y-%m-%d")).days)
                all_tasks.append(task)
    if not all_tasks:
        console.print("No tasks found!", style="warning")
        logger.warning(f"No tasks found for user {username}")
        return
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Title")
    table.add_column("Description")
    table.add_column("Duration")
    table.add_column("Priority")
    table.add_column("Status")
    table.add_column("Project")
    for task in all_tasks:
        table.add_row(task["title"], task["description"], task["duration"], task["priority"], task["status"], task["project"])
    console.print(table)
    logger.info(f"Displayed project board for {username}")

def main():
    console.print("Welcome to the Trellomize app!", style="success")
    logger.info("Application started")
    while True:
        user_choice = Prompt.ask("Choose an option", choices=["login", "register", "exit"], default="login")
        is_admin = False
        user = None
        try:
            if user_choice == "login":
                username = Prompt.ask("Enter your username, or enter 'exit' to go back")
                if username == "exit":
                    clear_screen()
                    continue
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
                username = Prompt.ask("Choose a username, enter 'exit' to go back")
                if username == "exit":
                    clear_screen()
                    continue
                password = Prompt.ask("Choose a password", password=True)
                while len(password) < 8 or not any(char.isdigit() for char in password) or not any(char.isalpha() for char in password):
                    password = Prompt.ask("Password must be at least 8 characters long, please try again", password=True)
                email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                email = Prompt.ask("Enter your email")
                while not re.match(email_regex, email):
                    if Prompt.ask("Proceed with registration? (yes/no)", default="yes") == "no":
                        console.print("Registration canceled.", style="bold magenta")
                        logger.info("User canceled registration")
                        return
                    email = Prompt.ask("Enter a valid email")

                if user_manager.create_user(username=username, password=password, email=email):
                    clear_screen()
                    console.print("Registration successful!", style="info")
                    logger.info(f"User {username} registered successfully")
                    break
                else:
                    clear_screen()
                    console.print("Registration failed, please try again.", style="danger")
                    logger.warning(f"Registration attempt failed for user {username}")

            elif user_choice == "exit":
                clear_screen()
                console.print("Exiting the app. Goodbye!", style="bold magenta")
                logger.info("Application exited by user")
                return

        except Exception as e:
            clear_screen()
            console.print(f"An error occurred: {e}", style="danger")
            logger.error(f"Error during login/registration: {e}")

    main_menu(is_admin, user["username"] if user else None)


def main_menu(is_admin=False, current_user=None):
    clear_screen()
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
            menu_options.pop("0")
            menu_options["5"] = "Admin Settings"
            menu_options["0"] = "Log Out"
            
        for key, value in menu_options.items():
            console.print(f"[{key}] {value}")
        choice = Prompt.ask("Select an option", choices=menu_options.keys())
        clear_screen()
        try:
            if choice == "1":
                display_project_list(project_manager, current_user)
            elif choice == "2":
                create_new_project(current_user)
            elif choice == "3":
                profile_settings(current_user)
            elif choice == "4":
                display_project_board(current_user)
            elif choice == "5" and is_admin:
                admin_panel()
            elif choice == "0":
                console.print("Logging Out...", style="danger")
                logger.info(f"User {current_user} logged out")
                break
            else:
                console.print("Invalid option, please try again.", style="danger")
                logger.warning(f"Invalid option selected in main menu by {current_user}")
        except Exception as e:
            console.print(f"An error occurred in the menu: {e}", style="danger")
            logger.error(f"Error in main menu for user {current_user}: {e}")

if __name__ == "__main__":
    user_manager = UserManager()
    project_manager = ProjectManager()
    task_manager = TaskManager()
    main()
