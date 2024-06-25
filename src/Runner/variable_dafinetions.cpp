#include "Runtime/CodeRuntime/symbol_table.h"
#include "Runtime/CompilerRuntime/variables.h"

void regist_all_varibles()
{
    static bool registed = false;

    if (registed) return;

    registed = true;

    variable_table.regist("debug", Variable(BasicType::BOOL, argument.debug));
}