#!/usr/bin/env python
"""HC-Inventory 계산기 백엔드 — Django 관리 진입점."""

import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hc_project.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
