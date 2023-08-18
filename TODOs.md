* ~~Check if exiftool is installed, else throw error~~
* tests
  --> test that dcim submodule ref exists on github
* ~~register SD-cards and confirm the modify date?~~
  ~~--> a new SD card might have different file modify date...~~ Irrelevant as I'm using Exif data only
* ~~setup linting (flake8)~~
* ~~setup black~~
* ~~setup isort~~
* ~~integrate pipeline~~
  ~~--> `isort . --diff` empty~~
  ~~--> `black . --diff` empty~~
  ~~--> `flake8` ok~~   
* ~~correctly set file modification date (https://stackoverflow.com/a/52858040/692634)~~
* ~~correctly set metadata?~~ Metadata will not be touched. Reliable information is timestamp in filename and modify date.
* use pydantic for dataclass type validation, parse camera model definitions from yaml
* use mypy?
* setup dependabot
* `[can-delete]_simple-sd-copy-test` does not exist.


* rename from simple-sd-copy to sd-copy
* document timestamp approach (filename: unaware, file modified date: aware, metadata timestamp: never use, unreliable) 
* dockerize
* rewrite tests
* replace pyexiftool with direct ExifTool calls
* add update timestamp feature