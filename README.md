# owokuro
 
Generate [mokuro](https://github.com/kha-white/mokuro) files using [owocr](https://github.com/AuroraWright/owocr) as the OCR backend.

## Install Instructions
Install [uv](https://docs.astral.sh/uv/getting-started/installation/) (should theoretically work with python3-pip as well)
```
uv tool install git+https://github.com/kamperemu/owokuro
```

## Usage Instructions

- Open owocr with read_from = websocket, write_to = websocket, output_format = json (commandline argument or config file/editor) and keep it open in the background

### Run on one volume

```
mokuro /path/to/manga/vol1
```
This will generate vol1.mokuro in manga folder which can be used with [mokuro reader](https://reader.mokuro.app).

### Run on a directory containing multiple volumes

If your directory structure looks somewhat like this:
```
manga_title/
├─vol1/
├─vol2/
├─vol3/
└─vol4/
```

You can process all volumes by running:

```
mokuro --parent_dir manga_title/
```