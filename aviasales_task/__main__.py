import os

from aviasales_task.server import start_server

os.chdir(os.path.dirname(__file__))
start_server()
