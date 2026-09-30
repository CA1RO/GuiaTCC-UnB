const PAGINAS = [
  {
    grupo: "Entrega E1",
    titulo: "Domínio e pergunta",
    resumo: "A fonte pública e a frase que a plataforma responde.",
    arquivo: "e1/01-dominio-e-pergunta.md",
  },
  {
    grupo: "Entrega E1",
    titulo: "Esquema e migrações",
    resumo: "SQL versionado, do banco vazio até a revisão da origem.",
    arquivo: "e1/02-esquema-e-migracoes.md",
  },
  {
    grupo: "Entrega E1",
    titulo: "Carga reprodutível",
    resumo: "Um comando baixa o portal da UnB e popula o banco.",
    arquivo: "e1/03-carga-reprodutivel.md",
  },
  {
    grupo: "Entrega E1",
    titulo: "Volume",
    resumo: "2.797 docentes e 86 unidades, o recorte inteiro publicado.",
    arquivo: "e1/04-volume.md",
  },
  {
    grupo: "Entrega E1",
    titulo: "Caracterização da carga",
    resumo: "Volume, escrita, leitura, padrão de acesso e latência medida.",
    arquivo: "e1/05-caracterizacao-da-carga.md",
  },
  {
    grupo: "Entrega E1",
    titulo: "Histórico da origem",
    resumo: "O cadastro sobrescreve o estado atual e separa os dois tempos.",
    arquivo: "e1/06-historico-da-origem.md",
  },
  {
    grupo: "Decisão",
    titulo: "ADR 0001",
    resumo: "Estado atual, com unidade normalizada, medido no dado da UnB.",
    arquivo: "adr/0001-origem-guarda-estado-atual.md",
  },
];

const nav = document.querySelector("#nav");
const conteudo = document.querySelector("#conteudo");
const menu = document.querySelector(".menu");

function raiz() {
  let caminho = window.location.pathname;
  if (!caminho.endsWith("/")) {
    const ultimo = caminho.split("/").pop();
    caminho = ultimo.includes(".") ? caminho.replace(/[^/]*$/, "") : `${caminho}/`;
  }
  return caminho;
}

function escapar(texto) {
  return texto
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function inline(texto) {
  let html = escapar(texto);
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  html = html.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    '<a href="$2" target="_blank" rel="noreferrer">$1</a>',
  );
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  return html;
}

