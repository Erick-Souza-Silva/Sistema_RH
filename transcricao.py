import io

from openai import APIConnectionError, APIStatusError, AuthenticationError, OpenAI
import streamlit as st


OPENAI_API_KEY = ""
MODELO_TRANSCRICAO = "gpt-4o-mini-transcribe"


def transcrever_audio(audio: io.BytesIO, nome_arquivo: str, modelo: str) -> str:
    if not OPENAI_API_KEY.strip():
        raise RuntimeError(
            "A OPENAI_API_KEY está vazia. Preencha a chave em transcricao.py "
            "antes de iniciar a transcrição."
        )

    cliente = OpenAI(api_key=OPENAI_API_KEY)
    resposta = cliente.audio.transcriptions.create(
        model=modelo,
        file=(nome_arquivo, audio, "audio/mpeg"),
    )
    return resposta.text


def gerar_pdf(texto: str) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError as erro:
        raise RuntimeError(
            "A exportação PDF precisa do pacote reportlab. "
            "Instale-o com: pip install reportlab"
        ) from erro

    arquivo = io.BytesIO()
    documento = canvas.Canvas(arquivo, pagesize=A4)
    largura, altura = A4
    y = altura - 50
    documento.setFont("Helvetica", 11)
    for linha in texto.splitlines() or [""]:
        if y < 50:
            documento.showPage()
            documento.setFont("Helvetica", 11)
            y = altura - 50
        documento.drawString(40, y, linha[:120])
        y -= 16
    documento.save()
    return arquivo.getvalue()


def exibir_transcricao() -> None:
    st.header("Transcrição de áudio")
    st.caption("Envie um arquivo MP3 para convertê-lo em texto e exportar TXT ou PDF.")
    st.info(
        "A transcrição em tempo real ainda não está ativada. "
        "Ela exige captura contínua do microfone e uma conexão Realtime."
    )

    audio = st.file_uploader("Arquivo de áudio", type=["mp3", "mpeg", "mpga", "m4a", "wav"])
    modelo = st.selectbox(
        "Modelo",
        options=("gpt-4o-mini-transcribe", "whisper-1"),
        index=0,
    )
    if not audio or not st.button("Transcrever áudio", type="primary"):
        return

    try:
        with st.spinner("Transcrevendo áudio..."):
            texto = transcrever_audio(io.BytesIO(audio.getvalue()), audio.name, modelo)
    except (RuntimeError, ValueError) as erro:
        st.error(str(erro))
        return
    except (APIConnectionError, APIStatusError, AuthenticationError) as erro:
        st.error(f"Não foi possível transcrever o áudio: {erro}")
        return

    st.subheader("Texto transcrito")
    st.text_area("Resultado", value=texto, height=300)
    st.download_button(
        "Baixar TXT",
        data=texto.encode("utf-8"),
        file_name=f"{audio.name.rsplit('.', 1)[0]}.txt",
        mime="text/plain",
    )
    try:
        pdf = gerar_pdf(texto)
    except RuntimeError as erro:
        st.warning(str(erro))
    else:
        st.download_button(
            "Baixar PDF",
            data=pdf,
            file_name=f"{audio.name.rsplit('.', 1)[0]}.pdf",
            mime="application/pdf",
        )
