#include "functions.h"

#include "Compiler/acompiler.h"
#include "Compiler/compile_function.h"

FUNCTION_BEGIN(compile_execute, BasicType::STRING, BasicType::STRING, BasicType::LIST, BasicType::LIST, BasicType::BOOL)
{
    return compile(args, CompileTarget::EXECUTE);
}
FUNCTION_END