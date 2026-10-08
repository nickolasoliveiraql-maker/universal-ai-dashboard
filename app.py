import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuração de Estilo do Dashboard (Dark Mode)
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

st.title("📊 Dashboard Executivo — Custos da não Qualidade")
st.markdown("Arraste e solte o arquivo original (.xlsx ou .xlsb) para atualizar os indicadores em tempo real.")

# 2. Componente de Upload do Arquivo
uploaded_file = st.file_uploader("Arraste o seu arquivo Excel aqui (.xlsx / .xlsb)", type=["xlsx", "xlsb"])

def processar_planilha_custos(file):
    extensao = file.name.split('.')[-1].lower()
    motor = 'pyxlsb' if extensao == 'xlsb' else 'openpyxl'
    
    # Varredura inteligente para achar a linha do cabeçalho real
    df_raw = pd.read_excel(file, header=None, engine=motor)
    
    linha_cabecalho = 0
    for idx, row in df_raw.head(20).iterrows():
        row_str = [str(x).upper().strip() for x in row.values]
        if "VALOR" in row_str or "EMPRESA" in row_str or "CUSTO COM" in row_str:
            linha_cabecalho = idx
            break
            
    df = pd.read_excel(file, skiprows=linha_cabecalho, engine=motor)
    df.columns = [str(c).strip() for c in df.columns]
    
    # Extrair os nomes exatos mapeados por palavra-chave
    c_prj = [c for c in df.columns if 'PROJETO' in c.upper()][0] if [c for c in df.columns if 'PROJETO' in c.upper()] else None
    c_val = [c for c in df.columns if 'VALOR' in c.upper()][0] if [c for c in df.columns if 'VALOR' in c.upper()] else None
    c_per = [c for c in df.columns if 'PERÍODO' in c.upper() or 'PERIODO' in c.upper()][0] if [c for c in df.columns if 'PERÍODO' in c.upper() or 'PERIODO' in c.upper()] else None
    c_emp = [c for c in df.columns if 'EMPRESA' in c.upper()][0] if [c for c in df.columns if 'EMPRESA' in c.upper()] else None
    c_cst = [c for c in df.columns if 'CUSTO' in c.upper()][0] if [c for c in df.columns if 'CUSTO' in c.upper()] else None
    
    if not c_val or not c_per:
        return pd.DataFrame(), None, None, None, None, None

    # Limpeza e conversão matemática blindada da moeda
    df[c_val] = df[c_val].astype(str).str.replace('R$', '', regex=False).str.replace(' ', '', regex=False)
    df[c_val] = df[c_val].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    df[c_val] = pd.to_numeric(df[c_val].str.strip(), errors='coerce').fillna(0)
    
    # Remover nulos e totalizadores
    df = df[df[c_per].notna()]
    df = df[~df[c_per].astype(str).str.upper().str.contains('TOTAL', na=False)]
    df = df[~df[c_val].astype(str).str.upper().str.contains('TOTAL', na=False)]
    
    return df, c_val, c_per, c_emp, c_cst, c_prj

# 3. Renderização da Interface e Filtros Cruzados
if uploaded_file is not None:
    try:
        df, c_val, c_per, c_emp, c_cst, c_prj = processar_planilha_custos(uploaded_file)
        
        if not df.empty:
            st.markdown("### 🎛️ Segmentação de Dados (Filtros Avançados)")
            col_f1, col_f2, col_f3 = st.columns(3)
            
            with col_f1:
                ordem_meses = ['JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO', 'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO']
                # Tratamento: Força todo elemento a virar string para não quebrar a comparação do Python
                meses_ativos = [m for m in ordem_meses if m in df[c_per].astype(str).str.upper().str.strip().unique()]
                opts_per = ["Todos"] + meses_ativos
                f_per = st.selectbox("Filtrar por Mês (Período)", opts_per)
                
            with col_f2:
                # CORREÇÃO: Forçado .astype(str) e removida a função sorted() perigosa
                opts_emp = ["Todos"] + list(df[c_emp].astype(str).str.upper().str.strip().unique())
                f_emp = st.selectbox("Filtrar por Empresa", opts_emp)
                
            with col_f3:
                # CORREÇÃO: Forçado .astype(str) e removida a função sorted() perigosa
                opts_cst = ["Todos"] + list(df[c_cst].astype(str).str.upper().str.strip().unique())
                f_cst = st.selectbox("Filtrar por Tipo de Custo", opts_cst)

            # Aplicação dinâmica das regras de filtros
            if f_per != "Todos":
                df = df[df[c_per].astype(str).str.upper().str.strip() == f_per]
            if f_emp != "Todos" and c_emp:
                df = df[df[c_emp].astype(str).str.upper().str.strip() == f_emp]
            if f_cst != "Todos" and c_cst:
                df = df[df[c_cst].astype(str).str.upper().str.strip() == f_cst]

            # 4. Cartões de Indicadores de KPI Financeiro
            total_financeiro = df[c_val].sum()
            total_linhas = len(df)
            maior_lancamento = df[c_val].max() if total_linhas > 0 else 0.0
            
            c_card1, c_card2, c_card3 = st.columns(3)
            st.metric(label="Custo Total Acumulado", value=f"R$ {total_financeiro:,.2f}")
            st.metric(label="Lançamentos Filtrados", value=f"{total_linhas} Registros")
            st.metric(label="Maior Valor no Escopo", value=f"R$ {maior_lancamento:,.2f}")

            # 5. Gráficos Executivos Lado a Lado (Barras por Marca + Pizza por Tipo de Custo)
            st.markdown("---")
            graph_col1, graph_col2 = st.columns(2)
            
            with graph_col1:
                st.markdown("#### Distribuição Financeira por Projeto")
                if c_prj and c_prj in df.columns:
                    df_grp_bar = df.groupby(c_prj)[c_val].sum().reset_index()
                    fig_bar = go.Figure(go.Bar(
                        y=df_grp_bar[c_prj].astype(str), x=df_grp_bar[c_val], orientation='h', marker_color='#2563EB',
                        text=[f"R$ {x:,.2f}" for x in df_grp_bar[c_val]], textposition='inside',
                        textfont=dict(color='white', size=11, weight='bold')
                    ))
                    fig_bar.update_layout(
                        paper_bgcolor='#1E1F22', plot_bgcolor='#1E1F22', font=dict(color='white'), height=320,
                        xaxis=dict(title="Custo Acumulado (R$)", gridcolor='#2F3136', zerolinecolor='#2F3136'),
                        yaxis=dict(gridcolor='rgba(0,0,0,0)'), margin=dict(l=50, r=20, t=10, b=20)
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)

            with graph_col2:
                st.markdown("#### Divisão Percentual por Categoria de Custo")
                if c_cst and c_cst in df.columns:
                    df_grp_pie = df.groupby(c_cst)[c_val].sum().reset_index()
                    df_grp_pie = df_grp_pie[df_grp_pie[c_val] > 0]
                    
                    fig_pie = go.Figure(go.Pie(
                        labels=df_grp_pie[c_cst].astype(str), values=df_grp_pie[c_val],
                        hole=0.4, marker=dict(colors=['#2563EB', '#EAB308', '#EF4444', '#10B981'])
                    ))
                    fig_pie.update_layout(
                        paper_bgcolor='#1E1F22', plot_bgcolor='#1E1F22', font=dict(color='white'), height=320,
                        margin=dict(l=20, r=20, t=10, b=20), legend=dict(orientation="h", y=-0.1)
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
            
    except Exception as e:
        st.error(f"⚠️ Erro de Leitura: Estrutura incompatível detectada. Detalhes: {e}")
