from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

DB_FILE = 'clientes.json'
ID_FILE = 'last_id.txt'

def carregar_clientes():
    if not os.path.exists(DB_FILE):
        return []
    
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def salvar_clientes(clientes):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(clientes, f, indent=4, ensure_ascii=False)

def gerar_id_sequencial():
    try:
        with open(ID_FILE, 'r') as f:
            last_id = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        last_id = 0
    
    new_id = last_id + 1
    
    if new_id > 999999:
        raise ValueError("Limite de IDs atingido (999999)")
    
    with open(ID_FILE, 'w') as f:
        f.write(str(new_id))
    
    return f"{new_id:06d}"

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    clientes = carregar_clientes()
    clientes_ativos = sum(1 for c in clientes if c.get('status', 'ATIVO') == 'ATIVO')
    ultimos_clientes = sorted(clientes, key=lambda x: x['data_cadastro'], reverse=True)[:5]
    
    return render_template('dashboard.html', 
                         clientes_ativos=clientes_ativos,
                         ultimos_clientes=ultimos_clientes,
                         clientes=clientes)  # Linha adicionada para o gráfico dinâmico

@app.route('/clientes')
def listar_clientes():
    clientes = carregar_clientes()
    termo_busca = request.args.get('busca', '').strip().lower()
    
    if termo_busca:
        clientes = [c for c in clientes if (
            termo_busca in c.get('nome', '').lower() or
            termo_busca in c.get('email', '').lower() or
            termo_busca in (c.get('cnpj', '') or '').lower() or
            termo_busca in c.get('agente', '').lower() or
            termo_busca in c.get('status', '').lower() or
            termo_busca in c.get('perfil', '').lower() or
            termo_busca in c.get('submercado', '').lower() or
            termo_busca in c.get('tipo_unidade', '').lower() or
            termo_busca in c.get('dhc', '').lower() or
            termo_busca in c.get('classe', '').lower() or
            termo_busca in c.get('tensao', '').lower() or
            termo_busca in c.get('cidade', '').lower() or
            termo_busca in c.get('bairro', '').lower() or
            termo_busca in (c.get('data_denuncia_contrato', '') or '').lower() or
            termo_busca in (c.get('codigo_unidade_consumidora', '') or '').lower()
        )]
    
    return render_template('listar_clientes.html', clientes=clientes)

@app.route('/cliente/novo', methods=['GET', 'POST'])
def cadastrar_cliente():
    if request.method == 'POST':
        try:
            demanda = float(request.form.get('demanda', 0))
            valor_multa = float(request.form.get('valor_multa_rescisoria', 0))
        except (ValueError, TypeError):
            demanda = 0
            valor_multa = 0
            
        cliente = {
            'id': gerar_id_sequencial(),
            'nome': request.form.get('nome'),
            'email': request.form.get('email'),
            'telefone': request.form.get('telefone'),
            'endereco': request.form.get('endereco'),
            'numero': request.form.get('numero'),
            'complemento': request.form.get('complemento'),
            'bairro': request.form.get('bairro'),
            'cidade': request.form.get('cidade'),
            'uf': request.form.get('uf'),
            'cep': request.form.get('cep'),
            'cnpj': request.form.get('cnpj'),
            'status': request.form.get('status', 'ATIVO'),
            'grupo': request.form.get('grupo'),
            'tipo_unidade': request.form.get('tipo_unidade', 'MATRIZ'),
            'dhc': request.form.get('dhc', ''),
            'classe': request.form.get('classe'),
            'tensao': request.form.get('tensao'),
            'demanda': demanda,
            'agente': request.form.get('agente'),
            'codigo_agente': request.form.get('codigo_agente'),
            'perfil': request.form.get('perfil'),
            'codigo_perfil': request.form.get('codigo_perfil'),
            'submercado': request.form.get('submercado'),
            'medidor': request.form.get('medidor'),
            'uc_instalacao': request.form.get('uc_instalacao'),
            'data_denuncia_contrato': request.form.get('data_denuncia_contrato'),
            'valor_multa_rescisoria': valor_multa,
            'observacoes': request.form.get('observacoes'),
            'data_cadastro': datetime.now().strftime("%d/%m/%Y %H:%M"),
            # Campos da API
            'codigo_unidade_consumidora': request.form.get('codigo_unidade_consumidora'),
            'codigo_agente_concessionaria': request.form.get('codigo_agente_concessionaria'),
            'tipo_documento': request.form.get('tipo_documento'),
            'numero_documento': request.form.get('numero_documento'),
            'codigo_agente_varejista': request.form.get('codigo_agente_varejista'),
            'mes_referencia': request.form.get('mes_referencia'),
            'data_denuncia': request.form.get('data_denuncia'),
            'codigo_perfil_varejista': request.form.get('codigo_perfil_varejista'),
            'email_unidade_consumidora': request.form.get('email_unidade_consumidora'),
            'comentario': request.form.get('comentario'),
            'status_migracao': request.form.get('status_migracao'),
            'data_solicitacao': request.form.get('data_solicitacao')
        }
        
        if not cliente['nome'] or not cliente['email']:
            flash('Nome e email são obrigatórios!', 'danger')
            return render_template('cadastrar_cliente.html', cliente=cliente)
        
        clientes = carregar_clientes()
        clientes.append(cliente)
        salvar_clientes(clientes)
        
        flash('Cliente cadastrado com sucesso!', 'success')
        return redirect(url_for('listar_clientes'))
    
    return render_template('cadastrar_cliente.html')

