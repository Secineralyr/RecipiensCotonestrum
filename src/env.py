import os.path as osp
from os import environ
import dotenv.main

dotenv_path = osp.join(osp.dirname(__file__), '.env')

if 'IS_DOCKER' in environ:
    dotenv.main.load_dotenv(dotenv_path)
    envs = environ
else:
    envs = dotenv.main.dotenv_values(dotenv_path)
