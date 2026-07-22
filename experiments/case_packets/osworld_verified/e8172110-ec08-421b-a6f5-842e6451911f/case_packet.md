# Case Packet

## Case Metadata

- domain: `osworld_verified`
- case_unit_id: `e8172110-ec08-421b-a6f5-842e6451911f`
- task_id: `e8172110-ec08-421b-a6f5-842e6451911f`

## Benchmark Task Summary

- benchmark: `OSWorld-Verified`
- split: `test_nogdrive`
- application domain: `multi_apps`
- snapshot: `gimp`
- related apps: `gimp, vs_code`
- official instruction: Open 'character.png' in GIMP and extract the pixel art character. Save the selected character as 'character_gimp.png'. Additionally, write a Python script to automate this selection process, ensuring it precisely mimics the manual extraction done in GIMP. Output the result from the script as 'character_code.png'.
- evaluator functions: `check_structure_sim_with_threshold, check_structure_sim_with_threshold`
- evaluator conjunction: `and`
- evaluator result getter types: `vm_file, vm_file`
- native success: official evaluator score equals `1.0`
- required retained run artifacts: `traj.jsonl`, `result.txt`, `runtime.log`

## Visibility Boundary

This canonical source-rich packet is controller/reviewer-only. The tested agent receives only the instruction in `agent_input.json`; do not place this packet, `raw_case/`, setup commands, evaluator expectations, or expected values in the agent prompt.

## Evaluator Contract

This contract is mechanically extracted from the immutable task JSON and the pinned official Python sources without importing or executing them. The exact evaluator/runtime excerpts below make comparison, threshold, failure, and multi-metric composition semantics locally reviewable.

## Source Inventory

- `derived/evaluator_contract.json`
- `official/desktop_env/desktop_env.py`
- `official/desktop_env/evaluators/getters/__init__.py`
- `official/desktop_env/evaluators/getters/file.py`
- `official/desktop_env/evaluators/metrics/__init__.py`
- `official/desktop_env/evaluators/metrics/gimp.py`
- `official/task.json`

## Packet Source Files

### `official/task.json`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/evaluation_examples/examples/multi_apps/e8172110-ec08-421b-a6f5-842e6451911f.json`

Source SHA-256: `b8b053522e3129e4577fd70e729eb8036bf563a74d4433548ef1d579b29db079`

