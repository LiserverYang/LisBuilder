#include "functions.h"
#include "Platform/FileIO/fileio.h"

FUNCTION_BEGIN(need_update, BasicType::LIST, BasicType::STRING)
{
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
FUNCTION_END