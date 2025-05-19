#!/usr/bin/env python
"""
Deploy the Werewolf game as an Azure AI Foundry Agent Service.

This script deploys the Werewolf game to Azure AI Foundry Agent Service using
the Azure AI SDK. It allows you to specify parameters for the deployment
through command line arguments or environment variables.

Reference: https://learn.microsoft.com/en-us/azure/ai-services/agents/quickstart?pivots=programming-language-python-azure
"""

import os
import argparse
import json
from typing import Dict, List, Any

from azure.ai.resources.client import AIClient
from azure.ai.resources.entities import Function, Action, ActionsOverrides
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Deploy the Werewolf game to Azure AI Foundry Agent Service"
    )
    
    parser.add_argument(
        "--subscription-id",
        type=str,
        help="Azure subscription ID (defaults to AZURE_SUBSCRIPTION_ID env var)"
    )
    
    parser.add_argument(
        "--resource-group",
        type=str,
        help="Azure resource group name (defaults to AZURE_RESOURCE_GROUP env var)"
    )
    
    parser.add_argument(
        "--ai-project",
        type=str,
        help="Azure AI project name (defaults to AZURE_AI_PROJECT env var)",
    )
    
    parser.add_argument(
        "--deployment-name",
        type=str,
        default="werewolf-agent",
        help="Name for the agent service deployment (default: werewolf-agent)"
    )
    
    parser.add_argument(
        "--model-deployment",
        type=str,
        help="Azure OpenAI model deployment name (defaults to MODEL_DEPLOYMENT env var)"
    )
    
    parser.add_argument(
        "--model-name",
        type=str,
        help="Azure OpenAI model name (defaults to MODEL_NAME env var)"
    )
    
    parser.add_argument(
        "--endpoint",
        type=str,
        help="Azure OpenAI endpoint URL (defaults to AZURE_OPENAI_ENDPOINT env var)"
    )
    
    parser.add_argument(
        "--api-version",
        type=str,
        default="2024-10-21",
        help="Azure OpenAI API version (default: 2024-10-21)"
    )
    
    return parser.parse_args()

def get_config_value(args_value, env_var, default=None):
    """Get configuration value from args, environment variable, or default."""
    if args_value is not None:
        return args_value
    return os.getenv(env_var, default)

def create_werewolf_agent_functions() -> List[Function]:
    """Define the functions for the Werewolf game agent."""
    
    # Function to get the player's role
    get_role_function = Function(
        name="get_role",
        description="Get the player's assigned role in the game",
        parameters={
            "type": "object",
            "properties": {
                "player_id": {
                    "type": "integer",
                    "description": "The player ID to get the role for"
                }
            },
            "required": ["player_id"]
        }
    )
    
    # Function to cast a vote during elimination
    cast_vote_function = Function(
        name="cast_vote",
        description="Cast a vote to eliminate a player",
        parameters={
            "type": "object",
            "properties": {
                "player_id": {
                    "type": "integer",
                    "description": "The ID of the player casting the vote"
                },
                "vote_for": {
                    "type": "integer",
                    "description": "The ID of the player being voted for"
                },
                "reason": {
                    "type": "string",
                    "description": "The reason for casting this vote"
                }
            },
            "required": ["player_id", "vote_for", "reason"]
        }
    )
    
    # Function for werewolf night phase actions
    werewolf_action_function = Function(
        name="werewolf_action",
        description="Perform the werewolf night action (eliminate a player)",
        parameters={
            "type": "object",
            "properties": {
                "player_id": {
                    "type": "integer",
                    "description": "The ID of the werewolf player"
                },
                "target_id": {
                    "type": "integer",
                    "description": "The ID of the player to eliminate"
                }
            },
            "required": ["player_id", "target_id"]
        }
    )
    
    # Function for seer night phase actions
    seer_action_function = Function(
        name="seer_action",
        description="Perform the seer night action (check a player's role)",
        parameters={
            "type": "object",
            "properties": {
                "player_id": {
                    "type": "integer",
                    "description": "The ID of the seer player"
                },
                "target_id": {
                    "type": "integer",
                    "description": "The ID of the player to check"
                }
            },
            "required": ["player_id", "target_id"]
        }
    )
    
    return [
        get_role_function,
        cast_vote_function,
        werewolf_action_function,
        seer_action_function
    ]

