# US-2 — Manutenção — Tentativa 3

## Ferramenta e modelo

- Ferramenta: Gemini
- Modelo: 3.1 Pro

## Ficheiros de contexto fornecidos

- `ARCHITECTURE.md`
- `docs/02-componentes.md`
- `docs/adr/ADR-004.md`
- `docs/adr/ADR-005.md`
- `src/manutencao/telemetria.py`
- `src/manutencao/manutencao.py`
- `src/main.py`
- `tests/test_us2_manutencao.py`

`telemetria.py` foi fornecido como contexto, mas não foi alterado nesta tentativa.

## Primeiro pedido enviado

Quero corrigir a implementação existente da US-2, não gerar novamente o projeto inteiro.

Usa os ficheiros atuais:

- ARCHITECTURE.md
- docs/02-componentes.md
- docs/adr/ADR-004.md
- docs/adr/ADR-005.md
- src/manutencao/telemetria.py
- src/manutencao/manutencao.py
- src/main.py
- tests/test_us2_manutencao.py

Na segunda tentativa, as fitness functions passaram e os testes funcionais passaram depois de eu corrigir manualmente a abertura das ligações SQLite com contextlib.closing. Preserva essa correção; não a removas.

A revisão identificou estas lacunas:

1. O main.py usa queue.Queue, que só mantém mensagens em memória. O ADR-005 exige que as mensagens sejam persistidas e confirmadas após processamento. Corrige a simulação local para respeitar esses comportamentos, sem acrescentar serviços externos nem alterar as decisões arquiteturais. Se não for claro nos documentos como simular localmente essa garantia, explica a dúvida antes de escolher uma solução.

2. A ordem de manutenção guarda apenas o resultado final. A arquitetura exige guardar a avaliação do técnico e a intervenção, quando aplicável, além do resultado. Ajusta o modelo e o fluxo para registar esses dados e respeitar o ciclo de vida definido. Não inventes estados ou regras que não estejam documentados.

3. Se o processamento de uma mensagem falhar, a mensagem deve continuar disponível para nova tentativa e o worker não deve deixar o programa bloqueado à espera da fila.

Mantém as dependências permitidas: Telemetria pode depender de Manutenção, mas Manutenção não pode depender de Telemetria, incluindo através de imports de tipos ou modelos.

Atualiza os testes funcionais para verificar:

- a persistência da mensagem até ser processada e confirmada;
- a disponibilidade da mensagem para nova tentativa se o processamento falhar;
- a avaliação do técnico, a intervenção quando aplicável e o resultado final;
- a persistência das ordens após reabrir a base de dados;
- a ausência de duplicados no reenvio da mesma mensagem.

Não alteres os testes de arquitetura. Indica os ficheiros alterados e os comandos de teste. Distingue os testes que executaste dos que apenas propões. Não alteres partes da implementação que não sejam necessárias para estas correções.

## Resultado do primeiro pedido

A implementação substituiu a fila em memória por um `SQLiteBroker` em `src/main.py`. O broker guarda as mensagens em `broker.db`, mantém as mensagens pendentes quando o processamento falha e confirma-as após o processamento sem erro.

A implementação de Manutenção passou a guardar a avaliação, a intervenção quando aplicável e o resultado. `telemetria.py` manteve-se igual à versão anterior.

Na primeira execução conjunta, passaram 8 testes: as duas fitness functions e os testes funcionais. O teste de reabertura do broker tinha sido acrescentado manualmente, com assistência do ChatGPT; não foi apresentado como teste gerado pelo Gemini.

Ao executar a CLI, foi detetado um problema não apanhado pelos testes: a base de dados SQLite existente tinha um esquema antigo, sem as colunas `necessita_intervencao` e `descricao_intervencao`.

## Deteção do problema do esquema

A incompatibilidade foi detetada pelo utilizador ao executar `python -m src.main`. Não foi detetada pelas fitness functions arquiteturais.

As fitness functions passaram:

- `test_allowed_to_use.py`: PASSED
- `test_no_cycles.py`: PASSED

## Follow-up enviado no mesmo chat

A CLI falhou porque já existe uma base de dados SQLite criada por uma versão anterior do código. A tabela ordens_manutencao tem as colunas ordem_id, bicicleta_id, origem, descricao_avaria, estado, mensagem_id_origem e resultado; a versão atual também precisa de necessita_intervencao e descricao_intervencao.

Corrige o repositório para migrar o esquema existente de forma idempotente, preservando os dados. Não apagues nem recries a base de dados. Garante também que as consultas leem as colunas corretamente, mesmo que as colunas novas tenham sido acrescentadas no fim da tabela. Acrescenta um teste para esta migração e indica os comandos para voltar a executar os testes e a CLI. Mantém as regras arquiteturais e os restantes comportamentos.

## Resultado do follow-up

Após a correção da migração:

- passaram 9 testes, incluindo os testes de arquitetura e o novo teste de migração;
- a CLI correu sem erro;
- as ordens existentes foram preservadas.

A CLI apresentou 3 ordens. São mensagens distintas acumuladas das execuções anteriores e da execução atual; o teste de reenvio confirmou que a mesma mensagem não cria uma ordem duplicada.

## Revisão humana e estado do resultado

A revisão humana identificou que o código associa o estado `CANCELADA` ao caso em que o técnico decide que não é necessária uma intervenção, embora essa regra não estivesse definida nos documentos fornecidos. As fitness functions não verificam a semântica dos estados.

O código também inclui `EM_INTERVENCAO`, mas não passa por esse estado no fluxo apresentado.

O resultado passou os testes após o follow-up da migração, mas ainda não é a versão final da US-2. Depois desta tentativa, o grupo decidiu clarificar o ciclo de vida nos documentos: usar `SEM_INTERVENCAO_NECESSARIA` quando não é necessário reparar e `EM_INTERVENCAO` enquanto a reparação decorre. A implementação e os testes de Manutenção terão de ser atualizados para corresponder a essa decisão.

A correção do estado foi identificada em revisão humana, não pelas fitness functions.