import multiprocessing
import re
import subprocess

import yaml
import itertools
from time import sleep
import os

def singleton(cls):
    instances = {}

    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return wrapper


def run_command(clash_path):
    os.system(clash_path)

@singleton
class Clash:
    def __init__(self, node_info_path, config_path, clash_path):
        self.clash_process = None
        self.clash_path = clash_path
        self.config_path = config_path
        with open(node_info_path, 'r', encoding='utf-8') as file:
            nodes_info = yaml.load(file, Loader=yaml.FullLoader)

        self.nodes_name = []
        for node_info in nodes_info['proxies']:
            name = node_info['name']
            match = re.search(r'境外专用', name)
            if not match:
                self.nodes_name.append(name)

        # Clash config
        # with open('C:\\Users\\admin\\.config\\clash\\profiles\\list.yml', 'r', encoding='utf-8') as file:
        with open(config_path, 'r', encoding='utf-8') as file:
            self.clash_config = yaml.load(file, Loader=yaml.FullLoader)

    def start(self):
        if self.clash_process is None:
            clash_process = multiprocessing.Process(target=run_command, args=(self.clash_path, ))
            clash_process.start()
            while not clash_process.is_alive():
                sleep(3)
            self.clash_process = clash_process

    def stop(self):
        if self.clash_process:
            self.clash_process.kill()
            while self.clash_process.is_alive():
                sleep(3)
            self.clash_process = None

    def next_node(self):
        cycle_iter = itertools.cycle(self.nodes_name)
        self.stop()
        self.clash_config[1]['selected'][0]['now'] = next(cycle_iter)
        with open(self.config_path, 'w', encoding='utf-8') as file:
            yaml.dump(self.clash_config, file)
        self.start()