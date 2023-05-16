import random
from hashlib import sha256
from pathlib import Path
from typing import List, Dict, Tuple
from string import ascii_letters

import typer
import toml

app = typer.Typer()

SECRETS_BASE_PATH: Path = Path("./.streamlit/secrets.toml")


def _read_toml(path: Path) -> Dict:
    """Reads the `secrets.toml` file.

    :param path: Path of the file.
    :return: Parsed TOML file.
    """
    with open(path) as file:
        data = toml.load(file)
    return data


def _write_toml(data: Dict, path: Path) -> None:
    """Writes the new data on the `secrets.toml` file.

    :param data: Data to write on the file.
    :param path: Path to the file.
    """
    with open(path, "w") as file:
        toml.dump(data, file)


def _generate_random_password() -> Tuple[str, str]:
    """Generates a random password and the corresponding hash.

    :return: Random password and hash.
    """
    # Generates a random password of 16 chars.
    password: str = "".join(random.choice(ascii_letters) for _ in range(16))
    # Generates the password hash
    password_hash: str = sha256(password.encode("utf-8")).hexdigest()
    return password, password_hash


@app.command()
def add_user(
    username: str, roles: List[str], secrets: Path = SECRETS_BASE_PATH
) -> None:
    """Adds a user with a random password.

    :param username: Username to add.
    :param roles: Roles that the user will have to have
    :param secrets: Path to the `secrets.toml` file.
    """
    # Checks the validity of the file
    assert secrets.is_file(), "Invalid `secrets.toml` path provided."
    # Generates a new password for the user.
    password, password_hash = _generate_random_password()
    # Reads the file
    data = _read_toml(secrets)
    # Checks that the user is not in the dataset
    assert username not in data["credentials"], "User already inserted"
    # Adds the user with password to the data
    data["credentials"][username] = password_hash
    # Adds the user roles to the data
    data["roles"][username] = roles
    # Prints the password to the user
    typer.echo(password)
    # Wtites the data
    _write_toml(data, secrets)


@app.command()
def reset_password(username: str, secrets: Path = SECRETS_BASE_PATH) -> None:
    """Resets the password for a user.

    :param username: Username to reset the password of.
    :param secrets: Path to the `secrets.toml` file.
    """
    # Checks the validity of the file
    assert secrets.is_file(), "Invalid `secrets.toml` path provided."
    # Generates a new password for the user
    password, password_hash = _generate_random_password()
    # Reads the file
    data = _read_toml(secrets)
    # Checks that the user is present in the data
    assert username in data["credentials"], "User not found."
    # Sets the new password
    data["credentials"][username] = password_hash
    # Prints the password to the user
    typer.echo(password)
    # Writes the data
    _write_toml(data, secrets)


if __name__ == '__main__':
    app()