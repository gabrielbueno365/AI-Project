# Instalação e Configuração do FFmpeg no Windows

Este guia fornece instruções detalhadas para instalar e configurar o FFmpeg no Windows, que é necessário para o processamento de áudio no chatbot.

## Instalação Automática

O método mais fácil é usar o script de instalação incluído:

1. Abra o Prompt de Comando ou PowerShell como administrador
2. Navegue até o diretório do projeto: `cd C:\AI\chatbot`
3. Execute o script: `python scripts\install_ffmpeg.py`
4. Reinicie o terminal após a instalação

## Instalação Manual

Se a instalação automática falhar, siga estes passos:

1. Baixe o FFmpeg do site oficial:
   - Acesse https://ffmpeg.org/download.html
   - Clique em "Windows Builds" e escolha uma das opções (recomendamos a build gpl do BtbN)
   - Baixe a versão para Windows 64-bit

2. Extraia o arquivo ZIP:
   - Extraia o conteúdo para `C:\Program Files\FFmpeg` (ou outro local de sua escolha)
   - Você deve ter um diretório `bin` contendo os executáveis (ffmpeg.exe, ffprobe.exe, etc.)

3. Adicione ao PATH do sistema:
   - Clique com o botão direito em "Este Computador" ou "Meu Computador"
   - Escolha "Propriedades"
   - Clique em "Configurações avançadas do sistema"
   - Clique no botão "Variáveis de Ambiente"
   - Em "Variáveis do sistema", encontre a variável "Path" e clique em "Editar"
   - Clique em "Novo" e adicione o caminho para o diretório bin do FFmpeg (ex: `C:\Program Files\FFmpeg\bin`)
   - Clique em "OK" para fechar todas as janelas

4. Verifique a instalação:
   - Abra um novo Prompt de Comando ou PowerShell
   - Execute: `ffmpeg -version`
   - Se mostrar informações da versão, está funcionando corretamente

## Solução de Problemas Comuns

### "The system cannot find the file specified"

Este erro ocorre quando o sistema não consegue encontrar o executável do FFmpeg, o que pode acontecer por:

1. **FFmpeg não instalado corretamente**
   - Verifique se os arquivos foram extraídos para o local correto

2. **FFmpeg não está no PATH**
   - Verifique se o diretório bin do FFmpeg está no PATH do sistema
   - Execute `echo %PATH%` para verificar se o caminho aparece

3. **Necessita reiniciar o terminal ou sistema**
   - Após adicionar ao PATH, abra um novo terminal ou reinicie o computador

4. **Conflitos com outras versões**
   - Verifique se há várias instalações de FFmpeg no sistema
   - Remova versões obsoletas ou conflitantes

### Teste Rápido

Para verificar se o FFmpeg está funcionando corretamente:

```cmd
ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 1 -q:a 9 -acodec pcm_s16le test.wav
ffmpeg -i test.wav -codec:a libmp3lame -qscale:a 2 test.mp3
```

Se estes comandos funcionarem e criarem os arquivos test.wav e test.mp3, o FFmpeg está configurado corretamente.

## Diagnóstico Completo

Execute o script de diagnóstico para verificar todos os componentes:

```cmd
python scripts\diagnostico_audio.py
```

Este script verifica a instalação do FFmpeg, permissões de diretório e capacidade de conversão.
