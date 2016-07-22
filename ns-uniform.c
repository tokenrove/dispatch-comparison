#include "dispatch.h"
#include <stdlib.h>

int next_state(void)
{
    return rand() % N_ENTRIES;  /* you should never do this. */
}
