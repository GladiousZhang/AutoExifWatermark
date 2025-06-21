# AutoExifWatermark 📷✨

一个本地部署的自动化照片水印工具，为您的摄影作品增添专业签名。我本人是用在nas上面的，亦可运行于任何Linux设备，如果用在Windows上请自行修改。


![](\target\e338596223da2e06c3e3efb486654191.jpg)

![IMG_20250330_160732_1](\target\IMG_20250330_160732_1.jpeg)

---

### 📖 项目简介

AutoExifWatermark本质上是一个轻量级的、**可本地部署的Python脚本**。它通过监控指定的文件夹，为新加入的照片自动添加一个包含EXIF信息、品牌Logo和主色调色卡的精美水印。

本项目的开发初衷是为了在**NAS（网络附加存储）**上实现一个全自动、无人值守的照片处理流程，但其设计具有良好的通用性，可以轻松地运行在**任何Linux环境**中，例如：

-   家用NAS (如群晖、威联通，或比如我正在使用的飞牛OS)
-   树莓派 (Raspberry Pi)
-   一台专门的Linux家用服务器
-   您的个人Linux台式机或笔记本电脑
-   云服务器 (VPS)

### ✨ 主要特性

- **全自动化运行**: 设置为 `systemd` 服务后，可7x24小时无人值守运行，真正的“即放即忘”(set-it-and-forget-it)。
- **EXIF信息驱动**: 水印内容自动从照片的EXIF数据中读取，无需手动输入。
- **专业且美观的排版**: 模仿主流摄影社区的风格，水印布局优雅，信息清晰。
- **品牌Logo支持**: 自动识别相机**品牌**（如SONY, Canon, FUJIFILM），并加载对应的PNG Logo，如果找不到Logo则优雅地降级为显示纯文本。
- **动态色彩分析**: 利用K-Means聚类算法，自动提取照片主色调，生成与画面风格匹配的色卡。
- **自适应动态缩放**: 水印的所有元素（Logo、字体、间距）会根据照片的宽度进行等比缩放，确保在任何分辨率的图片上都保持协调美观。
- **健壮可靠**: 
    - 采用**定时轮询**机制，完美兼容各种文件系统（特别是网络挂载的共享文件夹）。
    - 包含了丰富的错误处理逻辑，对不规范的EXIF数据、有问题的图片格式都能稳健处理。
    - 失败的文件会自动移入`failed_photos`文件夹，便于排查。

### 🔧 安装与配置

#### 1. 克隆仓库
```bash
git clone https://github.com/gladiouszhang/AutoExifWatermark.git
cd AutoExifWatermark
```

#### 2. 准备环境 (基于 Debian/Ubuntu)
```bash
# 安装Python虚拟环境工具
sudo apt update
sudo apt install python3-venv
```

#### 3. 创建并配置虚拟环境
```bash
# 在项目根目录下创建venv文件夹
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装所有Python依赖
pip install --upgrade pip
pip install Pillow numpy scikit-learn
```

#### 4. 个性化配置

1.  **字体**: 将您喜欢的`.ttf`或`.otf`字体文件放入 `fonts/` 文件夹。推荐使用无衬线、字重丰富的字体。请确保脚本中的`FONT_FILE`变量指向正确的文件名。
2.  **品牌Logo**: 将您的相机**品牌Logo**（必须是`.png`格式，支持透明背景）放入 `logos/` 文件夹。
    - **重要**: Logo文件名需要与照片EXIF元数据中的`Make`字段**完全一致**（包括大小写）。例如，如果EXIF中的品牌是`SONY`，您的Logo文件就必须命名为`SONY.png`。
    - 目前已经放了sony、尼康、富士、奥林巴斯的，还可以自己加
3.  **文件夹结构**: 脚本会自动创建以下文件夹：
    - `source/`: **原始照片入口**。请将您要处理的照片放入此文件夹。
    - `target/`: **成品出口**。带有水印的照片会出现在这里。
    - `failed_photos/`: 如果某张照片处理失败，原始文件会被移动到这里，方便您排查问题。

#### 5. 设置为开机自启服务 (推荐用于服务器/NAS)

1.  **编辑服务文件**: 使用您喜欢的编辑器修改 `photo_watermark.service` 模板文件，确保其中的`User`, `Group`, 和路径（`WorkingDirectory`, `ExecStart`）正确无误。

2.  **部署服务文件**: 将编辑好的文件复制到`systemd`的目录中。
    ```bash
    sudo cp photo_watermark.service /etc/systemd/system/photo_watermark.service
    ```

3.  **启动并启用服务**:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable photo_watermark.service
    sudo systemctl start photo_watermark.service
    ```

4.  **检查服务状态**:
    ```bash
    sudo systemctl status photo_watermark.service
    # 您应该会看到 'active (running)' 的绿色字样
    ```

### 🚀 如何使用

1.  将您的原始照片（`.jpg`或`.jpeg`格式）复制或移动到项目下的 `source/` 文件夹中。
2.  等待片刻（默认轮询周期为10秒）。
3.  在 `target/` 文件夹中找到处理完成、带有精美水印的照片！原始照片会自动从`source/`文件夹中移除。

### 🤝 贡献

欢迎提交PR或Issue来改进这个项目！

### 📜 许可证

本项目采用 [MIT许可证](LICENSE)。
