/* Common entry point for generated code.
 */

#include <string.h>
#include <stdlib.h>
#include "dispatch.h"

int state_trk = 0;

int main(int argc, char **argv)
{
    if (argc < 2) abort();
    size_t count = atoi(argv[1]);
    while (--count)
        dispatch(next_state());
    return state_trk;
}
