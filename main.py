import json
import re
from datetime import datetime, timedelta

import bcrypt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
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

def logout():
    st.session_state.clear()
    st.session_state['page'] = 'login'
    st.rerun()

def display_project_list(current_user):
    user = user_manager.get_user(current_user)
    if user["is_admin"]:
        projects = project_manager.list_projects()
    else:
        projects = project_manager.get_projects_for_user(current_user)

    st.header("Project List")
    st.markdown("---")
    if projects:
        columns = ["Title", "Start Date"]
        rows = [[project["title"], project["start_date"]] for project in projects]
        df = pd.DataFrame(rows, columns=columns)
        st.table(df)
        for index, row in enumerate(rows):
            if st.button(f"Open {row[0]}", key=f"open_{index}"):
                st.session_state['current_project'] = row[0]
                st.session_state['page'] = 'project_detail'
                st.rerun()
    else:
        st.write("No projects available!")

    st.markdown("---")
    if st.button("Back to Main Menu"):
        st.session_state['page'] = 'main_menu'
        st.rerun()

def create_new_project(current_user):
    st.header("Create New Project")
    st.markdown("---")
    title = st.text_input("Enter the title of the new project")
    start_date = st.date_input("Enter the start date of the project")
    if st.button("Create"):
        handle_create_project(title, start_date.strftime("%d/%m/%Y"), current_user)

    st.markdown("---")
    if st.button("Back to Main Menu"):
        st.session_state['page'] = 'main_menu'
        st.rerun()

def handle_create_project(title, start_date, current_user):
    try:
        project = project_manager.create_project(title, start_date, current_user)
        st.success(f"New project created successfully with Title: {project['title']}")
        st.session_state['page'] = 'project_list'
        st.rerun()
    except Exception as e:
        st.error(f"Error creating project: {e}")

def profile_settings(username):
    user = user_manager.get_user(username)
    if not user:
        st.error("User not found!")
        return

    st.header("Edit your profile")
    st.markdown("---")
    password = st.text_input("New password", type="password")
    email = st.text_input("New email")
    if st.button("Update"):
        handle_update_profile(username, password, email)

    st.markdown("---")
    if st.button("Back to Main Menu"):
        st.session_state['page'] = 'main_menu'
        st.rerun()

def handle_update_profile(username, password, email):
    updates = {}
    if password:
        updates["password"] = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    if email:
        updates["email"] = email
    try:
        user_manager.update_user(username, updates)
        st.success("Profile updated successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Error updating profile: {e}")

