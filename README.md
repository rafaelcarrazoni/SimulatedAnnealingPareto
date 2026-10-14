# Simulated Annealing Pareto

Aplicação de exemplo para atribuir histórias a desenvolvedores usando **Simulated Annealing com dominância de Pareto**. Também inclui uma busca aleatória como baseline para comparar resultados.

## Problema

Cada história tem um esforço (`duration`) e um valor de negócio (`payment`). Cada desenvolvedor tem uma capacidade máxima (`max_capacity`). O algoritmo procura atribuições que:

1. Maximizem a soma dos valores de negócio das histórias atribuídas.
2. Minimizem o desequilíbrio da equipe, definido como a diferença entre a maior e a menor taxa de ocupação.

A taxa de ocupação de cada desenvolvedor é:

```text
(max_capacity - current_capacity) / max_capacity
```

Uma atribuição é viável quando cada história está atribuída a no máximo um desenvolvedor e a soma dos esforços atribuídos a cada desenvolvedor não excede sua capacidade.

## Requisitos

- Python `>=3.12`
- [uv](https://docs.astral.sh/uv/)

## Instalação e execução

Na raiz do repositório, sincronize o ambiente e as dependências:

```bash
uv sync
```

Execute a instância de demonstração:

```bash
uv run simulated-annealing
```

O comando chama os dois algoritmos com a mesma equipe e conjunto de histórias e grava os resultados em:

- `results/blacksmith.json`
- `results/comparison.json`

Os arquivos são sobrescritos quando o programa é executado novamente.

## Dados de entrada

A instância de demonstração está definida em `src/simulated_annealing/main.py`. Desenvolvedores e histórias são criados com os modelos `Developer` e `History`:

```python
from simulated_annealing.developer import Developer
from simulated_annealing.history import History

team = [
    Developer(max_capacity=32),
    Developer(max_capacity=40),
]

histories = [
    History(id=0, duration=8, payment=500),
    History(id=1, duration=12, payment=750),
]
```

Cada história precisa de um `id` inteiro único dentro da instância, fornecido ao construtor. Os construtores aplicam estas validações:

- `History.id`: inteiro; IDs negativos são permitidos, mas não podem se repetir no conjunto.
- `History.duration`: inteiro maior que zero.
- `History.payment`: inteiro não negativo.
- `Developer.max_capacity`: inteiro maior que zero.

Valores booleanos não são aceitos como inteiros. IDs repetidos são rejeitados quando os algoritmos recebem o conjunto de histórias.

## Algoritmos

### `Blacksmith`

`Blacksmith.anneal(team, histories)` executa a busca por Simulated Annealing e retorna o arquivo de soluções não dominadas. A solução inicial e os vizinhos são construídos sem modificar os objetos de entrada.

Os parâmetros podem ser configurados ao criar o algoritmo:

```python
from simulated_annealing.blacksmith import Blacksmith

blacksmith = Blacksmith(
    temperature=1.0,
    alpha=0.99,
    max_iterations=1_000,
    minimum_temperature=0.01,
)
solutions = blacksmith.anneal(team, histories)
```

Uma solução domina outra quando tem valor de negócio pelo menos tão alto e desequilíbrio pelo menos tão baixo, sendo estritamente melhor em um dos dois objetivos.

### `Comparison`

`Comparison.search(team, histories)` gera atribuições aleatórias viáveis e mantém um arquivo das soluções não dominadas encontradas. É uma baseline heurística, não uma garantia de encontrar a fronteira Pareto completa.

```python
from simulated_annealing.comparison import Comparison

comparison = Comparison(n_evaluations=10_000, seed=42)
solutions = comparison.search(team, histories)
```

`seed` controla o gerador aleatório próprio da baseline e permite repetir a mesma sequência de sorteios.

## Resultados JSON

`Export.export(algorithm)` salva as soluções da instância de `Blacksmith` ou `Comparison` recebida e retorna o caminho do arquivo:

```python
from simulated_annealing.export import Export

blacksmith_path = Export.export(blacksmith)
comparison_path = Export.export(comparison)
```

Cada arquivo identifica o algoritmo e contém uma lista `solutions`. Cada solução inclui:

- `business_value`: soma dos valores (`payment`) atribuídos;
- `imbalance`: diferença entre as taxas de ocupação extremas;
- `developers`: capacidade, horas restantes, horas atribuídas e histórias de cada desenvolvedor.

## Estrutura do projeto

```text
src/simulated_annealing/
├── blacksmith.py   # Simulated Annealing e arquivo Pareto
├── comparison.py   # baseline de busca aleatória
├── developer.py   # modelo do desenvolvedor e controle de capacidade
├── export.py      # exportação das soluções em JSON
├── history.py     # modelo da história e identidade
└── main.py        # instância de demonstração e execução dos algoritmos
```

## Verificações

Compile os módulos do pacote com:

```bash
uv run python -m compileall -q src/simulated_annealing
```

O repositório não possui atualmente uma suíte de testes automatizados configurada.
