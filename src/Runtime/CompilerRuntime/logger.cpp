#include "logger.h"
#include <stdio.h>
#include <cassert>


void Logger::logError(std::string what)   
{
    fprintf_s(stderr, std::string("error: " + what + "\n").c_str());
    exit(-1);
}

void Logger::logInfo(std::string what)
{
    fprintf_s(stdout, std::string("info: " + what + "\n").c_str());
}

void Logger::logWarn(std::string what)
{
    fprintf_s(stdout, std::string("warn: " + what + "\n").c_str());
}