def create_game_actions() -> List[Action]:
    """Create the actions for the Werewolf game agent."""
    
    # Start a new game action
    start_game_action = Action(
        name="start_game", 
        description="Start a new game of Werewolf"
    )
    
    # End the current day phase and proceed to night
    end_day_phase_action = Action(
        name="end_day_phase",
        description="End the day phase discussion and move to voting"
    )
    
    # End the current night phase and proceed to day
    end_night_phase_action = Action(
        name="end_night_phase",
        description="End the night phase and move to the next day"
    )
    
    return [
        start_game_action,
        end_day_phase_action,
        end_night_phase_action
    ]

def create_agent_definition(args) -> Dict[str, Any]:
    """Create the agent definition for deployment."""
    
    # Create functions and actions
    functions = create_werewolf_agent_functions()
    actions = create_game_actions()
    
    # Define the system instructions for the agent
    system_instructions = """
    You are the host of a Werewolf game. You manage the game flow and enforce the rules.
    
    The game follows these phases:
    1. Game Setup: Assign roles to players
    2. Night Phase: Where werewolves choose a player to eliminate and the seer can check a player's role
    3. Day Phase: All players discuss to identify werewolves
    4. Voting Phase: All players vote to eliminate one player
    5. Repeat until win conditions are met
    
    Win conditions:
    - Villagers win if all werewolves are eliminated
    - Werewolves win if they equal or outnumber the villagers
    
    You must:
    - Maintain the game state and track eliminated players
    - Guide players through each phase
    - Announce the results of night and voting phases
    - Determine when win conditions are met and declare a winner
    - Clearly explain game events without revealing hidden information
    
    You must NOT:
    - Reveal player roles except to the player themselves or when required by game mechanics
    - Take actions on behalf of players
    - Allow eliminated players to participate in discussions or voting
    
    The available roles are:
    - Villager: A regular townsfolk with no special abilities
    - Werewolf: Can eliminate one player during the night phase
    - Seer: Can check one player's role during the night phase
    """
    
    # Create the agent definition
    agent_definition = {
        "systemInstructions": system_instructions,
        "description": "A host for the Werewolf game that manages game flow and enforces the rules",
        "capabilities": {
            "functions": functions,
            "actions": {
                "definitions": actions,
                "overrides": ActionsOverrides(allow_additional_actions=False)
            }
        }
    }
    
    return agent_definition

def deploy_agent(args):
    """Deploy the Werewolf game agent to Azure AI Foundry Agent Service."""
    # Load environment variables
    load_dotenv()
    
    # Get configuration values
    subscription_id = get_config_value(args.subscription_id, "AZURE_SUBSCRIPTION_ID")
    resource_group = get_config_value(args.resource_group, "AZURE_RESOURCE_GROUP")
    ai_project = get_config_value(args.ai_project, "AZURE_AI_PROJECT")
    deployment_name = args.deployment_name
    model_deployment = get_config_value(args.model_deployment, "MODEL_DEPLOYMENT")
    model_name = get_config_value(args.model_name, "MODEL_NAME")
    endpoint = get_config_value(args.endpoint, "AZURE_OPENAI_ENDPOINT")
    api_version = args.api_version
    
    # Validate required config
    required_vars = {
        "subscription_id": subscription_id,
        "resource_group": resource_group,
        "ai_project": ai_project,
        "model_deployment": model_deployment,
        "endpoint": endpoint
    }
    
    missing_vars = [k for k, v in required_vars.items() if v is None]
    if missing_vars:
        raise ValueError(f"Missing required configuration values: {', '.join(missing_vars)}")
    
    # Create Azure AI client
    credential = DefaultAzureCredential()
    ai_client = AIClient(
        subscription_id=subscription_id,
        resource_group_name=resource_group,
        project_name=ai_project,
        credential=credential
    )
    
    print(f"Creating agent definition for '{deployment_name}'...")
    agent_definition = create_agent_definition(args)
    
    # Configuration for the agent deployment
    deployment_config = {
        "model": {
            "source": "AzureOpenAI",
            "sourceName": model_deployment,
            "modelName": model_name,
            "apiVersion": api_version,
            "endpoint": endpoint
        }
    }
    
    print(f"Deploying agent '{deployment_name}' to Azure AI Foundry Agent Service...")
    ai_client.deployments.create_or_update(
        deployment_name=deployment_name,
        deployment=agent_definition,
        configuration=deployment_config
    )
    
    print(f"Successfully deployed agent '{deployment_name}'")
    print(f"Your agent will be available at: {ai_project}/agents/{deployment_name}")

def main():
    """Main function to deploy the agent."""
    args = parse_arguments()
    deploy_agent(args)

if __name__ == "__main__":
    main()