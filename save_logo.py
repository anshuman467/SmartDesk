"""
Run this once to copy the logo from the chat upload into assets/logo.png
Usage: python save_logo.py
"""
import glob, os, shutil

src_dir = os.path.expandvars(
    r"%USERPROFILE%\.gemini\antigravity\brain\fd62a4ff-fd2f-404d-8f33-4f58da99bf14\.tempmediaStorage"
)

# Get the most recently added media PNG (that's the logo the user uploaded)
pngs = sorted(
    glob.glob(os.path.join(src_dir, "media_*.png")),
    key=os.path.getmtime,
    reverse=True
)

if not pngs:
    print("❌ No media PNG found in temp storage.")
else:
    dst = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
    shutil.copy2(pngs[0], dst)
    print(f"✅ Logo saved to: {dst}")
    print(f"   Source: {pngs[0]}")
