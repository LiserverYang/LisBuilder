#include "tokenparser.h"
#include "token.h"

#include "Runtime/CompilerRuntime/variables.h"

#include <string>
#include <iostream>

using namespace TokenParser;

inline bool isLetter(char c)
{
    return 'a' <= c && 'z' >= c || c == '_';
}

inline bool isNameLetter(char c)
{
    return ('a' <= c && 'z' >= c) || ('0' <= c && '9' >= c) || c == '_';
}

inline int keywordPos(std::string str)
{
    for (int i = 0; i < sizeof(keywords) / MAX_KEYWORD_STR_SIZE; i++)
    {
        if (strcmp(keywords[i], str.c_str()) == 0)
        {
            return i;
        }
    }

    return -1;
}

TokenStream TokenParser::parse(FileIO file)
{
    TokenStream result;

    std::string code = file.read();

    int i = 0;

    int line = 1;
    int col = 1;

    while (i < code.size())
    {
        if (code[i] == '\n')
        {
            i++;
            line++;
            col = 0;

            continue;
        }

        if (code[i] == '\r')
        {
            i++;
            continue;
        }

        if (code[i] == ' ')
        {
            i++;
            col++;
            continue;
        }

        // 是字符
        if (isLetter(code[i]))
        {
            std::string cur_str = "";

            while (isNameLetter(code[i]) && i < code.size())
            {
                cur_str += code[i];
                i++;
                col++;
            }

            int pos = keywordPos(cur_str);

            if (pos == -1)
            {
                result.add(Token(TokenCode::TK_ID, cur_str, line, col - cur_str.size()));
            }
            else
            {
                result.add(Token((TokenCode)((int)TokenCode::TK_KW_IF + pos), cur_str, line, col - cur_str.size()));
            }

            continue;
        }

        // 是操作符
        switch (code[i])
        {
        case '=':
        {
            if (code[i + 1] == '=')
            {
                result.add(Token(TokenCode::TK_OP_IS_SAME, "==", line, col));
                i += 2;
                col += 2;
            }
            else
            {
                result.add(Token(TokenCode::TK_OP_IS, "=", line, col));
                i += 1;
                col += 1;
            }
            break;
        }
        case '!':
        {
            if (code[i + 1] == '=')
            {
                result.add(Token(TokenCode::TK_OP_ISNOT_SAME, "!=", line, col));
                i += 2;
                col += 2;
            }
            else
            {
                result.add(Token(TokenCode::TK_OP_NOT, "!", line, col));
                i += 1;
                col += 1;
            }
            break;
        }
        case '>':
        {
            if (code[i + 1] == '=')
            {
                result.add(Token(TokenCode::TK_OP_ISB, ">=", line, col));
                i += 2;
                col += 2;
            }
            else
            {
                result.add(Token(TokenCode::TK_OP_BIGGER, ">", line, col));
                i += 1;
                col += 1;
            }
            break;
        }
        case '<':
        {
            if (code[i + 1] == '=')
            {
                result.add(Token(TokenCode::TK_OP_ISS, "<=", line, col));
                i += 2;
                col += 2;
            }
            else
            {
                result.add(Token(TokenCode::TK_OP_SMALLER, "<", line, col));
                i += 1;
                col += 1;
            }
            break;
        }
        case '+':
        {
            result.add(Token(TokenCode::TK_OP_ADD, "+", line, col));
            i += 1;
            col += 1;
            break;
        }
        case '-':
        {
            result.add(Token(TokenCode::TK_OP_SUB, "-", line, col));
            i += 1;
            col += 1;
            break;
        }
        case '*':
        {
            result.add(Token(TokenCode::TK_OP_MUT, "*", line, col));
            i += 1;
            col += 1;
            break;
        }
        case '/':
        {
            if (code[i + 1] == '/')
            {
                while (code[i] != '\n' && code[i] < code.size())
                {
                    i++;
                }
                break;
            }
            result.add(Token(TokenCode::TK_OP_DVS, "/", line, col));
            i += 1;
            col += 1;
            break;
        }
        case '(':
        {
            result.add(Token(TokenCode::TK_OP_LEFT_PT, "(", line, col));
            i += 1;
            col += 1;
            break;
        }
        case ')':
        {
            result.add(Token(TokenCode::TK_OP_RIGHT_PT, ")", line, col));
            i += 1;
            col += 1;
            break;
        }
        case '[':
        {
            result.add(Token(TokenCode::TK_OP_LEFT_BK, "[", line, col));
            i += 1;
            col += 1;
            break;
        }
        case ']':
        {
            result.add(Token(TokenCode::TK_OP_RIGHT_BK, "]", line, col));
            i += 1;
            col += 1;
            break;
        }
        case '{':
        {
            result.add(Token(TokenCode::TK_OP_LEFT_CB, "{", line, col));
            i += 1;
            col += 1;
            break;
        }
        case '}':
        {
            result.add(Token(TokenCode::TK_OP_RIGHT_CB, "}", line, col));
            i += 1;
            col += 1;
            break;
        }
        case '"':
        {
            i += 1;
            col += 1;
            std::string str = "";
            while (code[i] != '"' && code[i] != '\n' && code[i] != '\r')
            {
                str += code[i];
                i += 1;
                col += 1;
            }
            if (code[i] == '"')
            {
                i += 1;
                col += 1;
            }
            result.add(Token(TokenCode::TK_STR, str, line, col));
            break;
        }
        case '\'':
        {
            i += 1;
            col += 1;
            std::string str = "";
            while (code[i] != '\'' && code[i] != '\n' && code[i] != '\r')
            {
                str += code[i];
                i += 1;
                col += 1;
            }
            if (code[i] == '\'')
            {
                i += 1;
                col += 1;
            }
            result.add(Token(TokenCode::TK_STR, str, line, col));
            break;
        }
        case ',':
        {
            result.add(Token(TokenCode::TK_NEXT_ARG, ",", line, col));
            i++;
            col++;
            break;
        }
        case '$':
        {
            result.add(Token(TokenCode::TK_VAR, "$", line, col));
            i++;
            col++;
            break;
        }
        case ';':
        {
            result.add(Token(TokenCode::TK_END_ST, ";", line, col));
            i++;
            col++;
            break;
        }
        default:
        {
            using namespace std::string_literals;
            logger.logError("Unknow letter '"s + code[i] + "' at line "s + std::to_string(line) + ", col " + std::to_string(col + 1));
        }
        }
    }

    return result;
}