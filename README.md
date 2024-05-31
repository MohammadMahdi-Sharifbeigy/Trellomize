
# Trellomize App

Trellomize is a project management tool inspired by Trello. This branch uses Streamlit for the graphical user interface (GUI). It allows users to manage projects, tasks, and user accounts with an interactive web-based interface. The application includes user authentication, project management, task management, and an admin panel for managing user accounts.

## Features

- User authentication (login and registration)
- Project creation and management
- Task creation, assignment, and management within projects
- Comments on tasks
- Admin panel for user management
- Interactive GUI with Streamlit
- Visualization of task distribution using Matplotlib
- Logging with `loguru`

## Installation

1. **Clone the Repository:**

   ```sh
    git clone https://github.com/MohammadMahdi-Sharifbeigy/Trellomize.git
    cd Trellomize
   ```

2. **Create and Activate a Virtual Environment:**

   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

4. **Run the Application:**

   ```sh
   streamlit run main.py
   ```

## Usage

### User Authentication

- **Login:** Enter your username and password to log in.
- **Register:** Create a new account with a unique username, password, and email.

### Main Menu

- **Project List:** View the list of projects you have access to.
- **Create New Project:** Create a new project by providing a title and start date.
- **Profile Settings:** Update your password and email.
- **Admin Panel:** Manage user accounts (for admin users).
- **Log Out:** Log out from the application.

### Project Management

- **View Project List:** See all projects available to you.
- **Create New Project:** Add a new project with a title and start date.
- **View Project Details:** See detailed information about a project, including tasks.
- **Add Task:** Add a new task to the project with details like title, description, duration, priority, and status.
- **Edit Task:** Update task details.
- **Move Task:** Change the status of a task (TODO, DOING, DONE, ARCHIVED).
- **Delete Task:** Remove a task from the project.
- **Manage Members:** Add or remove members from the project.
- **Manage Assignees and Comments:** Assign members to tasks and manage task comments.

### Admin Panel

- **User Management:** View all user accounts, activate/deactivate users, and manage their roles.

## Command Line Interface (CLI)

In addition to the web interface, the Trellomize App includes a CLI for managing administrative tasks.

### Usage

To use the CLI, run the `manager.py` script with the desired command and options. For example:

- Create a new user:
```sh
python manager.py create-user --username <username> --password <password> --is_active <true/false> --email <email>
```
- Create a new project:
```sh
python manager.py create-project --title <project_title> --start_date <dd/mm/yyyy>
```
- Purge all data:
```sh
python manager.py purge-data
```
For more details on available commands, run:
```sh
python manager.py --help
```
## File Structure
```
.
├── main.py                  # Main entry point of the application (Streamlit GUI)
├── manager.py               # Contains the UserManager, ProjectManager, and TaskManager classes
├── requirements.txt         # Project dependencies
├── LICENSE                  # License information
├── .gitignore               # Git ignore file
└── README.md                # This README file
```

## Dependencies

- `bcrypt` for password hashing
- `loguru` for logging
- `streamlit` for the graphical user interface
- `matplotlib` for task distribution visualization
- `argparse` for command-line argument parsing
- `json` for data storage and manipulation

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing
Contributions are welcome! Please fork the repository and create a pull request with your changes.

## Author

- [Mohammad Mahdi Sharifbeigy](https://github.com/MohammadMahdi-Sharifbeigy)
- [Yousof Shahrabi](https://github.com/yousofs)

---

**Note:** Ensure that the `users.json` and `data.json` files are present in the project directory to store user and project data. If these files do not exist, they will be created automatically when the application is run.