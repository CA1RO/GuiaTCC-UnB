const lista = document.querySelector("#lista");
const filtros = document.querySelector("#filtros");
const tipos = document.querySelector("#tipos");
const contagem = document.querySelector("#contagem");
const tituloCatalogo = document.querySelector("#titulo-catalogo");
const aviso = document.querySelector("#aviso");
const vazio = document.querySelector("#vazio");
const mensagens = document.querySelector("#mensagens");
const painel = document.querySelector("#painel");
const saude = document.querySelector("#saude");

const ROTULOS = { pesquisa: "Pesquisa", extensao: "Extensão", tcc: "TCC" };
let departamentoAtivo = "";
let tipoAtivo = "";

async function lerJson(resposta) {
  if (!resposta.ok) {
    const detalhe = await resposta.text();
    throw new Error(detalhe || "Falha na requisição");
  }
  return resposta.json();
}

function cartao(rotulo, titulo, linha, extra) {
  const card = document.createElement("button");
  card.className = "card";
  card.type = "button";
  const selo = document.createElement("span");
  selo.className = "selo";
  selo.textContent = rotulo;
  const nome = document.createElement("strong");
  nome.textContent = titulo;
  const detalhe = document.createElement("span");
  detalhe.textContent = linha;
  const complemento = document.createElement("span");
  complemento.textContent = extra;
  card.append(selo, nome, detalhe, complemento);
  return card;
}

function renderBusca(resultado) {
  lista.replaceChildren();
  const projetos = resultado.projetos || [];
  const docentes = resultado.docentes || [];
  const mostrandoDocentes = resultado.modo === "docentes";
  tituloCatalogo.textContent = mostrandoDocentes ? "Docentes" : "Projetos";
  aviso.hidden = !mostrandoDocentes;
  aviso.textContent = mostrandoDocentes
    ? "Não há projeto de pesquisa, extensão ou TCC nessa linha. Estes docentes seguem algo próximo."
    : "";

  if (mostrandoDocentes) {
    contagem.textContent = docentes.length === 1 ? "1 docente" : `${docentes.length} docentes`;
    vazio.hidden = docentes.length > 0;
    vazio.textContent = "Nenhum docente com linha próxima.";
    for (const docente of docentes) {
      const card = cartao(
        docente.departamento_sigla || "UnB",
        docente.nome,
        docente.linha_pesquisa || "Linha não informada",
        docente.titulacao || "",
      );
      card.addEventListener("click", () => abrirDocente(docente));
      lista.append(card);
    }
    return;
  }

  contagem.textContent = projetos.length === 1 ? "1 projeto" : `${projetos.length} projetos`;
  vazio.hidden = projetos.length > 0;
  vazio.textContent = "Nenhum projeto encontrado para essa busca.";
  for (const projeto of projetos) {
    const card = cartao(
      ROTULOS[projeto.tipo] || projeto.tipo,
      projeto.titulo,
      projeto.nome_docente,
      projeto.departamento_sigla || projeto.departamento_nome || "",
    );
    card.addEventListener("click", () => abrirProjeto(projeto));
    lista.append(card);
  }
}

async function carregarBusca() {
  const consulta = new URLSearchParams();
  const termo = document.querySelector("#busca").value.trim();
  if (termo) consulta.set("q", termo);
  if (tipoAtivo) consulta.set("tipo", tipoAtivo);
  if (departamentoAtivo) consulta.set("departamento", departamentoAtivo);
  const sufixo = consulta.toString() ? `?${consulta}` : "";
  const resultado = await lerJson(await fetch(`/api/v1/busca/${sufixo}`));
  renderBusca(resultado);
  return resultado;
}

function chip(grupo, texto, ativo, aoClicar) {
  const botao = document.createElement("button");
  botao.className = "chip";
  botao.type = "button";
  botao.textContent = texto;
  botao.setAttribute("aria-pressed", String(ativo));
  botao.addEventListener("click", () => aoClicar(botao));
  grupo.append(botao);
  return botao;
}

function marcar(grupo, botao) {
  for (const item of grupo.querySelectorAll(".chip")) {
    item.setAttribute("aria-pressed", item === botao ? "true" : "false");
  }
}

async function carregarFiltros() {
  tipos.replaceChildren();
  chip(tipos, "Todos os tipos", true, async (botao) => {
    tipoAtivo = "";
    marcar(tipos, botao);
    await carregarBusca();
  });
  for (const [valor, rotulo] of Object.entries(ROTULOS)) {
    chip(tipos, rotulo, false, async (botao) => {
      tipoAtivo = valor;
      marcar(tipos, botao);
      await carregarBusca();
    });
  }

  const departamentos = await lerJson(await fetch("/api/v1/departamentos/"));
  filtros.replaceChildren();
  chip(filtros, "Todos", true, async (botao) => {
    departamentoAtivo = "";
    marcar(filtros, botao);
    await carregarBusca();
  });
  for (const departamento of departamentos) {
    chip(filtros, departamento.sigla || departamento.nome, false, async (botao) => {
      departamentoAtivo = departamento.nome;
      marcar(filtros, botao);
      await carregarBusca();
    });
  }
}

