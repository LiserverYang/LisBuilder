#include "runner.h"
#include "TokenParser/tokenparser.h"
#include "Parser/AST.h"
#include "Parser/parser.h"
#include "evaluation.h"
#include "Runtime/CodeRuntime/symbol_table.h"
#include "Platform/FileIO/fileio.h"

using namespace Parser;

void run_runnable_statement(RunnableStatement *node)
{
    if (auto *condNode = dynamic_cast<ConditionStatementNode *>(node))
    {
        Variable if_ex = eval(condNode->if_expression);

        if (if_ex.getType() != BasicType::BOOL)
        {
            logger.logError("If statement expression must be bool type.");
        }

        if (std::get<bool>(if_ex.getValue()) == true)
        {
            run_runnable_statement(condNode->if_statement);
        }
        else
        {
            run_runnable_statement(condNode->else_statement);
        }
    }
    else if (auto *compNode = dynamic_cast<CompoundStatementNode *>(node))
    {
        for(int i = 0; i < compNode->statements.size(); i++)
        {
            run_runnable_statement(compNode->statements[i]);
        }
    }
    else if (auto *compNode = dynamic_cast<ExpressionNode *>(node))
    {
        eval(compNode);
    }
}

void run(Parser::AST ast)
{
    regist_all_functions();
    regist_all_varibles();

    for (int i = 0; i < ast.program.size(); i++)
    {
        run_runnable_statement(ast.program[i]);
    }
}

void run_file(FileIO io)
{
    TokenStream stream = TokenParser::parse(io);

    run(Parser::parse(stream));
}