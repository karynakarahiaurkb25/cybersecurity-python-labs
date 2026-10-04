import hashlib
import hmac
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import ClassVar

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

PBKDF2_ITERATIONS: int = 100_000
SESSION_TIMEOUT_SEC: int = 900
EMAIL_REGEX: re.Pattern = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{2,63}@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

class User:
    def __init__(self, username: str, email: str, role: str = "user", active: bool = True):
        self.username = username
        self.role = role
        self.active = active
        self.__password_hash: bytes = b""
        self.__password_salt: bytes = b""
        self.email = email

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        if not isinstance(value, str) or not EMAIL_REGEX.match(value):
            raise ValueError(f"Некоректний формат email: '{value}'")
        self._email = value

    def set_password(self, password: str) -> None:
        if not password or not isinstance(password, str):
            raise ValueError("Пароль не може бути порожнім.")
        self.__password_salt = os.urandom(16)
        self.__password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )

    def check_password(self, password: str) -> bool:
        if not self.__password_hash or not self.__password_salt:
            return False
        candidate_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )
        return hmac.compare_digest(self.__password_hash, candidate_hash)

    def deactivate(self) -> None:
        self.active = False

    def __str__(self) -> str:
        status = "Active" if self.active else "Inactive"
        return f"User(username='{self.username}', email='{self.email}', role='{self.role}', status={status})"

class Admin(User):
    def __init__(
        self,
        username: str,
        email: str,
        role: str = "admin",
        active: bool = True,
        permissions: set[str] | None = None,
    ):
        super().__init__(username=username, email=email, role=role, active=active)
        self.permissions: set[str] = set(permissions) if permissions is not None else set()

    def grant_permission(self, permission: str) -> None:
        if not permission:
            raise ValueError("Право доступу не може бути порожнім.")
        self.permissions.add(permission)

    def revoke_permission(self, permission: str) -> None:
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def __str__(self) -> str:
        base_info = super().__str__()
        perms_str = ", ".join(sorted(self.permissions)) if self.permissions else "None"
        return f"{base_info} | Permissions: [{perms_str}]"

class Session:
    def __init__(self, ip: str):
        self.ip: str = ip
        now = datetime.now(timezone.utc)
        self.login_time: datetime = now
        self.last_activity: datetime = now

    def touch(self) -> None:
        self.last_activity = datetime.now(timezone.utc)

    def is_active(self, timeout_sec: int) -> bool:
        if timeout_sec <= 0:
            raise ValueError("timeout_sec повинен бути додатним числом.")
        delta = datetime.now(timezone.utc) - self.last_activity
        return delta < timedelta(seconds=timeout_sec)

@dataclass(frozen=True)
class AuditRecord:
    timestamp: datetime
    username: str
    action: str


class AuditLog:
    def __init__(self):
        self._logs: list[AuditRecord] = []

    def add_log(self, username: str, action: str) -> None:
        record = AuditRecord(
            timestamp=datetime.now(timezone.utc),
            username=username,
            action=action,
        )
        self._logs.append(record)

    def show_all(self) -> None:
        print("\n" + "=" * 65)
        print(f"{'Час (UTC)':<24} | {'Користувач':<18} | {'Дія':<18}")
        print("-" * 65)
        for log in self._logs:
            time_str = log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            print(f"{time_str:<24} | {log.username:<18} | {log.action:<18}")
        print("=" * 65)


class UserAccount:
    ALLOWED_KEYS: ClassVar[frozenset[str]] = frozenset(
        {"user", "session", "audit_log"}
    )

    def __init__(
        self,
        user: User,
        session: Session | None = None,
        audit_log: AuditLog | None = None,
    ):
        self.user: User = user
        self.session: Session | None = session
        self.audit_log: AuditLog = audit_log if audit_log is not None else AuditLog()

    def login(self, username: str, password: str, ip: str) -> bool:
        if self.user.username != username or not self.user.active or not self.user.check_password(password):
            self.audit_log.add_log(username, "login_failure")
            return False

        self.session = Session(ip=ip)
        self.session.touch()
        self.audit_log.add_log(username, "login_success")
        return True

    def is_authenticated(self) -> bool:
        if self.session is None:
            return False
        return self.session.is_active(SESSION_TIMEOUT_SEC)

    def logout(self) -> None:
        username = self.user.username
        self.session = None
        self.audit_log.add_log(username, "logout")

    def __getitem__(self, item: str):
        if item not in self.ALLOWED_KEYS:
            raise KeyError(f"Доступ до ключа '{item}' заборонено або ключ не існує.")
        return getattr(self, item)

    def __setitem__(self, key: str, value) -> None:
        if key not in self.ALLOWED_KEYS:
            raise KeyError(f"Зміна ключа '{key}' заборонена.")

        if key == "user" and not isinstance(value, User):
            raise TypeError("Значення для 'user' повинно бути екземпляром User або його нащадка.")
        elif key == "session" and value is not None and not isinstance(value, Session):
            raise TypeError("Значення для 'session' повинно бути екземпляром Session або None.")
        elif key == "audit_log" and not isinstance(value, AuditLog):
            raise TypeError("Значення для 'audit_log' повинно бути екземпляром AuditLog.")

        setattr(self, key, value)