import sqlite3
import datetime
import html
from urllib.parse import parse_qs, urlparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# =========================================================
# CONFIGURAÇÕES
# =========================================================

HOST = "0.0.0.0"
PORT = 5000
BANCO = "helpdesk.db"

STATUS = [
    "Aberto",
    "Em atendimento",
    "Escalonado N2",
    "Fechado"
]

PRIORIDADES = ["Baixa", "Media", "Alta", "Critica"]

CATEGORIAS = [
    "Incidente",
    "Monitoramento",
    "Hardware",
    "Software",
    "Rede",
    "Acesso",
    "Duvida",
    "Outros"
]


# =========================================================
# BANCO DE DADOS
# =========================================================

def banco():
    con = sqlite3.connect(BANCO)
    con.row_factory = sqlite3.Row

    con.execute("""
        CREATE TABLE IF NOT EXISTS chamados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            cliente TEXT,
            categoria TEXT,
            prioridade TEXT,
            status TEXT,
            descricao TEXT,
            diagnostico TEXT,
            criado_em TEXT,
            atualizado_em TEXT
        )
    """)

    # Compatibilidade com o banco da versão anterior
    colunas = [
        c["name"]
        for c in con.execute("PRAGMA table_info(chamados)").fetchall()
    ]

    if "atualizado_em" not in colunas:
        con.execute("ALTER TABLE chamados ADD COLUMN atualizado_em TEXT")

    con.commit()
    return con


def agora():
    return datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def escapar(valor):
    return html.escape(str(valor or ""))


# =========================================================
# HTML BASE
# =========================================================