function preencherPainel(sobretitulo, titulo, meta, paragrafos, palavras = []) {
  document.querySelector("#painel-depto").textContent = sobretitulo;
  document.querySelector("#painel-nome").textContent = titulo;
  document.querySelector("#painel-meta").textContent = meta;
  const destino = document.querySelector("#painel-corpo");
  destino.replaceChildren();
  for (const texto of paragrafos.filter(Boolean)) {
    const paragrafo = document.createElement("p");
    paragrafo.textContent = texto;
    destino.append(paragrafo);
  }
  if (palavras.length) {
    const tags = document.createElement("div");
    tags.className = "tags";
    for (const palavra of palavras) {
      const tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = palavra;
      tags.append(tag);
    }
    destino.append(tags);
  }
  painel.showModal();
}

function abrirProjeto(projeto) {
  preencherPainel(
    `${ROTULOS[projeto.tipo] || projeto.tipo} · ${projeto.departamento_sigla || "UnB"}`,
    projeto.titulo,
    [projeto.nome_docente, projeto.titulacao, projeto.email_docente].filter(Boolean).join(" · "),
    [projeto.descricao],
    projeto.palavras_chave || [],
  );
}

function abrirDocente(docente) {
  preencherPainel(
    docente.departamento_nome || "UnB",
    docente.nome,
    [docente.titulacao, docente.email].filter(Boolean).join(" · "),
    ["Não há projeto cadastrado nessa linha.", docente.linha_pesquisa],
  );
}

function adicionarBolha(texto, tipo, itens = []) {
  const bolha = document.createElement("div");
  bolha.className = `bolha ${tipo}`;
  const paragrafo = document.createElement("p");
  paragrafo.textContent = texto;
  bolha.append(paragrafo);
  if (itens.length) {
    const ul = document.createElement("ul");
    for (const item of itens) {
      const li = document.createElement("li");
      li.textContent = item;
      ul.append(li);
    }
    bolha.append(ul);
  }
  mensagens.append(bolha);
  mensagens.scrollTop = mensagens.scrollHeight;
}

async function perguntar(texto) {
  const pergunta = texto.trim();
  if (!pergunta) return;
  adicionarBolha(pergunta, "aluno");
  const idEstudante = sessionStorage.getItem("id_estudante");
  const corpo = { pergunta };
  if (idEstudante) corpo.id_estudante = Number(idEstudante);

  const botao = document.querySelector("#chat-form button");
  botao.disabled = true;
  try {
    const resposta = await lerJson(await fetch("/api/v1/rag/buscar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
    }));
    const itens = (resposta.chunks_relevantes || []).map(
      (chunk) => `${chunk.nome_docente}: ${chunk.conteudo_texto}`,
    );
    adicionarBolha(resposta.resposta_rag || resposta.mensagem, "guia", itens);
  } catch (erro) {
    adicionarBolha("Não consegui consultar o guia agora. Tente de novo em instantes.", "guia");
  } finally {
    botao.disabled = false;
  }
}

document.querySelector("#busca-form").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  await carregarBusca();
});

document.querySelector("#perguntar").addEventListener("click", () => {
  const termo = document.querySelector("#busca").value.trim();
  if (termo) document.querySelector("#pergunta").value = termo;
  document.querySelector("#conversa").scrollIntoView({ behavior: "smooth" });
  document.querySelector("#pergunta").focus();
});

document.querySelector("#chat-form").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const campo = document.querySelector("#pergunta");
  await perguntar(campo.value);
  campo.value = "";
});

document.querySelector("#perfil-form").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const form = evento.currentTarget;
  const dados = new FormData(form);
  const areas = String(dados.get("areas") || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  const status = document.querySelector("#perfil-status");
  try {
    const estudante = await lerJson(await fetch("/api/v1/estudantes/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nome: dados.get("nome"),
        curso: dados.get("curso") || null,
        areas_interesse: areas.length ? areas : null,
        tema_pretendido: dados.get("tema") || null,
      }),
    }));
    sessionStorage.setItem("id_estudante", String(estudante.id_estudante));
    status.textContent = `Perfil salvo. As próximas perguntas saem associadas a ${estudante.nome}.`;
    form.reset();
  } catch (erro) {
    status.textContent = "Não foi possível salvar o perfil.";
  }
});

document.querySelector("#fechar").addEventListener("click", () => painel.close());
painel.addEventListener("click", (evento) => {
  if (evento.target === painel) painel.close();
});

document.querySelector("#menu").addEventListener("click", () => {
  const nav = document.querySelector("#navegacao");
  const aberto = nav.classList.toggle("aberta");
  document.querySelector("#menu").setAttribute("aria-expanded", String(aberto));
});

document.querySelectorAll("#navegacao a").forEach((link) => {
  link.addEventListener("click", () => {
    document.querySelector("#navegacao").classList.remove("aberta");
    document.querySelector("#menu").setAttribute("aria-expanded", "false");
  });
});

async function iniciar() {
  try {
    const estado = await lerJson(await fetch("/health"));
    const ok = estado.status === "healthy";
    saude.textContent = ok ? "Serviços no ar" : "Serviço degradado";
    saude.classList.add(ok ? "ok" : "erro");
    await carregarFiltros();
    await carregarBusca();
  } catch (erro) {
    saude.textContent = "API indisponível";
    saude.classList.add("erro");
    contagem.textContent = "Sem conexão com a API";
  }
}

iniciar();
