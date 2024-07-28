#ifndef __CORE_H__
#define __CORE_H__

#include <vector>

template <typename T>
std::vector<T> operator+(std::vector<T> v1, std::vector<T> v2)
{
    std::vector<T> result = v1;
    result.insert(result.end(), v2.begin(), v2.end());
    return result;
}

template <typename T>
void operator+=(std::vector<T> &v1, std::vector<T> v2)
{
    v1.insert(v1.end(), v2.begin(), v2.end());
}

#endif