def cabecalho(titulo):
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{escapar(titulo)} | HelpDesk N1</title>

        <style>

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            background: #0b1120;
            color: #e2e8f0;
            font-family: Arial, Helvetica, sans-serif;
        }}

        header {{
            background: #111827;
            border-bottom: 1px solid #263449;
            padding: 20px;
        }}

        .topo {{
            max-width: 1200px;
            margin: auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }}

        .logo {{
            font-size: 22px;
            font-weight: bold;
            color: #38bdf8;
        }}

        .logo span {{
            color: white;
        }}

        nav {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}

        nav a {{
            text-decoration: none;
            color: #cbd5e1;
            background: #1e293b;
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 14px;
        }}

        nav a:hover {{
            background: #334155;
        }}

        main {{
            max-width: 1200px;
            margin: auto;
            padding: 25px 18px;
        }}

        h1 {{
            font-size: 27px;
            margin-bottom: 8px;
        }}

        h2 {{
            margin-top: 0;
        }}

        .subtitulo {{
            color: #94a3b8;
            margin-bottom: 25px;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }}

        .card {{
            background: #151f32;
            border: 1px solid #263449;
            border-radius: 14px;
            padding: 20px;
        }}

        .card small {{
            color: #94a3b8;
        }}

        .numero {{
            font-size: 32px;
            font-weight: bold;
            margin-top: 12px;
        }}

        .azul {{
            color: #38bdf8;
        }}

        .amarelo {{
            color: #fbbf24;
        }}

        .verde {{
            color: #4ade80;
        }}

        .vermelho {{
            color: #f87171;
        }}

        .filtros {{
            background: #151f32;
            border: 1px solid #263449;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 20px;
        }}

        .filtros form {{
            display: grid;
            grid-template-columns: 2fr 1fr 1fr auto;
            gap: 10px;
        }}

        input, select, textarea {{
            width: 100%;
            background: #0f172a;
            color: white;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 12px;
            font-size: 14px;
            margin-bottom: 10px;
        }}

        textarea {{
            min-height: 130px;
            resize: vertical;
        }}

        label {{
            display: block;
            margin: 10px 0 5px;
            color: #cbd5e1;
        }}

        .btn {{
            display: inline-block;
            background: #38bdf8;
            color: #082f49;
            padding: 11px 16px;
            border: none;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            cursor: pointer;
        }}

        .btn:hover {{
            background: #7dd3fc;
        }}

        .btn-secundario {{
            background: #334155;
            color: white;
        }}

        .btn-alerta {{
            background: #7f1d1d;
            color: white;
        }}

        .btn-alerta:hover {{
            background: #991b1b;
        }}

        .chamado {{
            background: #151f32;
            border: 1px solid #263449;
            border-radius: 12px;
            padding: 17px;
            margin-bottom: 12px;
        }}

        .chamado:hover {{
            border-color: #38bdf8;
        }}

        .chamado-topo {{
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
        }}

        .chamado h3 {{
            margin: 0 0 10px;
        }}

        .chamado p {{
            color: #cbd5e1;
            margin: 7px 0;
        }}

        .badge {{
            display: inline-block;
            padding: 5px 9px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            margin: 3px;
        }}

        .status-aberto {{
            background: #1e3a8a;
            color: #bfdbfe;
        }}

        .status-atendimento {{
            background: #78350f;
            color: #fde68a;
        }}

        .status-n2 {{
            background: #581c87;
            color: #e9d5ff;
        }}

        .status-fechado {{
            background: #14532d;
            color: #bbf7d0;
        }}

        .prioridade-baixa {{
            background: #334155;
            color: #cbd5e1;
        }}

        .prioridade-media {{
            background: #854d0e;
            color: #fef3c7;
        }}

        .prioridade-alta {{
            background: #9a3412;
            color: #fed7aa;
        }}

        .prioridade-critica {{
            background: #991b1b;
            color: #fecaca;
        }}

        .detalhes {{
            background: #151f32;
            border: 1px solid #263449;
            border-radius: 14px;
            padding: 22px;
        }}

        .detalhes p {{
            line-height: 1.7;
            overflow-wrap: anywhere;
        }}

        .descricao {{
            background: #0f172a;
            padding: 15px;
            border-radius: 10px;
            white-space: pre-wrap;
        }}

        .acoes {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 20px 0;
        }}

        .vazio {{
            text-align: center;
            padding: 40px;
            color: #94a3b8;
        }}

        footer {{
            text-align: center;
            padding: 25px;
            color: #64748b;
            border-top: 1px solid #263449;
            margin-top: 30px;
        }}

        @media(max-width: 700px) {{
            .filtros form {{
                grid-template-columns: 1fr;
            }}

            .topo {{
                flex-direction: column;
                align-items: flex-start;
            }}

            h1 {{
                font-size: 23px;
            }}
        }}

        </style>
    </head>

    <body>

    <header>
        <div class="topo">
            <div class="logo">🖥️ HelpDesk <span>N1</span></div>

            <nav>
                <a href="/">Dashboard</a>
                <a href="/novo">+ Novo chamado</a>
                <a href="/alerta">⚠ Simular alerta</a>
            </nav>
        </div>
    </header>
    """


def rodape():
    return """
    <footer>
        HelpDesk N1 — Sistema demonstrativo de suporte técnico
        <br>
        Python • SQLite • HTTP Server
    </footer>
    </body>
    </html>
    """


# =========================================================
# DASHBOARD
# =========================================================

def dashboard(con, query):
    chamados = con.execute("""
        SELECT * FROM chamados
        ORDER BY
            CASE prioridade
                WHEN 'Critica' THEN 1
                WHEN 'Alta' THEN 2
                WHEN 'Media' THEN 3
                WHEN 'Baixa' THEN 4
                ELSE 5
            END,
            id DESC
    """).fetchall()

    total = len(chamados)

    abertos = sum(c["status"] == "Aberto" for c in chamados)

    atendimento = sum(
        c["status"] == "Em atendimento"
        for c in chamados
    )

    escalonados = sum(
        c["status"] == "Escalonado N2"
        for c in chamados
    )

    fechados = sum(c["status"] == "Fechado" for c in chamados)

    criticos = sum(
        c["prioridade"] == "Critica"
        and c["status"] != "Fechado"
        for c in chamados
    )

    busca = query.get("busca", [""])[0].strip()
    filtro_status = query.get("status", [""])[0]
    filtro_prioridade = query.get("prioridade", [""])[0]

    filtrados = []

    for c in chamados:

        texto = (
            str(c["titulo"] or "") +
            str(c["cliente"] or "") +
            str(c["descricao"] or "") +
            str(c["categoria"] or "")
        ).lower()

        if busca and busca.lower() not in texto:
            continue

        if filtro_status and c["status"] != filtro_status:
            continue

        if filtro_prioridade and c["prioridade"] != filtro_prioridade:
            continue

        filtrados.append(c)

    linhas = ""

    for c in filtrados:

        status_class = {
            "Aberto": "status-aberto",
            "Em atendimento": "status-atendimento",
            "Escalonado N2": "status-n2",
            "Fechado": "status-fechado"
        }.get(c["status"], "")

        prioridade_class = {
            "Baixa": "prioridade-baixa",
            "Media": "prioridade-media",
            "Alta": "prioridade-alta",
            "Critica": "prioridade-critica"
        }.get(c["prioridade"], "")

        linhas += f"""
        <div class="chamado">

            <div class="chamado-topo">

                <h3>
                    #{c['id']} — {escapar(c['titulo'])}
                </h3>

                <div>
                    <span class="badge {status_class}">
                        {escapar(c['status'])}
                    </span>

                    <span class="badge {prioridade_class}">
                        {escapar(c['prioridade'])}
                    </span>
                </div>

            </div>

            <p>
                <b>Cliente:</b> {escapar(c['cliente'])}
            </p>

            <p>
                <b>Categoria:</b> {escapar(c['categoria'])}
            </p>

            <p>
                <b>Aberto em:</b> {escapar(c['criado_em'])}
            </p>

            <a class="btn" href="/ver?id={c['id']}">
                Visualizar chamado →
            </a>

        </div>
        """

    if not linhas:
        linhas = """
        <div class="vazio">
            <h3>Nenhum chamado encontrado</h3>
            <p>Experimente alterar os filtros ou abrir um novo chamado.</p>
        </div>
        """

    return f"""
    {cabecalho("Dashboard")}

    <main>

        <h1>Central de Suporte</h1>

        <p class="subtitulo">
            Gerenciamento de incidentes, solicitações e monitoramento.
        </p>

        <div class="grid">

            <div class="card">
                <small>Total de chamados</small>
                <div class="numero azul">{total}</div>
            </div>

            <div class="card">
                <small>Chamados abertos</small>
                <div class="numero amarelo">{abertos}</div>
            </div>

            <div class="card">
                <small>Em atendimento</small>
                <div class="numero azul">{atendimento}</div>
            </div>

            <div class="card">
                <small>Escalonados N2</small>
                <div class="numero vermelho">{escalonados}</div>
            </div>

            <div class="card">
                <small>Fechados</small>
                <div class="numero verde">{fechados}</div>
            </div>

            <div class="card">
                <small>Alertas críticos ativos</small>
                <div class="numero vermelho">{criticos}</div>
            </div>

        </div>

        <div class="filtros">

            <form method="GET" action="/">

                <input
                    name="busca"
                    placeholder="Buscar chamado, cliente ou descrição..."
                    value="{escapar(busca)}"
                >

                <select name="status">
                    <option value="">Todos os status</option>
                    {''.join(
                        f"<option value='{escapar(s)}' "
                        f"{'selected' if filtro_status == s else ''}>"
                        f"{escapar(s)}</option>"
                        for s in STATUS
                    )}
                </select>

                <select name="prioridade">
                    <option value="">Todas as prioridades</option>
                    {''.join(
                        f"<option value='{escapar(p)}' "
                        f"{'selected' if filtro_prioridade == p else ''}>"
                        f"{escapar(p)}</option>"
                        for p in PRIORIDADES
                    )}
                </select>

                <button class="btn">Filtrar</button>

            </form>

        </div>

        <h2>Chamados registrados ({len(filtrados)})</h2>

        {linhas}

    </main>

    {rodape()}
    """


# =========================================================
# NOVO CHAMADO
# =========================================================

def formulario_novo():
    categorias = "".join(
        f"<option>{escapar(c)}</option>"
        for c in CATEGORIAS
    )

    prioridades = "".join(
        f"<option>{escapar(p)}</option>"
        for p in PRIORIDADES
    )

    return f"""
    {cabecalho("Novo chamado")}

    <main>

        <h1>Abrir novo chamado</h1>

        <p class="subtitulo">
            Registre o incidente ou solicitação do usuário.
        </p>

        <div class="detalhes">

            <form method="POST" action="/salvar">

                <label>Título do chamado</label>

                <input
                    name="titulo"
                    placeholder="Ex: Computador não conecta à rede"
                    required
                    maxlength="150"
                >

                <label>Cliente / Usuário</label>

                <input
                    name="cliente"
                    placeholder="Nome do cliente ou usuário"
                    required
                    maxlength="100"
                >

                <label>Categoria</label>

                <select name="categoria">
                    {categorias}
                </select>

                <label>Prioridade</label>

                <select name="prioridade">
                    {prioridades}
                </select>

                <label>Descrição do problema</label>

                <textarea
                    name="descricao"
                    placeholder="Descreva o problema relatado..."
                ></textarea>

                <button class="btn" type="submit">
                    Abrir chamado
                </button>

                <a class="btn btn-secundario" href="/">
                    Cancelar
                </a>

            </form>

        </div>

    </main>

    {rodape()}
    """


# =========================================================
# DETALHES DO CHAMADO
# =========================================================

def pagina_chamado(con, id_chamado):

    c = con.execute(
        "SELECT * FROM chamados WHERE id = ?",
        (id_chamado,)
    ).fetchone()

    if not c:
        return pagina_erro(
            "Chamado não encontrado",
            "O chamado solicitado não existe ou foi removido."
        )

    status_atual = c["status"]
    prioridade_atual = c["prioridade"]

    opcoes_status = "".join(
        f"<option value='{escapar(s)}' "
        f"{'selected' if s == status_atual else ''}>"
        f"{escapar(s)}</option>"
        for s in STATUS
    )

    opcoes_prioridade = "".join(
        f"<option value='{escapar(p)}' "
        f"{'selected' if p == prioridade_atual else ''}>"
        f"{escapar(p)}</option>"
        for p in PRIORIDADES
    )

    return f"""
    {cabecalho(f"Chamado #{id_chamado}")}

    <main>

        <h1>Chamado #{c['id']}</h1>

        <p class="subtitulo">
            Visualização e gerenciamento do incidente.
        </p>

        <div class="acoes">
            <a class="btn btn-secundario" href="/">
                ← Voltar ao dashboard
            </a>
        </div>

        <div class="detalhes">

            <h2>{escapar(c['titulo'])}</h2>

            <p>
                <b>Cliente:</b> {escapar(c['cliente'])}
            </p>

            <p>
                <b>Categoria:</b> {escapar(c['categoria'])}
            </p>

            <p>
                <b>Prioridade:</b> {escapar(c['prioridade'])}
            </p>

            <p>
                <b>Status:</b> {escapar(c['status'])}
            </p>

            <p>
                <b>Data de abertura:</b> {escapar(c['criado_em'])}
            </p>

            <p>
                <b>Última atualização:</b>
                {escapar(c['atualizado_em'] or c['criado_em'])}
            </p>

            <hr>

            <h3>Descrição do incidente</h3>

            <div class="descricao">
                {escapar(c['descricao'])}
            </div>

            <hr>

            <h3>Diagnóstico técnico</h3>

            <form method="POST" action="/atualizar">

                <input
                    type="hidden"
                    name="id"
                    value="{c['id']}"
                >

                <label>Status</label>

                <select name="status">
                    {opcoes_status}
                </select>

                <label>Prioridade</label>

                <select name="prioridade">
                    {opcoes_prioridade}
                </select>

                <label>Diagnóstico / Solução aplicada</label>

                <textarea
                    name="diagnostico"
                    placeholder="Descreva os testes realizados, diagnóstico e solução..."
                >{escapar(c['diagnostico'])}</textarea>

                <button class="btn" type="submit">
                    Salvar alterações
                </button>

            </form>

        </div>

    </main>

    {rodape()}
    """


# =========================================================
# PÁGINA DE ERRO
# =========================================================

def pagina_erro(titulo, mensagem):

    return f"""
    {cabecalho("Erro")}

    <main>

        <div class="detalhes">

            <h1>{escapar(titulo)}</h1>

            <p>{escapar(mensagem)}</p>

            <a class="btn" href="/">
                Voltar ao dashboard
            </a>

        </div>

    </main>

    {rodape()}
    """


# =========================================================
# SERVIDOR
# =========================================================

class Servidor(BaseHTTPRequestHandler):

    def responder(self, html_pagina, status=200):

        conteudo = html_pagina.encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(conteudo))
        )

        self.send_header(
            "X-Content-Type-Options",
            "nosniff"
        )

        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'unsafe-inline'; "
            "form-action 'self'; frame-ancestors 'none'"
        )

        self.end_headers()

        self.wfile.write(conteudo)


    def redirecionar(self, destino="/"):

        self.send_response(303)

        self.send_header("Location", destino)

        self.end_headers()


    # =====================================================
    # GET
    # =====================================================

    def do_GET(self):

        rota = urlparse(self.path)

        caminho = rota.path

        query = parse_qs(rota.query)

        con = banco()

        try:

            if caminho == "/":

                html_pagina = dashboard(con, query)

                self.responder(html_pagina)


            elif caminho == "/novo":

                self.responder(formulario_novo())


            elif caminho == "/ver":

                try:
                    id_chamado = int(
                        query.get("id", ["0"])[0]
                    )

                    if id_chamado <= 0:
                        raise ValueError

                except ValueError:

                    self.responder(
                        pagina_erro(
                            "ID inválido",
                            "O número do chamado informado é inválido."
                        ),
                        400
                    )

                    return

                html_pagina = pagina_chamado(
                    con,
                    id_chamado
                )

                self.responder(html_pagina)


            elif caminho == "/alerta":

                agora_texto = agora()

                con.execute("""
                    INSERT INTO chamados (
                        titulo,
                        cliente,
                        categoria,
                        prioridade,
                        status,
                        descricao,
                        diagnostico,
                        criado_em,
                        atualizado_em
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    "[ZABBIX] CPU acima de 90%",
                    "Cliente Demo",
                    "Monitoramento",
                    "Alta",
                    "Aberto",
                    "Alerta simulado de monitoramento. "
                    "Uso de CPU acima do limite de 90%.",
                    "Aguardando análise do suporte N1.",
                    agora_texto,
                    agora_texto
                ))

                con.commit()

                self.redirecionar("/")


            else:

                self.responder(
                    pagina_erro(
                        "Página não encontrada",
                        "A rota solicitada não existe."
                    ),
                    404
                )

        finally:
            con.close()


    # =====================================================
    # POST
    # =====================================================

    def do_POST(self):

        tamanho = int(
            self.headers.get("Content-Length", 0)
        )

        if tamanho > 1000000:

            self.responder(
                pagina_erro(
                    "Requisição muito grande",
                    "O formulário ultrapassou o limite permitido."
                ),
                413
            )

            return

        corpo = self.rfile.read(tamanho).decode(
            "utf-8",
            errors="replace"
        )

        dados = parse_qs(corpo)

        con = banco()

        try:

            # ---------------------------------------------
            # SALVAR NOVO CHAMADO
            # ---------------------------------------------

            if self.path == "/salvar":

                titulo = dados.get("titulo", [""])[0].strip()

                cliente = dados.get("cliente", [""])[0].strip()

                categoria = dados.get("categoria", ["Outros"])[0]

                prioridade = dados.get("prioridade", ["Media"])[0]

                descricao = dados.get("descricao", [""])[0].strip()

                if not titulo or not cliente:

                    self.responder(
                        pagina_erro(
                            "Campos obrigatórios",
                            "Título e cliente precisam ser preenchidos."
                        ),
                        400
                    )

                    return

                if categoria not in CATEGORIAS:
                    categoria = "Outros"

                if prioridade not in PRIORIDADES:
                    prioridade = "Media"

                data = agora()

                con.execute("""
                    INSERT INTO chamados (
                        titulo,
                        cliente,
                        categoria,
                        prioridade,
                        status,
                        descricao,
                        diagnostico,
                        criado_em,
                        atualizado_em
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    titulo,
                    cliente,
                    categoria,
                    prioridade,
                    "Aberto",
                    descricao,
                    "",
                    data,
                    data
                ))

                con.commit()

                self.redirecionar("/")


            # ---------------------------------------------
            # ATUALIZAR CHAMADO
            # ---------------------------------------------

            elif self.path == "/atualizar":

                try:

                    id_chamado = int(
                        dados.get("id", ["0"])[0]
                    )

                except ValueError:

                    self.responder(
                        pagina_erro(
                            "ID inválido",
                            "Não foi possível identificar o chamado."
                        ),
                        400
                    )

                    return

                diagnostico = dados.get(
                    "diagnostico", [""]
                )[0].strip()

                status = dados.get(
                    "status", ["Aberto"]
                )[0]

                prioridade = dados.get(
                    "prioridade", ["Media"]
                )[0]

                if status not in STATUS:
                    status = "Aberto"

                if prioridade not in PRIORIDADES:
                    prioridade = "Media"

                existente = con.execute(
                    "SELECT id FROM chamados WHERE id = ?",
                    (id_chamado,)
                ).fetchone()

                if not existente:

                    self.responder(
                        pagina_erro(
                            "Chamado inexistente",
                            "Não foi possível atualizar esse chamado."
                        ),
                        404
                    )

                    return

                con.execute("""
                    UPDATE chamados
                    SET diagnostico = ?,
                        status = ?,
                        prioridade = ?,
                        atualizado_em = ?
                    WHERE id = ?
                """, (
                    diagnostico,
                    status,
                    prioridade,
                    agora(),
                    id_chamado
                ))

                con.commit()

                self.redirecionar(
                    f"/ver?id={id_chamado}"
                )


            else:

                self.responder(
                    pagina_erro(
                        "Rota inválida",
                        "Não foi possível processar essa requisição."
                    ),
                    404
                )

        finally:
            con.close()


    # =====================================================
    # LOG
    # =====================================================

    def log_message(self, formato, *args):

        print(
            f"[{agora()}] {self.address_string()} - {formato % args}"
        )


# =========================================================
# INICIALIZAÇÃO
# =========================================================

if __name__ == "__main__":

    con = banco()
    con.close()

    servidor = ThreadingHTTPServer(
        (HOST, PORT),
        Servidor
    )

    print("=" * 50)
    print("HELPDESK N1 - CENTRAL DE SUPORTE")
    print("=" * 50)
    print(f"Servidor iniciado em http://localhost:{PORT}")
    print("Pressione CTRL+C para encerrar.")
    print("=" * 50)

    try:

        servidor.serve_forever()

    except KeyboardInterrupt:

        print("\nServidor encerrado.")

        servidor.server_close()