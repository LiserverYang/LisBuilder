#include "functions.h"

FUNCTION_BEGIN(_system, BasicType::STRING)
{
    int result = system(std::get<std::string>(args[0].getValue()).c_str());

    return Variable(BasicType::STRING, std::to_string(result));
}
FUNCTION_END