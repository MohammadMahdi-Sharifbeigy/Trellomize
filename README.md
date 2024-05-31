
# Trellomize

Trellomize is a command-line project management tool inspired by Trello. It allows users to manage projects, tasks, and user accounts with a rich command-line interface using `rich`. The application includes user authentication, project management, task management, and an admin panel for managing user accounts.

## Features

- User authentication (login and registration)
- Project creation and management
- Task creation, assignment, and management within projects
- Comments on tasks
- Admin panel for user management
- Rich CLI interface with `rich` for enhanced user experience
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
    python main.py
    ```

## Usage
### Command-line Interface

Once the application starts, you will be prompted with options to login, register, or exit. After logging in, you can navigate through the main menu to manage projects, tasks, and your profile.

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

For more details on available commands, run:
```bash
python manager.py --help
```

## Running Tests

Unit tests are included for `UserManager`, `ProjectManager`, and `TaskManager` classes. To run the tests, use the following commands:

- For `UserManager` tests:
    ```bash
    python -m unittest discover -s tests -p 'test_user_manager.py'
    ```

- For `ProjectManager` tests:
    ```bash
    python -m unittest discover -s tests -p 'test_project_manager.py'
    ```

- For `TaskManager` tests:
    ```bash
    python -m unittest discover -s tests -p 'test_task_manager.py'
    ```

## File Structure

```plaintext
.
├── main.py                  # Main entry point of the application
├── manager.py               # Contains the UserManager, ProjectManager, and TaskManager classes
├── data.json                # JSON file for storing project and task data
├── users.json               # JSON file for storing user data
├── app.log                  # Log file for logging
├── requirements.txt         # Project dependencies
├── README.md                # This README file
├── LICENSE                  # License information
├── .gitignore               # Git ignore file
└── tests                    # Directory containing test files
    ├── test.py
    ├── test_user_manager.py
    ├── test_project_manager.py
    └── test_task_manager.py
```

## Dependencies

- `bcrypt` for password hashing
- `loguru` for logging
- `rich` for the command-line interface
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