```json
{
  "config": [
    {
      "parameters": {
        "files": [
          {
            "path": "/home/user/Desktop/character.png",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/multi_apps/e8172110-ec08-421b-a6f5-842e6451911f/character.png"
          }
        ]
      },
      "type": "download"
    },
    {
      "parameters": {
        "command": [
          "python3",
          "-c",
          "with open('/home/user/Desktop/test.py', 'w', encoding='utf-8') as f: f.write('''from PIL import Image, ImageDraw\\nimport numpy as np\\nimport sys\\nimport os\\n\\ndef extract_character_gimp_style(image_path, output_path, bg_threshold=10):\\n    \\\"\\\"\\\"\\n    模仿GIMP手动提取过程，精确扣除背景并提取角色\\n    \\n    参数:\\n    image_path: 输入图像路径\\n    output_path: 输出图像路径\\n    bg_threshold: 背景检测阈值（0-255），值越小越严格\\n    \\\"\\\"\\\"\\n    \\n    # 打开图像\\n    try:\\n        img = Image.open(image_path)\\n    except FileNotFoundError:\\n        print(f\\\"错误：找不到文件 {image_path}\\\")\\n        return False\\n    except Exception as e:\\n        print(f\\\"错误：无法打开图像 - {e}\\\")\\n        return False\\n    \\n    print(f\\\"已加载图像: {image_path}\\\")\\n    print(f\\\"图像尺寸: {img.size}\\\")\\n    print(f\\\"图像模式: {img.mode}\\\")\\n    \\n    # 转换为RGBA模式（如果需要）\\n    if img.mode != \\'RGBA\\':\\n        img = img.convert(\\'RGBA\\')\\n    \\n    # 获取图像数据\\n    data = np.array(img)\\n    \\n    # 找到最可能为背景的颜色（通常是图像边缘的颜色）\\n    # 获取图像四角的像素作为背景样本\\n    height, width, _ = data.shape\\n    corners = [\\n        data[0, 0],           # 左上角\\n        data[0, width-1],     # 右上角\\n        data[height-1, 0],    # 左下角\\n        data[height-1, width-1] # 右下角\\n    ]\\n    \\n    # 计算背景颜色的平均值\\n    bg_color = np.mean(corners, axis=0).astype(int)\\n    print(f\\\"检测到的背景颜色 (RGBA): {bg_color}\\\")\\n    \\n    # 方法1: 使用魔棒工具类似的方法（基于颜色相似度）\\n    # 创建透明背景的新图像\\n    new_data = data.copy()\\n    \\n    # 计算每个像素与背景颜色的差异\\n    color_diff = np.sqrt(np.sum((data[:, :, :3] - bg_color[:3]) ** 2, axis=2))\\n    \\n    # 应用阈值来识别背景像素\\n    # 对于像素艺术，通常需要较严格的阈值\\n    bg_mask = color_diff <= bg_threshold\\n    \\n    # 将背景像素设置为完全透明\\n    new_data[bg_mask, 3] = 0  # 设置alpha通道为0（透明）\\n    \\n    # 方法2: 边缘检测增强（可选，用于更精确的边缘）\\n    # 对于像素艺术，我们可能想要保留锐利的边缘\\n    for i in range(1, height-1):\\n        for j in range(1, width-1):\\n            # 如果当前像素不是背景，但周围有背景像素，确保它保持不透明\\n            if not bg_mask[i, j] and (bg_mask[i-1, j] or bg_mask[i+1, j] or \\n                                      bg_mask[i, j-1] or bg_mask[i, j+1]):\\n                # 确保边缘像素保持不透明\\n                new_data[i, j, 3] = 255\\n    \\n    # 创建输出图像\\n    result_img = Image.fromarray(new_data, \\'RGBA\\')\\n    \\n    # 可选：添加一个棋盘背景用于预览（模仿GIMP的透明背景显示）\\n    preview_img = create_checkerboard_background(result_img)\\n    \\n    # 保存结果\\n    result_img.save(output_path, \\'PNG\\')\\n    print(f\\\"已保存提取的角色到: {output_path}\\\")\\n    \\n    # 保存预览版本（带棋盘背景）\\n    preview_path = output_path.replace(\\'.png\\', \\'_preview.png\\')\\n    preview_img.save(preview_path, \\'PNG\\')\\n    print(f\\\"已保存预览图像到: {preview_path}\\\")\\n    \\n    return True\\n\\ndef create_checkerboard_background(image, tile_size=10):\\n    \\\"\\\"\\\"\\n    创建棋盘背景（模仿GIMP的透明背景显示）\\n    \\\"\\\"\\\"\\n    # 创建棋盘背景\\n    checkerboard = Image.new(\\'RGB\\', image.size, (255, 255, 255))\\n    draw = ImageDraw.Draw(checkerboard)\\n    \\n    # 绘制棋盘格子\\n    for x in range(0, image.width, tile_size * 2):\\n        for y in range(0, image.height, tile_size * 2):\\n            # 绘制灰色格子\\n            draw.rectangle([x, y, x + tile_size, y + tile_size], fill=(200, 200, 200))\\n            draw.rectangle([x + tile_size, y + tile_size, \\n                           x + tile_size * 2, y + tile_size * 2], fill=(200, 200, 200))\\n    \\n    # 将角色合成到棋盘背景上\\n    if image.mode == \\'RGBA\\':\\n        checkerboard.paste(image, (0, 0), image)\\n    else:\\n        checkerboard.paste(image, (0, 0))\\n    \\n    return checkerboard\\n\\ndef manual_background_selection(image_path, output_path):\\n    \\\"\\\"\\\"\\n    手动选择背景颜色（更精确的方法）\\n    对于特殊情况，可以手动指定背景颜色\\n    \\\"\\\"\\\"\\n    img = Image.open(image_path).convert(\\'RGBA\\')\\n    data = np.array(img)\\n    \\n    # 显示图像并让用户选择背景颜色\\n    print(\\\"\\\\n手动背景选择模式:\\\")\\n    print(\\\"1. 请查看图像并确定背景颜色\\\")\\n    print(\\\"2. 输入背景颜色的RGBA值（如：255 255 255 255）\\\")\\n    \\n    try:\\n        bg_input = input(\\\"输入背景颜色 (R G B A)，或按Enter使用自动检测: \\\").strip()\\n        if bg_input:\\n            bg_color = list(map(int, bg_input.split()))\\n            if len(bg_color) < 3:\\n                print(\\\"错误：需要至少3个颜色值（RGB）\\\")\\n                return False\\n            if len(bg_color) == 3:\\n                bg_color.append(255)  # 默认不透明\\n        else:\\n            # 使用自动检测的背景颜色\\n            return extract_character_gimp_style(image_path, output_path)\\n    except ValueError:\\n        print(\\\"错误：请输入有效的数字\\\")\\n        return False\\n    \\n    # 创建新图像数据\\n    new_data = data.copy()\\n    \\n    # 精确匹配背景颜色\\n    tolerance = 20  # 容差\\n    bg_color = np.array(bg_color[:4])\\n    \\n    # 计算颜色差异\\n    diff = np.sqrt(np.sum((data[:, :, :4] - bg_color) ** 2, axis=2))\\n    \\n    # 应用容差阈值\\n    bg_mask = diff <= tolerance\\n    \\n    # 将背景设为透明\\n    new_data[bg_mask, 3] = 0\\n    \\n    # 保存结果\\n    result_img = Image.fromarray(new_data, \\'RGBA\\')\\n    result_img.save(output_path, \\'PNG\\')\\n    \\n    # 创建预览\\n    preview_img = create_checkerboard_background(result_img)\\n    preview_path = output_path.replace(\\'.png\\', \\'_preview.png\\')\\n    preview_img.save(preview_path, \\'PNG\\')\\n    \\n    print(f\\\"已保存手动提取的结果到: {output_path}\\\")\\n    print(f\\\"已保存预览图像到: {preview_path}\\\")\\n    \\n    return True\\n\\ndef main():\\n    \\\"\\\"\\\"主函数\\\"\\\"\\\"\\n    input_file = \\\"character.png\\\"\\n    output_file = \\\"character_code.png\\\"\\n    \\n    # 检查输入文件是否存在\\n    if not os.path.exists(input_file):\\n        print(f\\\"错误：输入文件 \\'{input_file}\\' 不存在\\\")\\n        print(\\\"请确保 \\'character.png\\' 在当前目录中\\\")\\n        return\\n    \\n    print(\\\"=== 像素艺术角色提取工具 ===\\\")\\n    print(f\\\"输入文件: {input_file}\\\")\\n    print(f\\\"输出文件: {output_file}\\\")\\n    print(\\\"\\\\n选择提取模式:\\\")\\n    print(\\\"1. 自动提取（推荐）\\\")\\n    print(\\\"2. 手动选择背景颜色\\\")\\n    \\n    try:\\n        choice = input(\\\"请输入选择 (1 或 2，默认1): \\\").strip()\\n    except KeyboardInterrupt:\\n        print(\\\"\\\\n操作取消\\\")\\n        return\\n    \\n    if choice == \\\"2\\\":\\n        success = manual_background_selection(input_file, output_file)\\n    else:\\n        # 尝试不同的阈值以获得最佳结果\\n        for threshold in [5, 10, 15, 20]:\\n            print(f\\\"\\\\n尝试阈值 {threshold}...\\\")\\n            temp_output = f\\\"character_threshold_{threshold}.png\\\"\\n            success = extract_character_gimp_style(input_file, temp_output, threshold)\\n            if success:\\n                print(f\\\"阈值 {threshold} 处理完成\\\")\\n        \\n        # 使用默认阈值10作为最终结果\\n        success = extract_character_gimp_style(input_file, output_file, bg_threshold=10)\\n    \\n    if success:\\n        print(\\\"\\\\n\\\" + \\\"=\\\"*50)\\n        print(\\\"提取完成！\\\")\\n        print(f\\\"主要结果: {output_file}\\\")\\n        print(f\\\"预览版本: character_code_preview.png\\\")\\n        print(\\\"其他阈值测试结果已保存为 character_threshold_*.png\\\")\\n        print(\\\"=\\\"*50)\\n    else:\\n        print(\\\"提取失败，请检查输入图像和参数。\\\")\\n\\nif __name__ == \\\"__main__\\\":\\n    main()\\n''')"
        ],
        "shell": false
      },
      "type": "execute"
    },
    {
      "parameters": {
        "command": [
          "gimp",
          "/home/user/Desktop/character.png"
        ]
      },
      "type": "launch"
    }
  ],
  "evaluator": {
    "expected": [
      {
        "dest": "character_no_background_gold.png",
        "path": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/multi_apps/e8172110-ec08-421b-a6f5-842e6451911f/character_no_background_gold.png",
        "type": "cloud_file"
      },
      {
        "dest": "character_no_background_gold.png",
        "path": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/multi_apps/e8172110-ec08-421b-a6f5-842e6451911f/character_no_background_gold.png",
        "type": "cloud_file"
      }
    ],
    "func": [
      "check_structure_sim_with_threshold",
      "check_structure_sim_with_threshold"
    ],
    "options": [
      {
        "ssim_threshold": 0.85
      },
      {
        "ssim_threshold": 0.85
      }
    ],
    "result": [
      {
        "dest": "character_gimp.png",
        "path": "/home/user/Desktop/character_gimp.png",
        "type": "vm_file"
      },
      {
        "dest": "character_code.png",
        "path": "/home/user/Desktop/character_code.png",
        "type": "vm_file"
      }
    ]
  },
  "fixed_ip": false,
  "id": "e8172110-ec08-421b-a6f5-842e6451911f",
  "instruction": "Open 'character.png' in GIMP and extract the pixel art character. Save the selected character as 'character_gimp.png'. Additionally, write a Python script to automate this selection process, ensuring it precisely mimics the manual extraction done in GIMP. Output the result from the script as 'character_code.png'.",
  "possibility_of_env_change": "low",
  "proxy": false,
  "related_apps": [
    "gimp",
    "vs_code"
  ],
  "snapshot": "gimp",
  "source": "",
  "trajectory": "trajectories/"
}
```

