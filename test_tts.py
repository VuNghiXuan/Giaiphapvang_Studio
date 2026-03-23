import asyncio
import edge_tts

async def test():
    text = "Xin chào Vũ, đây là bài kiểm tra âm thanh."
    voice = "vi-VN-NamMinhNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save("test.mp3")
    print("Xong rồi! Kiểm tra file test.mp3 xem có tiếng không.")

asyncio.run(test())
