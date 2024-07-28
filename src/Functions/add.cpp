#include "functions.h"

Variable add(std::vector<Variable> args)
{
    CHECK_SIZE(args, 2);

    // string add string
    if (args[0].getType() == BasicType::STRING)
    {
        ASSERT(args[0].getType(), BasicType::STRING);
        ASSERT(args[1].getType(), BasicType::STRING);

        return Variable(BasicType::STRING, std::get<std::string>(args[0].getValue()) + std::get<std::string>(args[1].getValue()));
    }
    else if (args[0].getType() == BasicType::LIST)
    {
        ASSERT(args[0].getType(), BasicType::LIST);
        ASSERT(args[1].getType(), BasicType::LIST);

        return Variable(BasicType::STRING, std::get<std::vector<Variable>>(args[0].getValue()) + std::get<std::vector<Variable>>(args[1].getValue()));
    }

    return Variable((BasicType)3, Variable::ValueType());
}