import pandas as pd
import streamlit as st


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



if __name__ == "__main__":
    Planiha_RH()
