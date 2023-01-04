# 具体讲稿

Low Memory Killer Daemon(LMKD)早在2013年被提交进AOSP代码库，其一开始就有两个部分的功能：

1、基于Memory的CGroup进行进程的回收；

2、作为frameworks与kernel的沟通桥梁传递参数与信息；

但由于kernel始终存在lowmemorykiller驱动，因此LMKD的第一个功能始终没有被启用。

> CGroup：将进程进行分组，为了对一组进程进行统一的资源监控和限制。

