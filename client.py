import json
import urllib

import default_workflow
import websocket

import requests
import uuid


class Client:
    pass

    def __enter__(self):

        # start the process
        self.client_id = str(uuid.uuid4())
        self.ws = websocket.WebSocket()
        self.ws.connect("ws://{}/ws?clientId={}".format(self.server_address, self.client_id))


        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ws.close()
        return

    def __init__(self, server_address: str, workflow: dict = default_workflow.DEFAULT_WORKFLOW):
        self.workflow = workflow
        self.server_address = server_address

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
        prompt_id = self.queue_prompt(prompt, client_id)['prompt_id']
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
