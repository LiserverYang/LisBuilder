#include "functions.h"
#include "Platform/FileIO/fileio.h"

#include <filesystem>
#include <string.h>

std::vector<std::string> search_files(const std::string &path, const std::string &suffix)
{
    std::vector<std::string> result;
    std::filesystem::path dir_path(path);

    for (const auto &entry : std::filesystem::directory_iterator(dir_path))
    {
        if (entry.is_directory())
        {
            std::vector<std::string> sub_result = search_files(entry.path().string(), suffix);
            result.insert(result.end(), sub_result.begin(), sub_result.end());
        }
        else if (entry.is_regular_file())
        {
            std::string file_suffix = entry.path().extension().string();
            if (file_suffix == suffix)
            { // 使用 == 而不是 strcmp
                result.push_back(entry.path().string());
            }
        }
    }

    return result;
}

FUNCTION_BEGIN(deep_search_files, BasicType::STRING, BasicType::STRING)
{
    std::vector<std::string> files = search_files(std::get<std::string>(args[0].getValue()), std::get<std::string>(args[1].getValue()));
    std::vector<Variable> result;

    result.resize(files.size());

    for (int i = 0; i < files.size(); i++)
    {
        result[i] = Variable(BasicType::STRING, files[i]);
    }

    return Variable(BasicType::LIST, result);
}
FUNCTION_END