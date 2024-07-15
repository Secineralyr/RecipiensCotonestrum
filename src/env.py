import os.path as osp
import dotenv.main

dotenv_path = osp.join(osp.dirname(__file__), '.env')
envs = dotenv.main.dotenv_values(dotenv_path)

