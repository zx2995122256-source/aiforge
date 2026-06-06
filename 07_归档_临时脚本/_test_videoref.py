import paramiko, time

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

script = r'''
import requests, time, os

BASE = "http://127.0.0.1:7861"

# Check if ffmpeg is available to create a test video
import subprocess
result = subprocess.run(["which", "ffmpeg"], capture_output=True, text=True)
has_ffmpeg = result.returncode == 0
print(f"ffmpeg available: {has_ffmpeg}")

if has_ffmpeg:
    # Create a 2s test video with ffmpeg
    vpath = "/tmp/test_video_ref.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=blue:s=640x360:d=2:r=24",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
        "-c:v", "libx264", "-c:a", "aac", "-shortest", vpath
    ], capture_output=True)
    
    if os.path.exists(vpath):
        vsize = os.path.getsize(vpath)
        print(f"Test video created: {vsize} bytes")
        
        # Upload as video ref
        with open(vpath, "rb") as f:
            vdata = f.read()
        r = requests.post(f"{BASE}/api/upload_video_ref", files={"file": ("test_video.mp4", vdata, "video/mp4")})
        print(f"Upload video ref: {r.status_code} {r.text[:200]}")
        vref_data = r.json()
        video_ref_url = vref_data.get("uri", "")
        print(f"Video ref URL: {video_ref_url}")
        
        if video_ref_url:
            # Test: Video gen WITH ref video
            print("\n=== TEST: Video gen with ref video (Gemini Omni) ===")
            r = requests.post(f"{BASE}/api/generate_video", json={
                "prompt": "a person walking in a forest, cinematic lighting",
                "model": "Gemini Omni",
                "ratio": "16:9",
                "duration": 6,
                "resolution": "720p",
                "reference_video": video_ref_url
            })
            print(f"Submit: {r.status_code} {r.text[:200]}")
            vid_task = r.json()
            vid_task_id = vid_task.get("task_id")
            
            if vid_task_id:
                for i in range(36):
                    time.sleep(10)
                    r = requests.get(f"{BASE}/api/task/{vid_task_id}", timeout=5)
                    t = r.json()
                    status = t.get("status", "")
                    uri = str(t.get("result_uri", ""))[:50]
                    err = str(t.get("error", ""))[:60]
                    print(f"  [{i*10}s] task {vid_task_id}: status={status} uri={uri} error={err}")
                    if status in ("completed", "failed"):
                        break
else:
    print("No ffmpeg, checking for existing video refs...")
    refs_dir = "/home/ubuntu/oiioii/data/output/refs/"
    vid_files = [f for f in os.listdir(refs_dir) if f.startswith("vidref_") and os.path.getsize(os.path.join(refs_dir, f)) > 100000]
    if vid_files:
        vf = vid_files[-1]
        vpath = os.path.join(refs_dir, vf)
        print(f"Using existing: {vf} ({os.path.getsize(vpath)} bytes)")
        with open(vpath, "rb") as f:
            vdata = f.read()
        r = requests.post(f"{BASE}/api/upload_video_ref", files={"file": (vf, vdata, "video/mp4")})
        print(f"Upload: {r.status_code} {r.text[:200]}")
        video_ref_url = r.json().get("uri", "")
        print(f"Video ref URL: {video_ref_url}")
    else:
        print("No video refs available!")

print("\n=== DONE ===")
'''

sftp = ssh.open_sftp()
with sftp.open('/tmp/test_videoref.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('nohup python3 -u /tmp/test_videoref.py > /tmp/test_videoref.log 2>&1 & echo $!')
pid = stdout.read().decode().strip()
print(f"Started video ref test, PID: {pid}")
time.sleep(15)

stdin, stdout, stderr = ssh.exec_command('cat /tmp/test_videoref.log')
log = stdout.read().decode()
print(log[:1500] if log else "(no output yet)")

ssh.close()
