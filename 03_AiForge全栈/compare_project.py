import os

local_file = r"c:\Users\Administrator\Documents\锤子Aicg\03_AiForge全栈\frontend\src\views\Project.vue"
local_lines = open(local_file, "r", encoding="utf-8").read().split("\n")
print(f"本地 Project.vue: {len(local_lines)} 行")

# Key features to compare
checks = {
    "onActivated/onDeactivated": ["onActivated", "onDeactivated"],
    "输入框硬编码颜色 #252540": ["#252540"],
    "硬编码边框 #556688": ["#556688"],
    "硬编码边框 #7c3aed": ["#7c3aed"],
    "硬编码背景 #181826": ["#181826"],
}

for name, keywords in checks.items():
    found = all(k in open(local_file, "r", encoding="utf-8").read() for k in keywords)
    print(f"  {'✅' if found else '❌'} {name}")
