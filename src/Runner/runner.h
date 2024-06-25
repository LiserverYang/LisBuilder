#ifndef __RUNNER_H__
#define __RUNNER_H__

#include "Parser/AST.h"
#include "Platform/FileIO/fileio.h"

void run(Parser::AST ast);
void run_file(FileIO io);

#endif