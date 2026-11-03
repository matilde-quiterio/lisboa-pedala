# Lisboa Pedala

Projeto desenvolvido no âmbito da unidade curricular de **Design de Software**.

O objetivo do trabalho foi definir a arquitetura de um sistema de bicicletas partilhadas e utilizar essa especificação para gerar um esqueleto funcional da aplicação.

## Trabalho realizado

Ao longo do projeto foram definidos:

- as principais características arquiteturais;
- os componentes do sistema;
- o particionamento da aplicação;
- as dependências permitidas entre componentes;
- as principais decisões arquiteturais, registadas através de ADRs;
- vistas e diagramas da arquitetura;
- fitness functions para validar algumas regras arquiteturais;
- testes funcionais para as user stories implementadas.

O código foi desenvolvido em **Python** e utiliza **SQLite** para persistência local.

Foram implementadas três user stories end-to-end relacionadas com:

- desbloqueio, devolução e cobrança de uma bicicleta;
- criação e tratamento de ordens de manutenção;
- reenvio de eventos armazenados por docas durante períodos sem ligação.

## Utilização de Inteligência Artificial

Durante o projeto foi utilizada IA generativa como ferramenta de apoio.

A IA foi usada principalmente para:

- gerar código a partir da arquitetura e dos ADRs definidos pelo grupo;
- ajudar a melhorar a escrita e organização de alguns documentos;
- apoiar a revisão de código e documentação.

As decisões arquiteturais não foram tomadas pela IA.

As decisões sobre componentes, dependências, características arquiteturais, particionamento e ADRs foram discutidas e tomadas pelo grupo. A IA foi utilizada apenas como ferramenta de apoio à implementação e à escrita.

As diferentes tentativas de geração de código e respetivos resultados encontram-se registadas na pasta:

```text
prompts/
```

A reflexão sobre os problemas encontrados durante a utilização da IA encontra-se em:

```text
docs/reflexao.md
```

## Estrutura do repositório

```text
ARCHITECTURE.md
README.md
CODEOWNERS

docs/
    adr/
    diagramas/
    01-caracteristicas.md
    02-componentes.md
    03-particionamento-e-vistas.md
    reflexao.md

prompts/
src/
tests/
```

O ficheiro `ARCHITECTURE.md` contém as principais regras que a implementação deve respeitar.

A pasta `docs/` contém a documentação arquitetural do projeto.

A pasta `src/` contém o código da aplicação.

A pasta `tests/` contém as fitness functions e os testes funcionais.

## Executar o projeto

É necessário ter **Python 3.11 ou superior**.

Na raiz do projeto:

```bash
python -m src.main
```

## Executar os testes

```bash
python -m pytest -v
```

Este comando executa os testes funcionais e as fitness functions do projeto.