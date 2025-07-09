import streamlit as st
from pathlib import Path
import tempfile

# ===== IMPORTAÇÕES DO PROJETO =====
from extractor.extractor import obter_naturalidade
from extractor.extractor_matricula import obter_matricula
from extractor.extractor_matricula_info import obter_info_matricula
from extractor.extractor_cnd import obter_cnd
from extractor.extractor_cnd_estadual import obter_cnd_estadual
from extractor.extractor_cnd_trabalhista import obter_cnd_trabalhista
from extractor.extractor_cnd_prefeitura import obter_cnd_prefeitura
from extractor.extractor_itbi import obter_itbi_info
from extractor.extractor_numero_contrato import obter_numero_contrato      # ⭐️ NOVO ⭐️

from doc_replace.doc_replace import substituir_dados
from doc_replace.doc_replace_matricula import substituir_matricula
from doc_replace.doc_replace_matricula_info import substituir_info_matricula
from doc_replace.doc_replace_cnd import substituir_cnd
from doc_replace.doc_replace_cnd_estadual import substituir_cnd_estadual
from doc_replace.doc_replace_cnd_trabalhista import substituir_cnd_trabalhista
from doc_replace.doc_replace_cnd_prefeitura import substituir_cnd_prefeitura
from doc_replace.doc_replace_itbi import substituir_itbi
from doc_replace.doc_replace_info_adicionais import substituir_num_contrato    # ⭐️ NOVO ⭐️

from transform_pdf.transformar_doc import main as transformar_modelo_docx   # padronizador

# ===== CONFIGURAÇÃO DA PÁGINA =====
st.set_page_config(page_title="Preencher Contrato", page_icon="📝", layout="wide")
st.title("📝 Preenchimento Automático de Contrato Completo")

# ===== SEXO =====
sexo = st.radio("Sexo do cliente:", ['Masculino', 'Feminino'], index=0, horizontal=True)

# ===== UPLOADS (2 linhas de 4 colunas) =====
col1, col2, col3, col4 = st.columns(4)
col5, col6, col7, col8 = st.columns(4)

with col1:
    modelo_file = st.file_uploader("Modelo do contrato (.docx)", type=["docx"], key="modelo")
with col2:
    ficha_file = st.file_uploader("Ficha cadastral (.pdf)", type=["pdf"], key="ficha")
with col3:
    matricula_file = st.file_uploader("Matrícula do imóvel (.pdf)", type=["pdf"], key="matricula")
with col4:
    cnd_file = st.file_uploader("CND Receita Federal (.pdf)", type=["pdf"], key="cnd")
with col5:
    cnd_estadual_file = st.file_uploader("CND Estadual SEFAZ (.pdf)", type=["pdf"], key="cnd_estadual")
with col6:
    cnd_trabalhista_file = st.file_uploader("CND Trabalhista TST (.pdf)", type=["pdf"], key="cnd_trab")
with col7:
    cnd_prefeitura_file = st.file_uploader("CND Prefeitura (.pdf)", type=["pdf"], key="cnd_pref")
with col8:
    itbi_file = st.file_uploader("Boleto ITBI (.pdf)", type=["pdf"], key="itbi")

run_btn = st.button(
    "🚀 Processar",
    disabled=not (modelo_file and ficha_file and matricula_file and cnd_file
                  and cnd_estadual_file and cnd_trabalhista_file
                  and cnd_prefeitura_file and itbi_file)
)

