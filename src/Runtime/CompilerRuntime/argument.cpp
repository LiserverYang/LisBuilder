#include "argument.h"
#include <string.h>

void Argument::parse(int argc, const char** argv)
{
    if (argc == 1) return;

    for(int i = 1; i < argc; i++)
    {
        if (strcmp(argv[i], "-debug") == 0)
        {
            debug = true;
        }
        else
        {
            file_path = argv[i];
        }
    }
}

Argument argument;