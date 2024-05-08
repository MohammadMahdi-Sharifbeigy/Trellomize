import json

import bcrypt
from rich.console import Console
from rich.prompt import Prompt
from rich.theme import Theme

from manager import UserManager

theme = Theme({"info": "bold blue", "warning": "bold yellow", "danger": "bold red", "success": "bold green"})
console = Console(theme=theme)

def login(username, password):
    with open("users.json") as f:
        users = json.load(f)["users"]

    for user in users:
        password = bcrypt.checkpw(
            password.encode("utf-8"), user["password"].encode("utf-8")
        )
        if user["username"] == username and password:
            return True
        else:
            return False

def main():
    console.print("Welcome to the Trellomize app!", style="bold green")

    while True:
        user_choice = Prompt.ask("Choose an option", choices=["login", "register", "exit"], default="login")

        try:
            if user_choice == "login":
                username = Prompt.ask("Enter your username")
                password = Prompt.ask("Enter your password", password=True)
                if login(username, password):
                    console.print(":white_check_mark:Login successful!", style="success")
                    break
                else:
                    console.print(":x:Login failed, please try again.", style="danger")
            elif user_choice == "register":
                username = Prompt.ask("Choose a username")
                password = Prompt.ask("Choose a password", password=True)
                user_manager = UserManager()
                if user_manager.create_user(username=username, password=password):
                    console.print("Registration successful!", style="bold blue")
                    break
                else:
                    console.print("Registration failed, please try again.", style="bold red")
            elif user_choice == "exit":
                console.print("Exiting the app. Goodbye!", style="bold magenta")
                return
        except Exception as e:
            console.print(f"An error occurred: {e}", style="bold red")

    # main_menu()

if __name__ == "__main__":
    main()