## 构建 Perl 5.36 指南
#### 安装 rpm-list-builder
```shell
$ pip3 install rpmlb
```
#### 使用 perl536.yml

该文件内已根据 perl-bootstrap.yml 的编译顺序调整好，且也使用了 bootstrap 进行构建

#### 下载 SOURCES
```shell
rpmlb --download fedpkg --branch f37 perl.yml perl536
```
使用上述命令，解析 yml 文件并从 Fedora Package Sources 内克隆仓库
记下所使用的文件夹，一般位于 /tmp 内，最开始会输出该路径

> 若提示 clone 时发生错误，请将 rpmlb/downloader/base_rpkg.py 第25行 加上 -a 参数

#### 使用 Mock 编译
```shell
rpmlb --build mock --mock-config fedora-36-x86_64 --work-directory /tmp/rpmlb-<directory> perl.yml perl536
```
这里使用 Mock 进行编译，需要将 `--work-directory` 后的参数指定为上一步所下载到的文件夹。Mock config为编译平台，可根据实际需求调整。本例中采用Fedora 36 x86_64为基准平台

#### 编译完成
可在 /var/lib/mock/fedora-36-x86_64/result 内找到生成的 rpm 包
