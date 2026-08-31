import os
import subprocess
import sys


def run(args):
    subprocess.check_call([sys.executable, *args])


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "logistics_hub.settings")
    run(["manage.py", "migrate", "--noinput"])
    run(["manage.py", "collectstatic", "--noinput"])
    run(["manage.py", "sync_roles"])
    port = os.environ.get("PORT", "8000")
    workers = os.environ.get("WEB_WORKERS", "2")
    os.execvp(
        "gunicorn",
        [
            "gunicorn",
            "logistics_hub.wsgi:application",
            "--bind",
            f"0.0.0.0:{port}",
            "--workers",
            workers,
            "--timeout",
            "120",
        ],
    )


if __name__ == "__main__":
    main()
