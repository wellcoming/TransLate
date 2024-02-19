import json
from typing import List, Callable

from openai import OpenAI
from openai.types.chat.completion_create_params import ResponseFormat

client = OpenAI(base_url="https://api.openai-proxy.com/v1")
template = """请将给出的日文翻译成中文，保持原有转义和格式，直接输出为json格式
EXAMPLE:
{"input":["ニャン","寿司食べたい"]}
{"output":["喵~"，“想吃寿司”]}"""


def batch_translate(ori: List[str], upd_callback: Callable[[List[str], int], None], limit=100) -> List[str]:
    result = []
    for i in range(0, len(ori), limit):
        sori = ori[i:i + limit]
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            response_format=ResponseFormat(type="json_object"),
            max_tokens=4096,
            messages=[
                {"role": "system", "content": template},
                {
                    "role": "system",
                    "content": json.dumps({"input": sori}, ensure_ascii=False)
                }
            ]
        )
        print(json.dumps(sori, ensure_ascii=False))

        # 提取翻译结果
        translated = json.loads(response.choices[0].message.content)["output"]
        upd_callback(translated, len(result))
        result += translated

    return result
