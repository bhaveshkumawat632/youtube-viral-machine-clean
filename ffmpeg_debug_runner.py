import subprocess
import os
from PIL import Image

def main():
    print("Creating temp directory if not exists...")
    os.makedirs("temp", exist_ok=True)
    
    print("Creating dummy 1080x1920 image at temp/test.jpg...")
    img = Image.new('RGB', (1080, 1920), color=(0, 0, 255))
    img.save('temp/test.jpg')
    print("Image created successfully.")

    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", "temp/test.jpg",
        "-vf", "scale=2160:-1,zoompan=z='min(zoom+0.002,1.5)':d=90:x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2':s=1080x1920",
        "-t", "3.0", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast", "temp/test.mp4"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    print("FFmpeg Finished.")
    print("Return code:", result.returncode)
    
    # Save the output to a temp file or print it out.
    with open("temp/ffmpeg_output.txt", "w") as f:
        f.write("=== STDOUT ===\n")
        f.write(result.stdout)
        f.write("\n=== STDERR ===\n")
        f.write(result.stderr)
        f.write(f"\n=== RETURN CODE: {result.returncode} ===\n")
        
    print("Stdout/stderr logged to temp/ffmpeg_output.txt")

if __name__ == "__main__":
    main()
