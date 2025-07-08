import time
import chat_model_request

for chunk in chat_model_request.chat_with_model("我觉得Ubuntu的动画好看"):
    print(chunk, end='', flush=True)
