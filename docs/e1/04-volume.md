# Volume

A maior tabela da origem, depois da carga pública, é `docente`.

| Conjunto | Linhas |
| --- | ---: |
| Linhas no CSV público | 2.797 |
| Nomes distintos no CSV | 2.797 |
| Unidades de lotação distintas | 86 |
| Docentes `ATIVO PERMANENTE` | 2.607 |
| Docentes no banco, com o exemplo local | 2.802 |
| Departamentos no banco, com o exemplo local | 91 |

As outras situações no arquivo: 154 `CONT.PROF.SUBSTITUTO`, 23 `CEDIDO`, 8 `CONT.PROF.VISITANTE`, 3 `EXCEDENTE A LOTAÇÃO` e 2 `CONTRATO TEMPORÁRIO`.

O arquivo compactado tem 106.001 bytes e o CSV interno tem 1.148.249 bytes. A tabela `docente`, com índices, ocupava 2.792 kB no PostgreSQL 16 logo após a carga. O nome mais longo tem 58 caracteres, a unidade mais longa tem 40 e a situação mais longa tem 20, todos dentro dos limites `VARCHAR` do esquema.

Esse volume cobre o cadastro institucional inteiro publicado pela UnB nesse recurso, não uma amostra de cem linhas.
