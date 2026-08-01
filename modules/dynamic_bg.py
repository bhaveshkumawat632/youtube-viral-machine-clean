import cv2
import numpy as np
import math
import os

def create_hypnotic_bg(output_path, duration=10, fps=30, width=1080, height=1920):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frames = duration * fps
    # Precompute grids for speed
    x = np.linspace(-1, 1, width)
    y = np.linspace(-1, 1, height)
    X, Y = np.meshgrid(x, y)
    
    for i in range(frames):
        t = i / fps
        # Complex mathematical flowing gradient
        Z1 = np.sin(X * 3 + t) + np.cos(Y * 5 + t * 1.5)
        Z2 = np.sin(np.sqrt(X**2 + Y**2) * 10 - t * 3)
        Z3 = np.cos(X * Y * 8 + t * 2)
        
        # Combine and normalize to 0-255
        Z = (Z1 + Z2 + Z3) / 3
        Z = (Z + 1) / 2 # 0 to 1
        
        # Map to colors (Hypnotic Neon Purple/Cyan)
        R = (np.sin(Z * np.pi + t) * 0.5 + 0.5) * 255
        G = (np.cos(Z * np.pi - t) * 0.5 + 0.5) * 255
        B = (np.sin(Z * np.pi * 2 + t * 0.5) * 0.5 + 0.5) * 255
        
        frame = np.stack([B, G, R], axis=-1).astype(np.uint8)
        
        # Add a vignette programmatically
        dist = np.sqrt(X**2 + Y**2)
        vignette = np.clip(1.5 - dist, 0, 1)
        frame = (frame * vignette[..., np.newaxis]).astype(np.uint8)
        
        out.write(frame)
        if i % 30 == 0:
            print(f"Rendered {i}/{frames} frames...")
            
    out.release()
    print("Done generating hypnotic background!")

if __name__ == '__main__':
    create_hypnotic_bg('/tmp/hypnotic.mp4', duration=3)
