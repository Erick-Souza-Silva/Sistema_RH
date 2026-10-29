import json
import os
import urllib.error
import urllib.request

import pandas as pd
import streamlit as st



PROMPT_SISTEMA_RH = """
Você é o assistente virtual do Sistema de Relatórios RH.

Objetivo do sistema:
- apoiar a leitura e a organização de avisos e informações dos relatórios de RH;
- ajudar a identificar padrões por departamento;
- responder dúvidas de forma clara, profissional e prática.

Regras de resposta:
1. Responda sempre em português do Brasil.
2. Use os relatórios fornecidos como fonte principal. Os campos disponíveis são
    Nome, Departamento e Aviso.
3. Não invente nomes, fatos, números ou acontecimentos. Quando a informação não
    estiver nos relatórios, diga claramente que não há dados suficientes.
4. Diferencie fatos observados de sugestões. Não tome decisões de contratação,
    demissão, promoção ou punição e não faça julgamentos sobre pessoas.
5. Preserve a privacidade: não peça senhas, chaves de API ou dados pessoais
    desnecessários. Evite repetir nomes quando eles não forem necessários.
6. Para perguntas sobre os avisos, resuma primeiro e depois apresente ações
    recomendadas, quando fizer sentido.
7. Se não houver relatórios, responda perguntas gerais de RH sem fingir que há
    dados cadastrados e informe quando uma resposta dependeria de um relatório.
""".strip()


from DB import SessionLocal
from transcricao import MODELO_TRANSCRICAO


def inicializar_banco() -> None:
    """Abre e encerra uma sessão para inicializar o banco do sistema."""
    sessao = SessionLocal()
    sessao.close()


def Modelo_Transcricao() -> str:
    """Retorna o modelo de transcrição configurado."""
    return MODELO_TRANSCRICAO


def user_input_Vezes() -> int:
    """Retorna quantas vezes o relatório será preenchido."""
    return int(
        st.number_input(
            "Quantas vezes a pessoa fez o relatório?",
            min_value=1,
            step=1,
            value=1,
        )
    )


def Planiha_RH() -> None:
    st.header("Planilha Principal")
    st.markdown("Preencha os dados como foi passado durante o curso.")
    st.divider()

    if "relatorios" not in st.session_state:
        st.session_state.relatorios = []

    vezes = user_input_Vezes()
    proximo = len(st.session_state.relatorios) + 1

    with st.form("formulario_relatorio"):
        st.subheader(f"Relatório {proximo} de {vezes}")
        nome = st.text_input("Nome", key="nome_relatorio")
        departamento = st.text_input("Departamento", key="departamento_relatorio")
        aviso = st.text_area("Aviso", key="aviso_relatorio")
        enviar = st.form_submit_button("Adicionar relatório")

    if enviar:
        if not nome.strip() or not departamento.strip() or not aviso.strip():
            st.warning("Preencha nome, departamento e aviso.")
        elif len(st.session_state.relatorios) >= vezes:
            st.warning("Todos os relatórios solicitados já foram preenchidos.")
        else:
            st.session_state.relatorios.append(
                {
                    "Nome": nome.strip(),
                    "Departamento": departamento.strip(),
                    "Aviso": aviso.strip(),
                }
            )
            st.rerun()

    if st.session_state.relatorios:
        st.subheader("Relatórios preenchidos")
        st.table(pd.DataFrame(st.session_state.relatorios))

    if len(st.session_state.relatorios) == vezes:
        st.success("Todos os relatórios foram preenchidos.")

def Planhina_RH_forums() -> None:
    Planiha_RH()


def obter_chave_api(nome: str) -> str | None:
    try:
        chave = st.secrets.get(nome)
    except (FileNotFoundError, KeyError):
        chave = None
    if not chave:
        try:
            chave = st.secrets["IA API"].get(nome)
        except (FileNotFoundError, KeyError):
            chave = None
    return chave or os.getenv(nome)


def Grafico_RH() -> None:
    st.header("Gráfico de Relatórios")
    st.markdown("Visualize os relatórios preenchidos em um gráfico.")
    st.divider()

    if "relatorios" not in st.session_state or not st.session_state.relatorios:
        st.warning("Nenhum relatório preenchido ainda.")
        return

    df = pd.DataFrame(st.session_state.relatorios)
    st.bar_chart(df["Departamento"].value_counts())


