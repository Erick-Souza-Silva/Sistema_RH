import csv
import io

import pandas as pd
import streamlit as st

from transcricao import exibir_transcricao


def dados_do_backend() -> dict[str, list[dict[str, object]]]:
    """Substitua esta função pela consulta ao backend quando ele estiver pronto."""
    return {
        "diario": [
            {"Nome": "Ana Souza", "Última data escrita": "2026-10-14"},
            {"Nome": "Bruno Lima", "Última data escrita": "2026-10-13"},
        ],
        "faltas": [
            {"Nome": "Carlos Silva", "Horas": 8.0, "Data": "2026-10-10"},
            {"Nome": "Daniela Costa", "Horas": 4.0, "Data": "2026-10-12"},
        ],
        "uniformes": [
            {"Nome": "Carlos Silva", "Data": "2026-10-10"},
            {"Nome": "Eduardo Alves", "Data": "2026-10-11"},
        ],
        "atividades_realizadas": [
            {
                "Departamento": "Operações",
                "Atividade": "Conferência de estoque",
                "Data": "2026-10-14",
            },
            {
                "Departamento": "Administrativo",
                "Atividade": "Atualização cadastral",
                "Data": "2026-10-14",
            },
        ],
        "atividades_futuras": [
            {
                "Departamento": "Logística",
                "Atividade": "Inventário semanal",
                "Data prevista": "2026-10-16",
            },
            {
                "Departamento": "Operações",
                "Atividade": "Treinamento de equipe",
                "Data prevista": "2026-10-17",
            },
        ],
    }


def exibir_tabela_com_grafico(
    chave: str,
    titulo: str,
    coluna_categoria: str,
    coluna_valor: str | None = None,
) -> None:
    st.subheader(titulo)
    tabela = st.data_editor(
        pd.DataFrame(dados_do_backend()[chave]),
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key=f"editor_{chave}",
    )

    if tabela.empty:
        st.info("Adicione registros na tabela para visualizar o gráfico.")
        return

    if coluna_valor:
        tabela[coluna_valor] = pd.to_numeric(
            tabela[coluna_valor], errors="coerce"
        ).fillna(0)
        grafico = tabela.groupby(coluna_categoria)[coluna_valor].sum()
    else:
        grafico = tabela[coluna_categoria].fillna("").value_counts()

    st.bar_chart(grafico, height=260)


def exibir_planilha() -> None:
    st.header("Painel da linha de frente")
    st.caption(
        "Esta área exibe os dados do backend. Por enquanto, os dados são demonstrativos; "
        "a edição será persistida quando a integração for conectada."
    )

    secoes = [
        ("diario", "Última data escrita do diário de bordo", "Última data escrita", None),
        ("faltas", "Lista de faltas com horas e nomes", "Nome", "Horas"),
        ("uniformes", "Faltas de uso de uniforme", "Nome", None),
        (
            "atividades_realizadas",
            "Atividades realizadas por departamento",
            "Departamento",
            None,
        ),
        (
            "atividades_futuras",
            "Atividades futuras por departamento",
            "Departamento",
            None,
        ),
    ]
    for secao in secoes:
        exibir_tabela_com_grafico(*secao)


def gerar_planilha() -> None:
    st.header("Criar planilha da equipe")
    st.caption("Preencha os dados e baixe um CSV para compartilhar ou importar no backend.")

    with st.form("formulario_planilha"):
        equipe = st.text_input("Equipe", placeholder="Ex.: Loja 01")
        data = st.date_input("Data")
        quantidade = st.number_input(
            "Quantidade de integrantes", min_value=1, value=1, step=1
        )

        integrantes = []
        for indice in range(int(quantidade)):
            col_nome, col_atividade, col_uniforme = st.columns([2, 3, 1])
            nome = col_nome.text_input("Nome", key=f"nome_{indice}")
            atividade = col_atividade.text_input("Atividade", key=f"atividade_{indice}")
            uniforme = col_uniforme.checkbox("Uniforme", key=f"uniforme_{indice}")
            integrantes.append(
                {
                    "Nome": nome.strip(),
                    "Atividade": atividade.strip(),
                    "Uniforme": "Sim" if uniforme else "Não",
                }
            )

        gerar = st.form_submit_button("Gerar planilha")

    if not gerar:
        return

    if not equipe.strip() or any(
        not integrante["Nome"] or not integrante["Atividade"]
        for integrante in integrantes
    ):
        st.error("Preencha a equipe, o nome e a atividade de todos os integrantes.")
        return

    linhas = [
        {"Equipe": equipe.strip(), "Data": data.isoformat(), **integrante}
        for integrante in integrantes
    ]
    st.success("Planilha gerada com sucesso.")
    st.dataframe(linhas, use_container_width=True, hide_index=True)

    arquivo = io.StringIO()
    escritor = csv.DictWriter(arquivo, fieldnames=linhas[0].keys())
    escritor.writeheader()
    escritor.writerows(linhas)
    st.download_button(
        "Baixar planilha (CSV)",
        data=arquivo.getvalue().encode("utf-8-sig"),
        file_name=f"planilha_{data.isoformat()}.csv",
        mime="text/csv",
    )


def Planhina() -> None:
    st.title("Planhina da Linha de Frente")
    st.write(
        "Organize as atividades da equipe, acompanhe o diário de bordo, "
        "faltas e uso de uniforme."
    )

    pagina = st.sidebar.radio(
        "Navegação",
        ["Painel", "Criar planilha", "Transcrição de áudio"],
    )
    if pagina == "Painel":
        exibir_planilha()
    elif pagina == "Criar planilha":
        gerar_planilha()
    else:
        exibir_transcricao()


def main() -> None:
    st.set_page_config(page_title="Planhina da Linha de Frente", layout="wide")
    st.sidebar.title("Linha de Frente")
    Planhina()


if __name__ == "__main__":
    main()
