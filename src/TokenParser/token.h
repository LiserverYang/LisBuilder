#ifndef __TOKEN_H__
#define __TOKEN_H__

#include <string>
#include <vector>

#include "Runtime/CompilerRuntime/variables.h"

namespace TokenParser
{
    enum class TokenCode
    {
        TK_UNDEFINED = 0,
        TK_ID, // abc

        TK_STR, // "abc" 'abc'

        TK_KW_IF,       // if
        TK_KW_ELSE,     // else
        TK_KW_TRUE,     // true
        TK_KW_FALSE,    // false
        TK_KW_NULL,     // null
        TK_KW_FUNCTION, // function
        TK_KW_RETURN,   // return

        TK_OP_ADD, // +
        TK_OP_SUB, // -
        TK_OP_MUT, // *
        TK_OP_DVS, // /

        TK_OP_IS,  // =
        TK_OP_NOT, // !

        TK_OP_LEFT_PT,    // (
        TK_OP_RIGHT_PT,   // )
        TK_OP_LEFT_BK,    // [
        TK_OP_RIGHT_BK,   // ]
        TK_OP_LEFT_CB,    // {
        TK_OP_RIGHT_CB,   // }
        TK_OP_IS_SAME,    // ==
        TK_OP_ISNOT_SAME, // !=
        TK_OP_BIGGER,     // >
        TK_OP_SMALLER,    // <
        TK_OP_ISB,        // >=
        TK_OP_ISS,        // <=

        TK_NEXT_ARG, // ,
        TK_VAR,      // $
        TK_END_ST,   // ;
    };

    const unsigned int MAX_KEYWORD_STR_SIZE = 10;

    const char keywords[][MAX_KEYWORD_STR_SIZE] = {
        "if",
        "else",
        "true",
        "false",
        "null",
        "function",
        "return"};

    class Token
    {
    public:
        TokenCode tokencode = TokenCode::TK_UNDEFINED;
        std::string value = "";

        int line = 0, col = 0;

        Token() = default;
        Token(TokenCode tc, std::string va, int ln, int cl) : tokencode(tc), value(va), line(ln), col(cl) {}
    };

    class TokenStream
    {
    private:
        std::size_t m_pos = 0;
        std::vector<Token> m_stream;

    public:
        Token &get()
        {
            return m_stream[m_pos];
        }

        TokenCode getcode()
        {
            return m_stream[m_pos].tokencode;
        }

        inline const std::size_t size()
        {
            return m_stream.size();
        }

        inline const std::size_t remain_token()
        {
            return m_stream.size() - m_pos - (m_stream.size() > 0);
        }

        void next()
        {
            m_pos += (m_pos < m_stream.size() - 1);
        }

        void previous()
        {
            m_pos -= (m_pos > 0);
        }

        void add(Token tk)
        {
            m_stream.push_back(tk);
        }

        void match(TokenCode code)
        {
            if (m_stream[m_pos].tokencode != code)
            {
                using namespace std::string_literals;
                logger.logWarn("Error code is "s + std::to_string((int)code));
                logger.logError("Not allowed token type at line "s + std::to_string(get().line) + ", col "s + std::to_string(get().col));
            }
            next();
        }
    };
};

#endif // __TOKEN_H__