with open(r'C:\Users\Administrator\Desktop\TwitCanva\src\components\canvas\NodeControls.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

# === 1. Replace IMAGE_MODELS ===
old_models = """const IMAGE_MODELS = [
    {
        id: 'gpt-image-1.5',
        name: 'GPT Image 1.5',
        provider: 'openai',
        supportsImageToImage: true,
        supportsMultiImage: true,
        recommended: true,
        resolutions: ["Auto", "1K", "2K", "4K"],
        // OpenAI uses exact pixel sizes, not aspect ratios
        aspectRatios: ["Auto", "1024x1024", "1536x1024", "1024x1536"]
    },
    {
        id: 'gemini-pro',
        name: 'Nano Banana Pro',
        provider: 'google',
        supportsImageToImage: true,
        supportsMultiImage: true,
        resolutions: ["1K", "2K", "4K"],
        aspectRatios: ["Auto", "1:1", "9:16", "16:9", "3:4", "4:3", "3:2", "2:3", "5:4", "4:5", "21:9"]
    },
    // Kling AI models - Consolidated: removed legacy v1, v2, v2-new
    {
        id: 'kling-v1-5',
        name: 'Kling V1.5',
        provider: 'kling',
        supportsImageToImage: true, // V1.5 supports image_reference for subject/face
        supportsMultiImage: false,
        resolutions: ["1K", "2K"],
        aspectRatios: ["Auto", "1:1", "9:16", "16:9", "3:4", "4:3", "3:2", "2:3", "21:9"]
    },
    {
        id: 'kling-v2-1',
        name: 'Kling V2.1',
        provider: 'kling',
        supportsImageToImage: false, // V2.1 requires Multi-Image API
        supportsMultiImage: true,    // Use Multi-Image API with subject_image_list
        recommended: true,
        resolutions: ["1K", "2K"],
        aspectRatios: ["Auto", "1:1", "9:16", "16:9", "3:4", "4:3", "3:2", "2:3", "21:9"]
    },
];"""

new_models = """const IMAGE_MODELS = [
    {
        id: 'grsai/gpt-image-2',
        name: 'GPT Image 2',
        provider: 'grsai',
        supportsImageToImage: true,
        supportsMultiImage: true,
        recommended: true,
        resolutions: ["Auto", "1K", "2K", "4K"],
        aspectRatios: ["Auto", "1:1", "9:16", "16:9", "3:4", "4:3", "3:2", "2:3", "5:4", "4:5", "21:9"]
    },
    {
        id: 'grsai/gpt-image-2-vip',
        name: 'GPT Image 2 VIP',
        provider: 'grsai',
        supportsImageToImage: true,
        supportsMultiImage: true,
        resolutions: ["Auto", "1K", "2K", "4K"],
        aspectRatios: ["Auto", "1:1", "9:16", "16:9", "3:4", "4:3", "3:2", "2:3", "5:4", "4:5", "21:9"]
    },
    {
        id: 'grsai/nano-banana-pro',
        name: 'Nano Banana Pro',
        provider: 'grsai',
        supportsImageToImage: true,
        supportsMultiImage: true,
        resolutions: ["Auto", "1K", "2K", "4K"],
        aspectRatios: ["Auto", "1:1", "9:16", "16:9", "3:4", "4:3", "3:2", "2:3", "5:4", "4:5", "21:9"]
    },
    {
        id: 'grsai/nano-banana-pro-vip',
        name: 'Nano Banana Pro VIP',
        provider: 'grsai',
        supportsImageToImage: true,
        supportsMultiImage: true,
        resolutions: ["Auto", "1K", "2K", "4K"],
        aspectRatios: ["Auto", "1:1", "9:16", "16:9", "3:4", "4:3", "3:2", "2:3", "5:4", "4:5", "21:9"]
    },
    {
        id: 'grsai/nano-banana-2',
        name: 'Nano Banana 2',
        provider: 'grsai',
        supportsImageToImage: true,
        supportsMultiImage: true,
        resolutions: ["Auto", "1K", "2K"],
        aspectRatios: ["Auto", "1:1", "9:16", "16:9", "3:4", "4:3", "3:2", "2:3", "5:4", "4:5", "21:9"]
    },
    {
        id: 'grsai/nano-banana',
        name: 'Nano Banana',
        provider: 'grsai',
        supportsImageToImage: false,
        supportsMultiImage: false,
        resolutions: ["Auto", "1K", "2K"],
        aspectRatios: ["Auto", "1:1", "9:16", "16:9", "3:4", "4:3", "3:2", "2:3"]
    },
];"""

if old_models in c:
    c = c.replace(old_models, new_models)
    print('1. IMAGE_MODELS replaced OK')
else:
    print('FAIL: IMAGE_MODELS not found!')
    # Show what's there
    idx = c.find('const IMAGE_MODELS')
    if idx >= 0:
        print(c[idx:idx+200])

# === 2. Add grsai provider icon check ===
old_icon = """currentImageModel.provider === 'kling' ? (
                                        <KlingIcon size={14} />
                                    ) : (
                                        <ImageIcon size={12} className="text-cyan-400" />
                                    )}"""

new_icon = """currentImageModel.provider === 'kling' ? (
                                        <KlingIcon size={14} />
                                    ) : currentImageModel.provider === 'grsai' ? (
                                        <span className="text-xs font-bold text-emerald-400">G</span>
                                    ) : (
                                        <ImageIcon size={12} className="text-cyan-400" />
                                    )}"""

if old_icon in c:
    c = c.replace(old_icon, new_icon)
    print('2. Grsai icon added')
else:
    print('WARN: icon pattern not found')

# === 3. Add Grsai section in image dropdown ===
old_kling_section = """{/* Kling Models */}
                                        {availableImageModels.filter(m => m.provider === 'kling').length > 0 && ("""

new_grsai_kling = """{/* Grsai Models */}
                                        {availableImageModels.filter(m => m.provider === 'grsai').length > 0 && (
                                            <>
                                                <div className="px-3 py-1.5 text-[10px] font-bold text-neutral-500 uppercase tracking-wider bg-[#1f1f1f] border-t border-neutral-700">
                                                    Grsai
                                                </div>
                                                {availableImageModels.filter(m => m.provider === 'grsai').map(model => (
                                                    <button
                                                        key={model.id}
                                                        onClick={() => handleImageModelChange(model.id)}
                                                        className={`w-full flex items-center justify-between px-3 py-2 text-xs text-left hover:bg-[#333] transition-colors ${currentImageModel.id === model.id ? 'text-blue-400' : 'text-neutral-300'
                                                            }`}
                                                    >
                                                        <span className="flex items-center gap-2">
                                                            <span className="text-xs font-bold text-emerald-400">G</span>
                                                            {model.name}
                                                            {model.recommended && (
                                                                <span className="text-[9px] px-1 py-0.5 bg-green-600/30 text-green-400 rounded">REC</span>
                                                            )}
                                                        </span>
                                                        {currentImageModel.id === model.id && <Check size={12} />}
                                                    </button>
                                                ))}
                                            </>
                                        )}

                                        {/* Kling Models */}
                                        {availableImageModels.filter(m => m.provider === 'kling').length > 0 && ("""

if old_kling_section in c:
    c = c.replace(old_kling_section, new_grsai_kling)
    print('3. Grsai dropdown section added')
else:
    print('WARN: Kling section pattern not found')

# === 4. Chinese translations (minimal, only visible user text) ===
replacements = [
    ("\n                ? \"Describe what you want to generate...\"\n                : \"Describe how to transform this image...\"", 
     '\n                ? "描述你想生成的内容..."\n                : "描述如何转换这张图片..."'),
    ("? 'Select Model'", "? '选择模型'"),
    ("'Describe how to animate this frame...'", "'描述如何让这一帧动起来...'"),
    ("'Prompt optional for Kling frame-to-frame...'", "'Kling 帧到帧模式可省略提示词...'"),
    ("'Write your text content here...'", "'在此输入文字...'"),
    ("'Loading models...'", "'加载模型中...'"),
    ("'Select a model and enter prompt'", "'选择模型并输入提示词'"),
    ("'Ready to animate'", "'可开始动画'"),
    ("'Waiting for input...'", "'等待输入...'"),
    ("'Enter prompt to generate'", "'输入提示词开始生成'"),
    ("'Edit in Image Editor'", "'图片编辑器'"),
    ("'Edit in Video Editor'", "'视频编辑器'"),
    ("'View full size'", "'查看大图'"),
    ("'Post to X'", "'发到 X'"),
    ("'Post to TikTok'", "'发到抖音'"),
    ("'Download'", "'下载'"),
    ("'Upload image'", "'上传图片'"),
    ("'Shrink prompt'", "'收起提示词'"),
    ("'Expand prompt'", "'展开提示词'"),
    ("'Change Angle'", "'调整角度'"),
    ("'Generate New Angle'", "'重新生成角度'"),
    ("'Generating new angle...'", "'生成新角度中...'"),
    ("'Generating...'", "'生成中...'"),
    ("'Regenerating...'", "'重新生成中...'"),
    ("'Regenerate'", "'重新生成'"),
    ("'Reset'", "'重置'"),
    ("'Group'", "'成组'"),
    ("'Ungroup'", "'取消成组'"),
    ("'Sort'", "'排序'"),
    # Model names in dropdown headers
    ("'Local Models'", "'本地模型'"),
    ("'OpenAI'", "'OpenAI'"),
    ("'Hailuo AI'", "'Hailuo AI'"),
    # Dropdown mode indicators
    ("'Text → Video'", "'文字 → 视频'"),
    ("'Image → Video'", "'图片 → 视频'"),
    ("'Motion Control'", "'动态控制'"),
    ("'Frame-to-Frame'", "'帧到帧'"),
    ("'Text → Image'", "'文字 → 图片'"),
    ("'Image → Image'", "'图片 → 图片'"),
    # Reference settings
    ("'Reference Settings'", "'参考设置'"),
    ("'Subject'", "'主体'"),
    ("'Face'", "'脸部'"),
    ("'Face Reference'", "'脸部参考'"),
    ("'Subject Reference'", "'主体参考'"),
    ("'Reference Strength'", "'参考强度'"),
    ("'Input References'", "'输入参考'"),
    ("'Connected Frames'", "'连接帧'"),
    ("'Audio'", "'音频'"),
    # Camera
    ("'3D Camera Control'", "'3D 相机控制'"),
    ("'Rotation (↔)'", "'旋转 (↔)'"),
    ("'Vertical Tilt (↕)'", "'垂直倾斜 (↕)'"),
    ("'Aspect Ratio'", "'比例'"),
    ("'Resolution'", "'分辨率'"),
    ("'Quality'", "'质量'"),
    ("'Size'", "'尺寸'"),
    ("'Duration'", "'时长'"),
    ("'Shrink'", "'收起'"),
    ("'Expand'", "'展开'"),
    # Advanced settings
    ("'Advanced Settings'", "'高级设置'"),
    # Tooltips
    ("'Double click to open editor'", "'双击打开编辑器'"),
    ("'Double-click to edit'", "'双击编辑'"),
    ("'Drag to chat'", "'拖到对话'"),
]

for old_t, new_t in replacements:
    if old_t in c:
        c = c.replace(old_t, new_t)

print('4. Chinese translations applied')

# === 5. Change 'Auto' label to Chinese ===
c = c.replace("'Auto' : ratio", "'自动' : ratio")
c = c.replace("'Auto' : res", "'自动' : res")

with open(r'C:\Users\Administrator\Desktop\TwitCanva\src\components\canvas\NodeControls.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

print('\nAll patches applied!')
