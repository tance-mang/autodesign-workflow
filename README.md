# AutoDesign Workflow

AI 自动视觉设计与素材集成工作流 · Codex + Python · 本地运行

> 当前版本 V0.1：可运行的素材搜索、人工审核、引用替换与恢复工具。不是已经实现全部 V1.0 的自主设计 Agent。

## 快速开始（Windows PowerShell）

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
$env:PEXELS_API_KEY="你的密钥"
autodesign --project C:/your/project analyze
autodesign --project C:/your/project search "soft flowers" --mode hybrid --role hero
autodesign --project C:/your/project serve
```

浏览器自动打开本地审核中心。无需服务器。也可设置 PIXABAY_API_KEY 并传入 `--provider pixabay`。不会读取 .env，请通过环境变量配置；不要提交密钥。

## 已实现

- Pexels / Pixabay 独立适配，下载真实图片、Pillow 缩放压缩、哈希去重。
- auto 全自动批准；review 全部等待审核；hybrid 仅 background、decoration、texture 自动批准。
- 本地图片预览，采用、拒绝、保留候选；素材作者、来源、许可链接记录。
- assets/pending、approved、rejected 分类；状态转换保留原文件，避免破坏既有引用。
- 精确文本引用替换，支持单张和多个文件批量绑定；批准前禁止接入。
- 每次替换保存文件检查点；回滚前校验文件，拒绝覆盖后续编辑。
- 项目页面扫描与初始需求报告，Codex 结合报告完成具体设计。

## 自动接入和批量换图

创建 bindings.json（asset 为审核界面的素材 ID，也可从 .autodesign/manifest.json 获取）：

```json
[{"file":"pages/index.html","old":"old-hero.jpg","asset":"素材ID"}]
```

```powershell
autodesign --project C:/your/project integrate bindings.json
autodesign --project C:/your/project rollback
```

替换采用相对于代码文件的路径，适用于普通 HTML/CSS 相对路径。小程序根路径、Flutter pubspec、JS 构建器 import 需要 Codex 按框架调整，目前没有专用适配器。绑定采用精确字符串全量替换，请用唯一引用并检查 diff。快照不是 Git commit；操作前建议自行提交 Git 检查点。不要同时启动多个实例写同一项目。

## Codex 调用提示

请阅读本仓库 AGENTS.md，运行 analyze，结合项目业务形成 design/visual_identity.md、color_palette.json、typography.json、layout_rules.json、asset_requirements.json。先规划需求，再搜索；默认 hybrid，主视觉必须审核。只集成 approved 素材，保留业务逻辑，检查 diff。使用目标项目自身预览工具截图，由视觉模型或用户评价后最多修改三轮。不要宣称截图成功等于审美合格。

## 能力边界与路线

V0.2：收藏、重新搜索按钮、持久化断点、框架适配和事务恢复。
V0.3：Playwright 截图、可配置多模态评分与有限修复循环。
V1.0：可执行 YAML 总控、生成提供商、多项目模板、风格重新生成、完整自动缺失元素识别。

当前重新找图通过重复 search 使用新关键词实现；没有生成 API、自动审美评价、自动运行 Codex、完整视觉策划或一键任意项目改造。config/settings.yaml 是配置示意，CLI 参数是当前执行入口。素材搜索需要用户自行申请 API Key，缺少密钥不会伪造搜索结果。

## 来源与授权

界面展示提供商和作者。图片许可与代码 MIT 许可证分开；来源和许可链接保存在项目 manifest，不代表自动确认所有用途授权。请按 [Pexels API](https://www.pexels.com/api/documentation/) 与 [Pixabay API](https://pixabay.com/api/docs/) 的要求使用素材。不要用示意图片、商业作品截图或搜索缩略图冒充可用素材。

## 开发验证

```powershell
python -m unittest discover -s tests -v
```

欢迎 Issue / PR。MIT 开源。

#ai #codex #autodesign #asset-management #design-automation #python #local-first #visual-design #素材审核 #自动找图
