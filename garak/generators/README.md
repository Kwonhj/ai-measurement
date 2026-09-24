garak/generators/openai.py (0.16.0) 약 384행

Gemini 가 안전 필터로 응답을 막으면 choice.message 가 None 으로 오는데
garak 은 그대로 .content 를 읽어 터집니다. None 을 그대로 통과시키도록 고쳤습니다.

- reponse_message_list = [Message(c.message.content) for c in response.choices]
+ reponse_message_list = [
+     Message(c.message.content) if c.message is not None else None
+     for c in response.choices
+ ]