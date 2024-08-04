#include "fileio.h"

#include <sys/stat.h>

FileIO::FileIO(std::string path) : _path(path)
{
    fileh = CreateFileW(std::wstring_convert<std::codecvt_utf8_utf16<wchar_t>>().from_bytes(_path).c_str(), GENERIC_READ | GENERIC_WRITE, FILE_SHARE_DELETE | FILE_SHARE_WRITE | FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    // 获取文件大小
    read_size();
}

std::string FileIO::read() noexcept
{
    if (-1 == access(_path.c_str(), 0))
        return "";

    if (!has_readpers())
        return "";

    // 文件太大，无法一次性读取
    if (size.HighPart > 0)
        return "";

    DWORD fileSize32 = static_cast<DWORD>(size.LowPart);
    std::string content(fileSize32, '\0');

    DWORD bytesRead;

    // 处理读取文件内容失败的情况
    if (!ReadFile(fileh, &content[0], fileSize32, &bytesRead, nullptr) || bytesRead != fileSize32)
        return "";

    return content;
}

void FileIO::write(std::string value) noexcept
{
    if (!has_writepers())
        return;

    SetFilePointer(fileh, 0, NULL, FILE_BEGIN);

    WriteFile(fileh, value.data(), value.length() * sizeof(std::string::value_type), nullptr, NULL);

    LARGE_INTEGER moveSize;
    moveSize.QuadPart = value.size();

    SetFilePointerEx(fileh, moveSize, NULL, FILE_BEGIN);
    SetEndOfFile(fileh);
}

time_t FileIO::get_last_time() noexcept
{
    struct stat result;

    if (stat(_path.c_str(), &result) == 0)
    {
        return result.st_mtime;
    }

    return 0;
}