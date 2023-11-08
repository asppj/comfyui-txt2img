import subprocess
import threading
import time

import requests
from cog import BasePredictor, Input, Path

import json

from client import Client
from default_workflow import DEFAULT_WORKFLOW


class Predictor(BasePredictor):
    # def setup(self):
    #     # start server
    #     self.server_address = "127.0.0.1:8188"
    #     self.start_server()
    #
    # def start_server(self):
    #     print("run start_server!")
    #
    #     server_thread = threading.Thread(target=self.run_server)
    #     server_thread.start()
    #
    #     while not self.is_server_running():
    #         time.sleep(1)  # Wait for 1 second before checking again
    #
    #     print("Server is up and running!")
    #
    # @staticmethod
    # def run_server():
    #     command = "python ./ComfyUI/main.py"
    #     print(command)
    #     server_process = subprocess.Popen(command, shell=True)
    #     server_process.wait()
    #
    # # hacky solution, will fix later
    # def is_server_running(self):
    #     try:
    #         res = requests.get("http://{}/history/{}".format(self.server_address, "123"))
    #         return res.status_code == 200
    #     except Exception as e:
    #         print(f"is_server_running status:{e}")
    #         return False

    def predict(
            self,
            workflow: str = Input(description="json str, custom workflow[other args is invalid if workflow is  exists]",
                                  default=json.dumps(DEFAULT_WORKFLOW))
    ) -> Path:
        print("run predict")
        with Client(self.server_address) as c:
            print("run workflow")
            res = c.run_workflow()
            print("result", res)
            return Path(res)
