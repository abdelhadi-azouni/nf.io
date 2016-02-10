Compile:
```bash
gcc -Wall -shared -fPIC nfio_errors.c -o nfioerrors.so -ldl
```
 
Interpose the library function `error` 
```bash
export LD_PRELOAD=/home/nfuser/nf.io/src/nfio-errors/nfioerrors.so
```
