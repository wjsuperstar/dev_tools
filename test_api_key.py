from openai import OpenAI

client = OpenAI(api_key="sk-MTQwLTExNTc0NzY2NTU4LTE3NzMzNjQ0MTU5NzQ=", base_url="https://api.scnet.cn/api/llm/v1")

response = client.chat.completions.create(
  model="MiniMax-M2.5",
  messages=[
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello"},
  ],
  max_tokens=1024,
  temperature=0.7,
  stream=False
)
print(response.choices[0].message.content)