def display_project(project_title):
    project = project_manager.get_project(project_title)

    if not project:
        st.error(f"Project '{project_title}' not found!")
        return

    st.header(f"Project: {project_title}")
    st.markdown("---")
    
    status_columns = {
        "TODO": [],
        "DOING": [],
        "DONE": [],
        "ARCHIVED": []
    }
    
    if "tasks" in project:
        for status, tasks in project["tasks"].items():
            for task in tasks:
                task_info = {
                    "title": task['title'],
                    "assignees": ", ".join(task.get('assignees', [])),
                    "priority": task['priority'],
                    "end_date": task['end_date'],
                    "status": status,
                    "description": task.get('description', '')
                }
                status_columns[status].append(task_info)
    else:
        st.write("")

    st.subheader("Task Distribution")
    statuses = list(status_columns.keys())
    task_counts = [len(tasks) for tasks in status_columns.values()]

    plt.style.use('dark_background')

    if sum(task_counts) == 0:
        st.write("No tasks available to display in the pie chart.")
    else:
        explode = [0.1 if status == "TODO" else 0.07 if status == "DOING" else 0.04 if status == "DONE" else 0.02 for status in statuses]
        colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99']

        def autopct_format(values):
            def my_format(pct):
                total = sum(values)
                val = int(round(pct*total/100.0))
                if val > 0:
                    return '{p:.1f}%'.format(p=pct)
                else:
                    return ''
            return my_format

        fig, ax = plt.subplots()
        wedges, texts, autotexts = ax.pie(task_counts, autopct=autopct_format(task_counts), startangle=90, explode=explode, colors=colors, shadow=True)

        legend = ax.legend(wedges, statuses, title="Statuses", bbox_to_anchor=(1, 0, 0.5, 1), loc="center left", facecolor='grey')
        legend.get_title().set_color('white')

        ax.axis('equal')
        st.pyplot(fig)
        
    st.markdown("---")

    total_tasks = sum(task_counts)
    completed_tasks = len(status_columns["DONE"]) + len(status_columns["ARCHIVED"])
    st.subheader("Overall Task Completion")
    st.progress(completed_tasks / total_tasks if total_tasks > 0 else 0)

    # Show task details with progress bars and colored labels
    columns = st.columns(len(status_columns))
    for idx, (status, tasks) in enumerate(status_columns.items()):
        with columns[idx]:
            st.subheader(status)
            st.progress(len(tasks) / total_tasks if total_tasks > 0 else 0)
            for task_info in tasks:
                with st.expander(task_info['title']):
                    st.write(f"**Priority:** {task_info['priority']}")
                    st.write(f"**Assignees:** {task_info['assignees']}")
                    st.write(f"**Due Date:** {task_info['end_date']}")
                    st.write(f"**Description:** {task_info['description']}")

                    new_status = st.selectbox(f"Move {task_info['title']} to", options=["TODO", "DOING", "DONE", "ARCHIVED"], index=["TODO", "DOING", "DONE", "ARCHIVED"].index(task_info['status']), key=f"move_{task_info['title']}")
                    if new_status != task_info['status']:
                        handle_move_task(project_title, task_info['title'], new_status)
                        
                    if st.button("Edit", key=f"edit_{task_info['title']}"):
                        st.session_state['current_task'] = task_info['title']
                        st.session_state['current_project'] = project_title
                        st.session_state['page'] = 'edit_task'
                        st.rerun()

                    if st.button("Delete", key=f"delete_{task_info['title']}"):
                        handle_delete_task(project_title, task_info['title'])

    st.sidebar.header("Project Actions")
    st.sidebar.markdown("---")
    if st.sidebar.button("Add Task", key="add_task"):
        st.session_state['page'] = 'add_task'
        st.session_state['current_project'] = project_title
        st.rerun()

    if st.sidebar.button("Manage Members", key="manage_members"):
        st.session_state['page'] = 'manage_members'
        st.session_state['current_project'] = project_title
        st.rerun()
        
    if st.sidebar.button("Manage Assignees", key="manage_assignees"):
        st.session_state['page'] = 'manage_assignees'
        st.session_state['current_project'] = project_title
        st.rerun()

    if st.sidebar.button("Back to Project List", key="back_to_project_list"):
        st.session_state['page'] = 'project_list'
        st.rerun()

def handle_move_task(project_title, task_title, new_status):
    try:
        task_manager.move_task(project_title, task_title, new_status)
        st.success(f"Task '{task_title}' moved to '{new_status}'")
        st.rerun()
    except Exception as e:
        st.error(f"Error moving task: {e}")

def add_task(project_title):
    st.header("Add Task")
    st.markdown("---")
    title = st.text_input("Task Title")
    description = st.text_input("Task Description")
    duration = st.number_input("Task Duration (days)", min_value=1)
    priority = st.selectbox("Priority", ["CRITICAL", "HIGH", "MEDIUM", "LOW"])
    status = st.selectbox("Status", ["TODO", "DOING", "DONE", "ARCHIVED"])
    if st.button("Add"):
        handle_add_task(project_title, title, description, duration, priority, status)

    st.markdown("---")
    if st.button("Back to Project"):
        st.session_state['page'] = 'project_detail'
        st.rerun()

def handle_add_task(project_title, title, description, duration, priority, status):
    try:
        task_manager.add_task(project_title, title, description, duration, priority, status)
        st.success(f"Task '{title}' added successfully")
        st.session_state['page'] = 'project_detail'
        st.rerun()
    except Exception as e:
        st.error(f"Error adding task: {e}")

