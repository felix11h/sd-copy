
# Sd-copy

Sd-copy moves DCIM files from an SD card and sorts them according to metadata into a given target folder. The following cameras are supported:
* Fujifilm X-T3
* DJI Osmo Action


## Usage

Executing sd-copy via
```shell
sd-copy sort [source path] [output path]
```
a DCIM folder structure in `[source path]` such as
```shell
[source_path]
├── DJI_0163.MOV
├── DSCF0226.JPG
├── DSCF0229.MOV
├── DSCF0230.MOV
├── DSCF0231.JPG
├── DSCF0231.RAF
└── DSCF0232.MOV
```
is copied to `[target path]` with the following structure
````shell
[target path]
out/
├── 2021-07-08
│   ├── 20210708-173628_x-t3_DSCF0226_6240x4160.jpg
│   ├── 20210708-173906_x-t3_DSCF0229_1080p-24fps.mov
│   ├── 20210708-174010_x-t3_DSCF0230_2160p-59.94fps.mov
│   ├── 20210708-174028_x-t3_DSCF0231_4416x2944.raf
│   ├── 20210708-174028_x-t3_DSCF0231_6240x4160.jpg
│   └── 20210708-174626_x-t3_DSCF0232_1080p-24fps.mov
└── 2021-07-12
    └── 20210712-075107_dji-oa_DJI0163_2160p-29.97fps.mov

````

### Why write this?

If you're looking for a general purpose tool for moving photos and videos from an SD card, please consider Damon Lynch's much more advanced [Rapid Photo Downloader](https://damonlynch.net/rapid/). In my case, the bug described [here](https://bugs.launchpad.net/rapid/+bug/1814014) and [here](https://bugs.launchpad.net/rapid/+bug/1837327) initially prevented me from using the tool.

After starting this project I realized that the problems are more severe, both the Fujifilm X-T3 and DJI Osmo Action set incorrect timestamps in either file modification date (X-T3) or the Exif modify date (Osmo Action). In order to have at least one reliable timestamp, I extended this tool to set file modification dates for all copied files explicitly.


## Installation

First install `exiftool` ([exiftool.org](https://exiftool.org/install.html#Unix)). Then, in the root directory of this project
```shell
pip install .
```
to install the tool in your current environment. Add `-e` for editable mode<sup>[1](#footnote1)</sup>. 

For development, install the project using Poetry as usual (`poetry install`).

### DCIM data
If you need DCIM data for local development or testing, use
```shell
git submodule init
``` 
to initialize your local configuration file, and 
```shell
git submodule update
```
to download the files. Alternatively you can clone this repository with the `--recurse-submodules` flag.

### Run tests

Run unit tests with
```shell
pytest tests/unit
```
and integration tests with
```shell
pytest tests/integration
```
Integration tests require the `dcim` git submodule.

<br />

#### Notes 
<a name="footnote1">1</a>: Editable installations now possible with PEP 660. See also See also [this discussion](https://github.com/python-poetry/poetry/issues/34#issuecomment-870454738), [PEP 606](https://discuss.python.org/t/pronouncement-on-peps-660-and-662-editable-installs/9450) and the discussion [here](https://github.com/python-poetry/poetry/issues/761).
