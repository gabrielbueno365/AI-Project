# Usando o Modelo Whisper Large V3 Turbo

## Visão Geral

Esta documentação explica o uso do modelo `whisper-large-v3-turbo` para transcrição de áudio em nosso chatbot. Este modelo é uma versão mais leve e otimizada do Whisper Large V3, oferecendo bom equilíbrio entre qualidade e velocidade de transcrição.

## Comparação com o Modelo Standard

| Característica | whisper-large-v3-turbo | whisper-large-v3 (standard) |
|---------------|------------------------|----------------------------|
| Tamanho | Menor | Maior |
| Velocidade | Mais rápido | Mais lento |
| Recursos | Otimizado para transcrição | Completo (transcrição + tradução) |
| Precisão | Excelente para a maioria dos casos | Potencialmente mais preciso em casos complexos |
| Uso de recursos | Mais eficiente | Mais intensivo |

## Integração no Projeto

### Via Groq API

A integração com a Groq API é direta, bastando especificar o nome correto do modelo:

```python
response = await groq_service.transcribe_audio(
    audio_file=audio_file,
    model="whisper-large-v3-turbo",
    language="pt-BR",
    response_format="json"
)
```

### Via Hugging Face

Para o Hugging Face, usamos o endpoint específico para o modelo turbo:

```python
url = f"https://router.huggingface.co/hf-inference/models/openai/whisper-large-v3-turbo"

# Com o cliente
response = await client.post(
    url=url,
    files={"file": ("audio.mp3", audio_file)},
    headers=headers,
    params={"language": "pt"}
)
```

## Configuração no Projeto

O modelo é definido centralmente nas configurações:

```python
# Em config.py
whisper_model: str = "whisper-large-v3-turbo"
whisper_language: str = "pt-BR"
```

Estes valores são então usados consistentemente em todo o código para garantir que todas as chamadas de API utilizem o mesmo modelo e idioma.

## Parâmetros Adicionais

Ao utilizar o modelo, é possível configurar diversos parâmetros:

- **language**: Define o idioma esperado do áudio (ex: "pt-BR" para português)
- **response_format**: Define o formato da resposta ("json", "text", "verbose_json")
- **temperature**: Controla a aleatoriedade (0 a 1, menor é mais determinístico)
- **prompt**: Texto opcional para orientar a transcrição

## Benefícios da Versão Turbo

- **Maior velocidade de processamento**: Respostas mais rápidas para o usuário
- **Menor uso de recursos**: Economia de processamento nas APIs
- **Menor latência**: Experiência mais fluida para o usuário
- **Boa precisão**: Mantém alta qualidade de transcrição para a maioria dos casos

## Considerações de Uso

- Ideal para transcrições gerais em português
- Suficiente para a maioria dos casos de uso do chatbot
- Caso específico de áudios muito complexos ou ruidosos, considerar fallback para o modelo completo

## Exemplos de Uso Direto

### Usando Python Requests

```python
import requests

API_URL = "https://router.huggingface.co/hf-inference/models/openai/whisper-large-v3-turbo"
headers = {"Authorization": "Bearer YOUR_TOKEN"}

def transcribe(filename):
    with open(filename, "rb") as f:
        data = f.read()
    response = requests.post(
        API_URL, 
        headers={"Content-Type": "audio/mp3", **headers}, 
        data=data
    )
    return response.json()
```

### Usando HuggingFace Hub Client

```python
from huggingface_hub import InferenceClient

client = InferenceClient(
    provider="hf-inference",
    api_key="YOUR_TOKEN",
)
output = client.automatic_speech_recognition(
    "audio.mp3", 
    model="openai/whisper-large-v3-turbo"
)
```
