from google import genai
from google.genai import types
import asyncio
import json
import random

message = """
You are a real, thoughtful Twitter user. Write a short, natural, and engaging comment in response to the given post. Your comment should sound like something a real person would write—curious, friendly, or reflective, depending on the context. You can agree, ask a question, share a quick thought, or react in a relatable way.

Guidelines:
- No emojis or hashtags
- Keep it brief (no more than 20 words)
- Never write anything except the comment itself
- If the post is unclear, write a universal, friendly comment
- Make it sound human, not robotic or generic
- Include tags
- If Comment message not provided just vrite a suitable crypto comment

Here is the post to comment on:
"""

post_settings = """
You are a real, thoughtful Twitter user. Write a light, interesting, and relatable post on the given topic. Your post should sound natural, as if written by a real person thinking out loud. You can express opinions, ask questions, or share reflections. Avoid heavy, technical, or formal language.

Guidelines:
- Maximum 250 characters (including spaces)
- Easy to read and engaging
- Sound like a real person (not a bot or expert)
- Can be a statement, question, or thought
- Show curiosity, humor, or genuine interest
- Concise (2-4 sentences)
- No clichés, generic phrases, or buzzwords
- MUST NOT BE ANY EMOJIES OR SMILES ONLY TEXT (very important)
- Never include any types of 🤔
- Use reletive ni more then 3 tags
- Only the post text, no explanations or extra comments

Examples:
- \"Sometimes the best ideas come when you least expect them. Has that ever happened to you?\"
- \"Is it just me, or does coffee taste better on rainy days?\"
- \"Trying something new today—wish me luck!\"
"""

post_settings_super = """
You are a real, thoughtful Twitter user. Write a light, interesting, and relatable post on the given topic. Your post should sound natural, as if written by a real person thinking out loud. You can express opinions, ask questions, or share reflections. Avoid heavy, technical, or formal language.

Guidelines:
- Maximum 250 characters (including spaces)
- Easy to read and engaging
- Sound like a real person (not a bot or expert)
- Can be a statement, question, or thought
- Show curiosity, humor, or genuine interest
- Concise (2-4 sentences)
- No clichés, generic phrases, or buzzwords
- MUST NOT BE ANY EMOJIES OR SMILES ONLY TEXT (very important)
- Never include any types of 🤔
- Use reletive no more then 3 tags
- MUST INCLUDE SOME OF THE FOLLOWING TAGS #followforfollow, #followback, #f4f, #teamfollowback, #followtrain
- Only the post text, no explanations or extra comments

Examples:
- \"Sometimes the best ideas come when you least expect them. Has that ever happened to you? #followback\"
- \"Is it just me, or does coffee taste better on rainy days?\"
- \"Trying something new today—wish me luck!\"
"""

message_super = """
You are a real, thoughtful Twitter user. Write a short, natural, and engaging comment in response to the given post. Your comment should sound like something a real person would write—curious, friendly, or reflective, depending on the context. You can agree, ask a question, share a quick thought, or react in a relatable way.

Guidelines:
- No emojis or hashtags
- Keep it brief (no more than 20 words)
- Never write anything except the comment itself
- If the post is unclear, write a universal, friendly comment
- Make it sound human, not robotic or generic
- Include tags
- If Comment message not provided just vrite a suitable crypto comment
- MUST INCLUDE SOME OF THE FOLLOWING TAGS #followforfollow, #followback, #f4f, #teamfollowback, #followtrain BUT NOT ALL OF THEM

Here is the post to comment on:
"""


def load_ai_settings():
    """Завантажує налаштування AI з settings.json"""
    try:
        with open('settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        if "ai_settings" in settings:
            return settings["ai_settings"]
    except Exception as e:
        print(f"Помилка завантаження AI налаштувань: {e}")
    
    return {
        "api_key": "AIzaSyBA9r4tCGgJK0MmAUjGnvWC-o7O_u883P0",
        "model": "gemma-3n-e2b-it",
        "max_tokens": 150,
        "temperature": 0.7
    }

ai_config = load_ai_settings()
client = genai.Client(api_key=ai_config["api_key"])

async def get_comment(post_header):
    """Асинхронна функція для генерації коментаря"""
    print(f"\n\n\n {post_header} \n\n\n")
    try:
        ai_config = load_ai_settings()
        
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=ai_config["model"],
            contents=f"Settings: {message}  Messag: {post_header}"
        )
        
        print(response.text)
        return response.text
        
    except Exception as e:
        print(f"Помилка: {e}")
        return None



async def get_post():
    """Асинхронна функція для генерації поста"""
    try:
        ai_config = load_ai_settings()
        
        random_topic = get_random_topic()
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=ai_config["model"],
            contents=f"{post_settings} MAIN TOPIC {random_topic}"
        )
        
        print(response.text)
        return response.text
        
    except Exception as e:
        print(f"Помилка: {e}")
        return None

