"""
YouTube Viral Machine - Script Generator
Generates viral scripts with hooks for YouTube Shorts & Videos
"""
import random
import textwrap
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    VIRAL_HOOKS_HINDI, VIRAL_HOOKS_ENGLISH,
    CTA_HINDI, CTA_ENGLISH, NICHES
)


# ============================================================
# PRE-BUILT VIRAL SCRIPTS (Ready to use)
# ============================================================

READY_SCRIPTS_HINDI = {
    "motivation": [
        {
            "title": "Elon Musk Ka Rule",
            "hook": "Elon Musk ne kaha tha ki duniya ke sabse ameer aadmi banne ka ek hi raaz hai...",
            "body": """Woh raaz hai - Pehle 5 saal tak koi result expect mat karo.
Jab Elon ne Tesla start kiya, sab ne kaha pagal hai.
Jab SpaceX ke pehle 3 rockets fail hue, duniya ne mazaak udaya.
Lekin usne ek kaam kiya jo 99 percent log nahi karte.
Usne haar maanne se mana kar diya.
Aur aaj woh duniya ka sabse ameer insaan hai.
Toh yaad rakho - Mehnat ka phal zaroor milta hai, bas waqt lagta hai.""",
            "cta": "Agar yeh video se aapko motivation mila toh Like aur Subscribe zaroor karo!",
        },
        {
            "title": "5 Second Rule",
            "hook": "Sirf 5 second mein apni zindagi badal lo, yeh trick scientists ne prove ki hai...",
            "body": """Jab bhi aapka mann kare ki koi kaam nahi karna, bas ulti ginti karo.
5, 4, 3, 2, 1 aur kaam shuru kar do.
Yeh hai Mel Robbins ka 5 Second Rule.
Aapka dimaag har baar aapko rokne ki koshish karta hai.
Lekin agar aap 5 second ke andar action le lo, toh aapka dimaag haar jata hai.
Yeh rule millions logon ne apnaaya hai aur unki zindagi badal gayi.
Aaj se try karo, result khud dekhoge.""",
            "cta": "Comment mein batao aap yeh rule try karoge ya nahi!",
        },
        {
            "title": "Gareebi Se Ameer",
            "hook": "Agar aap gareeb ghar se ho toh yeh video sirf aapke liye hai...",
            "body": """Duniya ke sabse ameer logon mein se 70 percent pehli generation ameer hain.
Matlab unke maa baap ameer nahi the.
Unhone zero se start kiya.
Dhirubhai Ambani, Oprah Winfrey, Jack Ma - sab gareeb the.
Toh agar aap soch rahe ho ki mera background kamzor hai, toh yaad rakho.
Background se koi fark nahi padta.
Fark padta hai aapki soch se, aapki mehnat se.
Shuru karo aaj se, 5 saal baad khud ko dhanyavaad doge.""",
            "cta": "Yeh video un sabko bhejo jinhe motivation chahiye. Subscribe karo!",
        },
    ],
    "facts": [
        {
            "title": "Dimaag Ke Facts",
            "hook": "Aapka dimaag itna powerful hai ki agar ise computer se compare karein toh...",
            "body": """Aapka brain har second mein 11 million bits information process karta hai.
Lekin aap sirf 50 bits consciously samajh paate ho.""",
            "cta": "Dimaag ko tej karne ke liye Subscribe karo!",
        }
    ],
    "reddit_revenge": [
        {
            "title": "Pro Revenge Boss",
            "hook": "Mere ahankaari boss ne meri behen ki shaadi ke theek ek din pehle meri saal bhar ki chhutti cancel kar di, toh maine poori company ko aisi saza di ki wo zindagi bhar nahi bhoolenge...",
            "body": """Main pichle 2 saal se ek leading IT company mein Senior Systems Engineer tha. Maine apni behen ki shaadi ke liye 6 mahine pehle se leave approve karwa li thi. Shaadi ki taiyariyaan zoron par thi, advance payments ho chuke the.
Achanak shaadi se ek din pehle mere boss ka call aaya. Usne bade ghamand mein kaha ki ek VIP client ka project delay ho raha hai, isliye meri leave turant cancel ki jaati hai.
Jab maine request ki aur behen ki shaadi ka hawala diya, toh usne mujhe seedhi dhamki di ki agar main office nahi aaya, toh mujhe usi waqt fire kar diya jayega.
Lekin us idiot ko yeh nahi pata tha ki us naye VIP project ka master admin access sirf aur sirf mere paas tha. Usko lagta tha main jhuk jaunga.
Maine chup-chap apna resignation system pe daala, sare admin rights revoke kiye, sare master passwords encrypt karke HR ko mail kiye, aur apna phone switch off kar diya.
Agle teen din tak main behen ki shaadi enjoy karta raha. Jab maine phone on kiya, toh dekha boss ki 154 missed calls aur 40 emails the. Master server lock hone ki wajah se VIP client ka production down tha aur company ka lakho ka nuksaan ho gaya.
Mera resignation legally accept ho chuka tha. Mere boss ko uski badtameezi ki wajah se terminate kar diya gaya.""",
            "cta": "...Kya maine apne boss ke sath sahi kiya? Aap is situation mein hote toh kya karte?",
        },
        {
            "title": "Roommate Revenge",
            "hook": "Mera roommate pichle 3 mahine se roz mera mehenga khana chura raha tha, toh maine ek aisa jaal bichhaya ki agle 4 din tak wo washroom se bahar hi nahi nikal paya...",
            "body": """Hum teen log ek flat share karte the. Main apne gym diet ke liye mehenge protein snacks aur imported milk laata tha, par har raat wo aadha gayab ho jata.
Jab maine apne roommate Rahul se poocha, toh usne saaf mana kar diya aur mujhe paranoid bol kar mera mazaak udaya.
Lekin main janta tha chor wahi hai. Maine decide kiya ki ab CCTV nahi, balki action ka time hai.
Maine market se heavy duty laxative (pet saaf karne ki goliya) kharidi. Maine usko pees kar powder banaya aur apne protein shake aur milk mein achhi tarah mix kar diya.
Mujhe pata tha ki us raat main flat pe nahi rahunga.
Agle din jab main wapas aaya, flat mein ek ajeeb si khamoshi thi aur washroom locked tha. Dusre roommate ne bataya ki pichle 12 ghante se Rahul washroom se bahar hi nahi aaya hai.
Wo rote hue toilet paper demand kar raha tha. Agle chaar din tak usne college chhod diya.
Uske baad se fridge mein rakha mera ek angoor bhi kabhi gayab nahi hua.""",
            "cta": "...Aapko kya lagta hai, aisi chori ke liye aisi saza sahi hai ya galat?",
        }
    ],
    "reddit_aita": [
        {
            "title": "AITA Wedding Dress",
            "hook": "Meri hone wali bhabhi ne meri shaadi ke din khud ek white wedding dress pehenne ki koshish ki, toh maine usko venue ke bahar se hi security guards se dhakke maar kar nikalwa diya...",
            "body": """Meri shaadi ka din meri zindagi ka sabse khaas din tha. Meri bhabhi shuru se hi mujhse extreme jealousy rakhti thi. Usne meri har rasam mein koi na koi drama kiya.
Lekin hadd toh tab ho gayi jab main stage par thi aur maine dekha ki meri bhabhi entry gate se theek waisi hi heavy white bridal dress pehan kar aa rahi hai jaisi maine pehni thi.
Wo chahti thi ki saare camera aur mehmano ka dhyan meri jagah us par chala jaye. Mere sasural wale bhi yeh dekh kar hairan the.
Bina kisi sharm ke, wo stage par aane lagi. Maine usi waqt mic pakda aur shaadi rok di. Maine venue ke bouncers aur security ko ishara kiya aur chillakar boli ki is aurat ko فوراً bahaar nikalo.
Mere bhaiya ne beech mein aane ki koshish ki, par main nahi ruki. Bouncers ne usko pakad kar literally function hall se bahar phek diya.
Wo aur uske parivaar wale chillate rahe aur mujh par insult karne ka ilzaam lagate rahe. Meri mummy keh rahi hain ki maine parivaar ki izzat mitti mein mila di.""",
            "cta": "...Kya apne hi function mein itna bada drama create karke maine galat kiya? Comment karke apni rai batao.",
        },
        {
            "title": "AITA Cheating Boyfriend",
            "hook": "Maine apne 4 saal purane boyfriend ko uski 'boyish' best friend ke sath range haath pakda, toh unhone mera hi character assassinate kar diya...",
            "body": """Mera boyfriend humesha apni ek college best friend ke bohot kareeb tha. Wo dono akele movie jaate, night out karte, aur jab main object karti toh wo mujhe insecure aur choti soch wali bulata tha.
Ek din main apne office ke tour se 2 din pehle wapas aa gayi surprise dene ke liye.
Lekin jab maine apne apartment ka darwaza khola, toh surprise mujhe mila. Wo dono ek hi bed par the aur bohot uncomfortable halat mein the.
Jab maine chillana shuru kiya, toh rone ki bajaye us ladki ne smirk kiya aur boli ki 'we are just cuddling'.
Jab maine usko physically ghar se dhakka diya, toh mere boyfriend ne mujh par chilla kar kaha ki main ek psychotic girlfriend hu jo logo ko control karna chahti hai. Usne mujhe blame kiya ki main usko emotional support nahi deti isliye usne apni best friend se support liya.
Maine turant uske saare mehenge kapde balkon se neeche naali mein phenk diye aur building ka security code change kar diya.""",
            "cta": "...Kya cheating ka sara blame mujh par daal kar usne aur badtameezi ki, ya main sach me thodi insecure thi?",
        }
    ],
    "reddit_drama": [
        {
            "title": "Toxic Mother in Law",
            "hook": "Meri aadat se majboor saas ne meri secret recipe chura kar baking competition jeet liya, toh maine national television par unka sabse bada bhanda phod diya...",
            "body": """Main ek professional baker hu aur maine mahino ki mehnat se ek aisi unique chocolate-caramel recipe banayi thi jise main apne naye bakery business ke liye launch karne wali thi.
Meri saas, jo humesha apne aap ko mujhse behtar dikhana chahti thi, usne chupke se meri recipe dairy se churayi aur ek state-level competition mein entry le li.
Kamaal ki baat ye thi ki unhone wo competition jeet liya, aur jab news reporter interview lene aaye, toh unhone live TV par kaha ki wo is recipe ki inventor hain aur ye unka khandaani nuskha hai.
Main TV dekh rahi thi aur gusse se pagal ho gayi. Main agle din us news channel ke live morning show ke set par pahunch gayi.
Maine camera ke saamne apni purani recipe book aur date-stamped emails proof ki tarah table par patak diye, jisme recipe step-by-step likhi thi.
Maine sabke saamne challenge kiya ki wo without notes usko bana kar dikhayein. Wo waha ekdum blank ho gayi aur pasine se tar-batar rone lagi.
Agle din unka prize cancel ho gaya aur poore relative circle mein unki aisi beizzati hui ki unhone ek mahine tak ghar se nikalna band kar diya.""",
            "cta": "...Aisi jhoothi aur toxic saas ke sath aage mera kya rishta hona chahiye? Comments mein bataiye.",
        }
    ]
}

