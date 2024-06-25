#ifndef __TOKENPARSER_H__
#define __TOKENPARSER_H__

#include "token.h"
#include "../Platform/FileIO/fileio.h"

namespace TokenParser
{
    TokenStream parse(FileIO file);
};

#endif // __TOKENPARSER_H__