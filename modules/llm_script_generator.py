import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

def generate_powerful_script(topic="Dark Psychology Tricks", language="hindi"):
    """Generates a high-retention, viral script using JARVIS UnifiedRouter failover loops."""
    # Import UnifiedRouter from the parent JARVIS universal folder
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    try:
        from jarvis_universal.core.api_router import UnifiedRouter
        router = UnifiedRouter()
    except Exception as e:
        print(f"⚠️ Could not load JARVIS UnifiedRouter: {e}")
        router = None

    system_prompt = (
        "You are a master YouTube Shorts viral scriptwriter and AI Film Director. "
        "Your goal is to write a script with EXTREMELY high retention, AND provide highly detailed AI-video prompts for each scene. "
        "The content MUST be mind-blowing and deeply psychological. "
        "Language must be 100% ENGLISH. "
        "Output ONLY valid JSON matching this schema:\n"
        '{"title": "Viral Title", "scenes": [{"text": "Sentence to be spoken", "visual_prompt": "Cinematic prompt of characters role-playing the scene", "youtube_search_query": "short 3-4 word youtube search query for cinematic stock footage of characters (e.g. scientist talking stock footage)"}]}'
    )

    user_prompt = f"Write a highly engaging viral YouTube Shorts script about: {topic}. Break it into 12-15 fast-paced, very short scenes (each scene should contain exactly 1 sentence, about 3-4 seconds of speech). Provide a highly descriptive visual prompt and a unique search query for each scene to ensure the visuals change constantly."

    print(f"🧠 Generating powerful LLM script for topic: '{topic}' via JARVIS UnifiedRouter...")
    
    try:
        if not router:
            raise RuntimeError("Router not initialized")
        response_text = router.completion(system_prompt, user_prompt, response_json=True)

        if response_text.startswith("```json"):
            response_text = response_text.split("```json", 1)[1].rsplit("```", 1)[0].strip()
        elif response_text.startswith("```"):
            response_text = response_text.split("```", 1)[1].rsplit("```", 1)[0].strip()
        
        # Find the JSON block aggressively
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            response_text = response_text[start_idx:end_idx+1]
            
        script_data = json.loads(response_text)
        return script_data
    except Exception as e:
        print(f"⚠️ LLM Script Generation failed or timed out: {e}. Using high-retention 12-scene fallback.")
        topic_lower = topic.lower()
        
        # Topic-specific premium fallbacks
        if "dark" in topic_lower or "manipulative" in topic_lower or "control" in topic_lower:
            return {
                "title": "Dark Psychology Secrets Exposed",
                "scenes": [
                    {"text": "Here is a dark psychology trick to make someone instantly trust you.", "visual_prompt": "A mysterious person speaking in shadows.", "youtube_search_query": "mysterious person shadow"},
                    {"text": "When talking to someone, match their breathing rate and body language subtly.", "visual_prompt": "A close up of two people talking closely.", "youtube_search_query": "people talking close"},
                    {"text": "This creates an unconscious bond known as mirroring.", "visual_prompt": "A split screen showing identical gestures.", "youtube_search_query": "reflection mirror"},
                    {"text": "Another secret is the Ben Franklin effect.", "visual_prompt": "A historic old book opening on a wooden desk.", "youtube_search_query": "old book open"},
                    {"text": "If you ask someone for a small favor, they will like you more.", "visual_prompt": "A person handing a cup of coffee to a friend.", "youtube_search_query": "friend sharing coffee"},
                    {"text": "Their brain rationalizes that they must like you if they helped you.", "visual_prompt": "A digital graphic of brain waves thinking.", "youtube_search_query": "brain thinking graphic"},
                    {"text": "To detect if someone is lying, watch their eye movements.", "visual_prompt": "A macro shot of a human eye blinking.", "youtube_search_query": "human eye close"},
                    {"text": "Liars often look up and to the right when fabricating details.", "visual_prompt": "A worried businessman looking up nervously.", "youtube_search_query": "worried man face"},
                    {"text": "While looking up and to the left usually means retrieving memory.", "visual_prompt": "A calm student remembering an answer.", "youtube_search_query": "student thinking calm"},
                    {"text": "Silence is the ultimate weapon in conversations.", "visual_prompt": "A finger placed on lips in a dark setting.", "youtube_search_query": "quiet finger lips"},
                    {"text": "If someone gives an incomplete answer, just look them in the eyes and stay silent.", "visual_prompt": "Two people lock eyes in an intense meeting.", "youtube_search_query": "intense eye contact"},
                    {"text": "They will feel uncomfortable and keep talking to fill the void.", "visual_prompt": "A person speaking nervously at a conference.", "youtube_search_query": "nervous speaker"},
                    {"text": "Subscribe to master the art of mind control.", "visual_prompt": "A clean subscribe graphic overlay.", "youtube_search_query": "subscribe button"}
                ]
            }
        elif "read" in topic_lower or "eye" in topic_lower or "attract" in topic_lower:
            return {
                "title": "How to Read Anyone Instantly",
                "scenes": [
                    {"text": "Want to read anyone like an open book? Pay attention to these three signs.", "visual_prompt": "A detective looking through a magnifying glass.", "youtube_search_query": "detective looking"},
                    {"text": "First, watch their feet. They reveal where the mind wants to go.", "visual_prompt": "Close up of feet pointing towards a doorway.", "youtube_search_query": "shoes walking feet"},
                    {"text": "If someone's feet are pointed away from you during a conversation, they want to leave.", "visual_prompt": "A person looking at their watch awkwardly.", "youtube_search_query": "person looking watch"},
                    {"text": "Second, look at their hand gestures.", "visual_prompt": "Open hands gesturing during a presentation.", "youtube_search_query": "presenter hand gestures"},
                    {"text": "Showing open palms indicates honesty and friendliness.", "visual_prompt": "A warm handshake between business partners.", "youtube_search_query": "partners handshake"},
                    {"text": "While hidden hands or clenched fists suggest defensiveness or secrets.", "visual_prompt": "A stressed man with clenched fists in pocket.", "youtube_search_query": "fists in pocket"},
                    {"text": "Third, observe the speed of their blinking.", "visual_prompt": "Close up of an eye blinking fast.", "youtube_search_query": "eye blinking fast"},
                    {"text": "Rapid blinking means someone is stressed or feeling pressured.", "visual_prompt": "A nervous executive sweating in an interview.", "youtube_search_query": "nervous sweating interview"},
                    {"text": "A steady, calm gaze shows confidence and control.", "visual_prompt": "A strong leader looking forward calmly.", "youtube_search_query": "confident leader face"},
                    {"text": "Fake smiles only use the mouth, leaving the eyes unchanged.", "visual_prompt": "A person forced smiling at the camera.", "youtube_search_query": "fake smile person"},
                    {"text": "A real smile, or Duchenne smile, creates wrinkles around the eyes.", "visual_prompt": "A happy grandmother laughing genuinely.", "youtube_search_query": "happy laughing grandmother"},
                    {"text": "Now you know how to read the hidden signals.", "visual_prompt": "A modern digital screen displaying data graphics.", "youtube_search_query": "digital data screen"},
                    {"text": "Subscribe to elevate your emotional intelligence.", "visual_prompt": "A subscribe button animation.", "youtube_search_query": "subscribe button"}
                ]
            }
        else:
            # Default fallback: 5 Mind-Blowing Psychological Facts
            return {
                "title": "5 Mind-Blowing Psychological Facts",
                "scenes": [
                    {
                        "text": "Did you know that your brain can easily create false memories?",
                        "visual_prompt": "A close up of a glowing neural network pulsing.",
                        "youtube_search_query": "brain neurons firing"
                    },
                    {
                        "text": "If you tell yourself you slept well, your brain actually believes it.",
                        "visual_prompt": "A person waking up happily in a bright bedroom.",
                        "youtube_search_query": "waking up happy"
                    },
                    {
                        "text": "This is known as placebo sleep, and it actually boosts your daily energy.",
                        "visual_prompt": "An energetic employee working efficiently at their computer.",
                        "youtube_search_query": "energetic working"
                    },
                    {
                        "text": "Smart people tend to underestimate themselves, thinking they know nothing.",
                        "visual_prompt": "A researcher looking thoughtfully at a complex whiteboard.",
                        "youtube_search_query": "scientist thinking"
                    },
                    {
                        "text": "While less intelligent people think they are absolute geniuses.",
                        "visual_prompt": "A confident person presenting arrogantly in a meeting room.",
                        "youtube_search_query": "confident talking"
                    },
                    {
                        "text": "This mental bias is called the Dunning-Kruger effect.",
                        "visual_prompt": "A sleek digital chart illustrating psychology levels.",
                        "youtube_search_query": "psychology concept"
                    },
                    {
                        "text": "Your brain is actually more creative when you are tired or sleepy.",
                        "visual_prompt": "An artist drawing passionately late at night under a desk lamp.",
                        "youtube_search_query": "artist drawing night"
                    },
                    {
                        "text": "That is why your best ideas always come in the shower.",
                        "visual_prompt": "Water droplets falling in a clean modern bathroom.",
                        "youtube_search_query": "shower water"
                    },
                    {
                        "text": "Also, being lonely is as bad for your health as smoking.",
                        "visual_prompt": "A lonely figure sitting on a beach overlooking the ocean.",
                        "youtube_search_query": "lonely beach"
                    },
                    {
                        "text": "It increases stress and weakens your body's immune system.",
                        "visual_prompt": "A stressed worker rubbing their temples at an office desk.",
                        "youtube_search_query": "stressed office worker"
                    },
                    {
                        "text": "Finally, the type of music you listen to changes how you view the world.",
                        "visual_prompt": "A person walking down a busy city street wearing headphones.",
                        "youtube_search_query": "person headphones street"
                    },
                    {
                        "text": "Subscribe now to unlock the deepest secrets of human behavior.",
                        "visual_prompt": "A modern subscribe animation or clean graphic.",
                        "youtube_search_query": "subscribe button"
                    }
                ]
            }

if __name__ == "__main__":
    script = generate_powerful_script()
    print(json.dumps(script, indent=2, ensure_ascii=False))
