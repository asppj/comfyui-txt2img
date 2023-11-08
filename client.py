import json
import subprocess
import threading
import time
import urllib

import default_workflow
import websocket

import requests
import uuid


class ComfyServer:
    _ins = None
    server_address = "127.0.0.1:8188"

    def __new__(cls, *args, **kwargs):
        if cls._ins:
            print("server already on")
            return cls._ins
        print("server on")
        cls._ins = super().__new__(cls)
        return cls._ins

    def __init__(self):
        self.setup()

    def setup(self):
        # start server
        self.server_address = "127.0.0.1:8188"
        self.start_server()

    def start_server(self):
        print("run start_server!")

        server_thread = threading.Thread(target=self.run_server)
        server_thread.start()

        while not self.is_server_running():
            time.sleep(1)  # Wait for 1 second before checking again

        print("Server is up and running!")

    @staticmethod
    def run_server():
        command = "python ./ComfyUI/main.py"
        print(command)
        server_process = subprocess.Popen(command, shell=True)
        server_process.wait()

    # hacky solution, will fix later
    def is_server_running(self):
        try:
            res = requests.get("http://{}/history/{}".format(self.server_address, "123"))
            return res.status_code == 200
        except Exception as e:
            print(f"is_server_running status:{e}")
            return False



class Client:
    pass

    def __enter__(self):
        # start the process
        self.client_id = str(uuid.uuid4())
        self.ws = websocket.WebSocket()
        self.ws.connect("ws://{}/ws?clientId={}".format(self.server_address, self.client_id))
        self.check_model()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ws.close()
        return

    def __init__(self,workflow: dict = default_workflow.DEFAULT_WORKFLOW):
        srv = ComfyServer()
        self.workflow = workflow
        self.server_address = srv.server_address

    def check_model(self):
        pass
        for item in self.workflow.values():
            if isinstance(item, dict):
                if item.get("class_type", "") == "CheckpointLoaderSimple":
                    pass
                    """"inputs": {
                      "ckpt_name": "sd_xl_base_1.0.safetensors"
                      # "ckpt_name": "sd_xl_base_1.0.safetensors"
                    },"""
                    if ckpt_name := item.get("inputs", {}).get("ckpt_name", None):
                        print("ckpt model is ", ckpt_name)
                        # from transformers import AutoModel
                        # print(f"pre load {ckpt_name}")
                        # model = AutoModel.from_pretrained(ckpt_name)
                        # model.save_pretrained("models/checkpoints")
                        # print(ckpt_name, "auto load")

    def run_workflow(self) -> str:
        images = self.get_images(self.ws, self.workflow, self.client_id)
        for node_id in images:
            for image_data in images[node_id]:
                from PIL import Image
                import io
                image = Image.open(io.BytesIO(image_data))
                img_path = "outputs/out-" + node_id + ".png"
                image.save(img_path)
                return str(img_path)

    def queue_prompt(self, prompt, client_id):
        p = {"prompt": prompt, "client_id": client_id}
        data = json.dumps(p).encode('utf-8')
        req = requests.post("http://{}/prompt".format(self.server_address), data=data)
        return req.json()

    def get_image(self, filename, subfolder, folder_type):
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        print(folder_type)
        res = requests.get("http://{}/view".format(self.server_address), params=data)
        return res.content
        # url_values = urllib.parse.urlencode(data)
        # with urllib.request.urlopen("http://{}/view?{}".format(self.server_address, url_values)) as response:
        #     return response.read()

    def get_images(self, ws, prompt, client_id):
        res = self.queue_prompt(prompt, client_id)
        print(res)
        prompt_id = res['prompt_id']
        output_images = {}
        while True:
            out = ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['node'] is None and data['prompt_id'] == prompt_id:
                        break  # Execution is done
            else:
                continue  # previews are binary data

        history = self.get_history(prompt_id)[prompt_id]
        for o in history['outputs']:
            for node_id in history['outputs']:
                node_output = history['outputs'][node_id]
                print("node output: ", node_output)
                images_output = []
                if 'images' in node_output:
                    images_output = []
                    for image in node_output['images']:
                        image_data = self.get_image(image['filename'], image['subfolder'], image['type'])
                        images_output.append(image_data)
                output_images[node_id] = images_output

        return output_images

    def get_history(self, prompt_id):
        res = requests.get("http://{}/history/{}".format(self.server_address, prompt_id))
        return res.json()
        # with urllib.request.urlopen("http://{}/history/{}".format(self.server_address, prompt_id)) as response:
        #     return json.loads(response.read())
