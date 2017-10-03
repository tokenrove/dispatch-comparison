#include "dispatch.h"
#include <stdlib.h>

int next_state(void)
{
    return next() % N_ENTRIES;  /* you should never do this. */
}