### `derived/evaluator_contract.json`

Source ref: `mechanically extracted from the pinned task and evaluator sources`

Source SHA-256: `d013bbf4e9034be5d84a4658a549d4d0c7e649af3b558f79ba985606be68c6d1`

```json
{
  "conjunction": "and",
  "exact_source_excerpts": [
    {
      "end_line": 414,
      "excerpt_sha256": "852396f1e81e91bbe65eaf5f778082c2728df3b4ac5bf54d2e8e663e67d39340",
      "packet_path": "official/desktop_env/desktop_env.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/desktop_env.py",
      "source_sha256": "ff73a546074d4cf3b13259f7261a82af5c3f6942bde27101aa74e58da70d84c1",
      "start_line": 369,
      "symbol": "DesktopEnv._set_evaluator_info",
      "upstream_path": "desktop_env/desktop_env.py"
    },
    {
      "end_line": 524,
      "excerpt_sha256": "ad91f9461384454de19eba8c1a65b8165259150f6d222f99183de340cfa90288",
      "packet_path": "official/desktop_env/desktop_env.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/desktop_env.py",
      "source_sha256": "ff73a546074d4cf3b13259f7261a82af5c3f6942bde27101aa74e58da70d84c1",
      "start_line": 458,
      "symbol": "DesktopEnv.evaluate",
      "upstream_path": "desktop_env/desktop_env.py"
    },
    {
      "end_line": 1,
      "excerpt_sha256": "3727adff524e0616022eadd8f4af21a0778b29fc4c77bdfefd1afce2cbf5e4b7",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "start_line": 1,
      "symbol": "import:os",
      "upstream_path": "desktop_env/evaluators/getters/file.py"
    },
    {
      "end_line": 2,
      "excerpt_sha256": "c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "start_line": 2,
      "symbol": "import:logging",
      "upstream_path": "desktop_env/evaluators/getters/file.py"
    },
    {
      "end_line": 3,
      "excerpt_sha256": "ab270e34de38d99f0364043ca1808983f498a9e3943133071931657340b5bc95",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "start_line": 3,
      "symbol": "import:uuid",
      "upstream_path": "desktop_env/evaluators/getters/file.py"
    },
    {
      "end_line": 4,
      "excerpt_sha256": "f3e1094d4dc7c94939f5e6d73e3ce61bc0f6d2ef7b39c1e1a3c7be9dff56e58a",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "start_line": 4,
      "symbol": "import:Dict",
      "upstream_path": "desktop_env/evaluators/getters/file.py"
    },
    {
      "end_line": 5,
      "excerpt_sha256": "e4f846484778f7f065efd3be851677c4495d57ac1dbaccc5a8b4880a9b9907d0",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "start_line": 5,
      "symbol": "import:Any",
      "upstream_path": "desktop_env/evaluators/getters/file.py"
    },
    {
      "end_line": 6,
      "excerpt_sha256": "2ed0247cc05b861fea3391ee7651aec4bb57304b71be6e96d2b74d171c551f55",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "start_line": 6,
      "symbol": "import:datetime",
      "upstream_path": "desktop_env/evaluators/getters/file.py"
    },
    {
      "end_line": 7,
      "excerpt_sha256": "333d1b652ae64febaa8b71b12c8fa33598ab9a6593d74ae7abf6bac592ef4884",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "start_line": 7,
      "symbol": "import:requests",
      "upstream_path": "desktop_env/evaluators/getters/file.py"
    },
    {
      "end_line": 10,
      "excerpt_sha256": "df15c4979fae995ded306279ba830d847eda92de71b795dad700bdbe5be696f5",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "start_line": 10,
      "symbol": "logger",
      "upstream_path": "desktop_env/evaluators/getters/file.py"
    },
    {
      "end_line": 80,
      "excerpt_sha256": "03900b07d6dae0c8c18f2ea96ad9183eba56ea056629742181995066d3f23c37",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "start_line": 32,
      "symbol": "get_cloud_file",
      "upstream_path": "desktop_env/evaluators/getters/file.py"
    },
    {
      "end_line": 158,
      "excerpt_sha256": "d0565cba192756ad787f28cd70cef2db7b0086183127c576ce303e3b95018291",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "start_line": 83,
      "symbol": "get_vm_file",
      "upstream_path": "desktop_env/evaluators/getters/file.py"
    },
    {
      "end_line": 2,
      "excerpt_sha256": "c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652",
      "packet_path": "official/desktop_env/evaluators/metrics/gimp.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/gimp.py",
      "source_sha256": "c0aeea13928927a97e06a15088d6049cef7a8dfdc9251203badbb6f17f931346",
      "start_line": 2,
      "symbol": "import:logging",
      "upstream_path": "desktop_env/evaluators/metrics/gimp.py"
    },
    {
      "end_line": 4,
      "excerpt_sha256": "9ecac4ed6c67ab8bcef7eb35cb5da7dee079ed03dc997f7e8c33741b115e4f7e",
      "packet_path": "official/desktop_env/evaluators/metrics/gimp.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/gimp.py",
      "source_sha256": "c0aeea13928927a97e06a15088d6049cef7a8dfdc9251203badbb6f17f931346",
      "start_line": 4,
      "symbol": "import:ssim",
      "upstream_path": "desktop_env/evaluators/metrics/gimp.py"
    },
    {
      "end_line": 5,
      "excerpt_sha256": "5ac6bfee5a58e47ad0911548db1f5d94066ddab4bf2775bd57c64eceb7f5feed",
      "packet_path": "official/desktop_env/evaluators/metrics/gimp.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/gimp.py",
      "source_sha256": "c0aeea13928927a97e06a15088d6049cef7a8dfdc9251203badbb6f17f931346",
      "start_line": 5,
      "symbol": "import:Image",
      "upstream_path": "desktop_env/evaluators/metrics/gimp.py"
    },
    {
      "end_line": 106,
      "excerpt_sha256": "d34aea06c990aeedd2f8f5ff809c1180b92fccca0381269b7c18654043b9a374",
      "packet_path": "official/desktop_env/evaluators/metrics/gimp.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/gimp.py",
      "source_sha256": "c0aeea13928927a97e06a15088d6049cef7a8dfdc9251203badbb6f17f931346",
      "start_line": 106,
      "symbol": "import:np",
      "upstream_path": "desktop_env/evaluators/metrics/gimp.py"
    },
    {
      "end_line": 947,
      "excerpt_sha256": "9605dab3544bf59e229b78f834e8a7715221ec03ee6fa37669e2978f6258fde8",
      "packet_path": "official/desktop_env/evaluators/metrics/gimp.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/gimp.py",
      "source_sha256": "c0aeea13928927a97e06a15088d6049cef7a8dfdc9251203badbb6f17f931346",
      "start_line": 818,
      "symbol": "check_structure_sim_with_threshold",
      "upstream_path": "desktop_env/evaluators/metrics/gimp.py"
    }
  ],
  "expected_getters": [
    {
      "config_path": "evaluator.expected[0]",
      "config_sha256": "b3d1c36451e43ec6a7fba378a8d6434a167e4a781a010c5dbd02f99c5aa2ab01",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "symbol": "get_cloud_file",
      "type": "cloud_file"
    },
    {
      "config_path": "evaluator.expected[1]",
      "config_sha256": "b3d1c36451e43ec6a7fba378a8d6434a167e4a781a010c5dbd02f99c5aa2ab01",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "slot": 1,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "symbol": "get_cloud_file",
      "type": "cloud_file"
    }
  ],
  "extraction": {
    "evaluator_config_sha256": "5e29b9a322bd309d2e346c4aadc71b309c6e2db93a839d2d1baeca5247707e2d",
    "method": "Python AST and immutable task JSON; no evaluator code executed",
    "official_commit": "87df18ff0e906dafdb1ea96b8299f35ec1e67e6b"
  },
  "list_mode": true,
  "metric_options": [
    {
      "ssim_threshold": 0.85
    },
    {
      "ssim_threshold": 0.85
    }
  ],
  "metrics": [
    {
      "name": "check_structure_sim_with_threshold",
      "packet_path": "official/desktop_env/evaluators/metrics/gimp.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/gimp.py",
      "source_sha256": "c0aeea13928927a97e06a15088d6049cef7a8dfdc9251203badbb6f17f931346"
    },
    {
      "name": "check_structure_sim_with_threshold",
      "packet_path": "official/desktop_env/evaluators/metrics/gimp.py",
      "slot": 1,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/gimp.py",
      "source_sha256": "c0aeea13928927a97e06a15088d6049cef7a8dfdc9251203badbb6f17f931346"
    }
  ],
  "official_source_files": [
    {
      "packet_path": "official/desktop_env/desktop_env.py",
      "sha256": "ff73a546074d4cf3b13259f7261a82af5c3f6942bde27101aa74e58da70d84c1",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/desktop_env.py",
      "upstream_path": "desktop_env/desktop_env.py"
    },
    {
      "packet_path": "official/desktop_env/evaluators/getters/__init__.py",
      "sha256": "a767ec1877446426817ec07ca386f63fc0fff8857a209b99bfa1f93865900754",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/__init__.py",
      "upstream_path": "desktop_env/evaluators/getters/__init__.py"
    },
    {
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "upstream_path": "desktop_env/evaluators/getters/file.py"
    },
    {
      "packet_path": "official/desktop_env/evaluators/metrics/__init__.py",
      "sha256": "f8e89039d448b715e99c14a939a566d4148fda3a67a71371a208baa1d6276a08",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/__init__.py",
      "upstream_path": "desktop_env/evaluators/metrics/__init__.py"
    },
    {
      "packet_path": "official/desktop_env/evaluators/metrics/gimp.py",
      "sha256": "c0aeea13928927a97e06a15088d6049cef7a8dfdc9251203badbb6f17f931346",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/gimp.py",
      "upstream_path": "desktop_env/evaluators/metrics/gimp.py"
    }
  ],
  "postconfig_present": false,
  "result_getters": [
    {
      "config_path": "evaluator.result[0]",
      "config_sha256": "89d32a3f1bc0bfbb4d1dbe73a04a40640b4f5ec2f3f17e4afda26e8ed7249219",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "symbol": "get_vm_file",
      "type": "vm_file"
    },
    {
      "config_path": "evaluator.result[1]",
      "config_sha256": "5f26a455b6e2b9aa32b2be35f8461f19fe19a5939fa7b4be8d17f8bd17fa642f",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "slot": 1,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "symbol": "get_vm_file",
      "type": "vm_file"
    }
  ],
  "runtime_composition": {
    "agent_fail_on_non_infeasible": "a final FAIL action forces score 0 before getters or metrics run",
    "binding": "metrics are resolved with getattr(metrics, func); getters are resolved with getattr(getters, 'get_' + type)",
    "file_not_found": "single-metric and multi-metric 'and' paths return 0; the official multi-metric 'or' exception path has no explicit return and must be interpreted from the embedded exact source",
    "formal_packet_success": "final evaluator score equals exactly 1.0",
    "infeasible": "when evaluator.func is the string 'infeasible', return 1 only when the last action is FAIL (string or action_type), else 0",
    "multi_metric_and": "evaluate in slot order; return 0 immediately when float(metric) == 0.0; otherwise return the arithmetic mean",
    "multi_metric_or": "evaluate in slot order; return 1 immediately when float(metric) == 1.0; otherwise return the maximum",
    "single_metric": "obtain result state; obtain expected state when configured; call metric(result, expected, **options) or metric(result, **options); return the metric value"
  },
  "schema_version": "osworld_verified_evaluator_contract/v1",
  "task_id": "e8172110-ec08-421b-a6f5-842e6451911f"
}
```

