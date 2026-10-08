            # CORREÇÃO DEFINITIVA SEM ORDENAÇÃO (Evita qualquer travamento por tipo de dado)
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
