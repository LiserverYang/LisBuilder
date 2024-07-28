#include <iostream>

#include "Runtime/CompilerRuntime/variables.h"
#include "Runtime/CodeRuntime/variables.h"
#include "Runtime/CodeRuntime/symbol_table.h"

#include "Functions/functions.h"

void regist_all_functions()
{
    static bool registed = false;

    if (registed)
        return;

    registed = true;

    init_functions();
}