#ifndef __SYMBOL_TABLE_H__
#define __SYNBOL_TABLE_H__

#include <unordered_map>

#include "Runtime/CompilerRuntime/variables.h"

#include "Parser/AST.h"
#include "variables.h"

template <class T, class V>
class Table
{
protected:
    std::unordered_map<T, V> map;

public:
    virtual void log_not_found_error(T key) = 0;

    void regist(T name, V func)
    {
        map.insert(std::pair<T, V>(name, func));
    }

    virtual void check(T key)
    {
        if (map.find(key) == map.end())
        {
            log_not_found_error(key);
        }
    }

    inline bool is(T key)
    {
        return (map.find(key) != map.end());
    }

    void set(T name, V func)
    {
        map[name] = func;
    }

    void remove(T name)
    {
        map.erase(name);
    }

    V get(T name)
    {
        check(name);
        return map[name];
    }
};

using function_type = Variable (*)(std::vector<Variable>);

class FunctionTable : public Table<std::string, function_type>
{
public:
    virtual void check(std::string key)
    {
        if (map.find(key) == map.end())
        {
            log_not_found_error(key);
        }

        if (map[key] == nullptr)
        {
            logger.logError("Not defined function " + key);
        }
    }

    virtual void log_not_found_error(std::string key) override final
    {
        logger.logError("Can't find function " + key);
    }
};

class VariableTable : public Table<std::string, Variable>
{
    virtual void log_not_found_error(std::string key) override final
    {
        logger.logError("Can't find variable " + key);
    }
};

void regist_all_functions();
void regist_all_varibles();

extern FunctionTable function_table;
extern VariableTable variable_table;

#endif