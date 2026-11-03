# US-2 — Manutenção — Tentativa 3

## Ferramenta e modelo

- Ferramenta: Gemini
- Modelo: 3.1 Pro

## Quarto pedido enviado
Quero corrigir a implementação existente de Manutenção da US-2, seguindo os documentos atuais. Altera apenas Manutenção e os testes funcionais necessários.

Ficheiros fornecidos:
- ARCHITECTURE.md
- docs/02-componentes.md
- src/manutencao/manutencao.py
- tests/test_us2_manutencao.py
- src/main.py e src/manutencao/telemetria.py como contexto de integração

O ciclo de vida definido nos documentos é:
- A ordem começa em `PENDENTE_AVALIACAO`.
- Sem necessidade de intervenção: regista a avaliação e o resultado, e passa a `SEM_INTERVENCAO_NECESSARIA`.
- Com necessidade de intervenção: passa a `EM_INTERVENCAO`; depois de registar a intervenção e o resultado, passa a `CONCLUIDA`.
- `CANCELADA` não faz parte do fluxo nem deve existir no enum.

Corrige também estas lacunas:
- Só permitir avaliar uma ordem em `PENDENTE_AVALIACAO`.
- Não exigir um resultado final ao avaliar uma ordem que vai para `EM_INTERVENCAO`; o resultado dessa intervenção é registado ao concluir o trabalho.
- Não converter estados desconhecidos da base de dados para outro estado: sinaliza-os com um erro claro.
- Na migração, converter registos antigos com estado `CANCELADA` para `SEM_INTERVENCAO_NECESSARIA` e definir `necessita_intervencao` como falso. A implementação anterior só usava `CANCELADA` quando não era necessária intervenção. Preserva os restantes dados.

Mantém a migração existente do esquema SQLite, o uso de `contextlib.closing`, a idempotência das mensagens e as dependências arquiteturais. Não alteres Telemetria, `src/main.py`, o broker nem os testes de arquitetura.

Atualiza os testes funcionais para verificar:
- os dois percursos do ciclo de vida;
- a rejeição de transições inválidas;
- a persistência de `EM_INTERVENCAO` após reabrir a base de dados;
- a migração dos registos antigos `CANCELADA`, preservando os outros dados;
- o tratamento explícito de estados desconhecidos.

Indica os ficheiros alterados e os comandos para executar os testes. Distingue os testes que executaste dos que apenas propões.

## Resultado e avaliação

A versão inicial da tentativa manteve `CANCELADA` no enum e convertia estados desconhecidos para esse estado. Os testes passaram, mas uma revisão humana identificou que isso contrariava a decisão documentada. As fitness functions não verificam a semântica dos estados.

Após o esclarecimento, o código passou a migrar os registos antigos, rejeitar estados desconhecidos e validar as transições. Foram acrescentados testes para a migração, as transições inválidas e a persistência de `EM_INTERVENCAO`.

## Testes

Comando:

`python -m pytest tests/architecture/ tests/test_us2_manutencao.py -v`