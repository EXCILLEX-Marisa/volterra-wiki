# 05 商业混合建模案例：SKY SA-1A 与 Revenger 2A

> 版本：v1 · 2026-11-13。本文按证据等级区分厂家公开说明、开发者公开发言、用户听感与研究假说；不将黑盒结果写成已证实的商业内部拓扑。

## 5.1 两个项目为什么值得一起研究？

Acustica SKY SA-1A 与 SevenTeamMusic Revenger 2A 都围绕光电压缩器的动态、谐波与器件状态开展建模，但其参考硬件不同，不能直接当成复刻同一台机器的精度竞赛。两种工程组织值得比较：SKY 公开强调 NOVA 的 Volterra/神经混合与多维模型训练，Revenger 则公开描述以电路白盒为主、网络对残差进行修正。我们应当研究它们提出了哪些可检验的系统行为，而不是先判断哪一种技术名词更高级。

## 5.2 SKY SA-1A：从相对独立的前级着色到状态耦合

[Acustica 官网](https://www.acustica-audio.com/shop/products/SKYSA1A) 描述 SKY 使用 NOVA 混合 Volterra 和神经处理，力图保留光电压缩、电子管与变压器对音色和动态的共同影响。[Gearspace 官方讨论](https://gearspace.com/threads/acustica-audio-sky-sa-1a-official-stam-audio-tube-opto-compressor-plug-in.1471233/) 的 #13 中，Acustica 技术人员 zaphod 表示其仍为 NOVA 家族，但模型系数来自不同于以往的 Trainer，研发中采用大量测量构造多维模型，并尝试过直接电路求解。开发者称，硬件中一些极强非线性器件的精细求解非常昂贵，压缩状态与谐波失真又难以像以往某些前级模型那样分离。

这支持“训练与模型组织显著变化”，却**不能证明整个实时 NOVA 引擎已被重构**。核阶次、低秩形式、是否使用实时门控、网络位于何处等均未公开到足以独立验证的程度。

可以提出一个候选状态条件化 Volterra 模型：

$$
y[n]=\sum_{p=1}^{P}\sum_{\boldsymbol k}h_p(s[n],\boldsymbol k)\prod_{i=1}^{p}x[n-k_i],
\qquad s[n+1]=G(s[n],x[n]).
$$

但这是本 Wiki 提出的研究表达，**不是 SKY 的已确认实现**。

## 5.3 Revenger 2A：白盒和网络残差的公开思路

[SevenTeamMusic 官方介绍](https://www.seventeammusic.com/plugins/revenger-2a) 描述了 LA-2A 电路建模与神经网络混合的路线，强调光电 T4、电子管、变压器与供电动态，并区分 Classic 纯电路和 Unit A 混合模式。由于产品页面没有提供完整可复核的内部网表、求解器代码和网络连接图，具体的逐元件运行方式与参数仍属于开发团队的公开声明，不等于本 Wiki 已独立复现。

一种可能的输出残差公式为 $\hat y=P_{\rm circuit}(x)+\Delta N_\theta(x,s)$，另一种可能方式则是神经网络修正物理状态更新。不能仅凭“电路 + 网络”就断言 Revenger 采用了哪一种公式。公开的包络拟合和 CPU/GPU 一致性指标可以作为待复核线索，但不等于完整的硬件波形、长期状态与听感验证。

## 5.4 压缩状态为什么会产生新的谐波？

不需要先假设一个静态三次多项式失真。若输入 $x(t)=A\cos(\omega t)$，而压缩的瞬时增益中包含二倍频成分 $g(t)=g_0+g_2\cos(2\omega t)$，则

$$
g(t)x(t)=A\left(g_0+\frac{g_2}{2}\right)\cos(\omega t)+
\frac{Ag_2}{2}\cos(3\omega t).
$$

三次谐波可以来自动态增益调制。真实机器中电子管、变压器及其他元件也可能同时产生失真，因此不能单凭 THD 就给谐波归因。类似地，双音边带并非高阶 Volterra 交叉核的独占特征，线性时变增益本身也能产生频率混合。

## 5.5 如何把产品线索变成研究实验？

第一，进行**历史条件化探针**：让两次测试在当前幅度和可观察 GR 接近的条件下，拥有不同的先前压缩历史，比较频响、谐波和瞬态。若存在差异，只能反驳单标量 GR 完全表征状态的假设，而不能直接证明光电或磁滞机制。

第二，进行弱探针加大信号驱动的频率依赖实验，区分侧链时变增益、工作点偏移和状态相关非线性。第三，比较低频驱动与高频双音/多音的互调结构，使用简单时变增益模型作为必要对照。第四，评估长时间释放、不同输入历史和休止后恢复。第五，记录 CPU、延迟、不同采样率、过采样档位与输出一致性。

对 Revenger 所宣称的变压器磁历史，要进一步区分“磁通积分带来的时间依赖”与严格路径依赖的磁滞。使用次回线、不同预磁化历史及速率扫掠，才能逐渐缩小可能的模型类别。

## 5.6 参考数据、独立性与结论范围

[SignalTrain LA-2A 数据集](https://zenodo.org/records/3824876) 为研究提供真实硬件输入输出数据的潜在起点。实际使用前需要核查许可、版本、时间对齐、采样率、不同硬件样本与测试划分。用 SKY 或 Revenger 的插件输出训练黑盒学生模型，至多能证明学生接近某个插件；没有相同硬件的独立配对录音，就不能证明接近真实硬件。

“听起来最像硬件”的用户评价属于主观线索，不是目前可以直接量化的行业共识。官网测量是厂商数据，Gearspace 技术发言是开发者公开陈述，本文的公式与实验矩阵是我们据此提出的研究计划。这三种证据必须保持区分。

## 5.7 对 Volterra Wiki 的意义

SKY 提醒我们：压缩状态可能与谐波和频率响应高度耦合，不能总把动态与静态着色独立处理。Revenger 提醒我们：白盒物理结构与数据驱动校正可以分工，不一定需要庞大网络替代全部电路。NAM 则提供统一的神经黑盒训练基线。三者共同构成研究 Volterra、长记忆状态和实时约简的可观察案例。

**本章结论：**商业产品的价值在于提出可检验问题，不在于提供未经证实的内部算法答案。严谨的研究必须区分公开声明、客观黑盒测量与真正复现硬件的证据。

## 参考资料

- [Acustica SKY SA-1A 官方页](https://www.acustica-audio.com/shop/products/SKYSA1A)
- [Gearspace SKY SA-1A 官方讨论帖](https://gearspace.com/threads/acustica-audio-sky-sa-1a-official-stam-audio-tube-opto-compressor-plug-in.1471233/)
- [SevenTeamMusic Revenger 2A](https://www.seventeammusic.com/plugins/revenger-2a)
- [SignalTrain LA-2A 数据集](https://zenodo.org/records/3824876)
