# AutoWolf 🐺 An AI Game of Werewolf using AutoGen

## Getting started

### Prerequisites

- Python 3.12 or later
- Poetry 1.9 or later
- Azure CLI
- An Azure AI Services resource with a model deployment (`gpt-4o`)
- [Cognitive Services OpenAI User](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/role-based-access-control#cognitive-services-openai-user) permissions on the Azure AI Services resource
- For deployment: Access to an Azure AI Foundry Project

### Installation

1. Clone the repository:

```bash
git clone
cd autowolf
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
poetry run chainlit run main.py
```

### Deploy to Azure AI Foundry Agent Service

1. Update your `.env` file with the following additional variables:

```
AZURE_SUBSCRIPTION_ID=your_azure_subscription_id
AZURE_RESOURCE_GROUP=your_resource_group_name
AZURE_AI_PROJECT=your_ai_project_name
```

2. Run the deployment script:

```bash
poetry run python deploy_agent_service.py
```

You can also specify parameters directly:

```bash
poetry run python deploy_agent_service.py \
    --subscription-id "your-subscription-id" \
    --resource-group "your-resource-group" \
    --ai-project "your-ai-project" \
    --deployment-name "custom-werewolf-agent" \
    --model-deployment "your-model-deployment"
```

Once deployed, you can find your agent in the Azure AI Studio portal under your project.
