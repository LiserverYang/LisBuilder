#include "functions.h"

#include <iostream>

void print_variable(Variable var)
{
    switch (var.getType())
    {
    case BasicType::STRING:
    {
        std::cout << std::get<std::string>(var.getValue());
        break;
    }
    case BasicType::BOOL:
    {
        std::get<bool>(var.getValue()) ? std::cout << "true" : std::cout << "false";
        break;
    }
    case BasicType::LIST:
    {
        std::cout << "[";
        std::vector<Variable> list = std::get<std::vector<Variable>>(var.getValue());
        for (int i = 0; i < list.size() - 1; i++)
        {
            print_variable(list[i]);
            std::cout << ",";
        }
        print_variable(list[list.size() - 1]);
        std::cout << "]";
        break;
    }
    }
}

// 非强制类型 不判断
Variable print(std::vector<Variable> args)
{
    CHECK_SIZE(args, 1);

    print_variable(args[0]); 
    std::cout << "\n";

    return Variable((BasicType)3, Variable::ValueType());
}