function renderizar(markdown) {
  const linhas = markdown.replace(/\r\n/g, "\n").split("\n");
  const blocos = [];
  let i = 0;

  while (i < linhas.length) {
    const linha = linhas[i];
    if (!linha.trim()) {
      i += 1;
      continue;
    }
    if (linha.startsWith("```")) {
      const codigo = [];
      i += 1;
      while (i < linhas.length && !linhas[i].startsWith("```")) {
        codigo.push(linhas[i]);
        i += 1;
      }
      i += 1;
      blocos.push(`<pre><code>${escapar(codigo.join("\n"))}</code></pre>`);
      continue;
    }
    if (linha.startsWith("|") && linhas[i + 1] && /^\|\s*:?-{3,}/.test(linhas[i + 1])) {
      const cabecalho = celulas(linha);
      const alinhamento = celulas(linhas[i + 1]).map((celula) => {
        if (celula.startsWith(":") && celula.endsWith(":")) return "";
        if (celula.endsWith(":")) return "num";
        return "";
      });
      i += 2;
      const corpo = [];
      while (i < linhas.length && linhas[i].startsWith("|")) {
        corpo.push(celulas(linhas[i]));
        i += 1;
      }
      blocos.push(tabela(cabecalho, alinhamento, corpo));
      continue;
    }
    const nivel = /^(#{1,3})\s+/.exec(linha);
    if (nivel) {
      const tag = `h${nivel[1].length}`;
      blocos.push(`<${tag}>${inline(linha.slice(nivel[1].length).trim())}</${tag}>`);
      i += 1;
      continue;
    }
    if (/^[-*] /.test(linha)) {
      const itens = [];
      while (i < linhas.length && /^[-*] /.test(linhas[i])) {
        itens.push(`<li>${inline(linhas[i].slice(2))}</li>`);
        i += 1;
      }
      blocos.push(`<ul>${itens.join("")}</ul>`);
      continue;
    }
    if (/^\d+\. /.test(linha)) {
      const itens = [];
      while (i < linhas.length && /^\d+\. /.test(linhas[i])) {
        itens.push(`<li>${inline(linhas[i].replace(/^\d+\. /, ""))}</li>`);
        i += 1;
      }
      blocos.push(`<ol>${itens.join("")}</ol>`);
      continue;
    }
    const paragrafo = [];
    while (
      i < linhas.length &&
      linhas[i].trim() &&
      !linhas[i].startsWith("#") &&
      !linhas[i].startsWith("|") &&
      !linhas[i].startsWith("```") &&
      !/^[-*] /.test(linhas[i]) &&
      !/^\d+\. /.test(linhas[i])
    ) {
      paragrafo.push(linhas[i].trim());
      i += 1;
    }
    blocos.push(`<p>${inline(paragrafo.join(" "))}</p>`);
  }
  return blocos.join("\n");
}

function celulas(linha) {
  return linha
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((celula) => celula.trim());
}

function tabela(cabecalho, alinhamento, corpo) {
  const th = cabecalho
    .map((celula, indice) => `<th class="${alinhamento[indice] || ""}">${inline(celula)}</th>`)
    .join("");
  const tr = corpo
    .map(
      (linha) =>
        `<tr>${linha
          .map((celula, indice) => `<td class="${alinhamento[indice] || ""}">${inline(celula)}</td>`)
          .join("")}</tr>`,
    )
    .join("");
  return `<table><thead><tr>${th}</tr></thead><tbody>${tr}</tbody></table>`;
}

function desenharNav(atual) {
  let grupo = "";
  nav.replaceChildren();
  const inicio = document.createElement("a");
  inicio.href = "#/";
  inicio.textContent = "Início";
  if (!atual) inicio.setAttribute("aria-current", "page");
  nav.append(inicio);
  for (const pagina of PAGINAS) {
    if (pagina.grupo !== grupo) {
      grupo = pagina.grupo;
      const rotulo = document.createElement("p");
      rotulo.className = "nav-grupo";
      rotulo.textContent = grupo;
      nav.append(rotulo);
    }
    const link = document.createElement("a");
    link.href = `#/${pagina.arquivo}`;
    link.textContent = pagina.titulo;
    if (atual === pagina.arquivo) link.setAttribute("aria-current", "page");
    nav.append(link);
  }
}

function inicio() {
  conteudo.className = "conteudo";
  conteudo.innerHTML = `
    <p class="olho">Banco de Dados 2 · 2026/2</p>
    <h1>Fonte transacional modelada e populada</h1>
    <p class="pergunta">Quais docentes da UnB estão em exercício, em que unidade estão lotados e com qual situação funcional, para o aluno localizar um projeto ou uma linha de pesquisa nessa unidade.</p>
    <ul class="numeros">
      <li><strong>2.797</strong><span>docentes na fonte pública</span></li>
      <li><strong>86</strong><span>unidades de lotação</span></li>
      <li><strong>2.607</strong><span>ativos permanentes</span></li>
    </ul>
    <div class="cartoes"></div>
  `;
  const cartoes = conteudo.querySelector(".cartoes");
  for (const pagina of PAGINAS) {
    const link = document.createElement("a");
    link.href = `#/${pagina.arquivo}`;
    link.innerHTML = `<small>${pagina.grupo}</small><strong>${pagina.titulo}</strong><span>${pagina.resumo}</span>`;
    cartoes.append(link);
  }
}

async function abrir(arquivo) {
  desenharNav(arquivo);
  conteudo.className = "conteudo prosa";
  conteudo.innerHTML = "<p>Carregando…</p>";
  try {
    const resposta = await fetch(`${raiz()}${arquivo}`);
    if (!resposta.ok) throw new Error(`${resposta.status}`);
    const markdown = await resposta.text();
    conteudo.innerHTML = renderizar(markdown);
  } catch (erro) {
    conteudo.innerHTML = `<p class="erro">Não foi possível abrir ${arquivo} (${erro.message}).</p>`;
  }
  menu.setAttribute("aria-expanded", "false");
  nav.classList.remove("aberto");
}

function rota() {
  const arquivo = decodeURIComponent(window.location.hash.replace(/^#\/?/, ""));
  if (!arquivo || !PAGINAS.some((pagina) => pagina.arquivo === arquivo)) {
    desenharNav("");
    inicio();
    return;
  }
  abrir(arquivo);
}

menu.addEventListener("click", () => {
  const aberto = nav.classList.toggle("aberto");
  menu.setAttribute("aria-expanded", String(aberto));
});

window.addEventListener("hashchange", rota);
rota();
