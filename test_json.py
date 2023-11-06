
import json

def main():
    with open('custom_workflows/sdxl_txt2img.json') as fd:
        content = fd.read()
        # json.dumps(content)
        print(str( json.dumps(content)))

if __name__ == '__main__':
    main()