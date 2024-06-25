#ifndef __ARGUMENT_H__
#define __ARGUMENT_H__

#include <string>

class Argument
{
public:
    bool debug = false;
    std::string file_path = "./build.pcc";

    void parse(int argc, const char** argv);
};

#endif // __ARGUMENT_H__