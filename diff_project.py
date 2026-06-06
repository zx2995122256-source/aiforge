local = open(r"c:\Users\Administrator\Documents\锤子Aicg\03_AiForge全栈\frontend\src\views\Project.vue", encoding="utf-8").read()
remote = open(r"c:\Users\Administrator\Documents\锤子Aicg\server_Project.vue", encoding="utf-8").read()

local_lines = local.split("\n")
remote_lines = remote.split("\n")

print(f"本地: {len(local_lines)} 行")
print(f"服务器: {len(remote_lines)} 行")

# Find differences
import difflib
diff = list(difflib.unified_diff(remote_lines, local_lines, n=3))
print(f"\n差异行数: {len(diff)}")
for line in diff[:80]:
    print(line)