def edit_task(project_title):
    st.header("Edit Task")
    st.markdown("---")
    task_title = st.session_state.get('current_task')
    task = task_manager.get_task(project_title, task_title)
    
    if not task:
        st.error("Task not found!")
        return

    new_title = st.text_input("New Title", value=task['title'])
    new_description = st.text_input("New Description", value=task.get('description', ''))
    new_end_date = st.date_input("New End Date", value=datetime.strptime(task['end_date'], "%Y-%m-%d"))
    new_priority = st.selectbox("Priority", ["CRITICAL", "HIGH", "MEDIUM", "LOW"], index=["CRITICAL", "HIGH", "MEDIUM", "LOW"].index(task['priority']))
    
    if st.button("Update"):
        handle_edit_task(project_title, task_title, new_title, new_description, new_end_date, new_priority)

    st.markdown("---")
    if st.button("Back to Project"):
        st.session_state['page'] = 'project_detail'
        st.rerun()

def handle_edit_task(project_title, task_title, new_title, new_description, new_end_date, new_priority):
    try:
        new_duration = (new_end_date - datetime.now().date()).days
        task_manager.edit_task(project_title, task_title, new_title, new_description, new_duration, new_priority)
        st.success(f"Task '{task_title}' updated successfully")
        st.session_state['page'] = 'project_detail'
        st.rerun()
    except Exception as e:
        st.error(f"Error updating task: {e}")

def delete_task(project_title):
    st.header("Delete Task")
    st.markdown("---")
    task_title = st.text_input("Task Title to Delete")
    if st.button("Delete"):
        handle_delete_task(project_title, task_title)

    st.markdown("---")
    if st.button("Back to Project"):
        st.session_state['page'] = 'project_detail'
        st.rerun()

def handle_delete_task(project_title, task_title):
    try:
        task_manager.delete_task(project_title, task_title)
        st.success(f"Task '{task_title}' deleted successfully")
        st.rerun()
    except Exception as e:
        st.error(f"Error deleting task: {e}")

def admin_panel():
    st.header("Admin Panel")
    st.markdown("---")
    users = user_manager.get_members()
    if not users:
        st.write("No users found!")
    else:
        columns = ["Username", "Email", "Is Active", "Is Admin"]
        rows = []
        for user in users:
            user_data = user_manager.get_user(user)
            rows.append([user_data["username"], user_data["email"], str(user_data["is_active"]), str(user_data["is_admin"])])
        df = pd.DataFrame(rows, columns=columns)
        st.table(df)

    user_options = [user_manager.get_user(user)["username"] for user in users]
    
    # Dropdown to select a user
    selected_user = st.selectbox("Select User", user_options)

    if selected_user:
        user_data = user_manager.get_user(selected_user)
        if user_data["is_active"]:
            if st.button(f"Deactivate {selected_user}"):
                handle_toggle_active(selected_user, False)
        else:
            if st.button(f"Activate {selected_user}"):
                handle_toggle_active(selected_user, True)

    st.markdown("---")
    if st.button("Back to Main Menu"):
        st.session_state['page'] = 'main_menu'
        st.rerun()

def handle_toggle_active(username, is_active):
    try:
        user_manager.update_user(username, {"is_active": is_active})
        st.success(f"User '{username}' {'activated' if is_active else 'deactivated'} successfully")
        st.rerun()
    except Exception as e:
        st.error(f"Error updating user status: {e}")

def login_dialog():
    st.title("Welcome to the Trellomize app!")
    st.header("Login")
    st.markdown("---")
    username = st.text_input("Enter your username")
    password = st.text_input("Enter your password", type="password")
    if st.button("Login"):
        success, user = login(username, password)
        if success:
            st.session_state['username'] = username
            st.session_state['current_user'] = username  # Set current user here
            st.session_state['is_admin'] = user["is_admin"]
            st.session_state['page'] = 'main_menu'
            st.rerun()
        else:
            st.error("Login failed, please try again.")
    if st.button("Register"):
        st.session_state['page'] = 'register'
        st.rerun()

def register_dialog():
    st.header("Register")
    st.markdown("---")
    username = st.text_input("Choose a username")
    password = st.text_input("Choose a password", type="password")
    email = st.text_input("Enter your email")
    if st.button("Register"):
        if len(username) == 0:
            st.error("Username cannot be empty!")
            return
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            st.error("Invalid email address!")
            return
        if len(password) < 8 or not any(char.isdigit() for char in password) or not any(char.isalpha() for char in password):
            st.error("Password must be at least 8 characters long and contain at least one letter and one number!")
            return
        if user_manager.get_user(username):
            st.error("Username already exists, please choose a different one.")
            return
        if user_manager.create_user(username=username, password=password, email=email):
            st.success("Registration successful!")
            st.session_state['page'] = 'login'
            st.rerun()
        else:
            st.error("Registration failed, please try again.")
    
    if st.button("Back to Login"):
        st.session_state['page'] = 'login'
        st.rerun()

