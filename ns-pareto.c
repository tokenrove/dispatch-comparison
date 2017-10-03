
#include "dispatch.h"
#include <math.h>
#include <stdlib.h>

int next_state(void)
{
    if (next() % 10 < 8)
        return 0;
    return next() % N_ENTRIES;  /* you should never do this. */
}
