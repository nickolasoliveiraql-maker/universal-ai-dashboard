import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuração da Página e Estilo Dark Mode Executivo
st.set_page_config(layout="wide", page_title="Dashboard de Custos")
st.markdown(
    """
    <style>
    .stApp { background-color: #1E1F22; color: white; }
    div[data-testid="stMetricValue"] { color: #4CAF50; font-weight: bold; }
    </style>
    """, 
    unsafe_allow_html=True
)

st.title("📊 Dashboard Executivo — Custos da não Qualidade Cliente")
st.markdown("Arraste e solte o arquivo original da semana para atualizar os indicadores automaticamente.")

# 2. Upload de Arquivos
uploaded_file = st.file_uploader("Arraste o seu arquivo Excel aqui (.xlsx)", type=["xlsx"])

def processar_planilha_real_custos(file):
    # Encontrar a linha exata que contém o cabeçalho financeiro
    df_raw = pd.read_excel(file, header=None)
    linha_cabecalho = None
    for idx, row in df_raw.head(15).iterrows():
        row_str = [str(x).upper().strip() for x in row.values]
        if "VALOR" in row_str or "EMPRESA" in row_str:
            linha_cabecalho = idx
            break
            
    if linha_cabecalho is not None:
        df = pd.read_excel(file, skiprows=linha_cabecalho)
    else:
        df = pd.read_excel(file)
        
    df.columns = [str(c).strip() for c in df.columns]
    
    # Mapeamento dinâmico para tolerar acentos ou letras maiúsculas/minúsculas diferentes
    col_valor = [c for c in df.columns if 'VALOR' in c.upper()][0] if [c for c in df.columns if 'VALOR' in c.upper()] else None
    col_periodo = [c for c in df.columns if 'PERÍODO' in c.upper() or 'PERIODO' in c.upper()][0] if [c for c in df.columns if 'PERÍODO' in c.upper() or 'PERIODO' in c.upper()] else None
    col_empresa = [c for c in df.columns if 'EMPRESA' in c.upper()][0] if [c for c in df.columns if 'EMPRESA' in c.upper()] else None
    col_custo = [c for c in df.columns if 'CUSTO' in c.upper()][0] if [c for c in df.columns if 'CUSTO' in c.upper()] else None
    col_projeto = [c for c in df.columns if 'PROJETO' in c.upper()][0] if [c for c in df.columns if 'PROJETO' in c.upper()] else None

    if not col_valor:
        return pd.DataFrame(), None, None, None, None

    # Limpeza e conversão matemática blindada da moeda (preservando o sinal de menos -)
    df[col_valor] = df[col_valor].astype(str).str.replace('R$', '', regex=False).str.replace(' ', '', regex=False)
    df[col_valor] = df[col_valor].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    df[col_valor] = pd.to_numeric(df[col_valor].str.strip(), errors='coerce').fillna(0)
    
    # Remover linhas de totais ou vazias
    if col_periodo:
        df = df[df[col_periodo].notna()]
        df = df[~df[col_periodo].astype(str).str.upper().str.contains('TOTAL', na=False)]
        
    return df, col_valor, col_periodo, col_empresa, col_custo, col_projeto

# 3. Execução da Página Visual
if uploaded_file is not None:
    try:
        df, c_val, c_per, c_emp, c_cst, c_prj = processar_planilha_real_custos(uploaded_file)
        
        if not df.empty:
            st.markdown("### 🎛️ Segmentação de Dados (Filtros por Cliques)")
            col_f1, col_f2, col_f3 = st.columns(3)
            
            with col_f1:
                # Ordenação cronológica correta dos meses para o filtro suspenso
                meses_ordem = ['JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO', 'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO']
                meses_na_tabela = [m for m in meses_ordem if m in df[c_per].astype(str).str.upper().str.strip().unique()]
                opts_per = ["Todos"] + meses_na_tabela if c_per else ["Todos"]
                f_per = st.selectbox("Selecione o Mês (Período)", opts_per)
                
            with col_f2:
                opts_emp = ["Todos"] + sorted(list(df[c_emp].astype(str).str.upper().str.strip().unique())) if c_emp else ["Todos"]
                f_emp = st.selectbox("Selecione a Empresa", opts_emp)
                
            with col_f3:
                opts_cst = ["Todos"] + sorted(list(df[c_cst].astype(str).str.upper().str.strip().unique())) if c_cst else ["Todos"]
                f_cst = st.selectbox("Selecione o Tipo de Custo", opts_cst)

            # Aplicar filtros múltiplos e cruzados
            if f_per != "Todos" and c_per:
                df = df[df[c_per].astype(str).str.upper().str.strip() == f_per]
            if f_emp != "Todos" and c_emp:
                df = df[df[c_emp].astype(str).str.upper().str.strip() == f_emp]
            if f_cst != "Todos" and c_cst:
                df = df[df[c_cst].astype(str).str.upper().str.strip() == f_cst]

            # 4. Cartões de Indicadores Financeiros
            total_sum = df[c_val].sum()
            quantidade_registros = len(df)
            maior_despesa = df[c_val].max() if quantidade_registros > 0 else 0.0
            
            c_card1, c_card2, c_card3 = st.columns(3)
            c_card1.metric(label="Custo Total Acumulado", value=f"R$ {total_sum:,.2f}")
            c_card2.metric(label="Lançamentos Filtrados", value=f"{quantidade_registros} Registros")
            c_card3.metric(label="Maior Valor no Escopo", value=f"R$ {maior_despesa:,.2f}")

            # 5. Gráfico Dinâmico por Projeto (VW vs GM) ou por Empresa
            st.markdown("---")
            eixo_grafico = c_prj if c_prj else c_emp
            df_grp = df.groupby(eixo_grafico)[c_val].sum().reset_index().sort_values(by=c_val, ascending=True)
            
            fig = go.Figure(go.Bar(
                y=df_grp[eixo_grafico].astype(str), x=df_grp[c_val], orientation='h', marker_color='#2563EB',
                text=[f"R$ {x:,.2f}" for x in df_grp[c_val]], textposition='inside',
                textfont=dict(color='white', size=11, weight='bold')
            ))
            
            fig.update_layout(
                paper_bgcolor='#1E1F22', plot_bgcolor='#1E1F22', font=dict(color='white'), height=320,
                xaxis=dict(title="Custo Acumulado (R$)", gridcolor='#2F3136', zerolinecolor='#2F3136'),
                yaxis=dict(gridcolor='rgba(0,0,0,0)'),
                margin=dict(l=120, r=20, t=10, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"⚠️ Conflito de Estrutura: Certifique-se de que o arquivo carregado é o correto de Custos. Log: {e}")