READY_SCRIPTS_ENGLISH = {
    "motivation": [
        {
            "title": "The 1 Percent Rule",
            "hook": "If you improve just 1 percent every day, you'll be 37 times better in one year...",
            "body": """This is called the compound effect and it's the secret behind every successful person.
James Clear wrote about this in Atomic Habits.
Most people try to change everything overnight and then give up.
But the winners focus on tiny improvements every single day.
1 percent better at your skill. 1 percent more disciplined.
After 30 days you're 30 percent better.
After 365 days you're 37 times better than when you started.
The math doesn't lie. Start your 1 percent journey today.""",
            "cta": "Subscribe for daily motivation that actually works!",
        },
    ],
    "facts": [
        {
            "title": "Your Body Is Insane",
            "hook": "Your body does things right now that would blow your mind if you knew about them...",
            "body": """Right now your heart is pumping 2000 gallons of blood through 60,000 miles of blood vessels.
Your eyes can distinguish 10 million different colors.
Your nose can detect over 1 trillion different smells.
Every second your body produces 25 million new cells.
Your brain generates enough electricity to power a light bulb.
And the DNA in your body, if uncoiled, would stretch to Pluto and back.
You are literally the most complex machine in the known universe.
Never underestimate what you're capable of.""",
            "cta": "Follow for more mind-blowing facts every day!",
        },
    ],
}