def manage_members(project_title):
    project = project_manager.get_project(project_title)
    if not project:
        st.error(f"Project '{project_title}' not found!")
        return
    
    with open("users.json", "r") as f:
        users_data = json.load(f)
    all_users = [user["username"] for user in users_data["users"]]

    st.header(f"Manage Members for Project: {project_title}")
    st.markdown("---")
    members = project.get("members", [])
    admin_user = list(next((member for member in members if "owner" in member.values()), None).keys())[0]
    member_usernames = [list(member.keys())[0] for member in members]
    
    users_to_add = [username for username in all_users if username not in member_usernames]
    
    st.subheader("Current Members")
    rows = [[username, list(role.values())[0]] for username, role in zip(member_usernames, members)]
    columns = ["Username", "Role"]
    df = pd.DataFrame(rows, columns=columns)
    st.table(df)

    st.markdown("---")
    st.subheader("Add Member")
    if not users_to_add:
        st.write("No users available to add.")
    else:
        user_to_add = st.selectbox("Select User to Add", users_to_add)
        role_to_add = st.selectbox("Select Role", ["member", "editor", "admin"])
        if st.button("Add Member"):
            handle_add_member(project_title, user_to_add, role_to_add)

    member_columns = ["Username", "Role"]
    member_rows = [[list(member.keys())[0], list(member.values())[0]] for member in members]
    all_user_rows = [[user, ""] for user in all_users if user not in member_usernames]

    st.markdown("---")
    st.subheader("Remove Member")
    removable_members = [username for username in [list(member.keys())[0] for member in members] if username != admin_user]
    user_to_remove = st.selectbox("Select Member to Remove", removable_members)
    if st.button("Remove Member"):
        handle_remove_member(project_title, user_to_remove)

    st.markdown("---")
    if st.button("Back to Project"):
        st.session_state['page'] = 'project_detail'
        st.rerun()

def handle_add_member(project_title, username, role):
    try:
        project_manager.add_member(project_title, username, role, project_manager)
        st.success(f"User '{username}' added to project '{project_title}' successfully")
        st.rerun()
    except Exception as e:
        st.error(f"Error adding member to project: {e}")

def handle_remove_member(project_title, username):
    try:
        project_manager.remove_member_from_project(project_title, username)
        st.success(f"User '{username}' removed from project '{project_title}' successfully")
        st.rerun()
    except Exception as e:
        st.error(f"Error removing member from project: {e}")

def manage_assignees(project_title):
    st.header("Manage Assignees and Comments")
    st.markdown("---")

    project = project_manager.get_project(project_title)
    if not project:
        st.error(f"Project '{project_title}' not found!")
        return

    tasks_by_status = project.get("tasks", {})
    if not tasks_by_status:
        st.info("No tasks found in this project.")
        return

    all_tasks = []
    for status, tasks in tasks_by_status.items():
        for task in tasks:
            all_tasks.append((task["title"], status))

    if not all_tasks:
        st.info("No tasks available.")
        return

    selected_task_title = st.selectbox("Select Task", options=[task[0] for task in all_tasks])

    if st.button("Manage Assignees and Comments for Selected Task"):
        st.session_state['selected_task'] = selected_task_title
        st.rerun()
    
    if st.button("Back to Project Detail"):
        st.session_state['page'] = 'project_detail'
        st.session_state['current_project'] = project_title
        st.rerun()

    if 'selected_task' in st.session_state:
        selected_task_title = st.session_state['selected_task']
        for task_title, status in all_tasks:
            if task_title == selected_task_title:
                manage_assignees_for_task(project_title, selected_task_title, status)

