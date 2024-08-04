#include "functions.h"

#include "Compiler/acompiler.h"
#include "Compiler/compile_function.h"

FUNCTION_BEGIN(compile_static, BasicType::STRING, BasicType::STRING, BasicType::LIST, BasicType::LIST, BasicType::BOOL)
{
    return compile(args, CompileTarget::STATIC);
}
FUNCTION_END