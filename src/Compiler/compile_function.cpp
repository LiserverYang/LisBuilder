#include "compile_function.h"
#include "Runtime/CodeRuntime/symbol_table.h"

std::vector<std::string> to_arr(Variable var)
{
    std::vector<Variable> list = var.getValue<std::vector<Variable>>();
    std::vector<std::string> result = {};

    for (std::size_t i = 0; i < list.size(); i++)
    {
        result.push_back(list[i].getValue<std::string>());
    }

    return result;
}

Variable to_arr(std::vector<std::string> var)
{
    std::vector<Variable> result = {};

    for (int i = 0; i < var.size(); i++)
    {
        result.push_back(Variable(BasicType::STRING, var[i]));
    }

    return Variable(BasicType::LIST, result);
}

Variable compile(std::vector<Variable> args, CompileTarget target)
{
    CompileArgument argument(StrToCompiler(variable_table.get("compiler").getValue<std::string>()));

    argument.o_level = variable_table.get("o_level").getValue<std::string>();

    argument.compiler_version = variable_table.get("compiler_version").getValue<std::string>();
    argument.target_name = args[0].getValue<std::string>();
    argument.target_dir = args[1].getValue<std::string>();
    argument.part_build = args[4].getValue<bool>();

    argument.files_path = to_arr(args[2]);
    argument.arguments = to_arr(args[3]);

    argument.include_dir = to_arr(variable_table.get("include_dir"));
    argument.link_dir = to_arr(variable_table.get("link_dir"));
    argument.link_lib = to_arr(variable_table.get("link_lib"));
    argument.definetions = to_arr(variable_table.get("definetions"));
    argument.undefinetions = to_arr(variable_table.get("undefinetions"));

    std::vector<std::string> compile_command = argument.to_string();

    for(auto command : compile_command)
    {
        system(command.c_str());
    }

    return to_arr(compile_command);
}