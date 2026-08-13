# LisBuilder

从LisEngine中抽离出来的编译库，现在包含两部分：

1. **BuildSystem** —— 用于编译 C++ 项目的 python 编译库（详细用法参见我的其它项目）。
2. **lisbuild** —— Lis 语言项目的构建工具（cargo 风格）。

## lisbuild —— Lis 项目构建工具

一个 Lis 项目只有一个编译单元：入口 `.lis` 文件（其余文件经 `impt` 由编译器
递归加载）。`lisproject.json`（全部字段可选）覆盖默认值：

```json
{
  "name": "myproj",
  "main": "main.lis",
  "include_dirs": ["lib"],
  "opt": 0
}
```

```
myproj/
  lisproject.json
  main.lis        # 入口(impt 其余模块)
  lib/…           # 本地模块(入口同目录自动可找;include_dirs 用于更远的位置)
  test/…          # `lisbuild test`:每个 .lis 是独立小程序,退出码 0 即通过
  build/          # 产物(gitignored):<name>.o + <name>.exe
```

```bash
python lisbuild.py new hello --dir /path/to       # 脚手架
python lisbuild.py build /path/to/hello --lisc <lisc.exe>   # 增量构建
python lisbuild.py run   /path/to/hello --lisc <lisc.exe>   # 构建+运行
python lisbuild.py test  /path/to/hello --lisc <lisc.exe>   # 跑 test/*.lis
python lisbuild.py clean /path/to/hello           # 清产物
```

- lisc.exe 通过 `--lisc`、环境变量 `LISC` 或 PATH 查找，并要求其旁有 `lstdlib/`。
- 增量：exe 比项目内所有 `.lis` 新则跳过（无操作构建瞬时完成）。
- 链接用系统 g++（Windows 需 MinGW bin 在 PATH）。
