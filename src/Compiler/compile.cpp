#include "compile.h"
#include "Platform/FileIO/fileio.h"

#include "Runtime/CompilerRuntime/variables.h"

inline void insert(std::string &str, std::string v = "")
{
    str += " ";
    str += v;
    str += " ";
}

inline std::string get_file_name(std::string path)
{
    std::size_t pos = std::max(path.find_last_of("\\"), path.find_last_of("/")) + 1;
    std::string with_s = path.substr(pos, path.size() - pos);
    return with_s.substr(0, with_s.rfind("."));
}

inline std::string vector_to_str(std::vector<std::string> vec)
{
    std::string result = "";

    for (std::size_t i = 0; i < vec.size(); i++)
    {
        result += " ";
        result += vec[i];
    }

    return result;
}

std::vector<std::string> CompileArgument::to_string()
{
    // sub-command , sub-command , ... , main-command
    std::vector<std::string> result;
    std::vector<std::string> o_files;

    std::string compiler_str = CompilerToStr(compiler);
    std::string arguments = vector_to_str(this->arguments);

    insert(arguments, "-O" + o_level);

    for (auto dir : include_dir)
        insert(arguments, "-I" + dir);

    for (auto dir : link_dir)
        insert(arguments, "-L" + dir);

    for (auto lib : link_lib)
        insert(arguments, "-l" + lib);

    for (auto de : definetions)
        insert(arguments, "-D" + de);

    for (auto Ude : undefinetions)
        insert(arguments, "-U" + Ude);

    if (!part_build)
    {
        result.push_back(compiler_str + arguments + vector_to_str(files_path) + " -o " + target_dir + "/" + target_name);
        return result;
    }

    for (auto file : files_path)
    {
        std::string bin_str = target_dir + "/obj/" + get_file_name(file) + ".o";

        time_t src_time = FileIO(file).get_last_time();
        time_t bin_time = FileIO(bin_str).get_last_time();

        o_files.push_back(bin_str);

        if (bin_time >= src_time)
            continue;

        result.push_back(compiler_str + arguments + file + " -c " + " -o " + bin_str);
    }

    if (o_files.size() == 0)
        return result;

    switch (target)
    {
    case CompileTarget::EXECUTE:
        result.push_back(compiler_str + arguments + vector_to_str(o_files) + " -o " + target_dir + "/" + target_name);
        break;
    case CompileTarget::STATIC:
        result.push_back("ar -rcs " + target_dir + "/" + target_name + ".lib " + vector_to_str(o_files));
        break;
    default:
        break;
    }

    return result;
}