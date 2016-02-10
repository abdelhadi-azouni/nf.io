
#define _GNU_SOURCE

#include <stdio.h>
#include <stdarg.h>
#include <dlfcn.h>

typedef void (*original_error_func_type)(int status,
    int errnum, const char* message, ...);

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
    printf("error: %d %d %s\n", status, errnum, message);
    if (errnum > 700) {
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
