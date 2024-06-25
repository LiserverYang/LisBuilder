#ifndef __EVALUATION_H__
#define __EVALUATION_H__

#include "Parser/AST.h"
#include "Runtime/CodeRuntime/variables.h"

Variable eval(Parser::ExpressionNode *node);

#endif