#include "Runtime/CodeRuntime/symbol_table.h"
#include "Runtime/CompilerRuntime/variables.h"

void regist_all_varibles()
{
    static bool registed = false;

    if (registed) return;

    registed = true;

    variable_table.regist("debug", Variable(BasicType::BOOL, argument.debug));

    variable_table.regist("o_level", Variable(BasicType::STRING, "0"));
    variable_table.regist("compiler", Variable(BasicType::STRING, "g++"));
    variable_table.regist("compiler_version", Variable(BasicType::STRING, "^0.0.1"));
    variable_table.regist("dependent_project", Variable(BasicType::LIST, std::vector<Variable>()));
    variable_table.regist("cpp_version", Variable(BasicType::STRING, ""));
    variable_table.regist("include_dir", Variable(BasicType::LIST, std::vector<Variable>()));
    variable_table.regist("link_dir", Variable(BasicType::LIST, std::vector<Variable>()));
    variable_table.regist("link_lib", Variable(BasicType::LIST, std::vector<Variable>()));
    variable_table.regist("definetions", Variable(BasicType::LIST, std::vector<Variable>()));
    variable_table.regist("undefinetions", Variable(BasicType::LIST, std::vector<Variable>()));
}