## Exact Official Evaluator Source Excerpts

### `DesktopEnv._set_evaluator_info` from `official/desktop_env/desktop_env.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/desktop_env.py#L369-L414`

Full source SHA-256: `ff73a546074d4cf3b13259f7261a82af5c3f6942bde27101aa74e58da70d84c1`

Exact excerpt SHA-256: `852396f1e81e91bbe65eaf5f778082c2728df3b4ac5bf54d2e8e663e67d39340`

```python
    def _set_evaluator_info(self, task_config: Dict[str, Any]):
        """Set evaluator information from task config"""
        # evaluator dict
        # func -> metric function string, or list of metric function strings
        # conj -> conjunction of multiple metrics if func is a list with length > 1, "and"/"or"
        # result -> result getter config, or list of result getter configs
        # expected (optional) -> expected getter config, or list of expected getter configs
        # options (optional) -> metric options, or list of metric options
        # if func is a str list, then result, expected (if exists), options (if exists) should also be lists of the same length
        # even if one of the metrics does not need expected or options field, it should be included in the list with None
        self.evaluator = task_config["evaluator"]
        self.metric: Metric = [getattr(metrics, func) for func in self.evaluator["func"]] \
            if isinstance(self.evaluator["func"], list) \
            else getattr(metrics, self.evaluator["func"])
        self.metric_conj: str = self.evaluator.get("conj", "and")  # take conjunction of multiple metrics
        if "result" in self.evaluator and len(self.evaluator["result"]) > 0:
            self.result_getter: Getter = [getattr(getters, "get_{:}".format(res["type"])) for res in
                                          self.evaluator["result"]] \
                if isinstance(self.evaluator["result"], list) \
                else getattr(getters, "get_{:}".format(self.evaluator["result"]["type"]))
        else:
            self.result_getter = [None] * len(self.metric) \
                if isinstance(self.metric, list) \
                else None

        if "expected" in self.evaluator and len(self.evaluator["expected"]) > 0:
            self.expected_getter: Getter = [getattr(getters, "get_{:}".format(exp["type"])) if exp else None for exp in
                                            self.evaluator["expected"]] \
                if isinstance(self.evaluator["expected"], list) \
                else getattr(getters, "get_{:}".format(self.evaluator["expected"]["type"]))
        else:
            self.expected_getter = [None] * len(self.metric) \
                if isinstance(self.metric, list) \
                else None
        self.metric_options: Union[List[Dict[str, Any]], Dict[str, Any]] = [opt if opt else {} for opt in
                                                                            self.evaluator["options"]] \
            if isinstance(self.evaluator.get("options", {}), list) \
            else self.evaluator["options"] \
            if "options" in self.evaluator \
            else [{}] * len(self.metric) \
            if isinstance(self.metric, list) \
            else {}

        assert (not isinstance(self.evaluator["func"], list)
                or (len(self.metric) == len(self.result_getter) == len(self.expected_getter) == len(
                    self.metric_options)))
```

