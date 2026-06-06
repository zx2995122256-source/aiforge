import sys
js = sys.stdin.buffer.read().decode(errors="replace")
print("has #252540:", "#252540" in js)
print("has onActivated:", "onActivated" in js)
print("has #7c3aed:", "#7c3aed" in js)
print("has #181826:", "#181826" in js)
print("has #556688:", "#556688" in js)
print("has onDeactivated:", "onDeactivated" in js)
print("length:", len(js))
