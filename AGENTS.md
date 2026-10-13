# Instruções para agentes

## Projeto

Este repositório implementa uma busca por Simulated Annealing com dominância de Pareto para o problema de atribuir histórias a desenvolvedores. Os objetivos são maximizar o valor de negócio (`payment`) e minimizar a diferença entre as maiores e menores taxas de ocupação. Cada história pode ser atribuída a no máximo um desenvolvedor, e a carga de cada desenvolvedor não pode exceder sua capacidade.

## Estrutura

- `src/simulated_annealing/blacksmith.py`: inicialização, geração de vizinhos, recozimento simulado e arquivo de soluções não dominadas.
- `src/simulated_annealing/developer.py`: capacidade disponível e histórias atribuídas a cada desenvolvedor.
- `src/simulated_annealing/history.py`: modelo da história e função `get_history_id`.
- `src/simulated_annealing/__init__.py`: entrada do pacote.

## Convenções e invariantes

- Mantenha a lógica e os modelos existentes; faça alterações pequenas e coerentes com a arquitetura.
- Use type hints nas funções e mantenha a compatibilidade com Python `>=3.12`.
- Use `uv` para gerenciar o ambiente e executar comandos do projeto.
- Cada história deve ter um `id` inteiro único no conjunto passado ao algoritmo. Use `get_history_id` para obter/validar essa identidade; não use duração e valor como substitutos de ID.
- Não atribua uma história a mais de um desenvolvedor e nunca ultrapasse a capacidade disponível.
- O algoritmo não deve modificar os objetos de entrada do usuário quando construir soluções ou vizinhos.
- Preserve soluções não dominadas considerando valor maior como melhor e desequilíbrio menor como melhor.
- Não remova nem reverta alterações preexistentes fora do escopo da tarefa.

## Ambiente e validação

Sincronize as dependências com:

```bash
uv sync
```

Execute verificações e scripts Python com `uv run`, por exemplo:

```bash
uv run python -m compileall -q src/simulated_annealing
```

Não há diretório de testes configurado atualmente. Para mudanças no algoritmo, valide casos de atribuição, limites de capacidade, identidade única das histórias e não dominância das soluções resultantes.
