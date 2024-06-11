# Trellomize (Flask)

Trellomize Flask is a web-based project management tool inspired by Trello, built with Flask. It allows users to manage projects, tasks, and user accounts through a web interface. The application includes user authentication, project management, task management, and an admin panel for managing user accounts.

## Features

- User authentication (login and registration)
- Project creation and management
- Task creation, assignment, and management within projects
- Comments on tasks
- Admin panel for user management
- Web-based interface with `Flask` for enhanced user experience
- Logging with `loguru`

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/MohammadMahdi-Sharifbeigy/Trellomize.git
   cd Trellomize
   ```
2. Create and Activate a Virtual Environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install Dependencies:

   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:

   ```bash
   python app.py
   ```

## Usage

### Web Interface

Once the application starts, navigate to http://127.0.0.1:5000 in your web browser. You will be prompted with options to login, register, or explore as a guest. After logging in, you can navigate through the dashboard to manage projects, tasks, and your profile.

### Admin Commands

You can also use command-line arguments for administrative tasks such as creating users and projects:

- Create a new user:

  ```bash
  python manager.py create-user --username <username> --password <password> --is_active <true/false> --email <email>
  ```
- Create a new project:

  ```bash
  python manager.py create-project --title <project_title> --start_date <dd/mm/yyyy>
  ```
- Purge all data:

  ```bash
  python manager.py purge-data
  ```
- For more details on available commands, run:

  ```bash
  python manager.py --help
  ```

## File Structure

```plaintext
.
├── static
│   └── styles.css             # CSS file for styling the web interface
├── templates                  # HTML templates for the Flask application
│   ├── admin.html
│   ├── create_project.html
│   ├── edit_email.html
│   ├── edit_password.html
│   ├── error.html
│   ├── forgot_password.html
│   ├── login_register.html
│   ├── main_menu.html
│   ├── manage_tasks.html
│   ├── profile.html
│   ├── projects_list.html
│   ├── projects.html
│   ├── reset_password.html
│   └── view_members.html
├── app.py                     # Main entry point of the Flask application
├── manager.py                 # Contains the UserManager, ProjectManager, and TaskManager classes
├── data.json                  # JSON file for storing project and task data
├── users.json                 # JSON file for storing user data
├── app.log                    # Log file for logging
├── requirements.txt           # Project dependencies
├── LICENSE                    # License information
├── .gitignore                 # Git ignore file
└── README.md                  # This README file
```

## Dependencies

- `bcrypt` for password hashing
- `loguru` for logging
- `flask` for the web framework
- `argparse` for command-line argument parsing
- `json` for data storage and manipulation

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes.

## Authors

- [Mohammad Mahdi Sharifbeigy](https://github.com/MohammadMahdi-Sharifbeigy)
- [Yousof Shahrabi](https://github.com/yousofs)

---

**Note:** Ensure that the `users.json` and `data.json` files are present in the project directory to store user and project data. If these files do not exist, they will be created automatically when the application is run.
