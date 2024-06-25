#include <iostream>

#include "Runtime/CompilerRuntime/variables.h"
#include "Runtime/CodeRuntime/variables.h"
#include "Runtime/CodeRuntime/symbol_table.h"

#define REGIST(func)                        \
    do                                      \
    {                                       \
        function_table.regist(#func, func); \
    } while (0)

#define assert(t, v)                                                                                                                                     \
    if ((t) != (v))                                                                                                                                      \
    {                                                                                                                                                    \
        logger.logError(std::string("Not allowed type in function ") + __func__ + std::string(". Need to ") + BasicTypeToStr(v) + std::string(" but ") + \
                        BasicTypeToStr(t));                                                                                                              \
    }

Variable set(std::vector<Variable> args)
{
    assert(args[0].getType(), BasicType::STRING);

    variable_table.set(std::get<std::string>(args[0].getValue()), args[1]);

    return Variable((BasicType)3, Variable::ValueType());
}

Variable platform(std::vector<Variable> args)
{
    assert(args[0].getType(), BasicType::LIST);

    variable_table.set("platform", args[0]);

    return Variable((BasicType)3, Variable::ValueType());
}

Variable project(std::vector<Variable> args)
{
    assert(args[0].getType(), BasicType::STRING);

    variable_table.set("project_name", args[0]);

    return Variable((BasicType)3, Variable::ValueType());
}

#include <filesystem>
#include <string.h>

#include "Platform/FileIO/fileio.h"

template <typename T>
std::vector<T> operator+(std::vector<T> v1, std::vector<T> v2)
{
    std::vector<T> result = v1;
    result.insert(result.end(), v2.begin(), v2.end());
    return result;
}

template <typename T>
void operator+=(std::vector<T> &v1, std::vector<T> v2)
{
    v1.insert(v1.end(), v2.begin(), v2.end());
}

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

Variable deep_search_files(std::vector<Variable> args)
{
    assert(args[0].getType(), BasicType::STRING);
    assert(args[1].getType(), BasicType::STRING);

    std::vector<std::string> files = search_files(std::get<std::string>(args[0].getValue()), std::get<std::string>(args[1].getValue()));
    std::vector<Variable> result;

    result.resize(files.size());

    for (int i = 0; i < files.size(); i++)
    {
        result[i] = Variable(BasicType::STRING, files[i]);
    }

    return Variable(BasicType::LIST, result);
}

Variable compile_execute(std::vector<Variable> args)
{
    assert(args[0].getType(), BasicType::STRING);
    assert(args[1].getType(), BasicType::STRING);
    assert(args[2].getType(), BasicType::LIST);
    assert(args[3].getType(), BasicType::LIST);

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

    std::string target_command = "g++ -o " + t(args[1]) + "/" + t(args[0]) + " -std=c++" + t(variable_table.get("cpp_version")) + " " + tl(args[2]) + " " + tl(args[3]);

    system(target_command.c_str());

    return Variable(BasicType::STRING, target_command);
}

void print_variable(Variable var)
{
    switch (var.getType())
    {
    case BasicType::STRING:
    {
        std::cout << std::get<std::string>(var.getValue());
        break;
    }
    case BasicType::BOOL:
    {
        std::get<bool>(var.getValue()) ? std::cout << "true" : std::cout << "false";
        break;
    }
    case BasicType::LIST:
    {
        std::cout << "[";
        std::vector<Variable> list = std::get<std::vector<Variable>>(var.getValue());
        for (int i = 0; i < list.size() - 1; i++)
        {
            print_variable(list[i]);
            std::cout << ",";
        }
        print_variable(list[list.size() - 1]);
        std::cout << "]";
        break;
    }
    }
}

Variable print(std::vector<Variable> args)
{
    print_variable(args[0]);
    std::cout << "\n";

    return Variable((BasicType)3, Variable::ValueType());
}

Variable type(std::vector<Variable> args)
{
    return Variable(BasicType::STRING, BasicTypeToStr(args[0].getType()));
}

Variable need_update(std::vector<Variable> args)
{
    assert(args[0].getType(), BasicType::LIST);
    assert(args[1].getType(), BasicType::STRING);

    time_t bin_time = FileIO(std::get<std::string>(args[1].getValue())).get_last_time();

    for (int i = 0; i < args.size(); i++)
    {
        std::string path = std::get<std::string>(std::get<std::vector<Variable>>(args[0].getValue())[i].getValue());

        if (FileIO(path).get_last_time() > bin_time)
        {
            return Variable(BasicType::BOOL, true);
        }
    }

    return Variable(BasicType::BOOL, false);
}

Variable add(std::vector<Variable> args)
{
    // string add string
    if (args[0].getType() == BasicType::STRING)
    {
        assert(args[0].getType(), BasicType::STRING);
        assert(args[1].getType(), BasicType::STRING);

        return Variable(BasicType::STRING, std::get<std::string>(args[0].getValue()) + std::get<std::string>(args[1].getValue()));
    }
    else if (args[0].getType() == BasicType::LIST)
    {
        assert(args[0].getType(), BasicType::LIST);
        assert(args[1].getType(), BasicType::LIST);

        return Variable(BasicType::STRING, std::get<std::vector<Variable>>(args[0].getValue()) + std::get<std::vector<Variable>>(args[1].getValue()));
    }

    return Variable((BasicType)3, Variable::ValueType());
}

Variable append(std::vector<Variable> args)
{
    assert(args[0].getType(), BasicType::STRING);
    assert(variable_table.get(std::get<std::string>(args[0].getValue())).getType(), BasicType::LIST);

    std::get<std::vector<Variable>>(variable_table.get(std::get<std::string>(args[0].getValue())).getValue()).push_back(args[1]);

    return Variable((BasicType)3, Variable::ValueType());
}

void regist_all_functions()
{
    static bool registed = false;

    if (registed) return;

    registed = true;

    REGIST(set);
    REGIST(platform);
    REGIST(project);
    REGIST(deep_search_files);
    REGIST(compile_execute);
    REGIST(print);
    REGIST(type);
    REGIST(need_update);
    REGIST(add);
    REGIST(append);
}