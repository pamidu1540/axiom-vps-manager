"""
Axiom User Management Module
Handles secure user creation, expiry enforcement, connection limits, and revocation.
"""
import os
import subprocess
import datetime
import secrets
import string
import logging
from typing import List, Dict, Optional

logger = logging.getLogger("AxiomUserManager")
USER_DB_PATH = "/root/usuarios.db"


class UserManager:
    def __init__(self, db_path: str = USER_DB_PATH):
        self.db_path = db_path

    def generate_secure_password(self, length: int = 12) -> str:
        """Generates an alphanumeric password with high entropy."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def list_users(self) -> List[Dict[str, str]]:
        """Returns a list of all active users with their connection limits and expiry."""
        users = []
        if not os.path.exists(self.db_path):
            return users

        with open(self.db_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    username, limit = parts[0], parts[1]
                    users.append({
                        "username": username,
                        "limit": limit
                    })
        return users

    def create_user(self, username: str, password: Optional[str] = None, days: int = 30, limit: int = 1) -> Dict[str, str]:
        """Creates a system user with nologin shell and an expiration date."""
        if not password:
            password = self.generate_secure_password()

        expiry_date = (datetime.date.today() + datetime.timedelta(days=days)).strftime("%Y-%m-%d")

        # Create system user without home directory and with false shell for tunneling
        cmd_useradd = [
            "useradd", "-M", "-N", "-s", "/bin/false",
            "-e", expiry_date, username
        ]
        subprocess.run(cmd_useradd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Set password using chpasswd (securely passing via stdin)
        p = subprocess.Popen(["chpasswd"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        p.communicate(input=f"{username}:{password}")

        # Update user database
        self._set_user_limit(username, limit)

        logger.info("Created user %s (valid for %d days, limit %d)", username, days, limit)
        return {
            "username": username,
            "password": password,
            "expiry_date": expiry_date,
            "limit": str(limit)
        }

    def delete_user(self, username: str) -> bool:
        """Kills active sessions and deletes the specified user."""
        try:
            # Terminate user processes
            subprocess.run(["pkill", "-u", username], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Delete user
            subprocess.run(["userdel", "-f", username], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Remove from database
            self._remove_from_db(username)
            logger.info("Deleted user %s", username)
            return True
        except Exception as e:
            logger.error("Failed to delete user %s: %s", username, e)
            return False

    def _set_user_limit(self, username: str, limit: int):
        lines = []
        if os.path.exists(self.db_path):
            with open(self.db_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if not line.strip().startswith(f"{username} ")]
        lines.append(f"{username} {limit}")
        with open(self.db_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    def _remove_from_db(self, username: str):
        if not os.path.exists(self.db_path):
            return
        with open(self.db_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if not line.strip().startswith(f"{username} ")]
        with open(self.db_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n" if lines else "")
