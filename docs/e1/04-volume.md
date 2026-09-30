# Volume e medição da fonte

A medição foi executada sobre o CSV público completo de 2024, depois do filtro para a UnB.

| Medida                                                           | Resultado |
| ---------------------------------------------------------------- | --------: |
| Docentes distintos                                               |     2.016 |
| Programas distintos                                              |       102 |
| Vínculos docente–programa–ano                                    |     2.472 |
| Docentes ligados a mais de um programa                           |       409 |
| Maior número de programas por docente                            |         5 |
| Vínculos perdidos em um modelo com um único programa por docente |       456 |

O volume ultrapassa o exemplo mínimo de cem linhas e representa todo o recorte da UnB presente na edição selecionada.

## Comparação das alternativas

Uma projeção reproduzível dos campos usados pelo sistema ocupou 456.148 bytes no formato desnormalizado e 333.912 bytes no formato normalizado. A redução medida foi de 26,8%.

Os bytes representam JSON compacto para comparar a repetição lógica dos mesmos atributos. Eles não são uma estimativa do armazenamento físico do PostgreSQL.

A medição pode ser repetida com:

```bash
python -m scripts.medir_modelagem_capes
```