### `DesktopEnv.evaluate` from `official/desktop_env/desktop_env.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/desktop_env.py#L458-L524`

Full source SHA-256: `ff73a546074d4cf3b13259f7261a82af5c3f6942bde27101aa74e58da70d84c1`

Exact excerpt SHA-256: `ad91f9461384454de19eba8c1a65b8165259150f6d222f99183de340cfa90288`

```python
    def evaluate(self):
        """
        Evaluate whether the task is successfully completed.
        """

        postconfig = self.evaluator.get("postconfig", [])
        self.setup_controller.setup(postconfig, self.enable_proxy)
        # Mark environment as used if there were postconfig setup operations
        if postconfig:
            self.is_environment_used = True

        if self.evaluator['func'] == "infeasible":
            if len(self.action_history) > 0:
                last_action = self.action_history[-1]
                if last_action == "FAIL" or (type(last_action) == dict and last_action.get('action_type') == 'FAIL'):
                    return 1
            return 0
        else:
            if len(self.action_history) > 0:
                last_action = self.action_history[-1]
                if last_action == "FAIL" or (type(last_action) == dict and last_action.get('action_type') == 'FAIL'):
                    return 0

        if type(self.metric) == list:
            # Multiple metrics to evaluate whether the task is successfully completed
            results = []
            assert len(self.metric) == len(self.result_getter), "The number of metrics and result getters must be the same"
            if "expected" in self.evaluator:
                assert len(self.metric) == len(self.expected_getter), "The number of metrics and expected getters must be the same"
            for idx, metric in enumerate(self.metric):
                try:
                    config = self.evaluator["result"][idx]
                    result_state = self.result_getter[idx](self, config)
                except FileNotFoundError:
                    logger.error("File not found!")
                    if self.metric_conj == 'and':
                        return 0

                if "expected" in self.evaluator and self.expected_getter and self.evaluator["expected"]:
                    expected_state = self.expected_getter[idx](self, self.evaluator["expected"][idx])
                    metric: int = metric(result_state, expected_state, **self.metric_options[idx])
                else:
                    metric: int = metric(result_state, **self.metric_options[idx])

                if self.metric_conj == 'and' and float(metric) == 0.0:
                    return 0
                elif self.metric_conj == 'or' and float(metric) == 1.0:
                    return 1
                else:
                    results.append(metric)

            return sum(results) / len(results) if self.metric_conj == 'and' else max(results)
        else:
            # Single metric to evaluate whether the task is successfully completed
            try:
                result_state = self.result_getter(self, self.evaluator["result"])
            except FileNotFoundError:
                logger.error("File not found!")
                return 0

            if "expected" in self.evaluator and self.expected_getter and self.evaluator["expected"]:
                expected_state = self.expected_getter(self, self.evaluator["expected"])
                metric: float = self.metric(result_state, expected_state, **self.metric_options)
            else:
                metric: float = self.metric(result_state, **self.metric_options)

        return metric
```

