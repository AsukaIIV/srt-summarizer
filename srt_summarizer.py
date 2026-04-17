# -*- coding: utf-8 -*-
"""
兼容入口壳：保留旧启动方式，统一转发到 app.py。
"""

from app import main


if __name__ == "__main__":
    main()
