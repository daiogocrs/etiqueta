import sys
import os
import re
import tempfile
import threading
import time
import tkinter as tk
from tkinter import messagebox

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfbase.pdfmetrics import stringWidth
except ImportError:
    print("Atenção: A biblioteca 'reportlab' não está instalada.")
    print("Rode: pip install reportlab")
    sys.exit(1)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

fila_pacientes = []

def formatar_cpf(event=None):
    texto = entry_cpf.get()
    numeros = re.sub(r'\D', '', texto)
    if len(numeros) > 9:
        formatado = f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:11]}"
    elif len(numeros) > 6:
        formatado = f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:]}"
    elif len(numeros) > 3:
        formatado = f"{numeros[:3]}.{numeros[3:]}"
    else:
        formatado = numeros
    entry_cpf.delete(0, tk.END)
    entry_cpf.insert(0, formatado)

def formatar_data(event=None):
    texto = entry_nasc.get()
    numeros = re.sub(r'\D', '', texto)
    if len(numeros) > 4:
        formatado = f"{numeros[:2]}/{numeros[2:4]}/{numeros[4:8]}"
    elif len(numeros) > 2:
        formatado = f"{numeros[:2]}/{numeros[2:]}"
    else:
        formatado = numeros
    entry_nasc.delete(0, tk.END)
    entry_nasc.insert(0, formatado)

def restaurar_padroes():
    entry_margem_esq.delete(0, tk.END)
    entry_margem_esq.insert(0, "10.0")
    entry_margem_sup.delete(0, tk.END)
    entry_margem_sup.insert(0, "12.70")
    entry_larg_etiqueta.delete(0, tk.END)
    entry_larg_etiqueta.insert(0, "70")
    entry_alt_etiqueta.delete(0, tk.END)
    entry_alt_etiqueta.insert(0, "25.4")
    entry_gap_horiz.delete(0, tk.END)
    entry_gap_horiz.insert(0, "1.0")
    entry_gap_vert.delete(0, tk.END)
    entry_gap_vert.insert(0, "1.0")
    messagebox.showinfo("Sucesso", "Medidas restauradas para o padrão de fábrica.")

def adicionar_paciente():
    formatar_cpf()
    formatar_data()
    
    nome = entry_nome.get().strip()
    cpf = entry_cpf.get().strip()
    nasc = entry_nasc.get().strip()
    
    try:
        reps = int(entry_repeticoes.get())
    except ValueError:
        messagebox.showerror("Erro", "O número de repetições deve ser um número inteiro.")
        return

    if not nome:
        messagebox.showerror("Erro", "O campo Nome é obrigatório.")
        return
    if reps < 1:
        messagebox.showerror("Erro", "O número de repetições deve ser pelo menos 1.")
        return

    fila_pacientes.append({"nome": nome, "cpf": cpf, "nasc": nasc, "reps": reps})
    lista_box.insert(tk.END, f"{nome} | {reps}x | {cpf} | {nasc}")
    
    entry_nome.delete(0, tk.END)
    entry_cpf.delete(0, tk.END)
    entry_nasc.delete(0, tk.END)
    entry_repeticoes.delete(0, tk.END)
    entry_repeticoes.insert(0, "1")
    entry_nome.focus()

def remover_selecionado():
    selecionados = lista_box.curselection()
    if not selecionados:
        messagebox.showwarning("Aviso", "Selecione um paciente na lista para remover.")
        return
    index = selecionados[0]
    lista_box.delete(index)
    del fila_pacientes[index]

def limpar_fila():
    if messagebox.askyesno("Confirmar", "Tem certeza que deseja apagar toda a fila?"):
        fila_pacientes.clear()
        lista_box.delete(0, tk.END)

def apagar_arquivo_temp(caminho):
    for _ in range(120): 
        time.sleep(5)
        try:
            if os.path.exists(caminho):
                os.remove(caminho)
            break 
        except Exception:
            pass

