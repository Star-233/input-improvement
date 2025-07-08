import requests
import json

def read_file_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"错误：文件 {file_path} 未找到。")
        return ""
    except Exception as e:
        print(f"读取文件 {file_path} 时出错：{e}")
        return ""


# 封装请求聊天模型的函数
def chat_with_model(
    prompt: str,  # 添加类型注解
    api_key="sk-zdxuyqwqckqwqnauqwqglpveqwqpiehqkqwqnynqwqwqow",
    base_url="https://api.siliconflow.cn/v1/chat/completions",
    model="Qwen/Qwen3-8B",
):
    url = base_url

    payload = {
        "model": model,
        "enable_thinking": False,
        "messages": [
            {"role": "system", "content": read_file_content("system_prompt.md")},
            {"role": "user", "content": prompt},
        ],
        "stream": True,
        "max_tokens": 100,
    }
    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, json=payload, headers=headers, stream=True)
    response.raise_for_status()

    # 流式处理响应
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode("utf-8")
            if decoded_line.startswith("data:"):
                data = decoded_line[len("data:") :].strip()
                if data == "[DONE]":
                    break
                try:
                    response_data = json.loads(data)
                    if response_data.get("choices"):
                        delta = response_data["choices"][0]["delta"]
                        content = delta.get("content", "")
                        if content:
                            yield content
                except json.JSONDecodeError:
                    continue
    # response_data = response.json()
    # ai_content = response_data["choices"][0]["message"].get("content", "")
    # return ai_content
if __name__ == "__main__":
    print(read_file_content("system_prompt.md"))
