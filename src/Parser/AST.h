#ifndef __AST_H__
#define __AST_H__

#include <string>
#include <vector>

namespace Parser
{
    // 定义AST节点基类
    class ASTNode
    {
    public:
        virtual ~ASTNode() {}
    };

    class RunnableStatement : public ASTNode
    {
    };

    class StatementNode : public RunnableStatement
    {
    };

    class ExpressionNode : public RunnableStatement
    {
    };

    class ConditionStatementNode : public StatementNode
    {
    public:
        ExpressionNode *if_expression;
        RunnableStatement *if_statement;
        RunnableStatement *else_statement;
    };

    class CompoundStatementNode : public StatementNode
    {
    public:
        std::vector<RunnableStatement *> statements;

        CompoundStatementNode(std::vector<RunnableStatement *> s) : statements(s) {}
    };

    class ReturnStatementNode : public StatementNode
    {
    public:
        ExpressionNode *return_value;
    };

    class FunctionCallExpressionNode : public ExpressionNode
    {
    public:
        std::string function_name;
        std::vector<ExpressionNode *> args;
    };

    class GetVaribleValueExpressionNode : public ExpressionNode
    {
    public:
        std::string varible_name;
    };

    class LiteralExpressionNode : public ExpressionNode
    {
    };

    class StringLiteral : public LiteralExpressionNode
    {
    public:
        std::string value;
    };

    class ListLiteral : public LiteralExpressionNode
    {
    public:
        std::vector<ExpressionNode *> value;
    };

    class BoolLiteral : public LiteralExpressionNode
    {
    public:
        bool value;
    };

    class NullLiteral : public LiteralExpressionNode
    {
    };

    // AST类
    class AST
    {
    public:
        std::vector<RunnableStatement *> program;

        AST(std::vector<RunnableStatement *> s) : program(s) {}
    };
};

#endif