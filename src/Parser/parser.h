#ifndef __PARSER_H__
#define __PARSER_H__

#include "TokenParser/tokenparser.h"
#include "./AST.h"

namespace Parser
{
    using namespace TokenParser;

    ConditionStatementNode *parse_condition_statement(TokenStream &stream);
    CompoundStatementNode *parse_compound_statement(TokenStream &stream);
    std::vector<ExpressionNode *> parse_function_call_args(TokenStream &stream);
    FunctionCallExpressionNode *parse_function_call_expression(TokenStream &stream);
    std::vector<ExpressionNode *> parse_list_literal_args(TokenStream &stream);
    LiteralExpressionNode *parse_literal_expression(TokenStream &stream);
    ExpressionNode *parse_expression(TokenStream &stream);
    StatementNode *parse_statement(TokenStream &stream);
    RunnableStatement *parse_runnable_statement(TokenStream &stream);
    std::vector<RunnableStatement *> parse_runnable_statementlist(TokenStream &stream);
    
    AST parse(TokenStream &stream);
};

#endif // __PARSER_H__