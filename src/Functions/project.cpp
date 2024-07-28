#include "functions.h"

FUNCTION_BEGIN(project, BasicType::STRING)
{
    variable_table.set("project_name", args[0]);

    return Variable((BasicType)3, Variable::ValueType());
}
FUNCTION_END