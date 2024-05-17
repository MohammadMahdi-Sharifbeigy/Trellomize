from flask import Flask, render_template, request, redirect, url_for, session
import json
import bcrypt
import os
from manager import ProjectManager, TaskManager, UserManager
app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

def create_json_files():
    if not os.path.exists("users.json"):
        with open("users.json", "w") as f:
            json.dump({"users": []}, f)
    if not os.path.exists("data.json"):
        with open("data.json", "w") as f:
            json.dump({"projects": []}, f)

create_json_files()

def login_user(username, password):  # Rename the function to avoid conflict
    with open("users.json") as f:
        users = json.load(f)["users"]
    user = next((user for user in users if user["username"] == username), None)
    if not user or not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
        return False
    session["username"] = username
    return True, user

def logout():
    session.pop("username", None)

def is_logged_in():
    return "username" in session

def get_current_user():
    return session.get("username")

def create_new_project(current_user,title, start_date):
    try:
        project = project_manager.create_project(title, start_date, current_user)
        console.print(f"New project created successfully with Title: {project['title']}", style="success")
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

def add_task_to_board(project_title, task_title, description, duration, priority):
    status = "TODO"  # Default status for new tasks
    # Create and add the task using the task manager
    task_manager.add_task(project_title, task_title, description, duration, priority, status)

def move_task_on_board(project_title, task_title, new_status):
    try:
        task_manager.move_task(project_title, task_title, new_status)
    except ValueError as e:
        console.print(e, style="danger")

def delete_task_from_board(project_title, task_title):
    try:
        task_manager.delete_task(project_title, task_title)
    except ValueError as e:
        console.print(e, style="danger")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if login_user(username, password):  # Call the renamed function
            return redirect(url_for('projects'))
        else:
            return render_template('login.html', error='Invalid username or password')
    else:
        return render_template('login.html')

@app.route('/logout')
def logout_route():
    logout()
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        # Check if username already exists
        with open("users.json", "r") as f:
            users_data = json.load(f)
            usernames = [user['username'] for user in users_data['users']]
            if username in usernames:
                return render_template('signup.html', error="Username already exists")
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        # Save user data
        with open("users.json", "w") as f:
            user = {"username": username, "password": hashed_password, "email": email, "is_active": True, "is_admin": False}
            users_data['users'].append(user)
            json.dump(users_data, f, indent=4)
        session['username'] = username
        return redirect(url_for('projects'))
    else:
        return render_template('signup.html')

@app.route('/projects')
def projects():
    if is_logged_in():
        # Fetch projects from data.json
        with open("data.json", "r") as f:
            projects_data = json.load(f)["projects"]
        username = get_current_user()
        return render_template('projects.html', projects=projects_data, username=username)
    else:
        return redirect(url_for('login'))


@app.route('/profile')
def profile():
    if is_logged_in():
        username = get_current_user()
        user = user_manager.get_user(username)  # Fetch user info using the username
        if not user:
            # Handle case where user info is not found
            return "User not found", 404
        return render_template('profile.html', user=user)
    else:
        return redirect(url_for('login'))

@app.route('/profile/edit_password', methods=['GET', 'POST'])
def edit_password():
    if is_logged_in():
        if request.method == 'POST':
            username = get_current_user()
            new_password = request.form['new_password']
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            try:
                user_manager.update_user(username, {"password": hashed_password})
                return redirect(url_for('profile'))
            except Exception as e:
                return render_template('error.html', error=str(e))
        else:
            return render_template('edit_password.html')
    else:
        return redirect(url_for('login'))

@app.route('/profile/edit_email', methods=['GET', 'POST'])
def edit_email():
    if is_logged_in():
        if request.method == 'POST':
            username = get_current_user()
            new_email = request.form['new_email']
            try:
                user_manager.update_user(username, {"email": new_email})
                return redirect(url_for('profile'))
            except Exception as e:
                return render_template('error.html', error=str(e))
        else:
            return render_template('edit_email.html')
    else:
        return redirect(url_for('login'))

