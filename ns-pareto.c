
#include "dispatch.h"
#include <math.h>
#include <stdlib.h>

int next_state(void)
{
    if (fmod((double)rand(), 100.0d) < 80.0d)
        return 42 % N_ENTRIES;
    return rand() % N_ENTRIES;  /* you should never do this. */
}
