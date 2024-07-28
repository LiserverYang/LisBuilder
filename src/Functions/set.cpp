#include "functions.h"

Variable set(std::vector<Variable> args)
{
    CHECK_SIZE(args, 2);

    ASSERT(args[0].getType(), BasicType::STRING);

    variable_table.set(std::get<std::string>(args[0].getValue()), args[1]);

    return Variable((BasicType)3, Variable::ValueType());
}