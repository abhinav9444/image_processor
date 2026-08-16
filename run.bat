@echo off
call .venv\Scripts\activate.bat
python image_processor.py %*
