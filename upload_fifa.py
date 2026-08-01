import sys
import os
sys.path.insert(0, '/home/junglee01/youtube-viral-machine')
from modules.youtube_uploader import upload_video

metadata = {
    "title": "Unforgettable FIFA World Cup Moments #shorts #fifa #worldcup #football",
    "description": "The most iconic and unforgettable moments in FIFA World Cup history! Experience the true emotion. \n\n#FIFA #WorldCup #FootballShorts #Messi #Zidane #Maradona #IconicMoments #Soccer",
    "tags": ["fifa", "worldcup", "football", "soccer", "shorts", "messi", "zidane", "maradona", "sports"],
    "category_id": "17"  # 17 is Sports
}

video_path = "/run/media/junglee01/New Volume/testing/output/real_fifa_world_cup_1782214429/real_fifa_iconic_moments.mp4"

if __name__ == "__main__":
    if not os.path.exists(video_path):
        print("Video not found at path.")
        sys.exit(1)
    
    success = upload_video(video_path, metadata)
    if success:
        print("Upload finished successfully.")
    else:
        print("Upload failed.")
