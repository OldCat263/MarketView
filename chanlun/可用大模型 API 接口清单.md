# 可用大模型 API 接口清单

> 基于 2026-06-23 实际连通性测试整理，仅保留**当前环境可连接**的接口。
> 测试环境：国内网络，无代理。

---

## 一、无需 API Key 即可使用（立即可用）

### 1. Pollinations AI

| 项目 | 内容 |
|------|------|
| **平台** | Pollinations AI |
| **接口地址** | `https://text.pollinations.ai/` |
| **认证方式** | **无需 API Key，无需注册** |
| **底层模型** | OpenAI GPT（GPT-3.5 / GPT-4） |
| **支持中文** | 是 |
| **延迟** | 约 1-8 秒 |
| **特点** | 完全免费，开箱即用 |

#### 接入方式（Python）

```python
import requests

url = "https://text.pollinations.ai/"
headers = {"Content-Type": "application/json"}
payload = {
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "你好，请用一句话介绍自己。"}
    ],
    "model": "openai",
    "seed": 42,
}

resp = requests.post(url, headers=headers, json=payload, timeout=60)
print(resp.text)
```

#### 接入方式（cURL）

```bash
curl -X POST https://text.pollinations.ai/ \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "你好，请用一句话介绍自己。"}
    ],
    "model": "openai",
    "seed": 42
  }'
```

#### 接入方式（JavaScript / Fetch）

```javascript
const resp = await fetch("https://text.pollinations.ai/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    messages: [
      { role: "user", content: "你好，请用一句话介绍自己。" }
    ],
    model: "openai",
    seed: 42
  })
});
const text = await resp.text();
console.log(text);
```

---

## 二、需要 API Key（端点可达，配置 Key 后可用）

### 2. 智谱 AI

| 项目 | 内容 |
|------|------|
| **平台** | 智谱 AI（Zhipu AI） |
| **免费模型** | GLM-4-Flash、GLM-4.7-Flash |
| **Base URL** | `https://open.bigmodel.cn/api/paas/v4` |
| **认证方式** | Bearer Token |
| **免费额度** | 2000 万 Token（永久有效） |
| **特点** | 128K-200K 上下文，中文和代码能力强 |

#### 接入方式（Python）

```python
import requests

url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
headers = {
    "Authorization": "Bearer YOUR_ZHIPU_API_KEY",
    "Content-Type": "application/json",
}
payload = {
    "model": "glm-4-flash",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 100,
}

resp = requests.post(url, headers=headers, json=payload)
print(resp.json()["choices"][0]["message"]["content"])
```

#### 环境变量

```bash
export ZHIPU_API_KEY="your-key-here"
```

---

### 3. 百度千帆

| 项目 | 内容 |
|------|------|
| **平台** | 百度千帆（QianFan） |
| **免费模型** | ERNIE-Speed、ERNIE-Lite |
| **Base URL** | `https://qianfan.baidubce.com/v2` |
| **认证方式** | Bearer Token |
| **特点** | 永久免费不限量，合规性强 |

#### 接入方式（Python）

```python
import requests

url = "https://qianfan.baidubce.com/v2/chat/completions"
headers = {
    "Authorization": "Bearer YOUR_QIANFAN_API_KEY",
    "Content-Type": "application/json",
}
payload = {
    "model": "ernie-speed",
    "messages": [{"role": "user", "content": "你好"}],
}

resp = requests.post(url, headers=headers, json=payload)
print(resp.json())
```

#### 环境变量

```bash
export QIANFAN_API_KEY="your-key-here"
```

---

### 4. 腾讯混元

| 项目 | 内容 |
|------|------|
| **平台** | 腾讯混元（Hunyuan） |
| **免费模型** | 混元-Lite |
| **Base URL** | `https://hunyuan.tencent.com/` |
| **认证方式** | Bearer Token |
| **免费额度** | 100 万 Token + 100 万 Embedding（1年） |
| **特点** | 256K 超长上下文，混元-Lite 永久免费 |

#### 接入方式（Python）

```python
import requests

url = "https://hunyuan.tencent.com/v1/chat/completions"
headers = {
    "Authorization": "Bearer YOUR_HUNYUAN_API_KEY",
    "Content-Type": "application/json",
}
payload = {
    "model": "hunyuan-lite",
    "messages": [{"role": "user", "content": "你好"}],
}

resp = requests.post(url, headers=headers, json=payload)
print(resp.json())
```

