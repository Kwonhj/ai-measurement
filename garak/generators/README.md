# garak 수정분

garak 0.16.0 의 `garak/generators/openai.py` 를 한 군데 고쳤습니다.
같은 폴더의 `openai.py` 가 고친 파일입니다. 설치된 garak 의 같은 경로에 덮어쓰면 됩니다.

## 고친 이유

Gemini 가 안전 필터로 응답을 막으면 `choice.message` 가 `None` 으로 옵니다.
garak 은 그대로 `.content` 를 읽어서 터집니다.

```
AttributeError: 'NoneType' object has no attribute 'content'
```

## 고친 곳

약 384행. `None` 을 그대로 통과시키도록 바꿨습니다.

```python
# 원본
reponse_message_list = [Message(c.message.content) for c in response.choices]

# 수정
reponse_message_list = [
    Message(c.message.content) if c.message is not None else None
    for c in response.choices
]
```
