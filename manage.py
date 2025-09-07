
import dotenv
dotenv.load_dotenv()
import os
import sys


def main():
    """Run administrative tasks."""
    if 'test' in sys.argv:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings_test')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
