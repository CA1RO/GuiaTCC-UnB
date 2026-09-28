const lista = document.querySelector("#lista");
const filtros = document.querySelector("#filtros");
const contagem = document.querySelector("#contagem");
const vazio = document.querySelector("#vazio");
const mensagens = document.querySelector("#mensagens");
const painel = document.querySelector("#painel");
const saude = document.querySelector("#saude");

let departamentoAtivo = "";

function iniciais(nome) {
  const partes = nome.trim().split(/\s+/);
  const ultima = partes.length > 1 ? partes[partes.length - 1] : "";
  return (partes[0][0] + (ultima[0] || "")).toUpperCase();
}

async function lerJson(resposta) {
  if (!resposta.ok) {
    const detalhe = await resposta.text();
    throw new Error(detalhe || "Falha na requisição");
  }
  return resposta.json();
}

function renderDocentes(docentes) {
  lista.replaceChildren();
  contagem.textContent = docentes.length === 1 ? "1 docente" : `${docentes.length} docentes`;
  vazio.hidden = docentes.length > 0;

  for (const docente of docentes) {
    const card = document.createElement("button");
    card.className = "card";
    card.type = "button";
    card.innerHTML = `
      <span class="avatar">${iniciais(docente.nome)}</span>
      <strong></strong>
      <span></span>
      <span></span>
    `;
    card.querySelector("strong").textContent = docente.nome;
    card.querySelectorAll("span")[1].textContent = docente.departamento_sigla || docente.departamento_nome || "Departamento não informado";
    card.querySelectorAll("span")[2].textContent = docente.titulacao || docente.situacao;
    card.addEventListener("click", () => abrirDocente(docente.id_docente));
    lista.append(card);
  }
}

async function carregarDocentes(params = {}) {
  const consulta = new URLSearchParams();
  if (params.nome) consulta.set("nome", params.nome);
  if (params.departamento) consulta.set("departamento", params.departamento);
  const sufixo = consulta.toString() ? `?${consulta}` : "";
  const docentes = await lerJson(await fetch(`/api/v1/docentes/${sufixo}`));
  renderDocentes(docentes);
  return docentes;
}

async function carregarFiltros() {
  const departamentos = await lerJson(await fetch("/api/v1/departamentos/"));
  filtros.replaceChildren();

  const todos = document.createElement("button");
  todos.className = "chip";
  todos.type = "button";
  todos.textContent = "Todos";
  todos.setAttribute("aria-pressed", "true");
  todos.addEventListener("click", () => selecionarDepartamento("", todos));
  filtros.append(todos);

  for (const departamento of departamentos) {
    const chip = document.createElement("button");
    chip.className = "chip";
    chip.type = "button";
    chip.textContent = departamento.sigla || departamento.nome;
    chip.title = departamento.nome;
    chip.setAttribute("aria-pressed", "false");
    chip.addEventListener("click", () => selecionarDepartamento(departamento.nome, chip));
    filtros.append(chip);
  }
}

async function selecionarDepartamento(nome, botao) {
  departamentoAtivo = nome;
  document.querySelector("#busca").value = "";
  for (const chip of filtros.querySelectorAll(".chip")) {
    chip.setAttribute("aria-pressed", chip === botao ? "true" : "false");
  }
  await carregarDocentes(nome ? { departamento: nome } : {});
}

async function abrirDocente(id) {
  const [docente, projetos] = await Promise.all([
    lerJson(await fetch(`/api/v1/docentes/${id}`)),
    lerJson(await fetch(`/api/v1/docentes/${id}/projetos`)),
  ]);

  document.querySelector("#painel-depto").textContent = docente.departamento_nome || "UnB";
  document.querySelector("#painel-nome").textContent = docente.nome;
  const meta = [docente.titulacao, docente.email].filter(Boolean).join(" · ");
  document.querySelector("#painel-meta").textContent = meta || "Cadastro sem contato informado";

  const destino = document.querySelector("#painel-projetos");
  destino.replaceChildren();
  if (!projetos.length) {
    destino.textContent = "Nenhum projeto cadastrado.";
    painel.showModal();
    return;
  }

  for (const projeto of projetos) {
    const bloco = document.createElement("article");
    bloco.className = "projeto";
    const titulo = document.createElement("div");
    titulo.className = "projeto-topo";
    const h = document.createElement("strong");
    h.textContent = projeto.titulo;
    const ano = document.createElement("span");
    ano.textContent = [projeto.ano_inicio, projeto.ano_fim].filter(Boolean).join("–") || projeto.status;
    titulo.append(h, ano);
    const descricao = document.createElement("p");
    descricao.textContent = projeto.descricao || "";
    bloco.append(titulo, descricao);
    if (projeto.palavras_chave?.length) {
      const tags = document.createElement("div");
      tags.className = "tags";
      for (const palavra of projeto.palavras_chave) {
        const tag = document.createElement("span");
        tag.className = "tag";
        tag.textContent = palavra;
        tags.append(tag);
      }
      bloco.append(tags);
    }
    destino.append(bloco);
  }
  painel.showModal();
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
  const termo = document.querySelector("#busca").value.trim();
  departamentoAtivo = "";
  for (const chip of filtros.querySelectorAll(".chip")) {
    chip.setAttribute("aria-pressed", chip.textContent === "Todos" ? "true" : "false");
  }
  if (!termo) {
    await carregarDocentes();
    return;
  }
  const porNome = await carregarDocentes({ nome: termo });
  if (!porNome.length) await carregarDocentes({ departamento: termo });
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
    await Promise.all([carregarFiltros(), carregarDocentes()]);
  } catch (erro) {
    saude.textContent = "API indisponível";
    saude.classList.add("erro");
    contagem.textContent = "Sem conexão com a API";
  }
}

iniciar();