### `import:os` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L1-L1`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `3727adff524e0616022eadd8f4af21a0778b29fc4c77bdfefd1afce2cbf5e4b7`

```python
import os
```

### `import:logging` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L2-L2`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652`

```python
import logging
```

### `import:uuid` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L3-L3`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `ab270e34de38d99f0364043ca1808983f498a9e3943133071931657340b5bc95`

```python
import uuid
```

### `import:Dict` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L4-L4`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `f3e1094d4dc7c94939f5e6d73e3ce61bc0f6d2ef7b39c1e1a3c7be9dff56e58a`

```python
from typing import Dict, List, Set
```

### `import:Any` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L5-L5`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `e4f846484778f7f065efd3be851677c4495d57ac1dbaccc5a8b4880a9b9907d0`

```python
from typing import Optional, Any, Union
```

### `import:datetime` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L6-L6`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `2ed0247cc05b861fea3391ee7651aec4bb57304b71be6e96d2b74d171c551f55`

```python
from datetime import datetime
```

### `import:requests` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L7-L7`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `333d1b652ae64febaa8b71b12c8fa33598ab9a6593d74ae7abf6bac592ef4884`

```python
import requests
```

### `logger` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L10-L10`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `df15c4979fae995ded306279ba830d847eda92de71b795dad700bdbe5be696f5`

```python
logger = logging.getLogger("desktopenv.getter.file")
```

### `get_cloud_file` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L32-L80`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `03900b07d6dae0c8c18f2ea96ad9183eba56ea056629742181995066d3f23c37`

```python
def get_cloud_file(env, config: Dict[str, Any]) -> Union[str, List[str]]:
    """
    Config:
        path (str|List[str]): the url to download from
        dest (str|List[str])): file name of the downloaded file
        multi (bool) : optional. if path and dest are lists providing
          information of multiple files. defaults to False
        gives (List[int]): optional. defaults to [0]. which files are directly
          returned to the metric. if len==1, str is returned; else, list is
          returned.
    """

    if not config.get("multi", False):
        paths: List[str] = [config["path"]]
        dests: List[str] = [config["dest"]]
    else:
        paths: List[str] = config["path"]
        dests: List[str] = config["dest"]
    cache_paths: List[str] = []

    gives: Set[int] = set(config.get("gives", [0]))

    for i, (p, d) in enumerate(zip(paths, dests)):
        _path = os.path.join(env.cache_dir, d)
        if i in gives:
            cache_paths.append(_path)

        if os.path.exists(_path):
            #return _path
            continue

        url = p
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Atomic write: stream into a temp file then rename, so a concurrent
        # reader never observes a partially-downloaded file.
        tmp_path = f"{_path}.tmp.{uuid.uuid4().hex}"
        try:
            with open(tmp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            os.replace(tmp_path, _path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    return cache_paths[0] if len(cache_paths)==1 else cache_paths
```