@app.route('/cliente/<id>/editar', methods=['GET', 'POST'])
def editar_cliente(id):
    clientes = carregar_clientes()
    cliente = next((c for c in clientes if c['id'] == id), None)
    
    if not cliente:
        flash('Cliente não encontrado!', 'danger')
        return redirect(url_for('listar_clientes'))
    
    if request.method == 'POST':
        try:
            demanda = float(request.form.get('demanda', 0))
            valor_multa = float(request.form.get('valor_multa_rescisoria', 0))
        except (ValueError, TypeError):
            demanda = cliente.get('demanda', 0)
            valor_multa = cliente.get('valor_multa_rescisoria', 0)
            
        cliente.update({
            'nome': request.form.get('nome', cliente['nome']),
            'email': request.form.get('email', cliente['email']),
            'telefone': request.form.get('telefone', cliente.get('telefone')),
            'endereco': request.form.get('endereco', cliente.get('endereco')),
            'numero': request.form.get('numero', cliente.get('numero')),
            'complemento': request.form.get('complemento', cliente.get('complemento')),
            'bairro': request.form.get('bairro', cliente.get('bairro')),
            'cidade': request.form.get('cidade', cliente.get('cidade')),
            'uf': request.form.get('uf', cliente.get('uf')),
            'cep': request.form.get('cep', cliente.get('cep')),
            'cnpj': request.form.get('cnpj', cliente.get('cnpj')),
            'status': request.form.get('status', cliente.get('status', 'ATIVO')),
            'grupo': request.form.get('grupo', cliente.get('grupo')),
            'tipo_unidade': request.form.get('tipo_unidade', cliente.get('tipo_unidade', 'MATRIZ')),
            'dhc': request.form.get('dhc', cliente.get('dhc', '')),
            'classe': request.form.get('classe', cliente.get('classe')),
            'tensao': request.form.get('tensao', cliente.get('tensao')),
            'demanda': demanda,
            'agente': request.form.get('agente', cliente.get('agente')),
            'codigo_agente': request.form.get('codigo_agente', cliente.get('codigo_agente')),
            'perfil': request.form.get('perfil', cliente.get('perfil')),
            'codigo_perfil': request.form.get('codigo_perfil', cliente.get('codigo_perfil')),
            'submercado': request.form.get('submercado', cliente.get('submercado')),
            'medidor': request.form.get('medidor', cliente.get('medidor')),
            'uc_instalacao': request.form.get('uc_instalacao', cliente.get('uc_instalacao')),
            'data_denuncia_contrato': request.form.get('data_denuncia_contrato', cliente.get('data_denuncia_contrato')),
            'valor_multa_rescisoria': valor_multa,
            'observacoes': request.form.get('observacoes', cliente.get('observacoes')),
            # Campos da API
            'codigo_unidade_consumidora': request.form.get('codigo_unidade_consumidora', cliente.get('codigo_unidade_consumidora')),
            'codigo_agente_concessionaria': request.form.get('codigo_agente_concessionaria', cliente.get('codigo_agente_concessionaria')),
            'tipo_documento': request.form.get('tipo_documento', cliente.get('tipo_documento')),
            'numero_documento': request.form.get('numero_documento', cliente.get('numero_documento')),
            'codigo_agente_varejista': request.form.get('codigo_agente_varejista', cliente.get('codigo_agente_varejista')),
            'mes_referencia': request.form.get('mes_referencia', cliente.get('mes_referencia')),
            'data_denuncia': request.form.get('data_denuncia', cliente.get('data_denuncia')),
            'codigo_perfil_varejista': request.form.get('codigo_perfil_varejista', cliente.get('codigo_perfil_varejista')),
            'email_unidade_consumidora': request.form.get('email_unidade_consumidora', cliente.get('email_unidade_consumidora')),
            'comentario': request.form.get('comentario', cliente.get('comentario')),
            'status_migracao': request.form.get('status_migracao', cliente.get('status_migracao')),
            'data_solicitacao': request.form.get('data_solicitacao', cliente.get('data_solicitacao'))
        })
        
        salvar_clientes(clientes)
        flash('Cliente atualizado com sucesso!', 'success')
        return redirect(url_for('listar_clientes'))
    
    return render_template('editar_cliente.html', cliente=cliente)

@app.route('/cliente/<id>/excluir', methods=['POST'])
def excluir_cliente(id):
    clientes = carregar_clientes()
    clientes = [c for c in clientes if c['id'] != id]
    salvar_clientes(clientes)
    flash('Cliente excluído com sucesso!', 'success')
    return redirect(url_for('listar_clientes'))

if __name__ == '__main__':
    app.run(debug=True)