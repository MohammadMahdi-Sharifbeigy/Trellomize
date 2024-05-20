import json
import os
import re
from datetime import date, datetime, timedelta

import bcrypt
import streamlit as st
from manager import ProjectManager, TaskManager, UserManager

user_manager = UserManager()
project_manager = ProjectManager()
task_manager = TaskManager()

def login(username, password):
    with open("users.json") as f:
        users = json.load(f)["users"]
    user = next((user for user in users if user["username"] == username), None)
    if not user:
        return False, None
    if not user["is_active"]:
        return False, None

    password_matches = bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8"))
    if password_matches:
        return True, user
    else:
        return False, None

def display_project_list(current_user):
    user = user_manager.get_user(current_user)
    if user["is_admin"]:
        projects = project_manager.list_projects()
    else:
        projects = project_manager.get_projects_for_user(current_user)

    st.write(f"Projects for user {current_user}: {projects}")  # Debugging line

    st.header("Project List")
    if projects:
        columns = ["Title", "Start Date"]
        rows = [[project["title"], project["start_date"]] for project in projects]
        
        st.write(f"Table columns: {columns}, rows: {rows}")  # Debugging line

        for row in rows:
            st.write(f"**Title**: {row[0]}, **Start Date**: {row[1]}")
            if st.button(f"Open {row[0]}"):
                st.session_state['current_project'] = row[0]
                st.session_state['page'] = 'project_detail'
    else:
        st.write("No projects available!")

def create_new_project(current_user):
    st.header("Create New Project")
    title = st.text_input("Enter the title of the new project")
    start_date = st.date_input("Enter the start date of the project")
    if st.button("Create"):
        handle_create_project(title, start_date.strftime("%d/%m/%Y"), current_user)

def handle_create_project(title, start_date, current_user):
    try:
        project = project_manager.create_project(title, start_date, current_user)
        st.success(f"New project created successfully with Title: {project['title']}")
    except Exception as e:
        st.error(f"Error creating project: {e}")

def profile_settings(username):
    user = user_manager.get_user(username)
    if not user:
        st.error("User not found!")
        return

    st.header("Edit your profile")
    password = st.text_input("New password", type="password")
    email = st.text_input("New email")
    if st.button("Update"):
        handle_update_profile(username, password, email)

def handle_update_profile(username, password, email):
    updates = {}
    if password:
        updates["password"] = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    if email:
        updates["email"] = email
    try:
        user_manager.update_user(username, updates)
        st.success("Profile updated successfully!")
    except Exception as e:
        st.error(f"Error updating profile: {e}")

def display_project(project_title):
    project = project_manager.get_project(project_title)
    if not project:
        st.error(f"Project '{project_title}' not found!")
        return

    st.header(f"Project: {project_title}")
    if st.button("Add Task"):
        st.session_state['page'] = 'add_task'
        st.session_state['current_project'] = project_title

    columns = ["Title", "Assignee", "Priority", "Due Date"]
    rows = []
    for status, task_list in project["tasks"].items():
        for task in task_list:
            assignees = ", ".join(task.get("assignees", []))
            rows.append([task["title"], assignees, task["priority"], task["end_date"]])

    st.table(rows)

    if st.button("Edit Task"):
        st.session_state['page'] = 'edit_task'
        st.session_state['current_project'] = project_title
    if st.button("Move Task"):
        st.session_state['page'] = 'move_task'
        st.session_state['current_project'] = project_title
    if st.button("Delete Task"):
        st.session_state['page'] = 'delete_task'
        st.session_state['current_project'] = project_title

def add_task(project_title):
    st.header("Add Task")
    title = st.text_input("Task Title")
    description = st.text_input("Task Description")
    duration = st.number_input("Task Duration (days)", min_value=1)
    priority = st.selectbox("Priority", ["CRITICAL", "HIGH", "MEDIUM", "LOW"])
    if st.button("Add"):
        handle_add_task(project_title, title, description, duration, priority)

def handle_add_task(project_title, title, description, duration, priority):
    try:
        task_manager.add_task(project_title, title, description, duration, priority)
        st.success(f"Task '{title}' added successfully")
        st.session_state['page'] = 'project_detail'
    except Exception as e:
        st.error(f"Error adding task: {e}")

