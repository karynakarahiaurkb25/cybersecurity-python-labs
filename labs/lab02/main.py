import os
import sys
from datetime import timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from labs.lab02.task01 import Admin, AuditLog, User, UserAccount
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER


def run_demo():
    print(f"  Студент: {STUDENT_NAME} | Група: {GROUP_NAME} | Варіант: {VARIANT_NUMBER}")
    print("#" * 70)

    print("\nСтворення користувача та валідація email")
    user = User("cyber_dev", "dev_ops@sec.domain.ua", role="engineer")
    user.set_password("SuperSecret2026_Secure")
    print("Створено:", user)

    try:
        user.email = "1invalid_email@domain.com"
    except ValueError as e:
        print("Перехоплено помилку валідації email:", e)

    user.email = "valid_admin2026@cloud.corp"
    print("Оновлений email успішно прийнято:", user.email)

    print("\nПеревірка класу Admin (Наслідування)")
    admin = Admin("root_master", "sec_admin@vault.net")
    admin.set_password("MasterPass_2026")
    admin.grant_permission("READ_CONFIDENTIAL")
    admin.grant_permission("DEPLOY_GATE")
    print(admin)
    print("Чи має право 'DEPLOY_GATE'?:", admin.has_permission("DEPLOY_GATE"))
    admin.revoke_permission("DEPLOY_GATE")
    print("Чи має право 'DEPLOY_GATE' після відкликання?:", admin.has_permission("DEPLOY_GATE"))

    print("\nАутентифікація через UserAccount (Композиція)")
    audit = AuditLog()
    account = UserAccount(user=user, audit_log=audit)

    print("Спроба входу з хибним паролем...")
    res1 = account.login("cyber_dev", "WrongPassword123", ip="192.168.1.15")
    print(f"Результат: {res1} | Аутентифіковано: {account.is_authenticated()}")

    print("Спроба входу з правильним паролем...")
    res2 = account.login("cyber_dev", "SuperSecret2026_Secure", ip="192.168.1.15")
    print(f"Результат: {res2} | Аутентифіковано: {account.is_authenticated()}")

    print("\nПеревірка таймауту сесії")

    account.session.last_activity -= timedelta(seconds=1000)
    print("Сесія після 1000 сек бездіяльності. Аутентифіковано?:", account.is_authenticated())

    print("\nПовторний логін та вихід (Logout)")
    account.login("cyber_dev", "SuperSecret2026_Secure", ip="192.168.1.15")
    print("Аутентифіковано після повторного входу:", account.is_authenticated())
    account.logout()
    print("Аутентифіковано після logout():", account.is_authenticated())

    print("\nПеревірка доступу через квадратні дужки")
    print("account['user']:", account["user"])
    try:
        _ = account["__password_hash"]
    except KeyError as e:
        print("[OK] Захищено: заборонено доступ до чутливих атрибутів ->", e)

    print("\nЖурнал аудиту (AuditLog)")
    account.audit_log.show_all()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_demo()
    else:
        print("Використання: python -m labs.lab02.main demo")


if __name__ == "__main__":
    main()