// iOS 8 compatibility shims: symbols newer SDKs reference that iOS 8 lacks.
// - __darwin_check_fd_set_overflow: fd_set bounds check, added to libSystem
//   around iOS 10. RoboVM 2.3.13's bundled conscrypt calls it during SSL
//   init (RAND_poll). Real semantics: nonzero when fd is out of range.
#include <sys/types.h>

int __darwin_check_fd_set_overflow(int fd, const void *fds, int check) {
    (void)fds;
    (void)check;
    return fd < 0 || fd >= FD_SETSIZE;
}
