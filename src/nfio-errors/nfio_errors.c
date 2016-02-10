#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <dlfcn.h>
#include <string.h>

#define MIN(x, y) (((x) < (y)) ? (x) : (y))

typedef void (*original_error_func_type)(int status,
    int errnum, const char* message, ...);
typedef char * (*original_strerror_func_type)(int errnum);
typedef char * (*original_strerror_r_func_type)(int errnum, char *buf, 
    size_t n);

char *nfio_errors[] = 
    {
        "Unknown error",
        "Cannot connect to hypervisor",
        "VNF does not exist",
        "Failed to execute command in VNF",
        "Failed to create VNF",
        "Failed to deploy VNF",
        "Failed to destroy VNF",
        "Failed to start VNF",
        "Failed to restart VNF",
        "Failed to stop VNF",
        "Failed to pause VNF",
        "Failed to resume VNF",
        "Operation failed abruptly, may cause inconsistent state",
        "VNF image name is missing",
        "VNF hostname is missing",
        "VNF instance name is missing",
        "Opeation failed. VNF is not runnning"
    };

void error(int status, int errnum, const char* message, ...) {
    puts("test string");
    printf("in my error: %d %d %s\n", status, errnum, message);
    if (abs(errnum) > 700) {
        printf("nfio-error: %s\n", nfio_errors[errnum-700]);
    }
    else {
        va_list args;
        va_start(args, message);
        
        char message_with_args[1024];
        vsnprintf(message_with_args, 1023, message, args);
        printf("msg: %s\n", message_with_args);
        
        original_error_func_type original_error_func;
        original_error_func = (original_error_func_type)dlsym(RTLD_NEXT, 
            "error");
        original_error_func(status, errnum, message_with_args);
    }
}

char *strerror(int errnum) {
    printf("in my strerror %d\n", errnum);
    if (errnum > 700) {
        return nfio_errors[errnum-700];
    }
    else {
        original_strerror_func_type original_strerror_func;
        original_strerror_func = (original_strerror_func_type)dlsym(RTLD_NEXT,
            "strerror");
        return original_strerror_func(errnum);
    }
}

char * strerror_r (int errnum, char *buf, size_t n) {
    printf("in my strerror_r %d\n", errnum);
    if (errnum > 700) {
        int message_len = MIN(strlen(nfio_errors[errnum-700]), n);
        strncpy(buf, nfio_errors[errnum-700], message_len);
        buf[message_len] = '\0';
        return buf;
    }
    else {
        original_strerror_r_func_type original_strerror_r_func;
        original_strerror_r_func = (original_strerror_r_func_type)dlsym(RTLD_NEXT,
            "strerror_r");
        return original_strerror_r_func(errnum, buf, n);
    }
}