#### 环境变量

```bash
export HUNYUAN_API_KEY="your-key-here"
```

---

### 5. 讯飞星火

| 项目 | 内容 |
|------|------|
| **平台** | 讯飞星火（Spark） |
| **免费模型** | Spark Lite |
| **Base URL** | `https://xinghuo.xfyun.cn/sparkapi` |
| **认证方式** | Bearer Token |
| **免费额度** | 500 万 Token（约 3 个月） |
| **特点** | 永久免费 Lite 版，独一份免费联网搜索能力 |

#### 环境变量

```bash
export XUNFEI_API_KEY="your-key-here"
```

---

### 6. 硅基流动

| 项目 | 内容 |
|------|------|
| **平台** | 硅基流动（SiliconFlow） |
| **免费模型** | Qwen2.5-7B、GLM-4-9B、DeepSeek-R1-Distill-8B 等 |
| **Base URL** | `https://api.siliconflow.cn/v1` |
| **认证方式** | Bearer Token（OpenAI 兼容格式） |
| **免费额度** | 2000-3000 万 Token（永久有效） |
| **特点** | 9B 以下模型永久免费不限量，OpenAI 兼容 |

#### 接入方式（Python）

```python
import requests

url = "https://api.siliconflow.cn/v1/chat/completions"
headers = {
    "Authorization": "Bearer YOUR_SILICONFLOW_API_KEY",
    "Content-Type": "application/json",
}
payload = {
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 100,
}

resp = requests.post(url, headers=headers, json=payload)
print(resp.json()["choices"][0]["message"]["content"])
```

#### 环境变量

```bash
export SILICONFLOW_API_KEY="your-key-here"
```

---

### 7. 阿里云百炼

| 项目 | 内容 |
|------|------|
| **平台** | 阿里云百炼 |
| **亮点模型** | Qwen 3.6、DeepSeek V3.2、Kimi K2.5 |
| **Base URL** | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| **认证方式** | Bearer Token（OpenAI 兼容格式） |
| **免费额度** | 7000 万 Token（90 天） |

#### 接入方式（Python）

```python
import requests

url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
headers = {
    "Authorization": "Bearer YOUR_DASHSCOPE_API_KEY",
    "Content-Type": "application/json",
}
payload = {
    "model": "qwen-turbo",
    "messages": [{"role": "user", "content": "你好"}],
}

resp = requests.post(url, headers=headers, json=payload)
print(resp.json())
```

#### 环境变量

```bash
export DASHSCOPE_API_KEY="your-key-here"
```

---

### 8. 火山引擎（豆包）

| 项目 | 内容 |
|------|------|
| **平台** | 火山引擎（豆包 / Ark） |
| **免费额度** | 200 万 Token/天 |
| **Base URL** | `https://ark.cn-beijing.volces.com/api/v3` |
| **认证方式** | Bearer Token |
| **特点** | 国内日额度最大，月约 6000 万 |

#### 环境变量

```bash
export ARK_API_KEY="your-key-here"
```

---

### 9. DeepSeek

| 项目 | 内容 |
|------|------|
| **平台** | DeepSeek |
| **亮点模型** | DeepSeek V4（百万上下文，推理强） |
| **Base URL** | `https://api.deepseek.com/v1` |
| **认证方式** | Bearer Token（OpenAI 兼容格式） |
| **免费额度** | 约 500 万 Token（10 元赠金） |

#### 接入方式（Python）

```python
import requests

url = "https://api.deepseek.com/v1/chat/completions"
headers = {
    "Authorization": "Bearer YOUR_DEEPSEEK_API_KEY",
    "Content-Type": "application/json",
}
payload = {
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "你好"}],
}

resp = requests.post(url, headers=headers, json=payload)
print(resp.json())
```

#### 环境变量

```bash
export DEEPSEEK_API_KEY="your-key-here"
```

---

### 10. Kimi（月之暗面）

| 项目 | 内容 |
|------|------|
| **平台** | Kimi（Moonshot） |
| **亮点模型** | K2.5（256K 上下文，长文档/RAG 强） |
| **Base URL** | `https://api.moonshot.cn/v1` |
| **认证方式** | Bearer Token（OpenAI 兼容格式） |
| **免费额度** | 500-1000 万 Token（新用户） |

#### 环境变量