def gerar_pdf():
    if not fila_pacientes:
        messagebox.showwarning("Aviso", "Adicione pelo menos um paciente na fila.")
        return

    try:
        inicio = int(entry_inicio.get())
        margem_esq_val = float(entry_margem_esq.get()) * mm
        margem_sup_val = float(entry_margem_sup.get()) * mm
        larg_etiqueta_val = float(entry_larg_etiqueta.get()) * mm
        alt_etiqueta_val = float(entry_alt_etiqueta.get()) * mm
        gap_horiz_val = float(entry_gap_horiz.get()) * mm
        gap_vert_val = float(entry_gap_vert.get()) * mm
    except ValueError:
        messagebox.showerror("Erro", "Verifique se as medidas e posições contêm apenas números válidos.")
        return

    if inicio < 1 or inicio > 30:
        messagebox.showerror("Erro", "A posição inicial deve ser entre 1 e 30.")
        return

    fd, nome_arquivo = tempfile.mkstemp(suffix=".pdf", prefix="etiquetas_hsr_")
    os.close(fd) 
    
    c = canvas.Canvas(nome_arquivo, pagesize=letter)
    c.setTitle("Etiquetas")
    
    posicao_atual = inicio - 1 
    usar_logo = var_logo.get()
    
    caminho_logo = resource_path("logo.png")
    if not os.path.exists(caminho_logo):
        caminho_logo = resource_path("logo.jpeg")
    if not os.path.exists(caminho_logo):
        caminho_logo = resource_path("logo.jpg")
        
    for paciente in fila_pacientes:
        for _ in range(paciente["reps"]):
            if posicao_atual >= 30:
                c.showPage() 
                posicao_atual = 0
                
            linha = posicao_atual // 3
            coluna = posicao_atual % 3
            
            x = margem_esq_val + (coluna * (larg_etiqueta_val + gap_horiz_val))
            y_base_etiqueta = letter[1] - margem_sup_val - (linha * (alt_etiqueta_val + gap_vert_val))
            
            # --- AJUSTE INTELIGENTE DE TAMANHO DE FONTE ---
            fonte_nome = "Helvetica-Bold"
            tamanho_nome = 10
            
            # Define o espaço limite (44mm com logo, 66mm sem logo)
            espaco_maximo = 44 * mm if usar_logo != 0 else 66 * mm
            texto_formatado = f"Nome: {paciente['nome']}"
            
            # Mede a largura exata que o texto ocupa em milímetros
            largura_texto = stringWidth(texto_formatado, fonte_nome, tamanho_nome)
            
            # Se for maior que o espaço permitido, reduzimos a fonte proporcionalmente
            if largura_texto > espaco_maximo:
                fator_reducao = espaco_maximo / largura_texto
                tamanho_nome = tamanho_nome * fator_reducao
                
                # Definimos um limite mínimo para não ficar invisível
                if tamanho_nome < 5.5:
                    tamanho_nome = 5.5
                    
            c.setFont(fonte_nome, tamanho_nome)
            c.drawString(x + 2*mm, y_base_etiqueta - 6*mm, texto_formatado)
            
            c.setFont("Helvetica", 9)
            c.drawString(x + 2*mm, y_base_etiqueta - 12*mm, f"CPF: {paciente['cpf']}")
            c.drawString(x + 2*mm, y_base_etiqueta - 18*mm, f"Nasc: {paciente['nasc']}")
            
            if usar_logo == 1:
                if os.path.exists(caminho_logo):
                    c.drawImage(caminho_logo, x + 48*mm, y_base_etiqueta - 18*mm, width=16*mm, height=16*mm, preserveAspectRatio=True, mask='auto')
            elif usar_logo == 2:
                if os.path.exists(caminho_logo):
                    c.drawImage(caminho_logo, x + 50.5*mm, y_base_etiqueta - 13*mm, width=11*mm, height=11*mm, preserveAspectRatio=True, mask='auto')
                c.setFont("Helvetica-Bold", 7)
                c.drawCentredString(x + 56*mm, y_base_etiqueta - 17*mm, "HOSPITAL")
                c.drawCentredString(x + 56*mm, y_base_etiqueta - 20*mm, "SÃO ROQUE")
            elif usar_logo == 3:
                c.setFont("Helvetica-Bold", 8)
                c.drawCentredString(x + 56*mm, y_base_etiqueta - 11*mm, "HOSPITAL")
                c.drawCentredString(x + 56*mm, y_base_etiqueta - 15*mm, "SÃO ROQUE")
                
            c.setFont("Helvetica", 9)
            posicao_atual += 1
            
    c.save()
    
    try:
        if os.name == 'nt': 
            os.startfile(nome_arquivo)
        else: 
            import subprocess
            subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', nome_arquivo])
        
        threading.Thread(target=apagar_arquivo_temp, args=(nome_arquivo,), daemon=True).start()
        
    except Exception as e:
        messagebox.showwarning("Aviso", f"O PDF foi gerado na pasta temporária, mas não consegui abri-lo.\nErro: {e}")

root = tk.Tk()
root.title("Gerador de Etiquetas - HSR")
root.geometry("530x760") 
root.configure(padx=15, pady=10)

try:
    caminho_icone = resource_path("hospital.ico")
    root.iconbitmap(caminho_icone)
except Exception:
    pass

frame_config = tk.LabelFrame(root, text="Ajustes (em milímetros)", font=("Arial", 9, "bold"), padx=10, pady=5)
frame_config.pack(fill="x", pady=5)

def criar_campo_medida(parent, texto, default, row, col):
    tk.Label(parent, text=texto, font=("Arial", 8)).grid(row=row, column=col, sticky="w", pady=2)
    entry = tk.Entry(parent, width=8)
    entry.insert(0, default)
    entry.grid(row=row, column=col+1, padx=5, pady=2)
    return entry

