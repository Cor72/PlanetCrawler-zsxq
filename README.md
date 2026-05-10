# **[PlanetCrawler-zsxq](https://github.com/Cor72/PlanetCrawler-zsxq)**



一个知识星球爬虫，按年份爬取知识星球，并逐月生成对应的PDF



## 特别说明

本代码参考了另一个爬虫[zsxq-spider](https://github.com/wbsabc/zsxq-spider)

不过zsxq-spider中使用的 `v1.10` 接口似乎已经被官方弃用或限制了，请求会出现版本过低的报错，需要升级到 **`v2`** 接口。

我的需求只有按固定年份来爬取文字并逐月生成对应的PDF文档，对功能进行了大改，没法PR，所以又发布了一版



## 使用方法

 1.下载并配置python环境，参考教程（https://blog.csdn.net/sensen_kiss/article/details/141940274）

2.安装 wkhtmltox，https://wkhtmltopdf.org/downloads.html，安装后将 bin 目录加入到环境变量，参考教程（http://www.gocit.cn/posts/14.html）

3.克隆本仓库到本地，参考教程（https://blog.csdn.net/m0_63564748/article/details/148012046）

4.修改参数配置

| 参数名称                   | 说明               | 获取方法                     |
| :------------------------- | :----------------- | :--------------------------- |
| TARGET_YEAR = 2026         | 你想爬取的年份     | 自行填写                     |
| ZSXQ_ACCESS_TOKEN          | 登录凭证           | 浏览器登录后从Cookie中获取   |
| USER_AGENT                 | 浏览器标识         | 保持与登录时一致             |
| GROUP_ID                   | 知识星球中的小组ID | 浏览器地址栏或网络请求中查看 |
| PDF_FILE_NAME = '文件.pdf' | 生成PDF文件的名字  | 自行填写                     |



## 声明

请合理使用本代码，仅供个人学习备份，请勿二次倒卖。