@app.route('/projects')
def list_projects():
    if is_logged_in():
        # Fetch projects from ProjectManager
        projects = project_manager.list_projects()
        return render_template('projects_list.html', projects=projects)
    else:
        return redirect(url_for('login'))
    
# Route to create a new project
@app.route('/projects/create', methods=['GET', 'POST'])
def create_project_route():
    if is_logged_in():
        if request.method == 'POST':
            title = request.form['title']
            start_date = request.form['start_date']
            # You can add validation and error handling here
            try:
                project_manager.create_project(title, start_date, get_current_user())
                return redirect(url_for('projects'))
            except Exception as e:
                return render_template('error.html', error=str(e))
        else:
            return render_template('create_project.html')
    else:
        return redirect(url_for('login'))

@app.route('/projects/<project_title>', methods=['GET', 'POST'])
def manage_tasks(project_title):
    if is_logged_in():
        project = project_manager.get_project(project_title)
        if not project:
            return render_template('error.html', error="Project not found")
        
        tasks = project["tasks"]
        
        if request.method == 'POST':
            if 'task_title' in request.form:
                task_title = request.form['task_title']
                description = request.form['description']
                duration = int(request.form['duration'])
                priority = request.form['priority']
                try:
                    add_task_to_board(project_title, task_title, description, duration, priority)
                    return redirect(url_for('manage_tasks', project_title=project_title))
                except Exception as e:
                    return render_template('error.html', error=str(e))
            elif 'task_title_move' in request.form:
                task_title_move = request.form['task_title_move']
                new_status = request.form['new_status']
                try:
                    move_task_on_board(project_title, task_title_move, new_status)
                    return redirect(url_for('manage_tasks', project_title=project_title))
                except Exception as e:
                    return render_template('error.html', error=str(e))
            elif 'task_title_delete' in request.form:
                task_title_delete = request.form['task_title_delete']
                try:
                    delete_task_from_board(project_title, task_title_delete)
                    return redirect(url_for('manage_tasks', project_title=project_title))
                except Exception as e:
                    return render_template('error.html', error=str(e))
            elif 'member_username' in request.form:
                member_username = request.form['member_username']
                try:
                    project_manager.add_member(project_title, member_username)
                    return redirect(url_for('manage_tasks', project_title=project_title))
                except Exception as e:
                    return render_template('error.html', error=str(e))
            elif 'remove_member_username' in request.form:
                remove_member_username = request.form['remove_member_username']
                try:
                    project_manager.remove_member_from_project(project_title, remove_member_username)
                    return redirect(url_for('manage_tasks', project_title=project_title))
                except Exception as e:
                    return render_template('error.html', error=str(e))
            elif 'task_title_assignee' in request.form:
                task_title_assignee = request.form['task_title_assignee']
                assignee_username = request.form['assignee_username']
                try:
                    task_manager.assign_member(project_title, task_title_assignee, assignee_username)
                    return redirect(url_for('manage_tasks', project_title=project_title))
                except Exception as e:
                    return render_template('error.html', error=str(e))
            elif 'task_title_remove_assignee' in request.form:
                task_title_remove_assignee = request.form['task_title_remove_assignee']
                assignee_username_remove = request.form['assignee_username_remove']
                try:
                    task_manager.remove_assignee_from_task(project_title, task_title_remove_assignee, assignee_username_remove)
                    return redirect(url_for('manage_tasks', project_title=project_title))
                except Exception as e:
                    return render_template('error.html', error=str(e))
            elif 'view_members' in request.form:
                # Handle view members option
                members = project_manager.get_members(project_title)
                return render_template('view_members.html', project_title=project_title, members=members)

        return render_template('manage_tasks.html', project_title=project_title, tasks=tasks)
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    user_manager = UserManager()
    project_manager = ProjectManager()
    task_manager = TaskManager()
    app.run(debug=True)