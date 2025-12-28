
# 🚀 Como colocar o Sistema na Nuvem (Grátis)

O método mais fácil e gratuito para hospedar projetos **Streamlit** (como o seu) é usar a infraestrutura oficial da Streamlit Community Cloud, conectada ao GitHub.

## ⚠️ AVISO IMPORTANTE SOBRE BANCO DE DADOS
Como estamos usando **SQLite** (um arquivo `.db` local):
1.  **Perda de Dados**: Toda vez que o site na nuvem "dormir" (ficar inativo) ou receber uma atualização, **o arquivo do banco zera**.
2.  **Uso Recomendado**: Ótimo para demos e testes.
3.  **Solução Definitiva**: Para uso profissional contínuo, precisaríamos migrar o banco para **Supabase** ou **Google Sheets** (posso fazer isso numa próxima etapa se desejar).

---

## Passo 1: Criar Repositório no GitHub
1.  Crie uma conta no [GitHub.com](https://github.com).
2.  Crie um novo repositório (ex: `alvorada-sistema`).
3.  Neste computador, abra o terminal e rode:
    ```bash
    git remote add origin https://github.com/SEU_USUARIO/alvorada-sistema.git
    git branch -M main
    git push -u origin main
    ```

## Passo 2: Conectar na Streamlit Cloud
1.  Acesse [share.streamlit.io](https://share.streamlit.io/).
2.  Faça login com seu GitHub.
3.  Clique em **"New App"**.
4.  Selecione o repositório `alvorada-sistema`.
5.  Em "Main file path", coloque: `app.py`.
6.  Clique em **Deploy!** 🎈

## Passo 3: Atualizações Futuras
Sempre que você quiser atualizar o site:
1.  Faça as alterações no código aqui.
2.  Rode os comandos de Git (ou me peça):
    ```bash
    git add .
    git commit -m "Melhorias no sistema"
    git push
    ```
    git push
    ```
3.  A nuvem detecta a mudança e atualiza o site sozinha em minutos.

## Passo 4: Dados que NUNCA somem (Opcional - Recomendado)
Para ter um banco de dados profissional:
1.  Crie uma conta gratuita no [Supabase.com](https://supabase.com).
2.  Crie um "New Project".
3.  Vá em **SQL Editor** -> **New Query**.
4.  Copie o conteúdo do arquivo `schema_postgres.sql` (que eu gerei) e cole lá. Clique em **RUN**.
5.  Vá em **Project Settings** -> **Database** -> **Connection String**.
6.  Na Streamlit Cloud, na tela do seu App, vá em **Settings** -> **Secrets** e adicione:

```toml
[postgres]
url = "postgres://postgres.xxxx:senha@aws-0-sa-east-1.pooler.supabase.com:5432/postgres"
```

O sistema vai detectar essa configuração e usar o Supabase automaticamente! 🚀
