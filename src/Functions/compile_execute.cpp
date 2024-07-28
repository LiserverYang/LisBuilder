#include "functions.h"

enum class AllowedCompiler
{
    GCC,
    GPP,
    CLANG,
    MSVC,
    NA
};

std::string CompilerToStr(AllowedCompiler cp)
{
    switch(cp)
    {
    case AllowedCompiler::GCC:
        return "gcc";
    case AllowedCompiler::GPP:
        return "g++";
    case AllowedCompiler::CLANG:
        return "clang";
    case AllowedCompiler::MSVC:
        return "msvc";
    case AllowedCompiler::NA:
        return "NA";
    }

    return "";
}

AllowedCompiler StrToCompiler(std::string cp)
{
    if (cp == "gcc")
    {
        return AllowedCompiler::GCC;
    }
    else if (cp == "g++")
    {
        return AllowedCompiler::GPP;
    }
    else if (cp == "clang")
    {
        return AllowedCompiler::CLANG;
    }
    else if (cp == "msvc")
    {
        return AllowedCompiler::MSVC;
    }
    else
    {
        return AllowedCompiler::NA;
    }
}

void check_compiler(std::string compiler_name, std::string compiler_version)
{
    AllowedCompiler compiler = StrToCompiler(compiler_name);

    if (compiler == AllowedCompiler::NA)
        logger.logError("Not allowed compiler.");

    // TODO Finish check
}

FUNCTION_BEGIN(compile_execute, BasicType::STRING, BasicType::STRING, BasicType::LIST, BasicType::LIST)
{
    auto t = [&](Variable v)
    {
        return std::get<std::string>(v.getValue());
    };

    auto tl = [&](Variable v)
    {
        std::vector<Variable> list = std::get<std::vector<Variable>>(v.getValue());

        std::string result;

        for (int i = 0; i < list.size(); i++)
        {
            result += " " + t(list[i]);
        }

        return result;
    };

    check_compiler(t(variable_table.get("compiler")), t(variable_table.get("compiler_version")));

    // TODO Update command line
    std::string target_command = std::string("g++") + " -o " + t(args[1]) + "/" + t(args[0]) + " -std=c++" + t(variable_table.get("cpp_version")) + " " + tl(args[2]) + " " + tl(args[3]);

    system(target_command.c_str());

    return Variable(BasicType::STRING, target_command);
}
FUNCTION_END