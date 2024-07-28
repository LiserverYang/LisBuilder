#include "functions.h"

Variable type(std::vector<Variable> args)
{
    CHECK_SIZE(args, 1);
    
    return Variable(BasicType::STRING, BasicTypeToStr(args[0].getType()));
}