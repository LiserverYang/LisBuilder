#ifndef __COMPILE_FUNCTION_H__
#define __COMPILE_FUNCTION_H__

#include "Runtime/CodeRuntime/variables.h"
#include "compile.h"

Variable compile(std::vector<Variable> args, CompileTarget target);

#endif // !__COMPILE_FUNCTION_H__