entry_margem_esq = criar_campo_medida(frame_config, "Margem Esq:", "10.0", 0, 0)
entry_margem_sup = criar_campo_medida(frame_config, "Margem Topo:", "12.70", 0, 2)
entry_larg_etiqueta = criar_campo_medida(frame_config, "Largura Etiq:", "70", 1, 0)
entry_alt_etiqueta = criar_campo_medida(frame_config, "Altura Etiq:", "25.4", 1, 2)
entry_gap_horiz = criar_campo_medida(frame_config, "Gap Horiz:", "1.0", 2, 0)
entry_gap_vert = criar_campo_medida(frame_config, "Gap Vert:", "1.0", 2, 2)

btn_padrao = tk.Button(frame_config, text="Voltar ao Padrão", command=restaurar_padroes, font=("Arial", 8))
btn_padrao.grid(row=0, column=4, rowspan=3, padx=10)

frame_inputs = tk.Frame(root)
frame_inputs.pack(fill="x", pady=5)

tk.Label(frame_inputs, text="Nome do Paciente:", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
entry_nome = tk.Entry(frame_inputs, width=70) 
entry_nome.grid(row=1, column=0, columnspan=2, pady=2, sticky="w")

tk.Label(frame_inputs, text="CPF:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=(5,0))
entry_cpf = tk.Entry(frame_inputs, width=32)
entry_cpf.grid(row=3, column=0, pady=2, sticky="w", padx=(0, 10))
entry_cpf.bind('<KeyRelease>', formatar_cpf)

tk.Label(frame_inputs, text="Data de Nasc.:", font=("Arial", 10, "bold")).grid(row=2, column=1, sticky="w", pady=(5,0))
entry_nasc = tk.Entry(frame_inputs, width=32)
entry_nasc.grid(row=3, column=1, pady=2, sticky="w")
entry_nasc.bind('<KeyRelease>', formatar_data)

frame_add = tk.Frame(root)
frame_add.pack(fill="x", pady=10)

tk.Label(frame_add, text="Qtd. p/ este paciente:", font=("Arial", 10)).pack(side="left")
entry_repeticoes = tk.Entry(frame_add, width=5)
entry_repeticoes.insert(0, "1")
entry_repeticoes.pack(side="left", padx=5)

btn_adicionar = tk.Button(frame_add, text="Adicionar à Fila", command=adicionar_paciente, bg="#27AE60", fg="white", font=("Arial", 9, "bold"))
btn_adicionar.pack(side="right")

frame_visual = tk.LabelFrame(root, text="Identificação na Etiqueta", font=("Arial", 9, "bold"), padx=10, pady=5)
frame_visual.pack(fill="x", pady=5)

var_logo = tk.IntVar(value=1)
tk.Radiobutton(frame_visual, text="Nenhum (Padrão)", variable=var_logo, value=0).grid(row=0, column=0, sticky="w")
tk.Radiobutton(frame_visual, text="1 Logo (logo.png/jpg)", variable=var_logo, value=1).grid(row=0, column=1, sticky="w")
tk.Radiobutton(frame_visual, text="Logo + Nome Hosp.", variable=var_logo, value=2).grid(row=0, column=2, sticky="w")
tk.Radiobutton(frame_visual, text="Apenas Nome Hosp.", variable=var_logo, value=3).grid(row=0, column=3, sticky="w")

frame_lista = tk.Frame(root)
frame_lista.pack(fill="both", expand=True, pady=5)

tk.Label(frame_lista, text="Fila de Impressão:", font=("Arial", 10, "bold")).pack(anchor="w")

scrollbar = tk.Scrollbar(frame_lista)
scrollbar.pack(side="right", fill="y")
lista_box = tk.Listbox(frame_lista, yscrollcommand=scrollbar.set, height=6)
lista_box.pack(side="left", fill="both", expand=True)
scrollbar.config(command=lista_box.yview)

frame_botoes_lista = tk.Frame(root)
frame_botoes_lista.pack(fill="x", pady=2)

btn_remover = tk.Button(frame_botoes_lista, text="Remover Selecionado", command=remover_selecionado, font=("Arial", 8))
btn_remover.pack(side="left")

btn_limpar = tk.Button(frame_botoes_lista, text="Limpar Fila Completa", command=limpar_fila, fg="red", font=("Arial", 8))
btn_limpar.pack(side="right")

frame_gerar = tk.Frame(root)
frame_gerar.pack(fill="x", pady=5)

tk.Label(frame_gerar, text="Começar na etiqueta nº da folha (1 a 30):", font=("Arial", 10)).pack(anchor="w")
entry_inicio = tk.Entry(frame_gerar, width=10)
entry_inicio.insert(0, "1")
entry_inicio.pack(anchor="w", pady=2)

tk.Button(root, text="Gerar PDF", command=gerar_pdf, bg="#2E86C1", fg="white", font=("Arial", 11, "bold")).pack(pady=10)

tk.Label(root, text="by Diogo Borges Corso", font=("Arial", 8, "italic"), fg="gray").pack(side="bottom", pady=5)

root.bind('<Return>', lambda event: adicionar_paciente())
root.mainloop()