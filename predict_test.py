import os
import urllib
import uuid

import torch
import websocket
import requests
import default_workflow
import json

from client import Client

server_address = "127.0.0.1:8188"


def queue_prompt(prompt, client_id):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = requests.post("http://{}/prompt".format(server_address), data=data)
    return req.json()


def get_history(prompt_id):
    with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
        return json.loads(response.read())


def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    print(folder_type)
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
        return response.read()


def get_images(ws, prompt, client_id):
    req = queue_prompt(prompt, client_id)
    prompt_id = req.get('prompt_id', "")
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

    history = get_history(prompt_id)[prompt_id]
    for o in history['outputs']:
        for node_id in history['outputs']:
            node_output = history['outputs'][node_id]
            print("node output: ", node_output)

            if 'images' in node_output:
                images_output = []
                for image in node_output['images']:
                    image_data = get_image(image['filename'], image['subfolder'], image['type'])
                    images_output.append(image_data)
            output_images[node_id] = images_output

    return output_images


def test_predict(seed, input_prompt, negative_prompt="", steps=20):
    # load config
    # prompt = None
    prompt = default_workflow.DEFAULT_WORKFLOW
    if prompt is None:
        workflow_config = "./custom_workflows/sdxl_txt2img.json"
        with open(workflow_config, 'r') as file:
            prompt = json.load(file)
        print(f"use default workflow:\n{prompt}\n")

    if not prompt:
        raise Exception('no workflow config found')

    # set input variables
    prompt["6"]["inputs"]["text"] = input_prompt
    prompt["7"]["inputs"]["text"] = negative_prompt

    prompt["3"]["inputs"]["seed"] = seed
    prompt["3"]["inputs"]["steps"] = steps

    # start the process
    client_id = str(uuid.uuid4())
    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
    images = get_images(ws, prompt, client_id)

    for node_id in images:
        for image_data in images[node_id]:
            from PIL import Image
            import io
            image = Image.open(io.BytesIO(image_data))
            image.save("out-" + node_id + ".png")
            return str("out-" + node_id + ".png")
    ws.close()


if __name__ == '__main__':
    # seed = int.from_bytes(os.urandom(3), "big")
    # print(f"Using seed: {seed}")
    # # generator = torch.Generator("cuda").manual_seed(seed)
    # print(test_predict(196429611935343, "beautiful scenery nature glass bottle landscape, purple galaxy bottle,dog",""))
    # pass
    with Client(server_address) as c:
        res = c.run_workflow()
        print(res)
