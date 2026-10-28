# Sistema_RH
Sistema automatizado para armazenamento e trascrição de audio/escrita

## Executar localmente

```bash
streamlit run main.py
```

O aplicativo local será iniciado na porta `8502`:
<http://localhost:8502>

## Configurar o chatbot

O chatbot funciona mesmo sem relatórios preenchidos. Para configurar as APIs
localmente, copie `.streamlit/secrets.toml.example` para
`.streamlit/secrets.toml` e substitua os valores de exemplo pelas suas chaves:

```toml
GEMINI_API_KEY = "sua-chave-do-gemini"
OPENAI_API_KEY = "sua-chave-da-openai"
```

Use apenas uma chave se preferir. Na tela do chatbot, selecione qual provedor
deve responder. O arquivo `secrets.toml` está bloqueado pelo `.gitignore` e
nunca deve ser enviado ao repositório. Para publicar o app, configure os mesmos
secrets no painel da plataforma de hospedagem.

Não é necessário criptografar a chave dentro do código: a aplicação precisa
recuperar o valor para chamar a API, então a criptografia não impediria a
extração por alguém que controle o servidor. A proteção correta é manter o
secret fora do Git, limitar permissões e revogar a chave se ela for exposta.
