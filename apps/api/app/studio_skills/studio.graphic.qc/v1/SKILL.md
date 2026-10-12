---
key: studio.graphic.qc
version: 1
source_kind: studio_builtin
---

使用注册的确定性检查工具检查已保存的Graphic Master及真实Renderer结果。结构检查包括画布顺序、封面、边距、文本估计溢出和声明支持的对比度；实际素材的权利、状态、原始字节及哈希继续由既有Domain Service验证。几何检查不等于渲染成功，也不能代替审美判断。旋转文本、透明背景或无法衡量的对比度必须明确报告覆盖率不足，不假装pass。最终PNG尺寸、MIME与哈希必须来自真实字节，结果精确绑定Master/render并保留人工审阅。
