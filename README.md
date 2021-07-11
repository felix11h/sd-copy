
## Simple-sd-copy

Simple tool to copy video and images from an SD card and assign a meaningful folder structure and file names based on the file's Exif metadata.  

Currently supported cameras
* Fujifilm X-T3

Planned support
* DJI Osmo Action

If you're looking for a more advanced general purpose tool, please consider Damon Lynch's [Rapid Photo Downloader](https://damonlynch.net/rapid/). In my case, the bug described [here](https://bugs.launchpad.net/rapid/+bug/1814014) and [here](https://bugs.launchpad.net/rapid/+bug/1837327) prevented me from using the tool.

### Usage
```shell
simple-sd-copy [source path] [output path]
```

### Installation

First install `exiftool` ([exiftool.org](https://exiftool.org/install.html#Unix)). Then, in the root directory of this project
```shell
pip install .
```
to install the tool in your current environment. 

For development, install the project using Poetry as usual (`poetry install`).

<br />

#### Note on editable mode
It is currently not possible to directly install a `pyproject.toml` based package in editable mode (`pip install -e`). If you need this, you can create a setup.py following the steps below.

First add `setuptools` to the `pyproject.toml`
```toml
[build-system]
requires = ["setuptools", "poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"
```
Then create a `setup.py` via
```shell
poetry build --format sdist
tar -xvf dist/*-`poetry version -s`.tar.gz -O --wildcards '*/setup.py' > setup.py
```
With `setup.py` present, you should be able to install in editable mode using `pip install -e`.

This solution is from the discussion [here](https://github.com/python-poetry/poetry/discussions/1135#discussioncomment-145763). See also [this discussion](https://github.com/python-poetry/poetry/issues/34#issuecomment-870454738), [PEP 606](https://discuss.python.org/t/pronouncement-on-peps-660-and-662-editable-installs/9450) and the discussion [here](https://github.com/python-poetry/poetry/issues/761).


