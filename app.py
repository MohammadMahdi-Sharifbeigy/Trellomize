from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import bcrypt
import os
from manager import ProjectManager, TaskManager, UserManager
import hashlib
import secrets

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

def generate_token():
    return secrets.token_urlsafe(16)

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

# def add_task_to_board(project_title, task_title, description, duration, priority, status):
#     task_manager.add_task(project_title, task_title, description, duration, priority, status)

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

def send_password_reset_email(email, token):
    """
    Sends a password reset email to the provided email address with a unique token.

    Args:
        email (str): The email address to send the password reset email to.
        token (str): The unique token to be included in the email for password reset.
    """

    subject = "Password Reset Request"
    body = f"""
    Dear user,

    You recently requested to reset your password for your account.

    Please click on the following link to reset your password:

    {url_for('reset_password', token=token, _external=True)}

    This link will expire in 24 hours.

    If you did not request a password reset, please ignore this email.

    Sincerely,
    The Task Management App Team
    """
    print(f"Sending password reset email to {email} with subject: {subject}")
    print(f"Email body: {body}")
    print("Note: This is a simulated email sending process for demonstration purposes only.")


# Routes
@app.route('/')
def index():
    return render_template('login_register.html')

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if login_user(username, password): 
            return redirect(url_for('projects'))
        else:
            return render_template('login_register.html', error='Invalid username or password')
    else:
        return render_template('login_register.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        with open("users.json") as f:
            users = json.load(f)["users"]
        
        user = next((user for user in users if user["email"] == email), None)
        if user:
            token = generate_token()
            user['reset_token'] = hashlib.sha256(token.encode()).hexdigest()
            with open("users.json", "w") as f:
                json.dump({"users": users}, f, indent=4)
            send_password_reset_email(user['email'], token)
            flash('An email has been sent with instructions to reset your password.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Email address not found.', 'error')
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    hashed_token = hashlib.sha256(token.encode()).hexdigest()
    with open("users.json") as f:
        users = json.load(f)["users"]
    
    user = next((user for user in users if user.get("reset_token") == hashed_token), None)
    if not user:
        flash('Invalid or expired token.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if password == confirm_password:
            user['password'] = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user['reset_token'] = None
            with open("users.json", "w") as f:
                json.dump({"users": users}, f, indent=4)
            flash('Your password has been reset successfully.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Passwords do not match.', 'error')
    return render_template('reset_password.html', token=token)

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
                return render_template('login_register.html', error="Username already exists")
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
        return render_template('login_register.html')


@app.route('/main_menu')
def main_menu():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    is_admin = session.get('is_admin', False)
    menu_options = {
        "1": "Project List",
        "2": "Create New Project",
        "3": "Profile Settings",
        "4": "Board",
        "0": "Log Out",
    }
    if is_admin:
        menu_options["5"] = "Admin Settings"
    
    return render_template('main_menu.html', menu_options=menu_options)

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
    
@app.route('/view_members/<project_title>')
def view_members(project_title):
    if 'username' not in session:
        return redirect(url_for('login'))

    members = project_manager.get_members(project_title)
    return render_template('view_members.html', project_title=project_title, members=members)

@app.route('/projects/<project_title>', methods=['GET', 'POST'])
def manage_tasks(project_title):
    if is_logged_in():
        project = project_manager.get_project(project_title)
        if not project:
            return render_template('error.html', error="Project not found")
        
        tasks = project["tasks"]
                        
        if request.method == 'POST':
            try:
                if 'task_title' in request.form:
                    task_title = request.form['task_title']
                    description = request.form['description']
                    duration = int(request.form['duration'])
                    priority = request.form['priority']
                    status = request.form['status']
                    task_manager.create_task(project_title, task_title, description, duration, priority, status)
                    flash('Task created successfully', 'success')
                    return redirect(url_for('manage_tasks', project_title=project_title))
                
                elif 'task_title_move' in request.form:
                    task_title_move = request.form['task_title_move']
                    new_status = request.form['new_status']
                    task_manager.move_task(project_title, task_title_move, new_status)
                    flash('Task moved successfully', 'success')
                    return redirect(url_for('manage_tasks', project_title=project_title))
                
                elif 'task_title_delete' in request.form:
                    task_title_delete = request.form['task_title_delete']
                    task_manager.delete_task(project_title, task_title_delete)
                    flash('Task deleted successfully', 'success')
                    return redirect(url_for('manage_tasks', project_title=project_title))
                
                elif 'member_username' in request.form:
                    member_username = request.form['member_username']
                    member_role = request.form['member_role']
                    project_manager.add_member_to_project(project_title, member_username, member_role)
                    flash('Member added successfully', 'success')
                    return redirect(url_for('manage_tasks', project_title=project_title))
                
                elif 'remove_member_username' in request.form:
                    remove_member_username = request.form['remove_member_username']
                    project_manager.remove_member_from_project(project_title, remove_member_username)
                    flash('Member removed successfully', 'success')
                    return redirect(url_for('manage_tasks', project_title=project_title))
                
                elif 'assign_task_title' in request.form:
                    assign_task_title = request.form['assign_task_title']
                    assignee_username = request.form['assignee_username']
                    task_manager.assign_task_to_member(project_title, assign_task_title, assignee_username)
                    flash('Member assigned to task successfully', 'success')
                    return redirect(url_for('manage_tasks', project_title=project_title))
                
                elif 'remove_assign_task_title' in request.form:
                    remove_assign_task_title = request.form['remove_assign_task_title']
                    remove_assignee_username = request.form['remove_assignee_username']
                    task_manager.remove_assignee_from_task(project_title, remove_assign_task_title, remove_assignee_username)
                    flash('Assignee removed from task successfully', 'success')
                    return redirect(url_for('manage_tasks', project_title=project_title))
                
                elif 'task_title_comment' in request.form:
                    task_title_comment = request.form['task_title_comment']
                    comment_text = request.form['comment_text']
                    # Assuming you have a function to add comments
                    task_manager.add_comment_to_task(project_title, task_title_comment, comment_text)
                    flash('Comment added successfully', 'success')
                    return redirect(url_for('manage_tasks', project_title=project_title))

                elif 'task_title_remove_comment' in request.form:
                    task_title_remove_comment = request.form['task_title_remove_comment']
                    comment_text_remove = request.form['comment_text_remove']
                    # Assuming you have a function to remove comments
                    task_manager.remove_comment_from_task(project_title, task_title_remove_comment, comment_text_remove)
                    flash('Comment removed successfully', 'success')
                    return redirect(url_for('manage_tasks', project_title=project_title))

                elif 'view_members' in request.form:
                    return view_members(project_title)
            
            except Exception as e:
                flash(f'An error occurred: {e}', 'danger')
        
        return render_template('manage_tasks.html', project_title=project_title, tasks=tasks)
    else:
        return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'username' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    users = []
    projects = []

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_user':
            username = request.form['username']
            password = request.form['password']
            role = request.form['role']
            try:
                user_manager.register(username, password, role)
                flash(f'User {username} added successfully')
            except Exception as e:
                flash(f'Error adding user: {e}')
        elif action == 'edit_user':
            username = request.form['username']
            new_role = request.form['role']
            try:
                user_manager.update_user_role(username, new_role)
                flash(f'User {username} role updated to {new_role}')
            except Exception as e:
                flash(f'Error updating user: {e}')
        elif action == 'delete_user':
            username = request.form['username']
            try:
                user_manager.delete_user(username)
                flash(f'User {username} deleted successfully')
            except Exception as e:
                flash(f'Error deleting user: {e}')

    users = user_manager.get_all_users()
    projects = project_manager.get_all_projects()
    return render_template('admin.html', users=users, projects=projects)

if __name__ == '__main__':
    user_manager = UserManager()
    project_manager = ProjectManager()
    task_manager = TaskManager()
    app.run(debug=True)
