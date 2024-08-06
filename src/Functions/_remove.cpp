#include "functions.h"

Variable _remove(std::vector<Variable> args)
{
    CHECK_SIZE(args, 2);

    ASSERT(args[0].getType(), BasicType::STRING);
    ASSERT(variable_table.get(args[0].getValue<std::string>()).getType(), BasicType::LIST);

    std::vector<Variable> v = variable_table.get(args[0].getValue<std::string>()).getValue<std::vector<Variable>>();

    for(std::size_t i = 0; i < v.size(); i++)
    {
        const BasicType t = v[i].getType();

        if (t == args[1].getType())
        {
            if (t == BasicType::STRING)
            {
                if (v[i].getValue<std::string>().compare(args[1].getValue<std::string>()) == 0)
                {
                    v.erase(v.begin() + i);
                    break;
                }
            }
            else if (t == BasicType::BOOL)
            {
                if (v[i].getValue<bool>() == args[1].getValue<bool>())
                {
                    v.erase(v.begin() + i);
                    break;
                }
            }
        }
    }

    variable_table.get(args[0].getValue<std::string>()) = Variable(BasicType::LIST, v);

    return Variable((BasicType)3, Variable::ValueType());
}