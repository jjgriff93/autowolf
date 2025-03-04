# AutoWolf 🐺 An AI Game of Werewolf using AutoGen

## Getting started

### Prerequisites

- Python 3.12 or later
- Poetry 1.9 or later
- Azure CLI
- An Azure AI Services resource with a model deployment (`gpt-4o`)
- [Cognitive Services OpenAI User](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/role-based-access-control#cognitive-services-openai-user) permissions on the Azure AI Services resource

### Installation

1. Clone the repository:

```bash
git clone
cd ai-werewolf
```

2. Install the dependencies:

```bash
poetry install
```

3. Set up the environment variables:

```bash
cp .env.example .env
```

4. Log in to Azure

```bash
az login
```

### Run the application

```bash
poetry run python main.py
```