```bash
export MOONSHOT_API_KEY="your-key-here"
```

---

### 11. OpenRouter

| 项目 | 内容 |
|------|------|
| **平台** | OpenRouter |
| **免费模型** | 29 个免费模型，50 次/天 |
| **Base URL** | `https://openrouter.ai/api/v1` |
| **认证方式** | Bearer Token（OpenAI 兼容格式） |
| **特点** | 全球最大聚合平台，返回 340+ 模型 |

#### 接入方式（Python）

```python
import requests

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": "Bearer YOUR_OPENROUTER_API_KEY",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://your-site.com",
    "X-Title": "Your App Name",
}
payload = {
    "model": "openrouter/auto",
    "messages": [{"role": "user", "content": "Hello"}],
}

resp = requests.post(url, headers=headers, json=payload)
print(resp.json())
```

#### 环境变量

```bash
export OPENROUTER_API_KEY="your-key-here"
```

---

### 12. GitHub Models

| 项目 | 内容 |
|------|------|
| **平台** | GitHub Models |
| **亮点模型** | GPT-4o、o3-mini、DeepSeek R1 |
| **Base URL** | `https://models.inference.ai.azure.com` |
| **认证方式** | Bearer Token（GitHub Token） |
| **免费额度** | 每天 50 次 |

#### 接入方式（Python）

```python
import requests

url = "https://models.inference.ai.azure.com/chat/completions"
headers = {
    "Authorization": "Bearer YOUR_GITHUB_TOKEN",
    "Content-Type": "application/json",
}
payload = {
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello"}],
}

resp = requests.post(url, headers=headers, json=payload)
print(resp.json())
```

#### 环境变量

```bash
export GITHUB_TOKEN="your-github-token"
```

---

### 13. Groq

| 项目 | 内容 |
|------|------|
| **平台** | Groq |
| **亮点模型** | Llama 4、DeepSeek R1 |
| **Base URL** | `https://api.groq.com/openai/v1` |
| **认证方式** | Bearer Token |
| **免费额度** | 约 14,400 次/天 |
| **特点** | 速度极快 |

#### 环境变量

```bash
export GROQ_API_KEY="your-key-here"
```

---

### 14. Cerebras

| 项目 | 内容 |
|------|------|
| **平台** | Cerebras |
| **亮点模型** | Llama 系列 |
| **Base URL** | `https://api.cerebras.ai/v1` |
| **认证方式** | Bearer Token |
| **免费额度** | 100 万 Token/天 |
| **特点** | 2000 tok/s 极速推理 |

#### 环境变量

```bash
export CEREBRAS_API_KEY="your-key-here"
```

---

## 三、快速选型建议

| 场景 | 推荐方案 | 接入难度 |
|------|----------|----------|
| **立即可用，零配置** | Pollinations AI | 无需 Key |
| **零成本国内开发** | 智谱 GLM-4-Flash + 硅基流动 | 需注册 |
| **长文档/RAG** | Kimi K2.5 / 智谱 GLM-4 | 需注册 |
| **代码/数学推理** | DeepSeek V4 | 需注册 |
| **多模型聚合** | OpenRouter | 需注册 |
| **企业级稳定** | 阿里百炼 + 火山引擎 | 需注册 |
| **GitHub 生态** | GitHub Models | 需 GitHub Token |

---

## 四、通用 OpenAI 兼容接入模板

国内大部分平台（硅基流动、阿里云百炼、DeepSeek、Kimi、OpenRouter 等）均采用 OpenAI 兼容格式：

```python
import requests

API_KEY = "your-api-key"
BASE_URL = "https://api.example.com/v1"  # 替换为对应平台地址
MODEL = "model-name"                      # 替换为对应模型名

url = f"{BASE_URL}/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}
payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 100,
}

resp = requests.post(url, headers=headers, json=payload)
result = resp.json()
print(result["choices"][0]["message"]["content"])
```

---

*整理时间: 2026-06-23*  
*已删除不可达接口：美团 LongCat、Google Gemini、xAI Grok、Mistral、Perplexity、DuckDuckGo、Blackbox、You.com、Monster API、Poe、Hugging Face、Lambda Labs、OctoAI、Reka AI、CatRouter、Lumi、Chintao AI、FreeModel.dev（页面可达但 API 需 Key）、诗云 API（页面可达但 API 需 Key）*