# =====================================================================
if run_btn:
    logs = []
    log_box = st.empty()

    def log(msg: str):
        logs.append(msg)
        log_box.text_area("Logs", "\n".join(logs[::-1]), height=200)   # <<< inverter a ordem dos logs

    log("🔄 Iniciando pipeline...")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # ------- SALVA UPLOADS -------
        modelo_path             = tmpdir / "modelo.docx"
        modelo_padronizado_path = tmpdir / "modelo_padronizado.docx"
        ficha_path              = tmpdir / "ficha.pdf"
        mat_path                = tmpdir / "matricula.pdf"
        cnd_path                = tmpdir / "cnd.pdf"
        cnd_estadual_path       = tmpdir / "cnd_estadual.pdf"
        cnd_trabalhista_path    = tmpdir / "cnd_trabalhista.pdf"
        cnd_prefeitura_path     = tmpdir / "cnd_prefeitura.pdf"
        itbi_path               = tmpdir / "itbi.pdf"

        modelo_path.write_bytes(modelo_file.getbuffer())
        ficha_path.write_bytes(ficha_file.getbuffer())
        mat_path.write_bytes(matricula_file.getbuffer())
        cnd_path.write_bytes(cnd_file.getbuffer())
        cnd_estadual_path.write_bytes(cnd_estadual_file.getbuffer())
        cnd_trabalhista_path.write_bytes(cnd_trabalhista_file.getbuffer())
        cnd_prefeitura_path.write_bytes(cnd_prefeitura_file.getbuffer())
        itbi_path.write_bytes(itbi_file.getbuffer())
        log("✅ Arquivos enviados e salvos temporariamente.")

        # ------- PADRONIZA MODELO -------
        log("🔄 Padronizando modelo do contrato (inserindo variáveis)...")
        transformar_modelo_docx(str(modelo_path), str(modelo_padronizado_path))
        log("✅ Modelo padronizado com variáveis.")

        # ------- NÚMERO DO CONTRATO (NOVO) -------
        log("🔍 Extraindo número do contrato (rodapé)...")
        numero_contrato = obter_numero_contrato(modelo_path)
        log(f"• Nº Contrato extraído: {numero_contrato or '⚠️ não encontrado'}")

        # ------- NATURALIDADE -------
        log("🔍 Extraindo naturalidade...")
        nat = obter_naturalidade(ficha_path)
        log(f"• Naturalidade extraída: {nat}")

        # ------- MATRÍCULA (descrição + detalhes) -------
        log("🔍 Extraindo descrição do imóvel...")
        mat = obter_matricula(mat_path)
        log(f"• Descrição do imóvel extraída (primeiros 100 caracteres): {mat[:100]}...")

        log("🔍 Extraindo informações detalhadas da matrícula...")
        info_matricula = obter_info_matricula(mat_path)
        log(
            f"• Nº Matrícula: {info_matricula.get('NUMERO_MATRICULA','')} | "
            f"Data: {info_matricula.get('DATA_MATRICULA','')} | "
            f"Cartório: {info_matricula.get('CARTORIO_MATRICULA','')} | "
            f"Zona: {info_matricula.get('ZONA_MATRICULA','')}"
        )

        # ------- CERTIDÕES -------
        log("🔍 Extraindo dados da CND Receita Federal...")
        cnd = obter_cnd(cnd_path)
        log(f"• Título: {cnd.get('titulo_certidao','')} | "
            f"Código: {cnd.get('codigo_certidao','')} | "
            f"Data: {cnd.get('data_emissao','')} {cnd.get('hora_emissao','')}")

        log("🔍 Extraindo dados da CND Estadual (SEFAZ)...")
        cnd_estadual = obter_cnd_estadual(cnd_estadual_path)
        log(f"• Nº Estadual: {cnd_estadual.get('numero_cnd_estadual','')} "
            f"({cnd_estadual.get('data_cnd_estadual','')} {cnd_estadual.get('hora_cnd_estadual','')})")

        log("🔍 Extraindo dados da CND Trabalhista (TST)...")
        cnd_trab = obter_cnd_trabalhista(cnd_trabalhista_path)
        log(f"• Nº Trabalhista: {cnd_trab.get('NUMERO_CND_TRAB','')} "
            f"({cnd_trab.get('DATA_CND_TRAB','')} {cnd_trab.get('HORA_CND_TRAB','')})")

        log("🔍 Extraindo dados da CND Prefeitura...")
        cnd_pref = obter_cnd_prefeitura(cnd_prefeitura_path)
        log(f"• Nº Prefeitura: {cnd_pref.get('NUMERO_CND_PREF','')} "
            f"({cnd_pref.get('DATA_CND_PREF','')})")

        # ------- ITBI -------
        log("🔍 Extraindo dados do Boleto ITBI...")
        itbi_info = obter_itbi_info(itbi_path)
        log(f"• Valor ITBI: {itbi_info.get('VALOR_ITBI','')} | "
            f"Guia: {itbi_info.get('GUIA_ITBI','')} | "
            f"Data: {itbi_info.get('DATA_ITBI','')}")

        # ------- SUBSTITUIÇÕES -------
        log("✍️ Aplicando naturalidade e gênero no contrato...")
        passo1 = tmpdir / "passo1.docx"
        substituir_dados(modelo_padronizado_path, passo1, nat, "", sexo)
        log("• Naturalidade e gênero aplicados.")

        log("✍️ Inserindo descrição do imóvel...")
        passo2 = tmpdir / "passo2.docx"
        substituir_matricula(passo1, passo2, mat)
        log("• Descrição do imóvel inserida.")

        log("✍️ Inserindo informações detalhadas da matrícula...")
        passo3 = tmpdir / "passo3.docx"
        substituir_info_matricula(passo2, passo3, info_matricula)
        log("• Informações detalhadas da matrícula inseridas.")

        log("✍️ Inserindo CND Federal...")
        passo4 = tmpdir / "passo4.docx"
        substituir_cnd(
            passo3, passo4,
            titulo_cnd=cnd.get('titulo_certidao',''),
            codigo_cnd=cnd.get('codigo_certidao',''),
            hora_cnd=cnd.get('hora_emissao',''),
            data_cnd=cnd.get('data_emissao',''),
            nome_cnd=cnd.get('nome_empresa','')
        )
        log("• CND Federal inserida.")

        log("✍️ Inserindo CND Estadual...")
        passo5 = tmpdir / "passo5.docx"
        substituir_cnd_estadual(
            passo4, passo5,
            titulo=cnd_estadual.get('titulo_cnd_estadual',''),
            numero=cnd_estadual.get('numero_cnd_estadual',''),
            data=cnd_estadual.get('data_cnd_estadual',''),
            hora=cnd_estadual.get('hora_cnd_estadual',''),
            nome=cnd_estadual.get('nome_cnd_estadual','')
        )
        log("• CND Estadual inserida.")

        log("✍️ Inserindo CND Trabalhista...")
        passo6 = tmpdir / "passo6.docx"
        substituir_cnd_trabalhista(
            passo5, passo6,
            titulo=cnd_trab.get('TITULO_CND_TRAB',''),
            numero=cnd_trab.get('NUMERO_CND_TRAB',''),
            data=cnd_trab.get('DATA_CND_TRAB',''),
            hora=cnd_trab.get('HORA_CND_TRAB',''),
            nome=cnd_trab.get('NOME_CND_TRAB','')
        )
        log("• CND Trabalhista inserida.")

        log("✍️ Inserindo CND Prefeitura...")
        passo7 = tmpdir / "passo7.docx"
        substituir_cnd_prefeitura(
            passo6, passo7,
            numero=cnd_pref.get('NUMERO_CND_PREF',''),
            data=cnd_pref.get('DATA_CND_PREF',''),
            endereco=cnd_pref.get('ENDERECO_CND_PREF','')
        )
        log("• CND Prefeitura inserida.")

        log("✍️ Inserindo ITBI...")
        passo8 = tmpdir / "passo8.docx"
        substituir_itbi(passo7, passo8, itbi_info)
        log("• ITBI inserido.")

        # ------- SUBSTITUIÇÃO DO NÚMERO DO CONTRATO (NOVO) -------
        log("✍️ Inserindo número do contrato no bloco INFORMAÇÕES ADICIONAIS/RESSALVAS...")
        passo_final = tmpdir / "contrato_final.docx"
        if not numero_contrato:
            numero_contrato = "{{NUM_CONTRATO}}"
        substituir_num_contrato(passo8, passo_final, numero_contrato=numero_contrato)
        log("• Número do contrato inserido.")

        # ------- DOWNLOAD -------
        log("⬇️ Preparando botão de download...")
        st.download_button(
            "⬇️ Baixar contrato completo",
            data=passo_final.read_bytes(),
            file_name="contrato_preenchido.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        log("🏁 Pipeline concluído com sucesso.")