def edit_task(project_title):
    st.header("Edit Task")
    task_title = st.text_input("Task Title to Edit")
    new_title = st.text_input("New Title (optional)")
    new_description = st.text_input("New Description (optional)")
    new_duration = st.number_input("New Duration (days, optional)", min_value=1)
    new_priority = st.selectbox("Priority", ["CRITICAL", "HIGH", "MEDIUM", "LOW"])
    if st.button("Update"):
        handle_edit_task(project_title, task_title, new_title, new_description, new_duration, new_priority)

def handle_edit_task(project_title, task_title, new_title, new_description, new_duration, new_priority):
    try:
        task_manager.edit_task(project_title, task_title, new_title, new_description, new_duration, new_priority)
        st.success(f"Task '{task_title}' updated successfully")
        st.session_state['page'] = 'project_detail'
    except Exception as e:
        st.error(f"Error updating task: {e}")

def move_task(project_title):
    st.header("Move Task")
    task_title = st.text_input("Task Title to Move")
    new_status = st.selectbox("New Status", ["TODO", "DOING", "DONE", "ARCHIVED"])
    if st.button("Move"):
        handle_move_task(project_title, task_title, new_status)

def handle_move_task(project_title, task_title, new_status):
    try:
        task_manager.move_task(project_title, task_title, new_status)
        st.success(f"Task '{task_title}' moved to '{new_status}'")
        st.session_state['page'] = 'project_detail'
    except Exception as e:
        st.error(f"Error moving task: {e}")

def delete_task(project_title):
    st.header("Delete Task")
    task_title = st.text_input("Task Title to Delete")
    if st.button("Delete"):
        handle_delete_task(project_title, task_title)

def handle_delete_task(project_title, task_title):
    try:
        task_manager.delete_task(project_title, task_title)
        st.success(f"Task '{task_title}' deleted successfully")
        st.session_state['page'] = 'project_detail'
    except Exception as e:
        st.error(f"Error deleting task: {e}")

def admin_panel():
    st.header("Admin Panel")
    users = user_manager.get_members()
    if not users:
        st.write("No users found!")
    else:
        columns = ["Username", "Email", "Is Active", "Is Admin"]
        rows = []
        for user in users:
            user_data = user_manager.get_user(user)
            rows.append([user_data["username"], user_data["email"], str(user_data["is_active"]), str(user_data["is_admin"])])
        st.table(rows)

def main():
    st.title("Welcome to the Trellomize app!")
    if 'page' not in st.session_state:
        st.session_state['page'] = 'login'
    if st.session_state['page'] == 'login':
        login_dialog()
    elif st.session_state['page'] == 'register':
        register_dialog()
    elif st.session_state['page'] == 'main_menu':
        main_menu()
    elif st.session_state['page'] == 'project_detail':
        display_project(st.session_state['current_project'])
    elif st.session_state['page'] == 'add_task':
        add_task(st.session_state['current_project'])
    elif st.session_state['page'] == 'edit_task':
        edit_task(st.session_state['current_project'])
    elif st.session_state['page'] == 'move_task':
        move_task(st.session_state['current_project'])
    elif st.session_state['page'] == 'delete_task':
        delete_task(st.session_state['current_project'])

def login_dialog():
    st.header("Login")
    username = st.text_input("Enter your username")
    password = st.text_input("Enter your password", type="password")
    if st.button("Login"):
        success, user = login(username, password)
        if success:
            st.session_state['username'] = username
            st.session_state['is_admin'] = user["is_admin"]
            st.session_state['page'] = 'main_menu'
        else:
            st.error("Login failed, please try again.")
    if st.button("Register"):
        st.session_state['page'] = 'register'

def register_dialog():
    st.header("Register")
    username = st.text_input("Choose a username")
    password = st.text_input("Choose a password", type="password")
    email = st.text_input("Enter your email")
    if st.button("Register"):
        if user_manager.create_user(username=username, password=password, email=email):
            st.success("Registration successful!")
            st.session_state['page'] = 'login'
        else:
            st.error("Registration failed, please try again.")

def main_menu():
    st.header("Main Menu")
    st.button("Project List", on_click=lambda: st.session_state.update({'page': 'project_list'}))
    st.button("Create New Project", on_click=lambda: st.session_state.update({'page': 'create_project'}))
    st.button("Profile Settings", on_click=lambda: st.session_state.update({'page': 'profile_settings'}))
    if st.session_state.get('is_admin', False):
        st.button("Admin Panel", on_click=lambda: st.session_state.update({'page': 'admin_panel'}))
    st.button("Log Out", on_click=lambda: st.session_state.update({'page': 'login'}))

if __name__ == "__main__":
    main()