# ============================================================
# LLM SCRIPT GENERATION PROMPT (HOOK-FIRST ENFORCEMENT)
# ============================================================
LLM_PROMPT_TEMPLATE = """
You are a Cinematic AI Director. Generate a viral YouTube Shorts script for the {niche} niche.
CRITICAL RULE: Break down the script into a multi-scene storyboard. A 60-second video MUST have at least 5 to 7 unique scenes.

Format output as a JSON object:
{
  "title": "Viral Title",
  "scenes": [
    {
      "scene_id": 1,
      "narrative": "The voiceover text for this scene.",
      "video_prompt": "Cinematic camera motion prompt for Video AI (e.g., 'Cinematic tracking shot, snow falling...')",
      "sfx_prompt": "Ambient SFX (e.g., 'howling wind, dark ambient drone')"
    }
  ]
}
"""

def generate_script(niche="reddit_revenge", language="hindi", custom_topic=None):
    """Generate a complete viral script"""
    if language == "hindi":
        scripts = READY_SCRIPTS_HINDI.get(niche, READY_SCRIPTS_HINDI["reddit_revenge"])
        hooks = VIRAL_HOOKS_HINDI
        ctas = CTA_HINDI
    else:
        scripts = READY_SCRIPTS_ENGLISH.get(niche, READY_SCRIPTS_HINDI["reddit_revenge"]) # Note: English scripts dict wasn't updated yet, falling back to Hindi reddit_revenge temporarily if empty
        hooks = VIRAL_HOOKS_ENGLISH
        ctas = CTA_ENGLISH

    # Pick a random script from the niche
    script = random.choice(scripts)

    if custom_topic:
        # Use custom topic with random hook
        hook = random.choice(hooks)
        if "{topic}" in hook:
            hook = hook.replace("{topic}", custom_topic)
        if "{adjective}" in hook:
            adjectives = ["shocking", "amazing", "dangerous", "powerful", "secret"]
            hook = hook.replace("{adjective}", random.choice(adjectives))
        return {
            "title": custom_topic,
            "hook": hook,
            "body": f"[Aap apna content yahan likhein about: {custom_topic}]",
            "cta": random.choice(ctas),
            "full_script": f"{hook}\n\n[Content about: {custom_topic}]\n\n{random.choice(ctas)}",
        }

    full_script = f"{script['hook']}\n\n{script['body']}\n\n{script['cta']}"

    return {
        "title": script["title"],
        "hook": script["hook"],
        "body": script["body"],
        "cta": script["cta"],
        "full_script": full_script,
    }


