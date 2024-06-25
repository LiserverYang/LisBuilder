#include "evaluation.h"
#include <Runtime/CodeRuntime/symbol_table.h>

using namespace Parser;

Variable eval(Parser::ExpressionNode *node)
{
    if (auto *condNode = dynamic_cast<FunctionCallExpressionNode *>(node))
    {
        std::vector<Variable> args;

        args.resize(condNode->args.size());

        for (int i = 0; i < condNode->args.size(); i++)
        {
            args[i] = eval(condNode->args[i]);
        }

        return function_table.get(condNode->function_name)(args);
    }
    else if (auto *condNode = dynamic_cast<GetVaribleValueExpressionNode *>(node))
    {
        return variable_table.get(condNode->varible_name);
    }
    else if (auto *condNode = dynamic_cast<StringLiteral *>(node))
    {
        return Variable(BasicType::STRING, condNode->value);
    }
    else if (auto *condNode = dynamic_cast<ListLiteral *>(node))
    {
        std::vector<Variable> list_value;

        list_value.resize(condNode->value.size());

        for (int i = 0; i < condNode->value.size(); i++)
        {
            list_value[i] = eval(condNode->value[i]);
        }

        return Variable(BasicType::LIST, list_value);
    }
    else if (auto *condNode = dynamic_cast<BoolLiteral *>(node))
    {
        return Variable(BasicType::BOOL, condNode->value);
    }
    else if (auto *condNode = dynamic_cast<NullLiteral *>(node))
    {
        return Variable(BasicType::NULL, Variable::ValueType());
    }

    return Variable();
}