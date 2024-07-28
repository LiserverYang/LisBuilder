#include <iostream>

#include "./TokenParser/tokenparser.h"
#include "./Parser/parser.h"

#include "Runner/runner.h"

/*
 * Application entry point
 */
int main(int argc, const char **argv)
{
    // Parse argument
    argument.parse(argc, argv);

    // run
    run_file(argument.file_path);

    return 0;
}