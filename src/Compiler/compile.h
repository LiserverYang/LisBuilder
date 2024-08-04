#ifndef __COMPILE_H__
#define __COMPILE_H__

#include <vector>
#include <unordered_map>

#include "acompiler.h"

enum class CompileTarget
{
    EXECUTE,
    STATIC,
    SHARED
};

class CompileArgument
{
public:
    AllowedCompiler compiler;
    std::vector<std::string> arguments;

    bool part_build = true; // build *.o file

    CompileTarget target = CompileTarget::EXECUTE;

    std::string compiler_version;
    std::string target_name;
    std::string target_dir;
    std::string o_level = "0"; // 0 - 3

    std::vector<std::string> include_dir;
    std::vector<std::string> link_dir;
    std::vector<std::string> link_lib;
    std::vector<std::string> definetions;
    std::vector<std::string> undefinetions;

    std::vector<std::string> files_path;

    CompileArgument() = default;
    CompileArgument(AllowedCompiler allowedcompiler) : compiler(allowedcompiler) {}
    CompileArgument(std::vector<std::string> args) : arguments(args) {}
    std::vector<std::string> to_string();
};

#endif // !__COMPILE_H__