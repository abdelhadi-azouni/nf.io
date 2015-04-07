### Installation

* Install [fuse](http://fuse.sourceforge.net/) >= 2.6 
* Add your username to the group fuse `sudo addgroup <username> fuse`
* Logout and login again to update user group

### Run

`python myfuse.py /your/dir /mount/point`


### Behaviour

All files and folders under `/your/dir` will be copied to `/mount/point`, and any change done under `mount/point` will be reflected to `your/dir`

