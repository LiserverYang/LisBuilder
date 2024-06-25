#ifndef __LOGGER_H__
#define __LOGGER_H__

#include <string>

class Logger
{
public:
    void logError(std::string what);
    void logInfo(std::string what);
    void logWarn(std::string what);
};

#endif // __LOGGER_H__