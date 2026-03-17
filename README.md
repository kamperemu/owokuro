# owokuro

Generate [mokuro](https://github.com/kha-white/mokuro) files using [owocr](https://github.com/AuroraWright/owocr) as the OCR backend.

## Install Instructions

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) (should theoretically work with python3-pip as well) and then run:

```
uv tool install git+https://github.com/kamperemu/owokuro
```

## Usage Instructions

Install and open owocr with read_from = websocket, write_to = websocket, output_format = json (cli argument or config file/editor) and keep it open in the background.

If you're running owocr through cli you can run:

```
owocr -r websocket -w websocket -of json
```

If your directory structure looks somewhat like this:

```
manga/
├─vol1/
├─vol2/
├─vol3/
└─vol4/
```

You can process one volume by running:

```
owokuro /path/to/manga/vol1
```

You can process all volumes by running:

```
owokuro --parent_dir /path/to/manga
```

This will generate mokuro files for each volume in the /path/to/manga folder which can be used with [mokuro reader](https://reader.mokuro.app).

## Supported Formats

Volumes via single or batch processing methods can be one of the following formats:

- Directory of images
- CBZ file
- ZIP file

All formats should contain the images to be processed at the top level of the volume, as any nested folders will be skipped.

Good examples:

```
vol1/
├─image_001.jpg
├─image_002.jpg
└─image_003.jpg
```

```
vol1.cbz
├─image_001.jpg
├─image_002.jpg
└─image_003.jpg
```

Bad examples:

```
vol1/
├─nested_folder/
│ └─image_001.jpg
├─image_001.jpg
├─image_002.jpg
└─image_003.jpg
```

```
vol1.cbz
└─nested_folder/
  ├─image_001.jpg
  ├─image_002.jpg
  └─image_003.jpg
```
