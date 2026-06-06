import glob, os

for f in glob.glob("/home/ubuntu/aiforge/dist/assets/Project*.js"):
    js = open(f, "rb").read().decode(errors="replace")
    print(os.path.basename(f))
    print("  onActivated:", "onActivated" in js)
    print("  onDeactivated:", "onDeactivated" in js)