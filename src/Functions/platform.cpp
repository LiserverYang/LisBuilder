#include "functions.h"

FUNCTION_BEGIN(platform, BasicType::LIST)
{
    variable_table.set("platform", args[0]);

    return Variable((BasicType)3, Variable::ValueType());
}
FUNCTION_END