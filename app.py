import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuração da Página e Estilo Dark Mode
st.set_page_config(layout="wide", page_title="AI Analytics Engine")
st.markdown(
    """
    <style>
    .stApp { background-color: #1E1F22; color: white; }
    div[data-testid="stMetricValue"] { color: #4CAF50; font-weight: bold; }
    </style>
    """, 
    unsafe_allow_html=True
)

st.title("🤖 Universal AI Analytics Engine")
st.markdown("Upload any structured corporate Excel sheet to dynamically generate a dashboard.")

# 2. Upload de Arquivos
uploaded_file = st.file_uploader("Drag and drop your Excel file here (.xlsx)", type=["xlsx"])

def find_and_clean_table(file):
    df_raw = pd.read_excel(file, header=None)
    
    # Localizar a linha do cabeçalho de forma estatística
    best_row = 0
    max_filled = 0
    for idx, row in df_raw.head(15).iterrows():
        filled = row.notna().sum()
        if filled > max_filled:
            max_filled = filled
            best_row = idx
            
    df = pd.read_excel(file, skiprows=best_row)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(how='all')
    
    for col in df.columns:
        df = df[~df[col].astype(str).str.upper().str.contains('TOTAL', na=False)]
    return df

def auto_map_columns(df):
    col_val, col_text, col_period = None, [], None
    time_keywords = ['MÊS', 'MES', 'PERÍODO', 'PERIODO', 'DATA', 'WEEK', 'SEMANA', 'DIA', 'SERVIÇO', 'SERVICO']
    val_keywords = ['VALOR', 'PREÇO', 'PRECO', 'CUSTO', 'TOTAL', 'HORAS', 'REAIS']

    for col in df.columns:
        col_upper = col.upper()
        if any(pt in col_upper for pt in time_keywords):
            col_period = col
            continue
        if any(pv in col_upper for pv in val_keywords) or pd.api.types.is_numeric_dtype(df[col]):
            col_val = col
            continue
        if df[col].dtype == 'object' and df[col].nunique() < 25:
            col_text.append(col)
            
    if not col_val:
        cols_num = df.select_dtypes(include=['number']).columns
        if len(cols_num) > 0: col_val = cols_num
    if not col_text:
        cols_obj = df.select_dtypes(include=['object']).columns
        col_text = list(cols_obj[:2])
        
    return col_val, col_text, col_period

# 3. Processamento dos Dados
if uploaded_file is not None:
    try:
        df = find_and_clean_table(uploaded_file)
        c_val, c_txt, c_per = auto_map_columns(df)
        
        if c_val:
            # Limpar e converter valores financeiros/horas de forma segura
            df[c_val] = df[c_val].astype(str).str.replace('R$', '', regex=False).str.replace(' ', '', regex=False)
            df[c_val] = df[c_val].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df[c_val] = pd.to_numeric(df[c_val].str.strip(), errors='coerce').fillna(0)

            st.markdown("### 🎛️ Data Slicers")
            col_f1, col_f2 = st.columns(2)
            
            # Alinhamento calibrado para as caixas de Dropdown dos filtros
            with col_f1:
                lbl_f1 = c_txt if len(c_txt) > 0 else "Dimension 1"
                opts_f1 = ["Todos"] + list(df[lbl_f1].astype(str).unique()) if len(c_txt) > 0 else ["Todos"]
                f1_select = st.selectbox(f"Filter by {lbl_f1}", opts_f1)
                
            with col_f2:
                if len(c_txt) > 1:
                    lbl_f2 = c_txt
                    opts_f2 = ["Todos"] + list(df[lbl_f2].astype(str).unique())
                elif c_per:
                    lbl_f2 = c_per
                    opts_f2 = ["Todos"] + list(df[lbl_f2].astype(str).unique())
                else:
                    lbl_f2, opts_f2 = "Dimension 2", ["Todos"]
                f2_select = st.selectbox(f"Filter by {lbl_f2}", opts_f2)

            # Aplicar filtros na base de dados com as margens corretas
            if len(c_txt) > 0 and f1_select != "Todos":
                df = df[df[lbl_f1].astype(str) == f1_select]
            if f2_select != "Todos":
                df = df[df[lbl_f2].astype(str) == f2_select]

            # 4. Cartões de Indicadores de Desempenho
            total_sum = df[c_val].sum()
            is_finance = any(x in c_val.upper() for x in ['VALOR', 'PREÇO', 'PRECO', 'CUSTO', 'REAIS'])
            formatted_sum = f"R$ {total_sum:,.2f}" if is_finance else f"{total_sum:.1f}"
            
            c_card1, c_card2 = st.columns(2)
            c_card1.metric(label=f"Accumulated Metrics ({c_val})", value=formatted_sum)
            c_card2.metric(label="Total Volumetric Rows", value=len(df))

            # 5. Gráfico de Barras Horizontal Dinâmico
            grp_col = c_per if c_per else (c_txt if c_txt else df.columns)
            df_grp = df.groupby(grp_col)[c_val].sum().reset_index()
            
            # Forçar os eixos do gráfico a exibirem as categorias de texto limpas
            df_grp[grp_col] = df_grp[grp_col].astype(str)
            
            fig = go.Figure(go.Bar(
                y=df_grp[grp_col], x=df_grp[c_val], orientation='h', marker_color='#2563EB',
                text=[f"R$ {x:,.2f}" if is_finance else f"{x:.1f}" for x in df_grp[c_val]], textposition='inside',
                textfont=dict(color='white', weight='bold')
            ))
            fig.update_layout(
                paper_bgcolor='#1E1F22', plot_bgcolor='#1E1F22', font=dict(color='white'), height=350,
                xaxis=dict(title=f"Total Dynamic {c_val}", gridcolor='#2F3136'), yaxis=dict(gridcolor='rgba(0,0,0,0)'),
                margin=dict(l=120, r=20, t=10, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Structure Conflict: Ensure columns are unmerged and clean. Error log: {e}")