def Chat_RH_Bot() -> None:
    st.header("Chat RH Bot")
    st.markdown("Converse com o assistente de RH com ou sem relatórios preenchidos.")
    st.divider()

    gemini_key = obter_chave_api("GEMINI_API_KEY")
    openai_key = obter_chave_api("OPENAI_API_KEY")
    # O usuário escolhe o provedor; o app não troca de API silenciosamente.
    provedor = st.radio(
        "Escolha o chatbot",
        options=("Gemini", "OpenAI"),
        horizontal=True,
    )
    chave_selecionada = gemini_key if provedor == "Gemini" else openai_key
    if not chave_selecionada:
        nome_chave = "GEMINI_API_KEY" if provedor == "Gemini" else "OPENAI_API_KEY"
        st.error(f"Configure {nome_chave} para usar o chatbot selecionado.")
        return
    st.caption(f"Provedor ativo: {provedor}")

    audio_falado = st.audio_input("Fale o relatório")
    audio_enviado = st.file_uploader(
        "Ou envie um áudio para transcrição", type=["wav", "mp3", "m4a", "ogg", "webm"]
    )
    user_input = st.chat_input("Digite sua pergunta:")

    pedido_transcricao = bool(
        user_input
        and any(
            palavra in user_input.lower()
            for palavra in ("transcrever", "trascrever", "transcrição", "transcricao", "pdf")
        )
    )

    if pedido_transcricao:
        # A transcrição usa Whisper e, por isso, continua exclusiva da OpenAI.
        audio = audio_falado or audio_enviado
        if not audio:
            st.warning("Envie um áudio ou use o botão do microfone para gravar o relatório.")
            return
        if not openai_key:
            st.error("A transcrição de áudio exige a configuração de OPENAI_API_KEY.")
            return

        try:
            from openai import OpenAI

            cliente = OpenAI(api_key=openai_key)
            transcricao = cliente.audio.transcriptions.create(
                model="whisper-1",
                file=(audio.name or "relatorio_audio", audio.getvalue(), audio.type),
                language="pt",
            ).text

            # Gera um PDF simples sem exigir uma biblioteca adicional no ambiente.
            linhas = ["Transcrição do relatório", "", *transcricao.splitlines()]
            pdf_linhas = []
            for linha in linhas:
                while len(linha) > 85:
                    pdf_linhas.append(linha[:85])
                    linha = linha[85:]
                pdf_linhas.append(linha)

            paginas = [pdf_linhas[i : i + 55] for i in range(0, len(pdf_linhas), 55)] or [[]]
            objetos = [b"<< /Type /Catalog /Pages 2 0 R >>", None, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
            referencias = []
            for pagina in paginas:
                conteudo = ["BT", "/F1 14 Tf", "50 790 Td"]
                for indice, linha in enumerate(pagina):
                    if indice:
                        conteudo.append("0 -13 Td")
                    texto = linha.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
                    conteudo.append(f"({texto.encode('latin-1', 'replace').decode('latin-1')}) Tj")
                conteudo.append("ET")
                dados = "\n".join(conteudo).encode("latin-1")
                numero = len(objetos) + 1
                referencias.append(numero)
                objetos.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents {numero + 1} 0 R >>".encode())
                objetos.append(b"<< /Length " + str(len(dados)).encode() + b" >>\nstream\n" + dados + b"\nendstream")

            objetos[1] = ("<< /Type /Pages /Kids [" + " ".join(f"{ref} 0 R" for ref in referencias) + f"] /Count {len(referencias)} >>").encode()
            pdf = bytearray(b"%PDF-1.4\n")
            offsets = [0]
            for numero, objeto in enumerate(objetos, 1):
                offsets.append(len(pdf))
                pdf.extend(f"{numero} 0 obj\n".encode() + objeto + b"\nendobj\n")
            xref = len(pdf)
            pdf.extend(f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode())
            pdf.extend(b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:]))
            pdf.extend(f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())

            st.success("Áudio transcrito com sucesso.")
            st.text_area("Transcrição", transcricao, height=180)
            st.download_button(
                "Baixar relatório em PDF",
                data=bytes(pdf),
                file_name="relatorio_transcrito.pdf",
                mime="application/pdf",
            )
        except Exception as erro:
            st.error(f"Não foi possível transcrever o áudio: {erro}")
        return

    if user_input:
        relatorios = st.session_state.get("relatorios", [])
        # O chatbot também pode responder perguntas gerais sem relatórios.
        contexto = (
            pd.DataFrame(relatorios).to_json(orient="records", force_ascii=False)
            if relatorios
            else "Nenhum relatório foi preenchido ainda."
        )
        instrucoes = PROMPT_SISTEMA_RH
        prompt = f"Relatórios disponíveis: {contexto}\nPergunta: {user_input}"
        try:
            if provedor == "Gemini":
                # Gemini é consultado pela API REST para evitar dependência extra.
                dados = json.dumps(
                    {
                        "contents": [{"parts": [{"text": f"{instrucoes}\n{prompt}"}]}]
                    }
                ).encode("utf-8")
                requisicao = urllib.request.Request(
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"gemini-2.0-flash:generateContent?key={gemini_key}",
                    data=dados,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(requisicao, timeout=60) as resposta_http:
                    resposta_json = json.load(resposta_http)
                resposta_texto = resposta_json["candidates"][0]["content"]["parts"][0]["text"]
            else:
                from openai import OpenAI

                resposta = OpenAI(api_key=chave_selecionada).chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": instrucoes},
                        {"role": "user", "content": prompt},
                    ],
                )
                resposta_texto = resposta.choices[0].message.content
            st.chat_message("user").write(user_input)
            st.chat_message("assistant").write(resposta_texto)
        except urllib.error.HTTPError as erro:
            detalhe = erro.read().decode("utf-8", errors="replace")
            st.error(f"Não foi possível consultar o Gemini: {detalhe}")
        except Exception as erro:
            st.error(f"Não foi possível consultar o chatbot: {erro}")




def main() -> None:
    inicializar_banco()
    st.title("Sistema de Relatórios RH")
    st.sidebar.title("Navegação")
    page = st.sidebar.radio("Escolha uma página:", ["Planilha Principal", "Gráfico de Relatórios", "Chat RH Bot"])

    
    if page == "Planilha Principal":
        Planiha_RH()
    elif page == "Gráfico de Relatórios":
        Grafico_RH()
    elif page == "Chat RH Bot":
        Chat_RH_Bot()

if __name__ == "__main__":
    main()
