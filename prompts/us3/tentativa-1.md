# US-3 — Tentativa 1: Verificação da implementação

## Pedido e contexto

Ferramenta: Gemini  
Modelo: 3.1 Pro

Ficheiros fornecidos como contexto:

- `ARCHITECTURE.md`
- Ficheiros atuais de Comunicação das Docas
- Ficheiros atuais de Viagens

Os testes existentes foram mencionados no pedido, mas não foram fornecidos como ficheiros de contexto.

### Pedido enviado

Quero verificar e testar a implementação existente da US-3: como doca sem rede, reenvio os eventos guardados quando a rede volta, sem duplicar viagens.

Usa os ficheiros atuais de Comunicação das Docas e Viagens, os documentos de arquitetura e os testes existentes. Não regeneres os componentes.

Acrescenta testes funcionais para verificar que:

- um evento ocorrido enquanto a doca está sem rede fica guardado;
- depois de a ligação ser restabelecida, o evento é reenviado e a viagem é atualizada usando o instante físico registado pela doca;
- o reenvio do mesmo evento não duplica a viagem nem a cobrança, quando aplicável.

Mantém as dependências e decisões arquiteturais atuais. Não alteres os testes de arquitetura nem introduzas dependências novas. Se encontrares uma falha na implementação, explica-a e corrige apenas o necessário para a US-3.

Indica os ficheiros alterados e os comandos para executar os testes. Distingue os testes que executaste dos que apenas propões.

## Avaliação do resultado

**Resultado: parcialmente aceite.** A revisão detetou que a verificação do reenvio duplicado podia não voltar a entregar o evento: após um reenvio bem-sucedido, o evento era removido do buffer da doca. Assim, o teste podia não confirmar de forma fiável que Viagens ignora a repetição e evita uma nova cobrança.

A falha foi identificada por revisão humana/assistida, não pelas fitness functions de arquitetura.

### Testes

Comando executado:

```bash
python -m pytest tests/test_us3_reenvio_eventos.py -v

## Tentativa 2 — Correção do teste de duplicados

Esta tentativa é um follow-up da primeira. Corrige apenas o teste de reenvio duplicado, mantendo a implementação dos componentes e os restantes testes inalterados.

Ferramenta: Gemini  
Modelo: 3.1 Pro

### Pedido enviado

No teste `tests/test_us3_reenvio_eventos.py`, a verificação de duplicados pode estar a não testar nada: depois de um evento ser reenviado com sucesso, é removido do buffer da doca. Por isso, chamar `reenviar_evento_duplicado(evento_id)` nessa altura pode não reenviar o evento.

Corrige apenas o teste para voltar a entregar diretamente ao `ViagensService` o mesmo evento de encaixe, com o mesmo `evento_id` e os mesmos dados. Verifica que o processamento o identifica como duplicado e não volta a fechar a viagem nem a cobrar.

Altera também o mock de cobrança para registar todas as chamadas recebidas, sem eliminar duplicados por conta própria; assim o teste consegue confirmar que a cobrança só foi chamada uma vez.

Não alteres a implementação dos componentes nem os restantes testes. Preserva as correções de fecho das ligações SQLite com `contextlib.closing`.

Indica os ficheiros alterados e o comando para executar o teste.

### Avaliação do resultado

**Resultado: aceite.** Foi alterado apenas `tests/test_us3_reenvio_eventos.py`. O teste passou, confirmando que o mesmo evento de encaixe é processado como duplicado sem voltar a fechar a viagem nem a efetuar uma segunda cobrança.

Comando executado: `python -m pytest tests/test_us3_reenvio_eventos.py -v`.