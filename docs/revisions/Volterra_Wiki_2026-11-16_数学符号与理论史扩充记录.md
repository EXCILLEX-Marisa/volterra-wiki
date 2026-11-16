# Volterra Wiki 数学符号与理论史扩充记录

**日期：2026-11-16**

## 修改范围

本轮围绕两项工作展开：扩展《00》的全书数学符号与运算记法索引；扩展《01》的 Volterra 理论历史导论。同步维护合订版、README 与编辑规范。

## 00：数学符号与运算记法

原 0.8 节仅覆盖输入输出、阶次、记忆长度、核、状态和参数等基础符号。本轮扩展为十个子节：

1. 信号、时间与模型变量；
2. 基本代数、求和与大小关系；
3. 关系、定义与集合记法；
4. 微积分、差分与泛函导数；
5. 线性代数、张量与系统算子；
6. 信号变换与输入—输出映射；
7. 集合、数域与函数空间；
8. 概率、统计与随机过程；
9. 优化、极限与计算复杂度；
10. 全书符号作用域与重名规则。

重点解释求和与连乘、极限、偏导、梯度、散度、旋度、Fréchet/Gâteaux 导数、泛函导数、离散差分、矩阵转置、行列式、秩、迹、张量积、Hadamard 积、函数复合、卷积、Fourier/Laplace/Z 变换、函数空间、期望与优化记号。

特别明确以下容易混淆的区别：
- 完整多维 Volterra 核 h_p 与对角支路核 g_p。
- 当前阶次 p、最高保留阶数 P 与历史窗口长度 M。
- Volterra 核与 Wiener 核的定义和归一化不能仅凭名称或符号互换。
- Fréchet 导数与 Gâteaux 方向导数的条件不同。
- Dirac 冲激、Kronecker delta 与泛函变分中的 delta 需要按对象类型区分。
- 点积、Hadamard 逐元素乘积、张量积、函数复合和卷积是不同运算。

## 01：理论史扩充

历史导论增加并细化以下阶段：

- 1887—1913：Volterra 早期泛函研究、Fréchet 1910 年连续泛函表示、Volterra 1912 年讲授与 1913 年专著。
- 1930—1949：Wiener 的随机过程与 Wiener 积分、1938 年 Homogeneous Chaos、1942 年非线性 RLC 案例、Cameron–Martin 1947 年 Fourier–Hermite 正交展开、1949 年向 Y. W. Lee 团队介绍相关理论。
- 1950—1960 年代：Bose Gate Function Model、Lee–Schetzen 互相关辨识、Wiener 核与 Volterra 核的区别，以及 Barrett、Brilliant、George、Zames、Sandberg、Schetzen、Alper、Bush 的系统理论与离散模型工作。
- 1970—1980 年代：核辨识综述、Schetzen 1980 年专著、Boyd–Chua 1985 年衰减记忆与 Volterra 逼近理论。
- 1990—2000 年代：Laguerre/Kautz 正交基约简、Campello 等人的最优 Laguerre 展开、Volterra-PARAFAC 张量分解。
- 2010 年代至今：正交基综述、ESS 与音频设备核辨识、电子管设备多方差辨识、简化非线性 Volterra 与多项式 ADAA，以及现代神经网络、物理模型和混合建模的交汇。

历史叙述将 Volterra、Wiener、核辨识、正交基与张量约简视为相关但并非单线继承的研究路线。Lee–Schetzen 方法直接辨识 Wiener 核；要得到采用 Volterra 记法的核，必须考虑相应统计条件与核转换关系。

## 参考文献

在 01 原有 [VH1]—[VH7] 基础上增加 [VH8]—[VH14]，覆盖 Volterra 1887、Fréchet 1910、Wiener 1938、Cameron–Martin 1947、Laguerre 最优展开、Volterra-PARAFAC 与正交基非线性模型综述。

## 同步文件

- 00_前置概念与术语约定_图文版.md
- 01_Volterra级数_图文版.md
- downloads/Volterra_Wiki_00-06_完整合订版_GitHub图床.md
- README.md
- docs/EDITORIAL_GUIDE.md
- 本修订记录

本轮未新增或修改 SVG 配图。