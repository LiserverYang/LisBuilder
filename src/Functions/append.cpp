#include "functions.h"

Variable append(std::vector<Variable> args)
{
    CHECK_SIZE(args, 2);

    ASSERT(args[0].getType(), BasicType::STRING);
    ASSERT(variable_table.get(std::get<std::string>(args[0].getValue())).getType(), BasicType::LIST);

    auto v = variable_table.get(args[0].getValue<std::string>()).getValue<std::vector<Variable>>();
    
    for(auto it : args[1].getValue<std::vector<Variable>>())
    {
        v.push_back(it);
    }

    variable_table.get(args[0].getValue<std::string>()) = Variable(BasicType::LIST, v);

    return Variable((BasicType)3, Variable::ValueType());
}