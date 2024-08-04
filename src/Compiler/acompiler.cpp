#include "acompiler.h"

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

    return "NA";
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
    
    return AllowedCompiler::NA;
}