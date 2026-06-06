import sys, re

content = sys.stdin.read()
print(f"服务器 Project.vue: {len(content.split(chr(10)))} 行")

checks = {
    "onActivated/onDeactivated": ["onActivated", "onDeactivated"],
    "输入框硬编码颜色 #252540": ["#252540"],
    "硬编码边框 #556688": ["#556688"],
    "硬编码边框 #7c3aed": ["#7c3aed"],
    "硬编码背景 #181826": ["#181826"],
}

for name, keywords in checks.items():
    found = all(k in content for k in keywords)
    print(f"  {'Y' if found else 'N'} {name}")