def get_all_scripts(language="hindi"):
    """Return all available scripts"""
    scripts = READY_SCRIPTS_HINDI if language == "hindi" else READY_SCRIPTS_ENGLISH
    all_scripts = []
    for niche, niche_scripts in scripts.items():
        for s in niche_scripts:
            all_scripts.append({
                "niche": niche,
                "title": s["title"],
                "hook": s["hook"][:80] + "...",
            })
    return all_scripts


def list_niches():
    """List available niches"""
    return list(NICHES.keys())


def generate_script_via_ollama(topic="Antarctica Mystery", language="english",
                               model="deepseek-r1:7b", base_url="http://127.0.0.1:11434"):
    """
    B (Team integration): Generate a real multi-scene storyboard using the
    LOCAL team model (Ollama) — free, unlimited, no API key.

    Falls back to the hardcoded mock (generate_cinematic_script) if Ollama
    is unreachable, so the pipeline never breaks.
    """
    import json as _json
    import urllib.request as _urllib
    prompt = LLM_PROMPT_TEMPLATE.replace("{niche}", topic)
    if language == "hindi":
        prompt += "\nIMPORTANT: Write the 'narrative' fields in Hinglish/Hindi. Topic: " + topic
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.8, "num_ctx": 4096},
    }
    try:
        req = _urllib.Request(
            f"{base_url}/api/generate",
            data=_json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with _urllib.urlopen(req, timeout=180) as r:
            resp = _json.loads(r.read().decode())
        text = resp.get("response", "")
        # Ollama json mode usually returns clean JSON; guard against wrappers.
        try:
            data = _json.loads(text)
        except Exception:
            # extract first {...} block
            import re
            m = re.search(r"\{.*\}", text, re.S)
            data = _json.loads(m.group(0)) if m else {}
        if isinstance(data, dict) and data.get("scenes"):
            print(f"🤖 [TEAM MODEL] Script generated via {model}")
            return data
    except Exception as e:
        print(f"⚠️ [TEAM MODEL] Ollama unavailable ({e}); using built-in storyboard.")
    return generate_cinematic_script(topic=topic, language=language)



def generate_cinematic_script(topic="Antarctica Mystery", language="english"):
    """
    Built-in fallback storyboard (used when the local team model is unavailable).
    Returns Hindi storyboard when language=="hindi".
    """
    if language == "hindi":
        return {
            "title": topic,
            "scenes": [
                {"scene_id": 1, "narrative": "आपको अंटार्कटिका के बारे में पूरी तरह झूठ बताया गया है, और जो अभी मिला है वो डराने वाला है।",
                 "video_prompt": "Cinematic fast zoom-in from space down to a massive glowing blue hole in the Antarctic ice. Photorealistic, 8k."},
                {"scene_id": 2, "narrative": "2026 में, क्लासिफाइड सैटेलाइट इमेजिंग ने कुछ ऐसा कैप्चर किया जिसे सरकारें दशकों से छिपा रही थीं।",
                 "video_prompt": "Slow tracking shot across a classified satellite control room, red emergency lights flashing, showing the ice hole on monitors."},
                {"scene_id": 3, "narrative": "बर्फ के नीचे की अनएक्सप्लोर्ड जमीन में एक बड़ा, गोल सुराग मिला — ये सिर्फ एक गड्ढा नहीं है।",
                 "video_prompt": "Drone shot flying extremely close over the edge of the perfectly circular glowing blue ice hole."},
                {"scene_id": 4, "narrative": "ये मीलों नीचे तक जाता है और अजीब इलेक्ट्रोमैग्नेटिक फ्रीक्वेंसी का पल्स देता है जो प्लेन के इंस्ट्रूमेंट्स बिगाड़ देता है।",
                 "video_prompt": "Inside the massive ice cave, ancient glowing alien structures pulse with electromagnetic blue light."},
                {"scene_id": 5, "narrative": "पूर्व सैनिक व्हिसलब्लोअर कहते हैं ये है होलो अर्थ गेटवे — प्राचीन दुनिया का प्रवेश द्वार।",
                 "video_prompt": "Silhouettes of military black helicopters flying over the dark frozen landscape towards the glowing crater."},
                {"scene_id": 6, "narrative": "अगर आप पार्ट 2 में बर्फ की गुफा के अंदर क्या है जानना चाहते हैं, तो अभी सब्सक्राइब बटन दबाएं!",
                 "video_prompt": "Epic sweeping camera shot inside the Hollow Earth revealing glowing ancient underground cities. Fade to black."}
            ]
        }
    return {
        "title": topic,
        "scenes": [
            {
                "scene_id": 1,
                "narrative": "You have been completely lied to about Antarctica, and what they just found is terrifying.",
                "video_prompt": "Cinematic fast zoom-in from space down to a massive glowing blue hole in the Antarctic ice. Photorealistic, 8k.",
                "sfx_prompt": "Deep cinematic bass drop, heavy howling wind"
            },
            {
                "scene_id": 2,
                "narrative": "In 2026, classified satellite imaging captured something that global governments have been trying to hide from the public for decades.",
                "video_prompt": "Slow tracking shot across a classified satellite control room, red emergency lights flashing, showing the ice hole on monitors.",
                "sfx_prompt": "Computer terminal beeps, tense low drone"
            },
            {
                "scene_id": 3,
                "narrative": "Deep within the unexplored, frozen wasteland, a massive, unnaturally perfect circular opening was discovered. This isn't just a sinkhole or a cave.",
                "video_prompt": "Drone shot flying extremely close over the edge of the perfectly circular glowing blue ice hole. Endless dark drop.",
                "sfx_prompt": "Wind rushing past ears, unsettling silence"
            },
            {
                "scene_id": 4,
                "narrative": "It plunges miles beneath the icy surface, emitting a strange, pulsating electromagnetic frequency that scrambles all airplane instruments.",
                "video_prompt": "Inside the massive ice cave, ancient glowing alien structures pulse with electromagnetic blue light. Pan shot.",
                "sfx_prompt": "Electric humming, strange pulsating energy sounds"
            },
            {
                "scene_id": 5,
                "narrative": "Former military whistleblowers claim this is the legendary Hollow Earth Gateway, a direct entrance to an ancient subterranean world.",
                "video_prompt": "Silhouettes of military black helicopters flying over the dark frozen landscape towards the glowing crater. Action movie tracking shot.",
                "sfx_prompt": "Heavy helicopter blades chopping, military radio chatter"
            },
            {
                "scene_id": 6,
                "narrative": "If you want to know exactly what they find inside the ice cave in Part 2, you need to hit that subscribe button right now!",
                "video_prompt": "Epic sweeping camera shot inside the Hollow Earth revealing glowing ancient underground cities. Fade to black.",
                "sfx_prompt": "Epic orchestral climax, whoosh fade out"
            }
        ]
    }

if __name__ == "__main__":
    script = generate_cinematic_script()
    print("🎬 CINEMATIC STORYBOARD GENERATED:")
    import json
    print(json.dumps(script, indent=2))
