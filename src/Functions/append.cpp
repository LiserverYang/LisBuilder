#include "functions.h"

Variable append(std::vector<Variable> args)
{
    CHECK_SIZE(args, 2);

    ASSERT(args[0].getType(), BasicType::STRING);
    ASSERT(variable_table.get(std::get<std::string>(args[0].getValue())).getType(), BasicType::LIST);

    std::get<std::vector<Variable>>(variable_table.get(std::get<std::string>(args[0].getValue())).getValue()).push_back(args[1]);

    return Variable((BasicType)3, Variable::ValueType());
}