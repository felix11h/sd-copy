## Sd-copy usage

Sorting and copying footage from my cameras adheres to the following principles:

1. Metadata of recordings (video, image, audio) will **never** be modified
2. Timestamps in the recording metadata are unreliable and cannot be used

<br/>
    
> [!IMPORTANT]
> The following sources are the only reliable timestamps, only these should be used:

- `Datetime string in file name (timezone unaware)`
- `File modification date (timezone aware)`

<br/>
<br/>

## Camera details

### DJI Osmo Action

Timestamps in videos created by the DJI Osmo Action camera are incorrect. This is for example reported here, [forum.dji.com](https://forum.dji.com/forum.php?mod=redirect&goto=findpost&ptid=242428&pid=2747596). Depending on the date, a daylight savings time correction is, for example, applied to file modification date. Through testing, I have found out that my camera follows a European daylight savings time schedule.

There are two timestamp sources to consider – the file modification date and one of the metadata timestamps (e.g. media create date as extracted by ExifTool). I have tested the two timestamps with the following code:

```python
import shlex
import subprocess
from datetime import datetime
from pathlib import Path

for file_path in sorted(Path("dcim/100MEDIA").rglob("DJI*.MOV")):
    print(file_path)
    print(datetime.fromtimestamp(file_path.stat().st_mtime))
    subprocess.run(shlex.split(f"exiftool -T -mediacreatedate {file_path}"), check=True)
```

With this I have analyzed two videos recorded in summer time (until October 27 in 2025) and winter time (starting from October 28 in 2035):
```shell
dcim/100MEDIA/DJI_0472.MOV
2035:10:27 12:11:58     correct date
2035-10-27 12:12:10     file modified date
2035:10:27 11:11:58     metadata timestamp

dcim/100MEDIA/DJI_0475.MOV
2035:10:28 12:13:08     correct date
2035-10-28 11:13:19     file modified date
2035:10:28 11:13:08     metadata timestamp
```
In words, while the file modified date can be off by 1 hour depending on the current data, the metadata timestamp is **always** off by 1 hour.

For photos, on the other hand, while file modified dates have the same issue as videos, metadata timestamps are always reported correctly.

```shell
dcim/100MEDIA/DJI_0473.JPG
2035:10:27 12:12:20     correct date
2035-10-27 12:12:21     file modified date
2035:10:27 12:12:20     metadata timestamp


dcim/100MEDIA/DJI_0474.JPG
2035:10:28 12:13:07     correct date
2035-10-28 11:13:08     file modified date
2035:10:28 12:13:07     metadata timestamp
```

In summary, the following tables describe the correctness of timestamps the DJI Osmo Action:

#### Video
| | file modified date  | metadata timestamp |
|--------| ------------- | ------------- |
| Summer time | correct  | -1 hour  |
| Winter time | -1 hour  | -1 hour  |


#### Image

| | file modified date  | metadata timestamp |
|--------| ------------- | ------------- |
| Summer time | correct  | correct  |
| Winter time | -1 hour  | correct  |

<br/>

Taken all of this together, `sd-copy` operates as follows. The metadata timestamp is used as a source for both video and images, but only for video the timestamp is corrected by 1 hour. The file modified date is then set correctly to this timestamp. 