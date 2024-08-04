#ifndef __FUNCTIONS_H__
#define __FUNCTIONS_H__

#include "Runtime/CodeRuntime/variables.h"
#include "Runtime/CompilerRuntime/variables.h"
#include "Runtime/CodeRuntime/variables.h"
#include "Runtime/CodeRuntime/symbol_table.h"
#include "Runtime/CompilerRuntime/core.h"

#define REGIST(func)                        \
    do                                      \
    {                                       \
        function_table.regist(#func, func); \
    } while (0)

#define ASSERT(t, v)                                                                                                            \
    do                                                                                                                          \
    {                                                                                                                           \
        if ((t) != (v))                                                                                                         \
        {                                                                                                                       \
            logger.logError(std::string("Not allowed type in function ") + __func__ + ". Need " + BasicTypeToStr(v) + " but " + \
                            BasicTypeToStr(t));                                                                                 \
        }                                                                                                                       \
    } while (0)

#define FUNCTION_HEADER(name) Variable name(std::vector<Variable> args)

#define FUNCTION_BEGIN(name, ...)                                                                                     \
    Variable name(std::vector<Variable> args)                                                                         \
    {                                                                                                                 \
        std::vector<BasicType> vars = {__VA_ARGS__};                                                                  \
        if (vars.size() != args.size())                                                                               \
            logger.logError(std::string("Unmatched the number of args list when calling function '") + #name + "'."); \
        for (std::size_t i = 0; i < vars.size(); i++)                                                                 \
            ASSERT(args[i].getType(), vars[i]);

#define FUNCTION_END \
    }

#define CHECK_SIZE(args, realsize)                                                                                       \
    do                                                                                                                   \
    {                                                                                                                    \
        if (args.size() != realsize)                                                                                     \
        {                                                                                                                \
            logger.logError(std::string("Unmatched the number of args list when calling function '") + __func__ + "'."); \
        }                                                                                                                \
    } while (0)

FUNCTION_HEADER(_system);
FUNCTION_HEADER(add);
FUNCTION_HEADER(append);
FUNCTION_HEADER(compile_execute);
FUNCTION_HEADER(compile_share);
FUNCTION_HEADER(compile_static);
FUNCTION_HEADER(deep_search_files);
FUNCTION_HEADER(need_update);
FUNCTION_HEADER(platform);
FUNCTION_HEADER(print);
FUNCTION_HEADER(project);
FUNCTION_HEADER(set);
FUNCTION_HEADER(type);

void init_functions();

#endif // __FUNCTIONS_H__