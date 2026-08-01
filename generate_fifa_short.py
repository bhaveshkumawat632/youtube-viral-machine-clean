import os
import sys
import time

sys.path.insert(0, '/home/junglee01/youtube-viral-machine')
from modules.voiceover import generate_voiceover, get_audio_duration
from modules.subtitle_generator import words_from_edge_tts, words_from_script_with_timestamps, generate_ass_subtitles
from modules.video_maker import create_video_from_audio_and_subtitles
from config import OUTPUT_DIR, TEMP_DIR

def generate_fifa_video():
    script_text = """FIFA World Cup chalu ho chuka hai, aur agar aap sachhe football fan ho toh aapko ye 3 sabse khatarnak moments zaroor yaad honge!
Number 3: Zinedine Zidane ka Headbutt. Final match chal raha tha, sabki dhadkane tez thi, aur achanak se Zidane ne Materazzi ke seene mein apna sir maar diya! Poori duniya hila di is red card ne.
Number 2: Maradona ka Hand of God. England ke khilaaf match mein Maradona ne hawa mein udkar ball ko haath se goal ke andar daal diya! Aaj bhi ye football history ka sabse bada chamatkar maana jata hai.
Number 1: Lionel Messi ki Ultimate Jeet. Saalon ki mehnat aur heartbreaks ke baad, GOAT ne aakhirkaar apna sapna poora kiya.
Aapka favorite World Cup moment kaun sa hai? Niche comment karke batao!"""

    output_dir = os.path.join(OUTPUT_DIR, f"fifa_world_cup_{int(time.time())}")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    output_mp4 = os.path.join(output_dir, "fifa_iconic_moments.mp4")
    temp_audio = os.path.join(TEMP_DIR, "fifa_voice.mp3")
    temp_ass = os.path.join(TEMP_DIR, "fifa_subtitles.ass")
    bg_video = "/home/junglee01/youtube-viral-machine/backgrounds/fifa_moments.mp4"
    
    print("🎙️ Generating Voiceover...")
    voice_file, tts_path, tts_metadata = generate_voiceover(script_text, temp_audio, "hindi_female")
    
    print("📝 Generating Subtitles...")
    if tts_metadata and len(tts_metadata) > 0:
        words = words_from_edge_tts(tts_metadata)
    else:
        words = words_from_script_with_timestamps(script_text, temp_audio)
        
    generate_ass_subtitles(words, temp_ass)
    
    print("🎬 Rendering Final Video...")
    create_video_from_audio_and_subtitles(
        temp_audio, temp_ass, output_mp4,
        background_video=bg_video,
        video_format="shorts"
    )
    print(f"✅ Finished! Video saved to: {output_mp4}")

if __name__ == "__main__":
    generate_fifa_video()
