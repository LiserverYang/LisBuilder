#include "parser.h"
#include <iostream>

using namespace TokenParser;
using namespace Parser;

namespace Parser
{
    template <typename T>
    void operator+=(std::vector<T> &v1, std::vector<T> v2)
    {
        v1.insert(v1.end(), v2.begin(), v2.end());
    }

    ConditionStatementNode *parse_condition_statement(TokenStream &stream)
    {
        ConditionStatementNode *result = new ConditionStatementNode();

        stream.match(TokenCode::TK_KW_IF);
        stream.match(TokenCode::TK_OP_LEFT_PT);
        result->if_expression = parse_expression(stream);
        stream.match(TokenCode::TK_OP_RIGHT_PT);
        result->if_statement = parse_runnable_statement(stream);

        if (stream.getcode() == TokenCode::TK_KW_ELSE)
        {
            stream.match(TokenCode::TK_KW_ELSE);
            result->else_statement = parse_runnable_statement(stream);
        }

        return result;
    }

    CompoundStatementNode *parse_compound_statement(TokenStream &stream)
    {
        stream.match(TokenCode::TK_OP_LEFT_CB);
        CompoundStatementNode *result = new CompoundStatementNode(parse_runnable_statementlist(stream));
        stream.match(TokenCode::TK_OP_RIGHT_CB);
        return result;
    }

    std::vector<ExpressionNode *> parse_function_call_args(TokenStream &stream)
    {
        std::vector<ExpressionNode *> result;

        if (stream.getcode() != TokenCode::TK_OP_RIGHT_PT)
            result.push_back(parse_expression(stream));

        if (stream.getcode() == TokenCode::TK_NEXT_ARG)
        {
            stream.match(TokenCode::TK_NEXT_ARG);
            result += parse_function_call_args(stream);
        }

        return result;
    }

    FunctionCallExpressionNode *parse_function_call_expression(TokenStream &stream)
    {
        FunctionCallExpressionNode *result = new FunctionCallExpressionNode();
        result->function_name = stream.get().value;
        
        stream.match(TokenCode::TK_ID);
        stream.match(TokenCode::TK_OP_LEFT_PT);
        result->args = parse_function_call_args(stream);
        stream.match(TokenCode::TK_OP_RIGHT_PT);

        return result;
    }

    std::vector<ExpressionNode *> parse_list_literal_args(TokenStream &stream)
    {
        std::vector<ExpressionNode *> result;

        result.push_back(parse_expression(stream));

        if (stream.getcode() == TokenCode::TK_NEXT_ARG)
        {
            stream.match(TokenCode::TK_NEXT_ARG);
            result += parse_list_literal_args(stream);
        }

        return result;
    }

    LiteralExpressionNode *parse_literal_expression(TokenStream &stream)
    {
        if (stream.getcode() == TokenCode::TK_STR)
        {
            StringLiteral *result = new StringLiteral();
            result->value = stream.get().value;
            stream.match(TokenCode::TK_STR);
            return result;
        }
        else if (stream.getcode() == TokenCode::TK_OP_LEFT_BK)
        {
            ListLiteral *result = new ListLiteral();
            stream.match(TokenCode::TK_OP_LEFT_BK);
            if (stream.getcode() != TokenCode::TK_OP_RIGHT_BK)
                result->value = parse_list_literal_args(stream);
            stream.match(TokenCode::TK_OP_RIGHT_BK);
            return result;
        }
        else if (stream.getcode() == TokenCode::TK_KW_NULL)
        {
            return new NullLiteral();
        }
        else
        {
            BoolLiteral *result = new BoolLiteral();
            
            if (stream.getcode() == TokenCode::TK_KW_TRUE)
            {
                stream.match(TokenCode::TK_KW_TRUE);
                result->value = true;
            }
            else
            {
                stream.match(TokenCode::TK_KW_FALSE);
                result->value = false;
            }

            return result;
        }
    }

    ExpressionNode *parse_expression(TokenStream &stream)
    {
        if (stream.getcode() == TokenCode::TK_ID)
        {
            return parse_function_call_expression(stream);
        }
        else if (stream.getcode() == TokenCode::TK_OP_LEFT_PT)
        {
            stream.match(TokenCode::TK_OP_LEFT_PT);
            ExpressionNode *result = parse_expression(stream);
            stream.match(TokenCode::TK_OP_RIGHT_PT);
            return result;
        }
        else if (stream.getcode() == TokenCode::TK_VAR)
        {
            GetVaribleValueExpressionNode *result = new GetVaribleValueExpressionNode();
            stream.match(TokenCode::TK_VAR);
            stream.match(TokenCode::TK_OP_LEFT_CB);
            result->varible_name = stream.get().value;
            stream.match(TokenCode::TK_ID);
            stream.match(TokenCode::TK_OP_RIGHT_CB);
            return result;
        }
        else
        {
            return parse_literal_expression(stream);
        }
    }

    StatementNode *parse_statement(TokenStream &stream)
    {
        if (stream.getcode() == TokenCode::TK_KW_IF)
        {
            return parse_condition_statement(stream);
        }
        else
        {
            return parse_compound_statement(stream);
        }
    }

    RunnableStatement *parse_runnable_statement(TokenStream &stream)
    {
        if (stream.getcode() == TokenCode::TK_KW_IF || stream.getcode() == TokenCode::TK_OP_LEFT_CB || stream.getcode() == TokenCode::TK_KW_FUNCTION || stream.getcode() == TokenCode::TK_KW_RETURN)
        {
            return parse_statement(stream);
        }
        else
        {
            return parse_expression(stream);
        }
    }

    std::vector<RunnableStatement *> parse_runnable_statementlist(TokenStream &stream)
    {
        std::vector<RunnableStatement *> result;

        result.push_back(parse_runnable_statement(stream));

        if (stream.getcode() == TokenCode::TK_END_ST)
        {
            stream.match(TokenCode::TK_END_ST);
            result += parse_runnable_statementlist(stream);
        }

        return result;
    }

    AST parse(TokenParser::TokenStream &stream)
    {
        return parse_runnable_statementlist(stream);
    }
}