### `get_vm_file` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L83-L158`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `d0565cba192756ad787f28cd70cef2db7b0086183127c576ce303e3b95018291`

```python
def get_vm_file(env, config: Dict[str, Any]) -> Union[Optional[str], List[Optional[str]]]:
    """
    Config:
        path (str): absolute path on the VM to fetch
        dest (str): file name of the downloaded file
        multi (bool) : optional. if path and dest are lists providing
          information of multiple files. defaults to False
        gives (List[int]): optional. defaults to [0]. which files are directly
          returned to the metric. if len==1, str is returned; else, list is
          returned.
        only support for single file now:
        time_suffix(bool): optional. defaults to False. if True, append the current time in required format.
        time_format(str): optional. defaults to "%Y%m%d_%H%M%S". format of the time suffix.
    """
    time_format = "%Y%m%d_%H%M%S"
    if not config.get("multi", False):
        paths: List[str] = [config["path"]]
        dests: List[str] = [config["dest"]]
        if config.get("time_suffix", False):
            time_format = config.get("time_format", time_format)
            # Insert time before file extension.
            dests = [f"{os.path.splitext(d)[0]}_{datetime.now().strftime(time_format)}{os.path.splitext(d)[1]}" for d in dests]
    else:
        paths: List[str] = config["path"]
        dests: List[str] = config["dest"]


    cache_paths: List[str] = []

    gives: Set[int] = set(config.get("gives", [0]))

    for i, (p, d) in enumerate(zip(paths, dests)):
        _path = os.path.join(env.cache_dir, d)
        
        try:
            # Try to get file from VM
            file = env.controller.get_file(p)
            if file is None:
                logger.warning(f"Failed to get file from VM: {p}")
                if i in gives:
                    cache_paths.append(None)
                continue

            if i in gives:
                cache_paths.append(_path)
                
            # Write file with robust error handling
            try:
                # Ensure cache directory exists
                os.makedirs(env.cache_dir, exist_ok=True)
                
                tmp_path = f"{_path}.tmp.{uuid.uuid4().hex}"
                try:
                    with open(tmp_path, "wb") as f:
                        f.write(file)
                    os.replace(tmp_path, _path)
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                logger.info(f"Successfully saved file: {_path} ({len(file)} bytes)")
                
            except IOError as e:
                logger.error(f"IO error writing file {_path}: {e}")
                if i in gives:
                    cache_paths[-1] = None  # Replace the path we just added with None
            except Exception as e:
                logger.error(f"Unexpected error writing file {_path}: {e}")
                if i in gives:
                    cache_paths[-1] = None
                    
        except Exception as e:
            logger.error(f"Error processing file {p}: {e}")
            if i in gives:
                cache_paths.append(None)
                
    return cache_paths[0] if len(cache_paths)==1 else cache_paths
```

### `import:logging` from `official/desktop_env/evaluators/metrics/gimp.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/gimp.py#L2-L2`

Full source SHA-256: `c0aeea13928927a97e06a15088d6049cef7a8dfdc9251203badbb6f17f931346`

Exact excerpt SHA-256: `c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652`

```python
import logging
```

### `import:ssim` from `official/desktop_env/evaluators/metrics/gimp.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/gimp.py#L4-L4`

Full source SHA-256: `c0aeea13928927a97e06a15088d6049cef7a8dfdc9251203badbb6f17f931346`

Exact excerpt SHA-256: `9ecac4ed6c67ab8bcef7eb35cb5da7dee079ed03dc997f7e8c33741b115e4f7e`

```python
from skimage.metrics import structural_similarity as ssim
```

### `import:Image` from `official/desktop_env/evaluators/metrics/gimp.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/gimp.py#L5-L5`

Full source SHA-256: `c0aeea13928927a97e06a15088d6049cef7a8dfdc9251203badbb6f17f931346`

Exact excerpt SHA-256: `5ac6bfee5a58e47ad0911548db1f5d94066ddab4bf2775bd57c64eceb7f5feed`

```python
from PIL import Image, ImageChops, ImageStat
```

### `import:np` from `official/desktop_env/evaluators/metrics/gimp.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/gimp.py#L106-L106`

Full source SHA-256: `c0aeea13928927a97e06a15088d6049cef7a8dfdc9251203badbb6f17f931346`

Exact excerpt SHA-256: `d34aea06c990aeedd2f8f5ff809c1180b92fccca0381269b7c18654043b9a374`

```python
import numpy as np
```

### `check_structure_sim_with_threshold` from `official/desktop_env/evaluators/metrics/gimp.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/gimp.py#L818-L947`

Full source SHA-256: `c0aeea13928927a97e06a15088d6049cef7a8dfdc9251203badbb6f17f931346`

Exact excerpt SHA-256: `9605dab3544bf59e229b78f834e8a7715221ec03ee6fa37669e2978f6258fde8`

