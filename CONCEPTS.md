## Concepts

It is not straightforward to correctly determine when a video or image was taken. Depending on the media type, the camera, and the camera's firmware version, different options are available. There is no one-fits-all solution, and some combinations of camera and media types provide incorrect information due to bugs. After some trial and error, and learning a lot about timestamps, here is how I decided to use metadata:

<br>

|  | Recording metadata (e.g. EXIF) | Filesystem metadata <br>(date modified, date created) | Filename timestamp <br> (`20241027-1752_[...].mov`)  | 
| ------------- | ------------- | ------------- | ------------- |
| Modified by `sd-copy`? |  Never modified | Yes | Yes  |
| Time zone information |  Depends on camera, firmware<br> version(!), and metadata field | Time zone aware (possibly<br> incorrect) | Time zone unaware, assumes time <br>zone where footage was recorded  |
| Reliable? |  $\color{red}{\textsf{No ✘}}$ | $\color{red}{\textsf{No ✘}}$ | $\color{green}{\textsf{Yes ✔️}}$ |


<br>
Some cameras (see below) simply do not support setting a time zone. For this reason, I have decided to primarily use naive timestamps. There are ideas to extend this, but in some cases this would require user input of the correct time zone during sorting (see https://github.com/felix11h/sd-copy/issues/26).

<br/>
<br/>

## Camera details

### DJI Osmo Action

The DJI Osmo Action cameras (as of version 4) do not have an option for setting a time zone. Therefore, recorded footage is also lacking this information, and filesystem metadata timestamps are using a camera internal default time zone ([forum.dji.com](https://forum.dji.com/thread-294957-1-1.html)).

The naive timestamps found in the EXIF metadata (as parsed by Exiftool) are partially incorrect, see table below. `sd-copy` applies corrections to the timestamp of the recording depending on media type:

| | metadata timestamp |
|--------| ------------- |
| images | correct  |
| videos | -1 hour  |

<br>

### Fujifilm X-T3

The Fujifilm X-T3 camera was released in 2018. Only with firmware version 5.00, from May 2023, support for setting the camera's time zone was added ([fujifilm-x.com](https://fujifilm-x.com/en-gb/support/download/firmware/cameras/x-t3/)). With this, full support for time zone aware timestamps is possible, however, it is at the moment not implemented (see https://github.com/felix11h/sd-copy/issues/26).
