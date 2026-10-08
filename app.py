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
st.markdown("Arraste e solte o arquivo original para atualizar os indicadores financeiros em tempo real.")

# 2. Componente de Upload do Arquivo
uploaded_file = st.file_uploader("Arraste o seu arquivo Excel aqui (.xlsx)", type=["xlsx"])

def processar_planilha_custos(file):
    # Pular as primeiras 6 linhas de metadados para focar no cabeçalho real da linha 7
    df = pd.read_excel(file, skiprows=6)
    
    # Limpar espaços em branco invisíveis no início ou fim dos títulos das colunas
    df.columns = [str(c).strip() for c in df.columns]
    
    # Criar um dicionário de mapeamento exato com base nas colunas físicas da sua imagem
    mapeamento_colunas = {
        'Projeto': [c for c in df.columns if 'PROJETO' in c.upper()][0] if [c for c in df.columns if 'PROJETO' in c.upper()] else None,
        'Valor': [c for c in df.columns if 'VALOR' in c.upper()][0] if [c for c in df.columns if 'VALOR' in c.upper()] else None,
        'Periodo': [c for c in df.columns if 'PERÍODO' in c.upper() or 'PERIODO' in c.upper()][0] if [c for c in df.columns if 'PERÍODO' in c.upper() or 'PERIODO' in c.upper()] else None,
        'Empresa': [c for c in df.columns if 'EMPRESA' in c.upper()][0] if [c for c in df.columns if 'EMPRESA' in c.upper()] else None,
        'Custo_Com': [c for c in df.columns if 'CUSTO' in c.upper()][0] if [c for c in df.columns if 'CUSTO' in c.upper()] else None
    }
    
    # Validar se as colunas essenciais foram encontradas
    if not mapeamento_colunas['Valor'] or not mapeamento_colunas['Periodo']:
        return pd.DataFrame(), None, None, None, None, None

    c_prj = mapeamento_colunas['Projeto']
    c_val = mapeamento_colunas['Valor']
    c_per = mapeamento_colunas['Periodo']
    c_emp = mapeamento_colunas['Empresa']
    c_cst = mapeamento_colunas['Custo_Com']

    # 🛠️ Limpeza profunda dos valores monetários (mantém o sinal negativo de créditos de Setembro)
    df[c_val] = df[c_val].astype(str).str.replace('R$', '', regex=False).str.replace(' ', '', regex=False)
    df[c_val] = df[c_val].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    df[c_val] = pd.to_numeric(df[c_val].str.strip(), errors='coerce').fillna(0)
    
    # Eliminar linhas de totalizadores amarelos do rodapé para evitar duplicações
    df = df[df[c_per].notna()]
    df = df[~df[c_per].astype(str).str.upper().str.contains('TOTAL', na=False)]
    df = df[~df[c_val].astype(str).str.upper().str.contains('TOTAL', na=False)]
    
    return df, c_val, c_per, c_emp, c_cst, c_prj

# 3. Renderização da Interface e Filtros
if uploaded_file is not None:
    try:
        df, c_val, c_per, c_emp, c_cst, c_prj = processar_planilha_custos(uploaded_file)
        
        if not df.empty:
            st.markdown("### 🎛️ Segmentação de Dados (Filtros Avançados)")
            col_f1, col_f2, col_f3 = st.columns(3)
            
            with col_f1:
                # Ordenação cronológica correta dos meses no filtro suspenso (Janeiro a Dezembro)
                ordem_meses = ['JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO', 'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO']
                meses_ativos = [m for m in ordem_meses if m in df[c_per].astype(str).str.upper().str.strip().unique()]
                opts_per = ["Todos"] + meses_ativos
                f_per = st.selectbox("Filtrar por Mês (Período)", opts_per)
                
            with col_f2:
                opts_emp = ["Todos"] + sorted(list(df[c_emp].astype(str).str.upper().str.strip().unique())) if c_emp else ["Todos"]
                f_emp = st.selectbox("Filtrar por Empresa", opts_emp)
                
            with col_f3:
                opts_cst = ["Todos"] + sorted(list(df[c_cst].astype(str).str.upper().str.strip().unique())) if c_cst else ["Todos"]
                f_cst = st.selectbox("Filtrar por Tipo de Custo", opts_cst)

            # Aplicação dos Filtros Cruzados Dinâmicos
            if f_per != "Todos":
                df = df[df[c_per].astype(str).str.upper().str.strip() == f_per]
            if f_emp != "Todos" and c_emp:
                df = df[df[c_emp].astype(str).str.upper().str.strip() == f_emp]
            if f_cst != "Todos" and c_cst:
                df = df[df[c_cst].astype(str).str.upper().str.strip() == f_cst]

            # 4. Cartões de Indicadores Financeiros
            total_financeiro = df[c_val].sum()
            total_linhas = len(df)
            maior_lancamento = df[c_val].max() if total_linhas > 0 else 0.0
            
            c_card1, c_card2, c_card3 = st.columns(3)
            c_card1.metric(label="Custo Total Acumulado", value=f"R$ {total_financeiro:,.2f}")
            c_card2.metric(label="Lançamentos Filtrados", value=f"{total_linhas} Registros")
            c_card3.metric(label="Maior Valor no Escopo", value=f"R$ {maior_lancamento:,.2f}")

            # 5. Gráfico Dinâmico por Projeto (VW vs GM)
            st.markdown("---")
            eixo_y = c_prj if c_prj else c_emp
            df_grp = df.groupby(eixo_y)[c_val].sum().reset_index().sort_values(by=c_val, ascending=True)
            
            fig = go.Figure(go.Bar(
                y=df_grp[eixo_y].astype(str), x=df_grp[c_val], orientation='h', marker_color='#2563EB',
                text=[f"R$ {x:,.2f}" for x in df_grp[c_val]], textposition='inside',
                textfont=dict(color='white', size=11, weight='bold')
            ))
            
            fig.update_layout(
                paper_bgcolor='#1E1F22', plot_bgcolor='#1E1F22', font=dict(color='white'), height=320,
                xaxis=dict(title="Custo Total Acumulado (R$)", gridcolor='#2F3136', zerolinecolor='#2F3136'),
                yaxis=dict(gridcolor='rgba(0,0,0,0)'),
                margin=dict(l=120, r=20, t=10, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"⚠️ Erro de Leitura: Verifique se as colunas originais da imagem foram alteradas. Log: {e}")