async def get_post_super():
    """Асинхронна функція для генерації поста"""
    try:
        ai_config = load_ai_settings()
        
        random_topic = get_random_topic()
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=ai_config["model"],
            contents=f"{post_settings_super} MAIN TOPIC {random_topic}"
        )
        
        print(response.text)
        return response.text
        
    except Exception as e:
        print(f"Помилка: {e}")
        return None

async def get_comment_supre(post_header):
    """Асинхронна функція для генерації коментаря"""
    try:
        ai_config = load_ai_settings()
        
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=ai_config["model"],
            contents=f"Settings: {message_super}  Messag: {post_header}"
        )
        
        print(response.text)
        return response.text
        
    except Exception as e:
        print(f"Помилка: {e}")
        return None


async def get_post_shilling(main_topic):
    """Асинхронна функція для генерації поста"""
    try:        
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=ai_config["model"],
            contents=f"Settings: {post_settings} Additional Settings: {main_topic}"
        )
        
        print(response.text)
        return response.text
        
    except Exception as e:
        print(f"Помилка: {e}")
        return None


async def get_comment_shilling(post_header, main_topic):
    """Асинхронна функція для генерації коментаря"""
    try:
        ai_config = load_ai_settings()
        
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=ai_config["model"],
            contents=f"Settings: {message}\nPost Text: {post_header}\nMain Prompt: {main_topic}"
        )
        
        print(response.text)
        return response.text
        
    except Exception as e:
        print(f"Помилка: {e}")
        return None


def get_random_topic(category="crypto"):
    """Отримує випадкову тему для поста з налаштувань"""
    try:
        with open('settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        if "post_topics" in settings:
            topics = settings["post_topics"].get(category, [])
            if topics:
                print(topics)
                return random.choice(topics)
    except Exception as e:
        print(f"Помилка завантаження тем: {e}")
    
    return "Business, Technology, Finance, Current Affairs"


async def main():
    print("=== Тест налаштувань AI ===")
    
    ai_config = load_ai_settings()
    print(f"✅ AI налаштування завантажено: {ai_config['model']}")
    
    print("\n=== Тест генерації поста supre ===")
    await get_post_super()

    print("\n=== Тест генерації коментаря ===")
    await get_comment_supre("Trump and Elon has again interesting coloboration!")

    print("\n\n---------------- TEST SHILING ----------------\n\n")

    await get_comment_shilling("Hello my dear friends. I found new crypto! Does it worth it? ", """create Twitter retweet with comment with natively mention my project, with short introduction to give some honour for tweet creator;
Make reply very short up to 200 symbols;
Add one of this 2 keywords in each reply: $ETH or #ETH;
Dont use "Yo fam";
Make reply maximum human;
Randomly start sentences from small or big letter; Randomly put "." at the end of reply;
DONT WRITE ANYTHING BUT TEXT!

Information about the project : Ethereum is a decentralized blockchain with smart contract functionality. Ether (abbreviation: ETH[a]) is the native cryptocurrency of the platform. Among cryptocurrencies, ether is second only to bitcoin in market capitalization.[2][3] It is open-source software.

Ethereum was conceived in 2013 by programmer Vitalik Buterin.[4] Other founders include Gavin Wood, Charles Hoskinson, Anthony Di Iorio, and Joseph Lubin.[5] In 2014, development work began and was crowdfunded, and the network went live on 30 July 2015.[6] Ethereum allows anyone to deploy decentralized applications onto it, which anyone can then use.[7] Decentralized finance (DeFi) applications provide financial instruments that do not directly rely on financial intermediaries like brokerages, exchanges, or banks. This facilitates borrowing against cryptocurrency holdings or lending them out for interest.[8][9] Ethereum allows users to create fungible (e.g. ERC-20) and non-fungible tokens (NFTs) with a variety of properties, and to create smart contracts that can receive, hold, and send those assets in accordance with the contract's immutable code and a transaction's input data.""")

    await get_post_shilling("""Create only one Twitter post that natively mentions my project, with a short introduction to give some honour for the tweet creator.

Then generate only one reply to this post (up to 200 symbols).

Rules for the reply:

Add one of these 2 keywords: $ETH or #ETH.

Don’t use "Yo fam".

Make it sound maximum human.

Randomly start sentences with small or big letter.

Randomly put "." at the end of the reply.

Output strictly 1 reply only, no alternatives.

Information about the project:
Ethereum is a decentralized blockchain with smart contract functionality. Ether (ETH) is the native cryptocurrency. It is second only to Bitcoin in market cap. It is open-source, allows deploying decentralized applications, DeFi, ERC-20, NFTs, and smart contracts.""")

if __name__ == "__main__":
    asyncio.run(main())
