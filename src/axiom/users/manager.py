"""
Axiom User Management Module
Handles secure user creation, expiry enforcement, connection limits, and revocation.
"""

import datetime
import logging
import os
import re
import secrets
import string
import subprocess
import tempfile

logger = logging.getLogger("AxiomUserManager")
USER_DB_PATH = "/root/usuarios.db"
TRIAL_DB_PATH = "/etc/VPSManager/trial_users.db"


class UserManager:
    def __init__(self, db_path: str = USER_DB_PATH, trial_db_path: str = TRIAL_DB_PATH):
        self.db_path = db_path
        self.trial_db_path = trial_db_path

    def generate_secure_password(self, length: int = 12) -> str:
        """Generates an alphanumeric password with high entropy."""
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def _atomic_write(self, target_path: str, content: str) -> None:
        """Atomically writes content to a file on the same filesystem."""
        target_dir = os.path.dirname(os.path.abspath(target_path)) or "."
        os.makedirs(target_dir, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(prefix=os.path.basename(target_path) + ".", dir=target_dir)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        if os.name != "nt":
            try:
                os.chmod(tmp_path, 0o644)
            except Exception:
                pass
        for attempt in range(5):
            try:
                os.replace(tmp_path, target_path)
                break
            except PermissionError:
                if attempt == 4:
                    raise
                import time

                time.sleep(0.02)

    def list_users(self) -> list[dict[str, str]]:
        """Returns a list of all active users with their connection limits."""
        users = []
        if not os.path.exists(self.db_path):
            return users

        with open(self.db_path, encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str or not re.match(r"^[a-zA-Z0-9_-]+\s+[0-9]+", line_str):
                    continue
                parts = line_str.split()
                if len(parts) >= 2:
                    username, limit = parts[0], parts[1]
                    users.append({"username": username, "limit": limit})
        return users

    def list_trial_users(self) -> list[dict[str, str]]:
        """Returns a list of all trial accounts from trial database."""
        trials = []
        if not os.path.exists(self.trial_db_path):
            return trials

        with open(self.trial_db_path, encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                parts = line_str.split()
                if len(parts) >= 3:
                    username, exp_epoch, limit = parts[0], parts[1], parts[2]
                    trials.append({"username": username, "expiration_epoch": exp_epoch, "limit": limit})
        return trials

    def get_user_info(self, username: str) -> dict[str, str] | None:
        """Retrieves comprehensive user information including limit, expiry, and status."""
        limit = None
        if os.path.exists(self.db_path):
            with open(self.db_path, encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if parts and parts[0] == username:
                        limit = parts[1] if len(parts) > 1 else "1"
                        break

        if limit is None and os.path.exists(self.trial_db_path):
            with open(self.trial_db_path, encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if parts and parts[0] == username:
                        limit = parts[2] if len(parts) > 2 else "1"
                        break

        if limit is None:
            return None

        expiry_date = "never"
        try:
            res = subprocess.run(
                ["chage", "-l", username],
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if "Account expires" in line:
                        exp_val = line.split(":", 1)[1].strip()
                        if exp_val and exp_val.lower() != "never":
                            expiry_date = exp_val
                        break
        except Exception:
            pass

        return {
            "username": username,
            "limit": limit,
            "expiry_date": expiry_date,
        }

    def create_user(
        self, username: str, password: str | None = None, days: int = 30, limit: int = 1
    ) -> dict[str, str]:
        """Creates a system user with nologin shell and an expiration date."""
        if not re.match(r"^[a-zA-Z0-9_-]{3,32}$", username):
            raise ValueError(f"Invalid username '{username}'. Must be 3-32 alphanumeric characters, dash or underscore.")
        if days < 1:
            raise ValueError("Validity days must be a positive integer.")
        if limit < 1 or limit > 999:
            raise ValueError("Connection limit must be between 1 and 999.")

        if not password:
            password = self.generate_secure_password()
        elif len(password) < 8:
            raise ValueError("Password must be at least 8 characters long.")

        expiry_date = (datetime.date.today() + datetime.timedelta(days=days)).strftime("%Y-%m-%d")

        # Create system user without home directory and with false shell for tunneling
        cmd_useradd = ["useradd", "-M", "-N", "-s", "/bin/false", "-e", expiry_date, username]
        subprocess.run(cmd_useradd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Set password using chpasswd (securely passing via stdin)
        p = subprocess.Popen(
            ["chpasswd"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        p.communicate(input=f"{username}:{password}")

        # Update user database atomically
        self._set_user_limit(username, limit)

        # OpenVPN client profile generation if easy-rsa is configured
        if os.path.isdir("/etc/openvpn/easy-rsa") and os.path.isfile("/etc/openvpn/client-common.txt"):
            try:
                subprocess.run(
                    ["./easyrsa", "build-client-full", username, "nopass"],
                    cwd="/etc/openvpn/easy-rsa",
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                ovpn_dest = f"/root/{username}.ovpn"
                with open("/etc/openvpn/client-common.txt", encoding="utf-8") as f_in, open(ovpn_dest, "w", encoding="utf-8") as f_out:
                    f_out.write(f_in.read() + "\n")
                    f_out.write("<ca>\n")
                    ca_path = "/etc/openvpn/easy-rsa/pki/ca.crt"
                    if os.path.exists(ca_path):
                        with open(ca_path, encoding="utf-8") as ca_f:
                            f_out.write(ca_f.read() + "\n")
                    f_out.write("</ca>\n<cert>\n")
                    crt_path = f"/etc/openvpn/easy-rsa/pki/issued/{username}.crt"
                    if os.path.exists(crt_path):
                        with open(crt_path, encoding="utf-8") as crt_f:
                            f_out.write(crt_f.read() + "\n")
                    f_out.write("</cert>\n<key>\n")
                    key_path = f"/etc/openvpn/easy-rsa/pki/private/{username}.key"
                    if os.path.exists(key_path):
                        with open(key_path, encoding="utf-8") as key_f:
                            f_out.write(key_f.read() + "\n")
                    f_out.write("</key>\n")
                os.chmod(ovpn_dest, 0o600)
            except Exception as e:
                logger.warning("Failed to generate OpenVPN profile for %s: %s", username, e)

        logger.info("Created user %s (valid for %d days, limit %d)", username, days, limit)
        return {"username": username, "password": password, "expiry_date": expiry_date, "limit": str(limit)}

    def create_trial_user(
        self, username: str | None = None, password: str | None = None, minutes: int = 60, limit: int = 1
    ) -> dict[str, str]:
        """Creates a temporary trial account with trial database isolation."""
        if not username:
            username = f"trial{secrets.randbelow(9000) + 1000}"

        if not re.match(r"^[a-zA-Z0-9_-]{3,32}$", username):
            raise ValueError(f"Invalid username '{username}'. Must be 3-32 alphanumeric characters, dash or underscore.")
        if minutes < 1:
            raise ValueError("Trial duration must be a positive integer.")
        if limit < 1 or limit > 999:
            raise ValueError("Connection limit must be between 1 and 999.")

        if not password:
            password = self.generate_secure_password(10)

        now_epoch = int(datetime.datetime.now(datetime.UTC).timestamp())
        exp_epoch = now_epoch + minutes * 60

        # Create system user
        cmd_useradd = ["useradd", "-M", "-N", "-s", "/bin/false", username]
        subprocess.run(cmd_useradd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Set password
        p = subprocess.Popen(
            ["chpasswd"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        p.communicate(input=f"{username}:{password}")

        # Update databases atomically
        self._set_user_limit(username, limit)
        self._set_trial_user(username, exp_epoch, limit)

        # Generate cleanup script for atd queueing if supported
        try:
            cleanup_dir = "/etc/VPSManager/userteste"
            os.makedirs(cleanup_dir, exist_ok=True)
            cleanup_script = os.path.join(cleanup_dir, f"{username}.sh")
            with open(cleanup_script, "w", encoding="utf-8") as f:
                f.write(
                    f"#!/usr/bin/env bash\n"
                    f"pkill -u {username} 2>/dev/null || true\n"
                    f"userdel -f {username} 2>/dev/null || true\n"
                    f"rm -f {cleanup_script}\n"
                )
            os.chmod(cleanup_script, 0o755)
            subprocess.run(
                ["at", f"now + {minutes} min"],
                input=cleanup_script,
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except Exception:
            pass

        logger.info("Created trial user %s (valid for %d minutes, limit %d)", username, minutes, limit)
        return {
            "username": username,
            "password": password,
            "expiration_epoch": str(exp_epoch),
            "duration_minutes": str(minutes),
            "limit": str(limit),
        }

    def change_password(self, username: str, new_password: str | None = None) -> str:
        """Changes user password silently via chpasswd and disconnects existing sessions."""
        if not re.match(r"^[a-zA-Z0-9_-]{3,32}$", username):
            raise ValueError(f"Invalid username '{username}'.")

        if not new_password:
            new_password = self.generate_secure_password()
        elif len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters long.")

        # Disconnect active sessions
        subprocess.run(["pkill", "-u", username], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

        # Apply password update
        p = subprocess.Popen(
            ["chpasswd"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        p.communicate(input=f"{username}:{new_password}")

        logger.info("Updated password for user %s", username)
        return new_password

    def change_limit(self, username: str, new_limit: int) -> bool:
        """Updates user connection limit in database."""
        if not re.match(r"^[a-zA-Z0-9_-]{3,32}$", username):
            raise ValueError(f"Invalid username '{username}'.")
        if new_limit < 1 or new_limit > 999:
            raise ValueError("Connection limit must be between 1 and 999.")

        self._set_user_limit(username, new_limit)

        # Synchronize trial database if present
        if os.path.exists(self.trial_db_path):
            trials = self.list_trial_users()
            for t in trials:
                if t["username"] == username:
                    self._set_trial_user(username, int(t["expiration_epoch"]), new_limit)
                    break

        logger.info("Updated connection limit for user %s to %d", username, new_limit)
        return True

    def change_expiration(self, username: str, days: int | None = None, date_str: str | None = None) -> str:
        """Modifies user expiration date using relative days or absolute YYYY-MM-DD string."""
        if not re.match(r"^[a-zA-Z0-9_-]{3,32}$", username):
            raise ValueError(f"Invalid username '{username}'.")

        if days is not None:
            if days < 1:
                raise ValueError("Days must be a positive integer.")
            target_date = (datetime.date.today() + datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        elif date_str is not None:
            try:
                datetime.date.fromisoformat(date_str)
                target_date = date_str
            except ValueError as err:
                raise ValueError(f"Invalid date format '{date_str}'. Expected YYYY-MM-DD.") from err
        else:
            raise ValueError("Must specify either days or date_str.")

        subprocess.run(
            ["chage", "-E", target_date, username],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info("Updated expiration for user %s to %s", username, target_date)
        return target_date

    def _check_system_user_protection(self, username: str) -> None:
        """Ensures system accounts (root or UID < 1000) are protected from accidental removal."""
        if username == "root":
            raise PermissionError("Cannot modify or delete root system user.")

        try:
            import pwd

            user_entry = pwd.getpwnam(username)
            if user_entry.pw_uid < 1000:
                raise PermissionError(f"Cannot delete protected system user '{username}' (UID: {user_entry.pw_uid}).")
        except PermissionError:
            raise
        except (ImportError, KeyError):
            # Fallback for platforms without pwd module or user not in local pwd
            uid = None
            try:
                res = subprocess.run(
                    ["id", "-u", username],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if res.returncode == 0:
                    uid = int(res.stdout.strip())
            except Exception:
                pass

            if uid is not None and uid < 1000:
                raise PermissionError(f"Cannot delete protected system user '{username}' (UID: {uid}).") from None

    def delete_user(self, username: str) -> bool:
        """Kills active sessions, revokes OpenVPN certs, and deletes user with system protection."""
        self._check_system_user_protection(username)

        try:
            # Terminate user processes
            subprocess.run(["pkill", "-u", username], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            # Delete system user
            subprocess.run(
                ["userdel", "-f", username], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

            # Revoke OpenVPN certificate if easy-rsa is configured
            if os.path.isdir("/etc/openvpn/easy-rsa"):
                try:
                    subprocess.run(
                        ["./easyrsa", "--batch", "revoke", username],
                        cwd="/etc/openvpn/easy-rsa",
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
                    subprocess.run(
                        ["./easyrsa", "gen-crl"],
                        cwd="/etc/openvpn/easy-rsa",
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
                    crl_src = "/etc/openvpn/easy-rsa/pki/crl.pem"
                    crl_dst = "/etc/openvpn/crl.pem"
                    if os.path.exists(crl_src):
                        with open(crl_src, "rb") as f_src, open(crl_dst, "wb") as f_dst:
                            f_dst.write(f_src.read())
                        os.chmod(crl_dst, 0o644)
                except Exception as e:
                    logger.warning("Failed to revoke OpenVPN cert for %s: %s", username, e)

            # Remove client profile and trial cleanup script
            for path in [f"/root/{username}.ovpn", f"/etc/VPSManager/userteste/{username}.sh"]:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass

            # Remove from databases
            self._remove_from_db(username)
            self._remove_from_trial_db(username)

            logger.info("Deleted user %s", username)
            return True
        except Exception as e:
            if isinstance(e, PermissionError):
                raise
            logger.error("Failed to delete user %s: %s", username, e)
            return False

    def purge_expired(self) -> list[str]:
        """Scans managed and trial databases and purges all expired user accounts."""
        purged = []
        now_dt = datetime.datetime.now(datetime.UTC)
        now_epoch = int(now_dt.timestamp())

        # Purge standard users
        for user_entry in self.list_users():
            username = user_entry["username"]
            info = self.get_user_info(username)
            if not info:
                continue
            exp_str = info.get("expiry_date", "never")
            if exp_str and exp_str.lower() != "never":
                try:
                    # Account expires at 23:59:59 of the given date
                    exp_date = datetime.datetime.strptime(exp_str, "%b %d, %Y")
                except ValueError:
                    try:
                        exp_date = datetime.datetime.strptime(exp_str, "%Y-%m-%d")
                    except ValueError:
                        exp_date = None

                if exp_date:
                    exp_date_end = exp_date.replace(hour=23, minute=59, second=59, tzinfo=datetime.UTC)
                    if now_dt > exp_date_end:
                        try:
                            if self.delete_user(username):
                                purged.append(username)
                        except Exception as err:
                            logger.error("Error deleting expired user %s: %s", username, err)

        # Purge trial users
        for trial in self.list_trial_users():
            username = trial["username"]
            if username in purged:
                continue
            try:
                exp_epoch = int(trial["expiration_epoch"])
                if now_epoch >= exp_epoch:
                    try:
                        if self.delete_user(username):
                            purged.append(username)
                    except Exception as err:
                        logger.error("Error deleting expired trial user %s: %s", username, err)
            except ValueError:
                continue

        # Reset expiration counter cache
        exp_cache = "/etc/VPSManager/Exp"
        if os.path.exists(os.path.dirname(exp_cache)):
            try:
                with open(exp_cache, "w", encoding="utf-8") as f:
                    f.write("0\n")
            except OSError:
                pass

        return purged

    def _set_user_limit(self, username: str, limit: int) -> None:
        lines = []
        if os.path.exists(self.db_path):
            with open(self.db_path, encoding="utf-8") as f:
                for line in f:
                    line_str = line.strip()
                    if line_str and not line_str.startswith(f"{username} "):
                        lines.append(line_str)
        lines.append(f"{username} {limit}")
        self._atomic_write(self.db_path, "\n".join(lines) + "\n")

    def _remove_from_db(self, username: str) -> None:
        if not os.path.exists(self.db_path):
            return
        with open(self.db_path, encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith(f"{username} ")]
        self._atomic_write(self.db_path, "\n".join(lines) + "\n" if lines else "")

    def _set_trial_user(self, username: str, exp_epoch: int, limit: int) -> None:
        lines = []
        if os.path.exists(self.trial_db_path):
            with open(self.trial_db_path, encoding="utf-8") as f:
                for line in f:
                    line_str = line.strip()
                    if line_str and not line_str.startswith(f"{username} "):
                        lines.append(line_str)
        lines.append(f"{username} {exp_epoch} {limit}")
        self._atomic_write(self.trial_db_path, "\n".join(lines) + "\n")

    def _remove_from_trial_db(self, username: str) -> None:
        if not os.path.exists(self.trial_db_path):
            return
        with open(self.trial_db_path, encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith(f"{username} ")]
        self._atomic_write(self.trial_db_path, "\n".join(lines) + "\n" if lines else "")
