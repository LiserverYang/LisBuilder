#include "functions.h"

void init_functions()
{
    REGIST(set);
    REGIST(platform);
    REGIST(project);
    REGIST(deep_search_files);
    REGIST(compile_execute);
    REGIST(compile_share);
    REGIST(compile_static);
    REGIST(print);
    REGIST(type);
    REGIST(need_update);
    REGIST(add);
    REGIST(append);

    function_table.regist("system", _system);
    function_table.regist("remove", _remove);
}