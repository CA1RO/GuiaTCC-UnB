# Histórico da origem

A fonte é tratada com uma estratégia híbrida: cadastro atual para docentes e programas, histórico anual para seus vínculos.

## Docentes e programas

As tabelas `docente` e `programa_pos_graduacao` seguem CRUD com sobrescrita. Uma nova carga atualiza os atributos associados ao mesmo `id_capes` ou `codigo_capes`.

Esse desenho mantém o cadastro conhecido mais recente, mas não preserva cada correção intermediária publicada dentro de um mesmo ano.

## Vínculos anuais

A identidade de `docente_programa` é formada por docente, programa e `ano_base`.

- Outra edição anual acrescenta novos vínculos sem apagar os anos anteriores.
- A repetição da mesma edição não duplica linhas.
- Uma correção para o mesmo vínculo e ano atualiza `categoria_docente`.

Essa separação permite responder em quais programas um docente apareceu em cada edição anual disponível, sem confundir o ano da fonte com o instante em que o carregador foi executado.

## Limite da decisão

Caso seja necessário guardar cada correção recebida dentro do mesmo ano, será preciso acrescentar versionamento temporal ou uma camada bruta imutável. Esse cenário é um dos gatilhos de revisão registrados no ADR 0001.
