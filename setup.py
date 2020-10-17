# -*- codeing = utf-8 -*-
# @Time : 2020/10/14 11:46
# @Author : Cj
# @File : setup.py
# @Software : PyCharm

from distutils.core import setup
from Cython.Build import cythonize
import os

'''
该文件的执行需要的在Terminal中输入   python setup.py build_ext --inplace ！！！
使用Cpython 编译python文件，关键函数编译成pyd文件（相当于dll）
'''
# 针对多文件情况设置，单文件就只写一个就行
# key_funs = ["amzComment.py", "register.py"]
key_funs = ["test.py"]

setup(
    name="XX app",
    ext_modules=cythonize(key_funs),
)

'''
1、将编译后的pyd文件的命名更改成与原py文件一致
2、删除编译后得到的c文件和原py文件
'''

print("——————", os.getcwd(), "——————")

files = os.listdir(os.getcwd())
print(files)

for fi in files:
    if fi.__contains__(".pyd"):
        re_name = fi.split(".")[0] + ".pyd"
        print(re_name)
        os.rename(fi, re_name)
    elif fi.__contains__(".c") or fi in key_funs:
        os.remove(fi)

# 运行方式 在原目录的命令行下执行