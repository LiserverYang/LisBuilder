#ifndef __ACOMPILER_H__
#define __ACOMPILER_H__

#include <string>

enum class AllowedCompiler
{
    GCC,
    GPP,
    CLANG,
    MSVC,
    NA
};

std::string CompilerToStr(AllowedCompiler cp);
AllowedCompiler StrToCompiler(std::string cp);

#endif // !__ACOMPILER_H__