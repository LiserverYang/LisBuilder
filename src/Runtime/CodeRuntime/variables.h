#ifndef __VARIBLES_H__
#define __VARIBLES_H__

#include <variant>
#include <string>
#include <vector>

#include "Runtime/CompilerRuntime/variables.h"

#undef NULL

enum class BasicType
{
    STRING,
    BOOL,
    LIST,
    NULL,
};

inline std::string BasicTypeToStr(BasicType b)
{
    switch (b)
    {
    case BasicType::STRING:
        return "string";
    case BasicType::BOOL:
        return "bool";
    case BasicType::LIST:
        return "list";
    case BasicType::NULL:
        return "null";
    }

    return "";
}

class Variable
{
public:
    using ValueType = std::variant<std::string, bool, std::vector<Variable>>;

    Variable() = default;

    Variable(BasicType type, ValueType value) : type(type), value(value) {}

    // 设置值
    void setValue(BasicType type, const ValueType &value)
    {
        this->type = type;
        this->value = value;
    }

    // 获取值
    ValueType getValue() const
    {
        if (type == BasicType::NULL)
        {
            logger.logError("Can't get null variable value.");
        }

        return value;
    }

    template<class T>
    T getValue() const
    {
        return std::get<T>(value);
    }

    // 获取类型
    BasicType getType() const
    {
        return type;
    }

    bool operator == (const Variable &other) const
    {
        return ((type == other.type) && (value == other.value)); 
    }

private:
    BasicType type;  // 存储类型
    ValueType value; // 存储值
};

#endif // __VARIBLES_H__