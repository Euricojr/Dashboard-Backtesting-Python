# Guia de Inicialização do Projeto - Dashboard de Investimentos

Como seu Engenheiro de Software Sênior, preparei este guia prático para configurar seu ambiente de desenvolvimento.

## 1. Ambiente Virtual (.venv)

O ambiente virtual isola as bibliotecas do projeto, evitando conflitos com outras instalações de Python no seu sistema.

### Windows (PowerShell/CMD)

```powershell
# Criar o ambiente
python -m venv .venv

# Ativar o ambiente
.\.venv\Scripts\activate
```

### Linux / macOS

```bash
# Criar o ambiente
python3 -m venv .venv

# Ativar o ambiente
source .venv/bin/activate
```

---

## 2. Instalação de Dependências

Com o ambiente **ativado**, instale as bibliotecas necessárias:

```bash
pip install -r requirements.txt
```

---

## 3. Git e GitHub

### Status Atual

Eu já inicializei o repositório local e fiz o primeiro commit com os arquivos `requirements.txt` e `.gitignore`.

### Conectando ao Repositório Remoto (GitHub)

Para conectar este projeto a um repositório vazio no seu GitHub, siga estes passos:

1.  Crie um novo repositório **vazio** no GitHub (não adicione README, License ou .gitignore lá).
2.  Copie a URL do repositório (ex: `https://github.com/seu-usuario/nome-do-projeto.git`).
3.  No seu terminal, execute:

```bash
# Adicionar o endereço do repositório remoto
git remote add origin https://github.com/seu-usuario/nome-do-projeto.git

# Renomear a branch principal para 'main' (padrão atual)
git branch -M main

# Enviar os arquivos para o GitHub
git push -u origin main
```

---

## 4. Estrutura de Arquivos Criada

- `requirements.txt`: Lista de bibliotecas (pandas, streamlit, etc).
- `.gitignore`: Configurado para ignorar a pasta `.venv` e outros arquivos temporários.

---

**Dica de Sênior:** Sempre verifique se o nome `(.venv)` aparece no início da sua linha de comando antes de rodar comandos `pip` ou `python`. Isso garante que você está no ambiente correto!
