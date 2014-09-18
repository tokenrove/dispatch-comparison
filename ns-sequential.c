
#include "dispatch.h"

int next_state(void)
{
    static int c;
    return (c++) % N_ENTRIES;
}
