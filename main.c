/* Common entry point for generated code.
 */

#include "dispatch.h"
#include <string.h>
#include <stdlib.h>

int state_trk = 0;
extern uint64_t xorshift_seed[2];

static void seed(void);

#if defined(HAVE_RDRAND)
static void seed(void)
{
    asm volatile("0:   rdrand %0; jnc 0b" : "=r" (xorshift_seed[0]));
    asm volatile("0:   rdrand %0; jnc 0b" : "=r" (xorshift_seed[1]));
}

#elif defined(HAVE_GETRANDOM)
#include <linux/random.h>
#include <sys/syscall.h>

static void seed(void)
{
    ssize_t rv = syscall(SYS_getrandom, xorshift_seed, sizeof(xorshift_seed), 0);
    if (rv != sizeof(xorshift_seed)) abort();
}
#else
#error "Need a way to seed the PRNG"
#endif

int main(int argc, char **argv)
{
    if (argc < 2) abort();

    seed();
    size_t count = atoi(argv[1]);
    while (--count)
        dispatch(next_state());
    return state_trk;
}
