#ifndef __FILEIO_H__
#define __FILEIO_H__

#include <locale>
#include <string>
#include <cstring>
#include <codecvt>

#include <Windows.h>
#include <io.h>

/*
一个对文件的输入/输出控制类，包含了基本的读与写，以及对于权限的判断
*/
class FileIO
{
private:
    // 文件路径
    std::string _path = "";
    // 通过CreateFile函数获取的文件句柄
    HANDLE fileh;
    // 通过read_size函数获取的文件大小
    LARGE_INTEGER size;

public:
    FileIO() = delete;
    FileIO(std::string path);

    ~FileIO() { CloseHandle(fileh); }

    /*
    检查文件是否存在
    */
    bool check() noexcept { return access(_path.c_str(), 0x00) != -1; }

    /*
    检查文件是否有读权限
    */
    inline bool has_readpers() noexcept { return access(_path.c_str(), 0x02) == 0; }

    /*
    检查文件是否有写权限
    */
    inline bool has_writepers() noexcept { return access(_path.c_str(), 0x04) == 0; }

    /*
    读取文件大小
    */
    void read_size() { GetFileSizeEx(fileh, &size); }

    /*
    读取文件 返回字符串
    */
    std::string read() noexcept;

    /*
    覆盖式地写入
    */
    void write(std::string value) noexcept;

    /*
    获取文件路径
    */
    inline std::string getpath() { return _path; }

    /*
    读取文件时间戳
    */
    time_t get_last_time() noexcept;
};

#endif // __FILEIO_H__