```python
def check_structure_sim_with_threshold(src_path, tgt_path, **options):
    """
    Check if the structure of the two images are similar with customizable SSIM threshold.
    This function is based on check_structure_sim but allows adjusting the similarity threshold
    to accept images that are visually identical but have minor pixel differences.
    
    Args:
        src_path: Path to source image
        tgt_path: Path to target image
        **options: Optional parameters:
            ssim_threshold: SSIM similarity threshold (default 0.85, lower than original 0.9)
                           Lower values accept more differences, higher values are more strict.
                           Range: 0.0 to 1.0
    
    Returns:
        1.0 if images are similar enough (SSIM >= threshold), 0.0 otherwise
    """
    if src_path is None or tgt_path is None:
        print(f"[IMAGE_COMPARISON] ✗ ERROR: One or both paths are None (src={src_path}, tgt={tgt_path})")
        logging.warning(f"check_structure_sim_with_threshold: One or both paths are None (src={src_path}, tgt={tgt_path})")
        return 0.

    # Get threshold from options, default to 0.85 (more lenient than original 0.9)
    ssim_threshold = options.get('ssim_threshold', 0.85)
    
    # Use both print and logging to ensure output is visible
    print(f"[IMAGE_COMPARISON] Starting comparison")
    print(f"[IMAGE_COMPARISON]   Source image: {src_path}")
    print(f"[IMAGE_COMPARISON]   Target image: {tgt_path}")
    print(f"[IMAGE_COMPARISON]   SSIM threshold: {ssim_threshold}")
    
    logging.info(f"check_structure_sim_with_threshold: Starting comparison")
    logging.info(f"  Source image: {src_path}")
    logging.info(f"  Target image: {tgt_path}")
    logging.info(f"  SSIM threshold: {ssim_threshold}")

    try:
        img_src = Image.open(src_path)
        img_tgt = Image.open(tgt_path)
        
        print(f"[IMAGE_COMPARISON]   Source image info: size={img_src.size}, mode={img_src.mode}")
        print(f"[IMAGE_COMPARISON]   Target image info: size={img_tgt.size}, mode={img_tgt.mode}")
        
        logging.info(f"  Source image info: size={img_src.size}, mode={img_src.mode}")
        logging.info(f"  Target image info: size={img_tgt.size}, mode={img_tgt.mode}")

        # Resize source image to match target image size if they differ
        # This is necessary because generated images may have different dimensions
        # but should still be compared for visual similarity
        if img_src.size != img_tgt.size:
            print(f"[IMAGE_COMPARISON]   ⚠ Image size mismatch: src={img_src.size} vs tgt={img_tgt.size}")
            print(f"[IMAGE_COMPARISON]   ⚠ Resizing source image to match target size for comparison")
            logging.info(f"  Image size mismatch: src={img_src.size} vs tgt={img_tgt.size}")
            logging.info(f"  Resizing source image to match target size for comparison")
            img_src = img_src.resize(img_tgt.size, Image.Resampling.LANCZOS)
            print(f"[IMAGE_COMPARISON]   ✓ Source image resized to: {img_src.size}")
            logging.info(f"  Source image resized to: {img_src.size}")
        
        # Convert to RGB if needed
        if img_src.mode != 'RGB':
            img_src = img_src.convert('RGB')
            logging.debug(f"  Converted source image to RGB")
        if img_tgt.mode != 'RGB':
            img_tgt = img_tgt.convert('RGB')
            logging.debug(f"  Converted target image to RGB")
        
        # Calculate SSIM directly for detailed logging
        array1 = np.array(img_src)
        array2 = np.array(img_tgt)
        
        # Determine the window size for SSIM
        min_dim = min(array1.shape[0], array1.shape[1])
        if min_dim < 7:
            win_size = min_dim if min_dim % 2 == 1 else min_dim - 1
            if win_size < 1:
                logging.error(f"  Image too small for SSIM computation (min dimension < 1)")
                return 0.0
        else:
            win_size = 7
        
        print(f"[IMAGE_COMPARISON]   SSIM window size: {win_size}")
        logging.info(f"  SSIM window size: {win_size}")
        
        try:
            # Calculate SSIM
            try:
                similarity = ssim(array1, array2, win_size=win_size, channel_axis=2)
            except TypeError:
                similarity = ssim(array1, array2, win_size=win_size, multichannel=True)
            
            # Detailed logging - use print to ensure visibility
            print(f"[IMAGE_COMPARISON]   SSIM similarity score: {similarity:.6f}")
            print(f"[IMAGE_COMPARISON]   SSIM threshold: {ssim_threshold:.6f}")
            print(f"[IMAGE_COMPARISON]   Difference: {similarity - ssim_threshold:.6f}")
            
            logging.info(f"  SSIM similarity score: {similarity:.6f}")
            logging.info(f"  SSIM threshold: {ssim_threshold:.6f}")
            logging.info(f"  Difference: {similarity - ssim_threshold:.6f}")
            
            structure_same = similarity >= ssim_threshold
            
            if structure_same:
                print(f"[IMAGE_COMPARISON]   ✓ Comparison PASSED: SSIM ({similarity:.6f}) >= threshold ({ssim_threshold:.6f})")
                logging.info(f"  ✓ Comparison PASSED: SSIM ({similarity:.6f}) >= threshold ({ssim_threshold:.6f})")
            else:
                print(f"[IMAGE_COMPARISON]   ✗ Comparison FAILED: SSIM ({similarity:.6f}) < threshold ({ssim_threshold:.6f})")
                print(f"[IMAGE_COMPARISON]   💡 Consider lowering threshold if images are visually identical")
                logging.warning(f"  ✗ Comparison FAILED: SSIM ({similarity:.6f}) < threshold ({ssim_threshold:.6f})")
                logging.warning(f"  Consider lowering threshold if images are visually identical")
            
            return 1.0 if structure_same else 0.0
            
        except Exception as e:
            print(f"[IMAGE_COMPARISON]   ✗ ERROR: SSIM computation failed: {e}")
            print(f"[IMAGE_COMPARISON]   Error details: {type(e).__name__}: {str(e)}")
            logging.error(f"  SSIM computation failed: {e}")
            logging.error(f"  Error details: {type(e).__name__}: {str(e)}")
            return 0.0
        
    except FileNotFoundError as e:
        print(f"[IMAGE_COMPARISON]   ✗ ERROR: File not found: {e}")
        logging.error(f"  File not found: {e}")
        return 0.0
    except Exception as e:
        print(f"[IMAGE_COMPARISON]   ✗ ERROR: check_structure_sim_with_threshold error: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"[IMAGE_COMPARISON]   Traceback: {traceback.format_exc()}")
        logging.error(f"  check_structure_sim_with_threshold error: {type(e).__name__}: {str(e)}")
        logging.error(f"  Traceback: {traceback.format_exc()}")
        return 0.0
```