def manage_assignees_for_task(project_title, task_title, status):
    st.header(f"Manage Assignees and Comments for Task: {task_title}")
    st.markdown("---")

    project = project_manager.get_project(project_title)
    if not project:
        st.error(f"Project '{project_title}' not found!")
        return

    tasks_by_status = project.get("tasks", {})
    tasks = tasks_by_status.get(status, [])

    task = next((t for t in tasks if t["title"] == task_title), None)
    if not task or not isinstance(task, dict):
        st.error(f"Task '{task_title}' data is corrupted or invalid!")
        return

    st.subheader("Manage Assignees")
    st.markdown("---")
    assignees = task.get("assignees", [])
    project_members = [member for member_dict in project.get("members", []) for member in member_dict.keys()]

    new_assignee = st.selectbox("Select Assignee", options=project_members)

    if st.button("Add Assignee"):
        task_manager.assignee_member(project_title, task_title, new_assignee)
        st.rerun()

    if assignees:
        st.subheader("Current Assignees")
        for assignee in assignees:
            if st.button(f"Remove {assignee}"):
                task_manager.remove_assignee(project_title, task_title, assignee)
                st.rerun()

    st.subheader("Manage Comments")
    st.markdown("---")
    comments = task.get("comments", [])

    new_comment = st.text_area("New Comment")
    current_user = st.session_state.get('username', 'Anonymous')

    if st.button("Add Comment"):
        task_manager.add_comment(project_title, task_title, new_comment, current_user)
        st.rerun()

    if comments:
        for i, comment in enumerate(comments):
            st.markdown(f"**Comment {i + 1} by {comment['author']} on {datetime.strptime(comment['timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%B %d, %Y %H:%M:%S')}**")
            col1, col2, col3 = st.columns([6, 1, 1])
            with col1:
                st.write(f"{comment['comment']}")
            with col2:
                if st.button("Edit", key=f"edit_comment_{i}"):
                    new_comment_text = st.text_area(f"Edit Comment {i + 1}", value=comment['comment'], key=f"new_comment_text_{i}")
                    if st.button(f"Save", key=f"save_comment_{i}"):
                        task_manager.edit_comment(project_title, task_title, i, new_comment_text)
                        st.rerun()
            with col3:
                if st.button("Delete", key=f"delete_comment_{i}"):
                    task_manager.delete_comment(project_title, task_title, i)
                    st.rerun()

    st.markdown("---")
    if st.button("Back to Task Selection"):
        del st.session_state['selected_task']
        st.rerun()

def main_menu():
    st.header("Main Menu")
    st.markdown("---")
    if st.button("Project List"):
        st.session_state['page'] = 'project_list'
        st.rerun()
    if st.button("Create New Project"):
        st.session_state['page'] = 'create_project'
        st.rerun()
    if st.button("Profile Settings"):
        st.session_state['page'] = 'profile_settings'
        st.rerun()
    if st.session_state.get('is_admin', False):
        if st.button("Admin Panel"):
            st.session_state['page'] = 'admin_panel'
            st.rerun()
    if st.button("Log Out"):
        logout()

def main():
    if 'page' not in st.session_state:
        st.session_state['page'] = 'login'
    if st.session_state['page'] == 'login':
        login_dialog()
    elif st.session_state['page'] == 'register':
        register_dialog()
    elif st.session_state['page'] == 'main_menu':
        main_menu()
    elif st.session_state['page'] == 'project_list':
        display_project_list(st.session_state['username'])
    elif st.session_state['page'] == 'project_detail':
        display_project(st.session_state['current_project'])
    elif st.session_state['page'] == 'create_project':
        create_new_project(st.session_state['username'])
    elif st.session_state['page'] == 'add_task':
        add_task(st.session_state['current_project'])
    elif st.session_state['page'] == 'edit_task':
        edit_task(st.session_state['current_project'])
    elif st.session_state['page'] == 'move_task':
        move_task(st.session_state['current_project'])
    elif st.session_state['page'] == 'delete_task':
        delete_task(st.session_state['current_project'])
    elif st.session_state['page'] == 'profile_settings':
        profile_settings(st.session_state['username'])
    elif st.session_state['page'] == 'admin_panel':
        admin_panel()
    elif st.session_state['page'] == 'manage_members':
        manage_members(st.session_state['current_project'])
    elif st.session_state['page'] == 'manage_assignees':
        project_title = st.session_state.get('current_project')
        if project_title:
            manage_assignees(project_title)
        else:
            st.session_state['page'] = 'project_list'
            st.rerun()

if __name__ == "__main__":
    main()
