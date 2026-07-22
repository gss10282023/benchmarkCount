# Case Packet

## Case Metadata

- domain: `tau3_retail`
- case_unit_id: `88`
- task_id: `88`

## Source Inventory

- `derived/task.json`
- `official/policy.md`
- `official/split_tasks.json`
- `official/tau2_bench/src/tau2/evaluator/evaluator.py`
- `official/tau2_bench/src/tau2/evaluator/evaluator_env.py`
- `official/tau2_bench/src/tau2/evaluator/evaluator_nl_assertions.py`
- `official/tau2_bench/src/tau2/data_model/tasks.py`
- `official/tau2_bench/src/tau2/domains/retail/data_model.py`
- `derived/evaluator_bundle_manifest.json`
- `derived/artifact_inventory.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/tau3_retail_tasks.json#id=88`

```json
{
  "description": {
    "notes": null,
    "purpose": null,
    "relevant_policies": null
  },
  "evaluation_criteria": {
    "actions": [
      {
        "action_id": "88_0",
        "arguments": {
          "order_id": "#W8835847",
          "reason": "ordered by mistake"
        },
        "info": null,
        "name": "cancel_pending_order"
      }
    ],
    "communicate_info": [],
    "nl_assertions": null,
    "reward_basis": [
      "DB",
      "NL_ASSERTION"
    ]
  },
  "id": "88",
  "initial_state": null,
  "user_scenario": {
    "instructions": {
      "domain": "retail",
      "known_info": "You name is Daiki Silva and your email is daiki.silva6295@example.com.",
      "reason_for_call": "You want to change the book shelf to 4 foot but with the same material and color. If it is not available, cancel the whole order and you will buy again. If the agent asks for the cancellation reason, you say you ordered by mistake.",
      "task_instructions": "You are insecure, creative, direct, relaxing.",
      "unknown_info": null
    },
    "persona": null
  }
}
```

### `official/policy.md`

Source ref: `<REPO_ROOT>/experiments/official_splits/tau3_retail_policy.md`

```markdown
# Retail agent policy

As a retail agent, you can help users:

- **cancel or modify pending orders**
- **return or exchange delivered orders**
- **modify their default user address**
- **provide information about their own profile, orders, and related products**

At the beginning of the conversation, you have to authenticate the user identity by locating their user id via email, or via name + zip code. This has to be done even when the user already provides the user id.

Once the user has been authenticated, you can provide the user with information about order, product, profile information, e.g. help the user look up order id.

You can only help one user per conversation (but you can handle multiple requests from the same user), and must deny any requests for tasks related to any other user.

Before taking any action that updates the database (cancel, modify, return, exchange), you must list the action details and obtain explicit user confirmation (yes) to proceed.

You should not make up any information or knowledge or procedures not provided by the user or the tools, or give subjective recommendations or comments.

You should at most make one tool call at a time, and if you take a tool call, you should not respond to the user at the same time. If you respond to the user, you should not make a tool call at the same time.

You should deny user requests that are against this policy.

You should transfer the user to a human agent if and only if the request cannot be handled within the scope of your actions. To transfer, first make a tool call to transfer_to_human_agents, and then send the message 'YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD ON.' to the user.

## Domain basic

- All times in the database are EST and 24 hour based. For example "02:30:00" means 2:30 AM EST.

### User

Each user has a profile containing:

- unique user id
- email
- default address
- payment methods.

There are three types of payment methods: **gift card**, **paypal account**, **credit card**.

### Product

Our retail store has 50 types of products.

For each **type of product**, there are **variant items** of different **options**.

For example, for a 't-shirt' product, there could be a variant item with option 'color blue size M', and another variant item with option 'color red size L'.

Each product has the following attributes:

- unique product id
- name
- list of variants

Each variant item has the following attributes:

- unique item id
- information about the value of the product options for this item.
- availability
- price

Note: Product ID and Item ID have no relations and should not be confused!

### Order

Each order has the following attributes:

- unique order id
- user id
- address
- items ordered
- status
- fullfilments info (tracking id and item ids)
- payment history

The status of an order can be: **pending**, **processed**, **delivered**, or **cancelled**.

Orders can have other optional attributes based on the actions that have been taken (cancellation reason, which items have been exchanged, what was the exchane price difference etc)

## Generic action rules

Generally, you can only take action on pending or delivered orders.

Exchange or modify order tools can only be called once per order. Be sure that all items to be changed are collected into a list before making the tool call!!!

## Cancel pending order

An order can only be cancelled if its status is 'pending', and you should check its status before taking the action.

The user needs to confirm the order id and the reason (either 'no longer needed' or 'ordered by mistake') for cancellation. Other reasons are not acceptable.

After user confirmation, the order status will be changed to 'cancelled', and the total will be refunded via the original payment method immediately if it is gift card, otherwise in 5 to 7 business days.

## Modify pending order

An order can only be modified if its status is 'pending', and you should check its status before taking the action.

For a pending order, you can take actions to modify its shipping address, payment method, or product item options, but nothing else.

### Modify payment

The user can only choose a single payment method different from the original payment method.

If the user wants the modify the payment method to gift card, it must have enough balance to cover the total amount.

After user confirmation, the order status will be kept as 'pending'. The original payment method will be refunded immediately if it is a gift card, otherwise it will be refunded within 5 to 7 business days.

### Modify items

This action can only be called once, and will change the order status to 'pending (items modifed)'. The agent will not be able to modify or cancel the order anymore. So you must confirm all the details are correct and be cautious before taking this action. In particular, remember to remind the customer to confirm they have provided all the items they want to modify.

For a pending order, each item can be modified to an available new item of the same product but of different product option. There cannot be any change of product types, e.g. modify shirt to shoe.

The user must provide a payment method to pay or receive refund of the price difference. If the user provides a gift card, it must have enough balance to cover the price difference.

## Return delivered order

An order can only be returned if its status is 'delivered', and you should check its status before taking the action.

The user needs to confirm the order id and the list of items to be returned.

The user needs to provide a payment method to receive the refund.

The refund must either go to the original payment method, or an existing gift card.

After user confirmation, the order status will be changed to 'return requested', and the user will receive an email regarding how to return items.

## Exchange delivered order

An order can only be exchanged if its status is 'delivered', and you should check its status before taking the action. In particular, remember to remind the customer to confirm they have provided all items to be exchanged.

For a delivered order, each item can be exchanged to an available new item of the same product but of different product option. There cannot be any change of product types, e.g. modify shirt to shoe.

The user must provide a payment method to pay or receive refund of the price difference. If the user provides a gift card, it must have enough balance to cover the price difference.

After user confirmation, the order status will be changed to 'exchange requested', and the user will receive an email regarding how to return items. There is no need to place a new order.
```

### `official/split_tasks.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/tau3_retail_split_tasks.json`

```json
{
    "train": [
        "0",
        "1",
        "2",
        "3",
        "4",
        "6",
        "7",
        "8",
        "10",
        "11",
        "13",
        "14",
        "15",
        "16",
        "19",
        "20",
        "21",
        "22",
        "23",
        "24",
        "25",
        "28",
        "29",
        "30",
        "31",
        "34",
        "35",
        "37",
        "41",
        "43",
        "44",
        "46",
        "47",
        "48",
        "50",
        "52",
        "54",
        "57",
        "58",
        "59",
        "63",
        "66",
        "67",
        "69",
        "72",
        "73",
        "75",
        "76",
        "78",
        "80",
        "81",
        "82",
        "83",
        "84",
        "85",
        "87",
        "88",
        "89",
        "91",
        "92",
        "93",
        "95",
        "96",
        "98",
        "99",
        "103",
        "104",
        "105",
        "106",
        "107",
        "109",
        "110",
        "112",
        "113"
    ],
    "test": [
        "5",
        "9",
        "12",
        "17",
        "18",
        "26",
        "27",
        "32",
        "33",
        "36",
        "38",
        "39",
        "40",
        "42",
        "45",
        "49",
        "51",
        "53",
        "55",
        "56",
        "60",
        "61",
        "62",
        "64",
        "65",
        "68",
        "70",
        "71",
        "74",
        "77",
        "79",
        "86",
        "90",
        "94",
        "97",
        "100",
        "101",
        "102",
        "108",
        "111"
    ],
    "base": [
        "0",
        "1",
        "2",
        "3",
        "4",
        "6",
        "7",
        "8",
        "10",
        "11",
        "13",
        "14",
        "15",
        "16",
        "19",
        "20",
        "21",
        "22",
        "23",
        "24",
        "25",
        "28",
        "29",
        "30",
        "31",
        "34",
        "35",
        "37",
        "41",
        "43",
        "44",
        "46",
        "47",
        "48",
        "50",
        "52",
        "54",
        "57",
        "58",
        "59",
        "63",
        "66",
        "67",
        "69",
        "72",
        "73",
        "75",
        "76",
        "78",
        "80",
        "81",
        "82",
        "83",
        "84",
        "85",
        "87",
        "88",
        "89",
        "91",
        "92",
        "93",
        "95",
        "96",
        "98",
        "99",
        "103",
        "104",
        "105",
        "106",
        "107",
        "109",
        "110",
        "112",
        "113",
        "5",
        "9",
        "12",
        "17",
        "18",
        "26",
        "27",
        "32",
        "33",
        "36",
        "38",
        "39",
        "40",
        "42",
        "45",
        "49",
        "51",
        "53",
        "55",
        "56",
        "60",
        "61",
        "62",
        "64",
        "65",
        "68",
        "70",
        "71",
        "74",
        "77",
        "79",
        "86",
        "90",
        "94",
        "97",
        "100",
        "101",
        "102",
        "108",
        "111"
    ]
}
```

### `official/tau2_bench/src/tau2/evaluator/evaluator.py`

Source ref: `https://github.com/sierra-research/tau2-bench/blob/2be691669909439cf88dedc13decf94b7664d262/src/tau2/evaluator/evaluator.py`

```python
from enum import Enum
from typing import Optional

from tau2.data_model.simulation import RewardInfo, SimulationRun, TerminationReason
from tau2.data_model.tasks import RewardType, Task
from tau2.environment.toolkit import ToolType, get_tool_types
from tau2.evaluator.evaluator_action import ActionEvaluator, FullDuplexActionEvaluator
from tau2.evaluator.evaluator_communicate import (
    CommunicateEvaluator,
    FullDuplexCommunicateEvaluator,
)
from tau2.evaluator.evaluator_env import (
    EnvironmentEvaluator,
    FullDuplexEnvironmentEvaluator,
)
from tau2.evaluator.evaluator_nl_assertions import (
    FullDuplexNLAssertionsEvaluator,
    NLAssertionsEvaluator,
)
from tau2.orchestrator.modes import CommunicationMode
from tau2.registry import registry


class EvaluationType(str, Enum):
    """
    Specifies which evaluation criteria to apply when scoring a simulation run.

    The evaluation system supports multiple types of checks:
    - **Environment (ENV)**: Validates database state changes and environment assertions.
      Checks if the agent correctly modified the environment (e.g., updated orders,
      changed user records) according to task requirements.
    - **Communicate (COMMUNICATE)**: Evaluates the agent's communication with the user.
      Checks if required information was conveyed or specific phrases were used.
    - **Action (ACTION)**: Validates that the agent called the correct tools/functions
      with the expected arguments during the simulation.
    - **NL Assertions**: Uses natural language assertions evaluated by an LLM to check
      qualitative aspects of the agent's behavior (experimental/WIP).

    Evaluation Types:
    -----------------
    ENV:
        Evaluate only environment criteria (DB checks + env assertions).
        Use when you only care about the final state of the environment.

    COMMUNICATE:
        Evaluate only communication criteria.
        Use when you only care about what the agent said to the user.

    ACTION:
        Evaluate only action criteria.
        Use when you only care about which tools the agent called.

    ALL:
        Evaluate ENV, COMMUNICATE, ACTION, and NL_ASSERTIONS (when in the
        task's `reward_basis`). Only includes each component in the final
        reward if it's part of the task's `reward_basis`. The final reward
        is the product of all applicable component rewards.

    NL_ASSERTIONS:
        Evaluate only natural language assertions (WIP).
        Use for qualitative LLM-judged evaluation criteria.

    ALL_WITH_NL_ASSERTIONS:
        Like ALL, but forces the NL assertions evaluator to run even when
        NL_ASSERTION is not in the task's `reward_basis`. Useful for
        debugging or previewing NL assertion results.

    ALL_IGNORE_BASIS:
        Evaluate ENV, COMMUNICATE, and ACTION, ignoring the task's reward_basis.
        Always multiplies all component rewards together regardless of what
        the task specifies. Useful for comprehensive evaluation or debugging.

    ALL_WITH_NL_ASSERTIONS_IGNORE_BASIS:
        Like ALL_IGNORE_BASIS, but also includes NL_ASSERTIONS (WIP).
        Multiplies all four component rewards together unconditionally.
    """

    ENV = "env"
    COMMUNICATE = "communicate"
    ACTION = "action"
    ALL = "all"
    NL_ASSERTIONS = "nl_assertions"  # WIP
    ALL_WITH_NL_ASSERTIONS = "all_with_nl_assertions"  # WIP
    ALL_IGNORE_BASIS = "all_ignore_basis"
    ALL_WITH_NL_ASSERTIONS_IGNORE_BASIS = "all_with_nl_assertions_ignore_basis"


def evaluate_simulation(
    simulation: SimulationRun,
    task: Task,
    evaluation_type: EvaluationType,
    solo_mode: bool,
    domain: str,
    mode: CommunicationMode = CommunicationMode.HALF_DUPLEX,
    env_kwargs: dict = None,
) -> RewardInfo:
    """
    Evaluate the simulation based on the evaluation type.

    Args:
        simulation: The simulation run to evaluate.
        task: The task specification.
        evaluation_type: The type of evaluation to perform.
        solo_mode: Whether the agent is in solo mode.
        domain: The domain name.
        mode: The communication mode (HALF_DUPLEX or FULL_DUPLEX).
              Defaults to HALF_DUPLEX. In FULL_DUPLEX mode, evaluation uses
              simulation.ticks instead of simulation.messages.

    Returns:
        RewardInfo with the evaluation results.
    """
    if simulation.termination_reason not in {
        TerminationReason.AGENT_STOP,
        TerminationReason.USER_STOP,
    }:
        return RewardInfo(
            reward=0.0,
            reward_basis=None,
            info={
                "note": f"Simulation terminated prematurely. Termination reason: {simulation.termination_reason.value}"
            },
        )
    if task.evaluation_criteria is None:
        return RewardInfo(
            reward=1.0,
            reward_basis=None,
            info={"note": "No evaluation criteria"},
        )
    if env_kwargs is None:
        env_kwargs = {}

    # Select trajectory and evaluators based on mode
    is_full_duplex = mode == CommunicationMode.FULL_DUPLEX
    trajectory = simulation.ticks if is_full_duplex else simulation.messages

    # Select evaluator classes based on mode
    EnvEvaluator = (
        FullDuplexEnvironmentEvaluator if is_full_duplex else EnvironmentEvaluator
    )
    NLEvaluator = (
        FullDuplexNLAssertionsEvaluator if is_full_duplex else NLAssertionsEvaluator
    )
    CommEvaluator = (
        FullDuplexCommunicateEvaluator if is_full_duplex else CommunicateEvaluator
    )
    ActEvaluator = FullDuplexActionEvaluator if is_full_duplex else ActionEvaluator

    # Get tool types from the environment for action evaluation
    tool_types: Optional[dict[str, ToolType]] = None
    try:
        env = registry.get_env_constructor(domain)(solo_mode=solo_mode, **env_kwargs)
        if env.tools is not None:
            tool_types = get_tool_types(env.tools)
        if env.user_tools is not None:
            user_tool_types = get_tool_types(env.user_tools)
            if tool_types is None:
                tool_types = user_tool_types
            else:
                tool_types.update(user_tool_types)
    except Exception:
        # If we can't get tool types, continue without them
        pass

    if evaluation_type == EvaluationType.ENV:
        reward_info = EnvEvaluator.calculate_reward(
            environment_constructor=registry.get_env_constructor(domain),
            task=task,
            full_trajectory=trajectory,
            solo_mode=solo_mode,
            env_kwargs=env_kwargs,
        )
    elif evaluation_type == EvaluationType.NL_ASSERTIONS:
        reward_info = NLEvaluator.calculate_reward(
            task=task,
            full_trajectory=trajectory,
        )
    elif evaluation_type == EvaluationType.COMMUNICATE:
        reward_info = CommEvaluator.calculate_reward(
            task=task,
            full_trajectory=trajectory,
        )
    elif evaluation_type == EvaluationType.ACTION:
        reward_info = ActEvaluator.calculate_reward(
            task=task,
            full_trajectory=trajectory,
            tool_types=tool_types,
        )
    elif evaluation_type in {EvaluationType.ALL, EvaluationType.ALL_WITH_NL_ASSERTIONS}:
        env_reward_info = EnvEvaluator.calculate_reward(
            environment_constructor=registry.get_env_constructor(domain),
            task=task,
            full_trajectory=trajectory,
            solo_mode=solo_mode,
            env_kwargs=env_kwargs,
        )
        action_reward_info = ActEvaluator.calculate_reward(
            task=task,
            full_trajectory=trajectory,
            tool_types=tool_types,
        )
        communicate_reward_info = CommEvaluator.calculate_reward(
            task=task,
            full_trajectory=trajectory,
        )
        nl_reward_info = None
        task_needs_nl = RewardType.NL_ASSERTION in task.evaluation_criteria.reward_basis
        if evaluation_type == EvaluationType.ALL_WITH_NL_ASSERTIONS or task_needs_nl:
            nl_reward_info = NLEvaluator.calculate_reward(
                task=task,
                full_trajectory=trajectory,
            )

        ## Combine all the rewards.
        reward = 1.0
        env_bases = {RewardType.DB, RewardType.ENV_ASSERTION}
        action_bases = {RewardType.ACTION}
        nl_bases = {RewardType.NL_ASSERTION}
        comm_bases = {RewardType.COMMUNICATE}
        task_reward_basis = set(task.evaluation_criteria.reward_basis)

        evaluated_bases = env_bases | action_bases | comm_bases
        if nl_reward_info is not None:
            evaluated_bases |= nl_bases
        unevaluated = task_reward_basis - evaluated_bases
        if unevaluated:
            raise ValueError(
                f"Task reward_basis includes {unevaluated} but these were "
                f"not evaluated. evaluation_type={evaluation_type.value}"
            )

        reward_breakdown = {}
        if task_reward_basis & env_bases:
            if env_reward_info.reward_breakdown is not None:
                reward_breakdown.update(env_reward_info.reward_breakdown)
            reward *= env_reward_info.reward
        if task_reward_basis & action_bases:
            if action_reward_info.reward_breakdown is not None:
                reward_breakdown.update(action_reward_info.reward_breakdown)
            reward *= action_reward_info.reward
        if task_reward_basis & nl_bases:
            if nl_reward_info.reward_breakdown is not None:
                reward_breakdown.update(nl_reward_info.reward_breakdown)
            reward *= nl_reward_info.reward
        if task_reward_basis & comm_bases:
            if communicate_reward_info.reward_breakdown is not None:
                reward_breakdown.update(communicate_reward_info.reward_breakdown)
            reward *= communicate_reward_info.reward

        reward_info = RewardInfo(
            reward=reward,
            db_check=env_reward_info.db_check,
            env_assertions=env_reward_info.env_assertions,
            action_checks=action_reward_info.action_checks,
            nl_assertions=(
                nl_reward_info.nl_assertions if nl_reward_info is not None else None
            ),
            communicate_checks=communicate_reward_info.communicate_checks,
            reward_basis=task.evaluation_criteria.reward_basis,
            reward_breakdown=reward_breakdown,
            info={
                "env": env_reward_info.info,
                "nl": nl_reward_info.info if nl_reward_info is not None else None,
                "communicate": communicate_reward_info.info,
                "action": action_reward_info.info,
            },
        )
    elif evaluation_type in {
        EvaluationType.ALL_IGNORE_BASIS,
        EvaluationType.ALL_WITH_NL_ASSERTIONS_IGNORE_BASIS,
    }:
        env_reward_info = EnvEvaluator.calculate_reward(
            environment_constructor=registry.get_env_constructor(domain),
            task=task,
            full_trajectory=trajectory,
            solo_mode=solo_mode,
            env_kwargs=env_kwargs,
        )
        action_reward_info = ActEvaluator.calculate_reward(
            task=task,
            full_trajectory=trajectory,
            tool_types=tool_types,
        )
        communicate_reward_info = CommEvaluator.calculate_reward(
            task=task,
            full_trajectory=trajectory,
        )
        nl_reward_info = None
        if evaluation_type == EvaluationType.ALL_WITH_NL_ASSERTIONS_IGNORE_BASIS:
            nl_reward_info = NLEvaluator.calculate_reward(
                task=task,
                full_trajectory=trajectory,
            )

        # Combine all rewards regardless of the task's reward_basis
        reward = 1.0
        reward_breakdown = {}

        if env_reward_info.reward_breakdown is not None:
            reward_breakdown.update(env_reward_info.reward_breakdown)
        reward *= env_reward_info.reward

        if action_reward_info.reward_breakdown is not None:
            reward_breakdown.update(action_reward_info.reward_breakdown)
        reward *= action_reward_info.reward

        if communicate_reward_info.reward_breakdown is not None:
            reward_breakdown.update(communicate_reward_info.reward_breakdown)
        reward *= communicate_reward_info.reward

        if nl_reward_info is not None:
            if nl_reward_info.reward_breakdown is not None:
                reward_breakdown.update(nl_reward_info.reward_breakdown)
            reward *= nl_reward_info.reward

        reward_info = RewardInfo(
            reward=reward,
            db_check=env_reward_info.db_check,
            env_assertions=env_reward_info.env_assertions,
            action_checks=action_reward_info.action_checks,
            nl_assertions=(
                nl_reward_info.nl_assertions if nl_reward_info is not None else None
            ),
            communicate_checks=communicate_reward_info.communicate_checks,
            # Reflect that all checks were used
            reward_basis=[
                RewardType.DB,
                RewardType.ENV_ASSERTION,
                RewardType.ACTION,
                RewardType.COMMUNICATE,
                *([RewardType.NL_ASSERTION] if nl_reward_info is not None else []),
            ],
            reward_breakdown=reward_breakdown,
            info={
                "env": env_reward_info.info,
                "nl": nl_reward_info.info if nl_reward_info is not None else None,
                "communicate": communicate_reward_info.info,
                "action": action_reward_info.info,
            },
        )
    else:
        raise ValueError(f"Unknown evaluation type: {evaluation_type}")
    return reward_info
```

### `official/tau2_bench/src/tau2/evaluator/evaluator_env.py`

Source ref: `https://github.com/sierra-research/tau2-bench/blob/2be691669909439cf88dedc13decf94b7664d262/src/tau2/evaluator/evaluator_env.py`

```python
from typing import Callable

from loguru import logger

from tau2.data_model.message import (
    AssistantMessage,
    Message,
    Tick,
    UserMessage,
)
from tau2.data_model.simulation import DBCheck, EnvAssertionCheck, RewardInfo
from tau2.data_model.tasks import RewardType, Task
from tau2.environment.environment import Environment
from tau2.evaluator.evaluator_base import EvaluatorBase


class EnvironmentEvaluator(EvaluatorBase[Message]):
    """
    Evaluator focuses on endstate of the simulation environment.
    """

    @classmethod
    def calculate_reward(
        cls,
        environment_constructor: Callable[[], Environment],
        task: Task,
        full_trajectory: list[
            Message
        ],  # FIXME: It would be better to be able to get only the messages that are after the initial state
        solo_mode: bool = False,
        env_kwargs: dict = None,
    ) -> RewardInfo:
        """
        Calculate the reward for the simulation.
        Args:
            environment_constructor: Callable[[], Environment]
            task: Task
            full_trajectory: list[Message] (Must include the message history from task initial state)
            solo_mode: bool
        Returns:
            RewardInfo
        """
        if task.evaluation_criteria is None:
            return RewardInfo(
                reward=1.0,
                info={"note": "No evaluation criteria"},
            )
        expected_actions = task.evaluation_criteria.actions
        env_assertions = task.evaluation_criteria.env_assertions
        if expected_actions is None and env_assertions is None:
            return RewardInfo(
                reward=1.0,
                db_check=DBCheck(db_match=True, db_reward=1.0),
                info={"note": "No expected actions or env assertions"},
            )

        initialization_data = None
        if (
            task.initial_state is not None
            and task.initial_state.initialization_data is not None
        ):
            initialization_data = task.initial_state.initialization_data

        initialization_actions = None
        if (
            task.initial_state is not None
            and task.initial_state.initialization_actions is not None
        ):
            initialization_actions = task.initial_state.initialization_actions

        message_history = []
        if (
            task.initial_state is not None
            and task.initial_state.message_history is not None
        ):
            message_history = task.initial_state.message_history

        if env_kwargs is None:
            env_kwargs = {}

        predicted_environment = environment_constructor(
            solo_mode=solo_mode, **env_kwargs
        )

        predicted_environment.set_state(
            initialization_data=initialization_data,
            initialization_actions=initialization_actions,
            message_history=list(full_trajectory),
        )

        # Setting up gold environment
        gold_environment = environment_constructor(**env_kwargs)
        gold_environment.set_state(
            initialization_data=initialization_data,
            initialization_actions=initialization_actions,
            message_history=message_history,
        )
        golden_actions = task.evaluation_criteria.actions or []
        for action in golden_actions:
            try:
                gold_environment.make_tool_call(
                    tool_name=action.name,
                    requestor=action.requestor,
                    **action.arguments,
                )
            except Exception as e:
                logger.warning(
                    f"Error in golden actions {action.name}({action.arguments}): {e}"
                )

        # Comparing the environments
        agent_db_hash = gold_environment.get_db_hash()
        user_db_hash = gold_environment.get_user_db_hash()
        predicted_agent_db_hash = predicted_environment.get_db_hash()
        predicted_user_db_hash = predicted_environment.get_user_db_hash()
        agent_db_match = agent_db_hash == predicted_agent_db_hash
        user_db_match = user_db_hash == predicted_user_db_hash
        if agent_db_match and user_db_match:
            db_reward = 1.0
            db_match = True
        else:
            db_reward = 0.0
            db_match = False

        db_check = DBCheck(db_match=db_match, db_reward=db_reward)

        # Run env assertions
        env_assertions = task.evaluation_criteria.env_assertions or []
        env_assertion_checks = []
        env_assertion_reward = 1.0
        for env_assertion in env_assertions:
            success = predicted_environment.run_env_assertion(
                env_assertion,
                raise_assertion_error=False,
            )
            res = EnvAssertionCheck(
                env_assertion=env_assertion,
                met=success,
                reward=1.0 if success else 0.0,
            )
            env_assertion_checks.append(res)
            env_assertion_reward *= res.reward

        reward = 1.0
        reward_breakdown = {}
        if RewardType.DB in task.evaluation_criteria.reward_basis:
            reward_breakdown[RewardType.DB] = db_reward
            reward *= db_reward
        if RewardType.ENV_ASSERTION in task.evaluation_criteria.reward_basis:
            reward_breakdown[RewardType.ENV_ASSERTION] = env_assertion_reward
            reward *= env_assertion_reward

        return RewardInfo(
            reward=reward,
            db_check=db_check,
            env_assertions=env_assertion_checks,
            reward_basis=task.evaluation_criteria.reward_basis,
            reward_breakdown=reward_breakdown,
        )


class FullDuplexEnvironmentEvaluator(EvaluatorBase[Tick]):
    """
    Evaluator focuses on endstate of the simulation environment.
    """

    @classmethod
    def ticks_to_message_history(cls, ticks: list[Tick]) -> list[Message]:
        """
        Convert a list of Ticks to a message history suitable for Environment.set_state().

        The order follows the execution order in FullDuplexOrchestrator:
        - User tool calls are processed before agent tool calls within each tick
        - Each tool call message is followed by its corresponding tool results

        Args:
            ticks: List of Tick objects from full-duplex simulation.

        Returns:
            List of Messages in the format expected by Environment.set_state():
            [UserMessage with tool_calls, ToolMessage results, AssistantMessage with tool_calls, ToolMessage results, ...]
        """
        messages: list[Message] = []

        for tick in ticks:
            # 1. User tool calls first (processed before agent in orchestrator)
            if tick.user_tool_calls:
                user_msg = UserMessage(
                    role="user",
                    content=tick.user_chunk.content if tick.user_chunk else None,
                    tool_calls=tick.user_tool_calls,
                    timestamp=(
                        tick.user_chunk.timestamp if tick.user_chunk else tick.timestamp
                    ),
                    contains_speech=(
                        tick.user_chunk.contains_speech if tick.user_chunk else False
                    ),
                )
                messages.append(user_msg)
                messages.extend(tick.user_tool_results)

            # 2. Agent tool calls second
            if tick.agent_tool_calls:
                agent_msg = AssistantMessage(
                    role="assistant",
                    content=tick.agent_chunk.content if tick.agent_chunk else None,
                    tool_calls=tick.agent_tool_calls,
                    timestamp=(
                        tick.agent_chunk.timestamp
                        if tick.agent_chunk
                        else tick.timestamp
                    ),
                    contains_speech=(
                        tick.agent_chunk.contains_speech if tick.agent_chunk else False
                    ),
                )
                messages.append(agent_msg)
                messages.extend(tick.agent_tool_results)

        return messages

    @classmethod
    def calculate_reward(
        cls,
        environment_constructor: Callable[[], Environment],
        task: Task,
        full_trajectory: list[Tick],
        solo_mode: bool = False,
        env_kwargs: dict = None,
    ) -> RewardInfo:
        """
        Calculate the reward for the simulation.
        Args:
            environment_constructor: Callable[[], Environment]
            task: Task
            full_trajectory: list[Tick]
            solo_mode: bool
            env_kwargs: dict
        Returns:
            RewardInfo
        """
        if env_kwargs is None:
            env_kwargs = {}
        if task.evaluation_criteria is None:
            return RewardInfo(
                reward=1.0,
                info={"note": "No evaluation criteria"},
            )
        expected_actions = task.evaluation_criteria.actions
        env_assertions = task.evaluation_criteria.env_assertions
        if expected_actions is None and env_assertions is None:
            return RewardInfo(
                reward=1.0,
                db_check=DBCheck(db_match=True, db_reward=1.0),
                info={"note": "No expected actions or env assertions"},
            )

        initialization_data = None
        if (
            task.initial_state is not None
            and task.initial_state.initialization_data is not None
        ):
            initialization_data = task.initial_state.initialization_data

        initialization_actions = None
        if (
            task.initial_state is not None
            and task.initial_state.initialization_actions is not None
        ):
            initialization_actions = task.initial_state.initialization_actions

        message_history = []
        if (
            task.initial_state is not None
            and task.initial_state.message_history is not None
        ):
            message_history = task.initial_state.message_history

        # Convert ticks to message history for set_state
        # Note: Audio native does not support task history, so we only use the simulation trajectory
        predicted_message_history = cls.ticks_to_message_history(full_trajectory)

        predicted_environment = environment_constructor(
            solo_mode=solo_mode, **env_kwargs
        )
        predicted_environment.set_state(
            initialization_data=initialization_data,
            initialization_actions=initialization_actions,
            message_history=predicted_message_history,
        )

        # Setting up gold environment
        gold_environment = environment_constructor(**env_kwargs)
        gold_environment.set_state(
            initialization_data=initialization_data,
            initialization_actions=initialization_actions,
            message_history=message_history,
        )
        golden_actions = task.evaluation_criteria.actions or []
        for action in golden_actions:
            try:
                gold_environment.make_tool_call(
                    tool_name=action.name,
                    requestor=action.requestor,
                    **action.arguments,
                )
            except Exception as e:
                logger.warning(
                    f"Error in golden actions {action.name}({action.arguments}): {e}"
                )

        # Comparing the environments
        agent_db_hash = gold_environment.get_db_hash()
        user_db_hash = gold_environment.get_user_db_hash()
        predicted_agent_db_hash = predicted_environment.get_db_hash()
        predicted_user_db_hash = predicted_environment.get_user_db_hash()
        agent_db_match = agent_db_hash == predicted_agent_db_hash
        user_db_match = user_db_hash == predicted_user_db_hash
        if agent_db_match and user_db_match:
            db_reward = 1.0
            db_match = True
        else:
            db_reward = 0.0
            db_match = False

        db_check = DBCheck(db_match=db_match, db_reward=db_reward)

        # Run env assertions
        env_assertions = task.evaluation_criteria.env_assertions or []
        env_assertion_checks = []
        env_assertion_reward = 1.0
        for env_assertion in env_assertions:
            success = predicted_environment.run_env_assertion(
                env_assertion,
                raise_assertion_error=False,
            )
            res = EnvAssertionCheck(
                env_assertion=env_assertion,
                met=success,
                reward=1.0 if success else 0.0,
            )
            env_assertion_checks.append(res)
            env_assertion_reward *= res.reward

        reward = 1.0
        reward_breakdown = {}
        if RewardType.DB in task.evaluation_criteria.reward_basis:
            reward_breakdown[RewardType.DB] = db_reward
            reward *= db_reward
        if RewardType.ENV_ASSERTION in task.evaluation_criteria.reward_basis:
            reward_breakdown[RewardType.ENV_ASSERTION] = env_assertion_reward
            reward *= env_assertion_reward

        return RewardInfo(
            reward=reward,
            db_check=db_check,
            env_assertions=env_assertion_checks,
            reward_basis=task.evaluation_criteria.reward_basis,
            reward_breakdown=reward_breakdown,
        )
```

### `official/tau2_bench/src/tau2/evaluator/evaluator_nl_assertions.py`

Source ref: `https://github.com/sierra-research/tau2-bench/blob/2be691669909439cf88dedc13decf94b7664d262/src/tau2/evaluator/evaluator_nl_assertions.py`

```python
import json

from tau2.agent.base.streaming import (
    LinearizationStrategy,
    ParticipantTick,
    linearize_ticks,
)
from tau2.config import DEFAULT_LLM_NL_ASSERTIONS, DEFAULT_LLM_NL_ASSERTIONS_ARGS
from tau2.data_model.message import Message, SystemMessage, Tick, UserMessage
from tau2.data_model.simulation import NLAssertionCheck, RewardInfo
from tau2.data_model.tasks import RewardType, Task
from tau2.evaluator.evaluator_base import EvaluatorBase
from tau2.utils.llm_utils import generate


class NLAssertionsEvaluator(EvaluatorBase[Message]):
    """
    Judge that evaluates whether a trajectory adheres to all the natural-language assertions.
    """

    @classmethod
    def calculate_reward(
        cls,
        task: Task,
        full_trajectory: list[Message],
    ) -> RewardInfo:
        """
        Calculate the reward for the simulation by using an LLM to evaluate whether the trajectory adheres to all the natural-language assertions
        """
        if task.evaluation_criteria is None:
            return RewardInfo(
                reward=1.0,
                nl_assertions=[],
                info={"note": "No evaluation criteria"},
                reward_breakdown={RewardType.NL_ASSERTION: 1.0},
            )
        nl_assertions = task.evaluation_criteria.nl_assertions
        if not nl_assertions:
            return RewardInfo(
                reward=1.0,
                nl_assertions=[],
                info={"note": "No nl_assertions to evaluate"},
                reward_breakdown={RewardType.NL_ASSERTION: 1.0},
            )

        nl_assertions_checks = cls.evaluate_nl_assertions(
            full_trajectory, nl_assertions
        )

        # Calculate reward: 1 if all expectations are met, 0 otherwise
        all_expectations_met = all(result.met for result in nl_assertions_checks)
        reward = 1.0 if all_expectations_met else 0.0

        return RewardInfo(
            reward=reward,
            nl_assertions=nl_assertions_checks,
            reward_breakdown={RewardType.NL_ASSERTION: reward},
        )

    @classmethod
    def evaluate_nl_assertions(
        cls,
        trajectory: list[Message],
        nl_assertions: list[str],
    ) -> list[NLAssertionCheck]:
        """
        Evaluate whether the trajectory meets each expected outcome.

        Args:
            trajectory: List of messages from the conversation
            nl_assertions: List of natural-language assertions to evaluate

        Returns:
            List of evaluation results for each NL assertion, containing:
            - nl_assertion: The NL assertion being evaluated
            - metExpectation: Boolean indicating if the assertion was met
            - reasoning: Explanation for the evaluation
        """
        trajectory_str = "\n".join(
            [f"{message.role}: {message.content}" for message in trajectory]
        )
        # System prompt similar to the TypeScript implementation
        system_prompt = """
        TASK
        - You will be given a list of expected outcomes and a conversation that was collected during a test case run.
        - The conversation is between an agent and a customer.
        - Your job is to evaluate whether the agent satisfies each of the expected outcomes.
        - Grade each expected outcome individually.

        FORMAT
        - Your response should be a JSON object with the following fields:
        - `reasoning`: a short explanation for your classification
        - `metExpectation`: `true` if the agent satisfies the expected outcomes, `false` otherwise
        - `expectedOutcome`: repeat the expectation from the input that you are grading
        
        Example response structure:
        {
            "results": [
                {
                    "expectedOutcome": "<one of the expected outcomes from the input>",
                    "reasoning": "<reasoning trace>",
                    "metExpectation": <false or true>,
                }
            ]
        }
        """

        user_prompt = f"""
        conversation:
        {trajectory_str}
        
        expectedOutcomes:
        {nl_assertions}
        """

        messages = [
            SystemMessage(role="system", content=system_prompt),
            UserMessage(role="user", content=user_prompt),
        ]

        assistant_message = generate(
            model=DEFAULT_LLM_NL_ASSERTIONS,
            messages=messages,
            call_name="nl_assertions_eval",
            **DEFAULT_LLM_NL_ASSERTIONS_ARGS,
        )
        result_data = json.loads(assistant_message.content)
        return [
            NLAssertionCheck(
                nl_assertion=result["expectedOutcome"],
                met=result["metExpectation"],
                justification=result["reasoning"],
            )
            for result in result_data.get("results", [])
        ]


class FullDuplexNLAssertionsEvaluator(EvaluatorBase[Tick]):
    """
    Judge that evaluates whether a full-duplex trajectory adheres to all the
    natural-language assertions.
    """

    @classmethod
    def ticks_to_message_history(cls, ticks: list[Tick]) -> list[Message]:
        """
        Convert a list of Ticks to a linearized message history suitable for NL evaluation.

        This converts orchestrator Ticks to ParticipantTicks (from the agent's perspective),
        then uses containment-aware linearization to create a sequential message list.
        Only speech content is included (tool calls are ignored for NL evaluation).

        Args:
            ticks: List of Tick objects from full-duplex simulation.

        Returns:
            List of Messages linearized using containment-aware strategy.
        """
        # Convert orchestrator Ticks to ParticipantTicks from agent's perspective
        # self_chunk = agent_chunk, other_chunk = user_chunk
        # We only care about speech content, not tool calls
        participant_ticks: list[ParticipantTick] = []

        for tick in ticks:
            # Only include chunks that have content (not tool calls)
            agent_chunk = tick.agent_chunk
            user_chunk = tick.user_chunk

            # Skip tool call messages - we only want speech content
            if agent_chunk is not None and agent_chunk.is_tool_call():
                agent_chunk = None
            if user_chunk is not None and user_chunk.is_tool_call():
                user_chunk = None

            participant_tick = ParticipantTick(
                tick_id=tick.tick_id,
                timestamp=tick.timestamp,
                self_chunk=agent_chunk,
                other_chunk=user_chunk,
            )
            participant_ticks.append(participant_tick)

        # Linearize using containment-aware strategy
        messages = linearize_ticks(
            participant_ticks,
            strategy=LinearizationStrategy.CONTAINMENT_AWARE,
        )

        return messages

    @classmethod
    def calculate_reward(
        cls,
        task: Task,
        full_trajectory: list[Tick],
    ) -> RewardInfo:
        """
        Calculate the reward for the simulation by using an LLM to evaluate whether
        the trajectory adheres to all the natural-language assertions.
        """
        if task.evaluation_criteria is None:
            return RewardInfo(
                reward=1.0,
                nl_assertions=[],
                info={"note": "No evaluation criteria"},
                reward_breakdown={RewardType.NL_ASSERTION: 1.0},
            )
        nl_assertions = task.evaluation_criteria.nl_assertions
        if not nl_assertions:
            return RewardInfo(
                reward=1.0,
                nl_assertions=[],
                info={"note": "No nl_assertions to evaluate"},
                reward_breakdown={RewardType.NL_ASSERTION: 1.0},
            )

        # Convert ticks to linearized message history
        messages = cls.ticks_to_message_history(full_trajectory)

        nl_assertions_checks = cls.evaluate_nl_assertions(messages, nl_assertions)

        # Calculate reward: 1 if all expectations are met, 0 otherwise
        all_expectations_met = all(result.met for result in nl_assertions_checks)
        reward = 1.0 if all_expectations_met else 0.0

        return RewardInfo(
            reward=reward,
            nl_assertions=nl_assertions_checks,
            reward_breakdown={RewardType.NL_ASSERTION: reward},
        )

    @classmethod
    def evaluate_nl_assertions(
        cls,
        trajectory: list[Message],
        nl_assertions: list[str],
    ) -> list[NLAssertionCheck]:
        """
        Evaluate whether the trajectory meets each expected outcome.

        Delegates to NLAssertionsEvaluator.evaluate_nl_assertions.
        """
        return NLAssertionsEvaluator.evaluate_nl_assertions(trajectory, nl_assertions)
```

### `official/tau2_bench/src/tau2/data_model/tasks.py`

Source ref: `https://github.com/sierra-research/tau2-bench/blob/2be691669909439cf88dedc13decf94b7664d262/src/tau2/data_model/tasks.py`

```python
# Copyright Sierra

import json
import textwrap
import uuid
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from typing_extensions import Annotated

from tau2.data_model.message import Message, ToolCall, ToolRequestor


class StructuredUserInstructions(BaseModel):
    """
    User instructions. This information defines the specific situation the user is in and the tasks they are trying to complete.
    """

    domain: Annotated[str, Field(description="The domain of the task.")]
    reason_for_call: Annotated[
        str, Field(description="The reason for the user to call the agent.")
    ]
    known_info: Annotated[
        Optional[str],
        Field(description="Known information about the user.", default=None),
    ]
    unknown_info: Annotated[
        Optional[str],
        Field(description="Unknown information about the user.", default=None),
    ]
    task_instructions: Annotated[str, Field(description="Instructions for the User.")]

    def __str__(self) -> str:
        lines = []
        tab = "\t"
        lines.append(f"Domain: {self.domain}")
        lines.append(f"Reason for call:\n{textwrap.indent(self.reason_for_call, tab)}")
        if self.known_info is not None:
            lines.append(f"Known info:\n{textwrap.indent(self.known_info, tab)}")
        if self.unknown_info is not None:
            lines.append(f"Unknown info:\n{textwrap.indent(self.unknown_info, tab)}")
        lines.append(
            f"Task instructions:\n{textwrap.indent(self.task_instructions, tab)}"
        )
        return "\n".join(lines)


UserInstructions = StructuredUserInstructions | str


class UserScenario(BaseModel):
    """
    User scenario. All the information that will be sent to the user simulator.
    """

    persona: Annotated[
        Optional[str],
        Field(
            description="User's persona. This information defines the user in general, not the specific situation they are in.",
            default=None,
        ),
    ]
    instructions: Annotated[
        UserInstructions,
        Field(
            description="Instructions for the User. This information defines the specific situation the user is in and the tasks they are trying to complete."
        ),
    ]

    def __str__(self) -> str:
        lines = []
        if self.persona is not None:
            lines.append("Persona:")
            lines.append(textwrap.indent(self.persona, "\t"))
        lines.append("Instructions:")
        lines.append(textwrap.indent(str(self.instructions), "\t"))
        return "\n".join(lines)


class Description(BaseModel):
    """
    Description of a scenario. This can be sent to the evaluator.
    """

    purpose: Annotated[
        Optional[str],
        Field(description="Explains what the scenario is testing.", default=None),
    ]
    relevant_policies: Annotated[
        Optional[str],
        Field(
            description="The part of the policy that is relevant to the scenario.",
            default=None,
        ),
    ]
    notes: Annotated[
        Optional[str],
        Field(
            description="Any additional information about the scenario that is not covered by the other fields.",
            default=None,
        ),
    ]

    def __str__(self) -> str:
        lines = []
        if self.purpose is not None:
            lines.append(f"Purpose: {self.purpose}")
        if self.relevant_policies is not None:
            lines.append(f"Relevant Policies: {self.relevant_policies}")
        if self.notes is not None:
            lines.append(f"Notes: {self.notes}")
        return "\n".join(lines)


class Action(BaseModel):
    """
    An Agent/User action.
    Example:
      {
      "action_id": "get_user_details_1",
      "requestor": "assistant",
      "name": "get_user_details",
      "arguments": { "user_id": "sophia_silva_7557", "note": "I need to get the user details for user_id: sophia_silva_7557" },
      "compare_args": ["user_id"]
    },
    A tool call can be compared with an action by comparing the arguments in compare_args.
    If compare_args is None, will check all the arguments.
    """

    action_id: str = Field(
        description="The unique identifier for the action within a scenario."
    )
    requestor: ToolRequestor = Field(
        description="The requestor of the action.",
        default="assistant",
    )
    name: str = Field(description="The name of the action.")
    arguments: dict = Field(description="The arguments for the action.")
    info: Optional[str] = Field(
        description="Information about the action.", default=None
    )
    compare_args: Optional[list[str]] = Field(
        description="The arguments to check in tool call. If None, will check all the arguments.",
        default=None,
    )

    def __str__(self) -> str:
        lines = []
        lines.append(f"Action ID: {self.action_id}")
        lines.append(f"Requestor: {self.requestor}")
        lines.append(f"Name: {self.name}")
        lines.append(f"Arguments:\n{json.dumps(self.arguments, indent=2)}")
        if self.info is not None:
            lines.append(f"Info:\n{textwrap.indent(self.info, '    ')}")
        return "\n".join(lines)

    def get_func_format(self) -> str:
        """
        Get the function format of the action.
        """
        return (
            f"{self.name}({', '.join([f'{k}={v}' for k, v in self.arguments.items()])})"
        )

    def compare_with_tool_call(self, tool_call: ToolCall) -> bool:
        """
        Compare the action with a tool call.
        If the name is not the same, return False.
        If compare_args is None, will check all the arguments.
        Otherwise, will check only the arguments in compare_args.
        """
        if self.name != tool_call.name:
            return False
        if self.compare_args is None:
            compare_args = tool_call.arguments.keys()
        else:
            compare_args = self.compare_args
        if len(compare_args) == 0:
            return True
        tool_args = {k: v for k, v in tool_call.arguments.items() if k in compare_args}
        action_args = {k: v for k, v in self.arguments.items() if k in compare_args}
        return tool_args == action_args


class EnvFunctionCall(BaseModel):
    """
    A function call on the agent or user environment.
    """

    env_type: Annotated[
        ToolRequestor,
        Field(description="The type of environment to call the function on."),
    ]
    func_name: Annotated[str, Field(description="The name of the function to call.")]
    arguments: Annotated[
        dict, Field(description="The arguments to pass to the function.")
    ]

    def __str__(self) -> str:
        lines = []
        lines.append(f"Env Type: {self.env_type}")
        lines.append(f"Func Name: {self.func_name}")
        lines.append(f"Arguments:\n{json.dumps(self.arguments, indent=2)}")
        return "\n".join(lines)


class EnvAssertion(EnvFunctionCall):
    """
    An assertion on the agent or user environment.
    """

    assert_value: Annotated[
        bool, Field(default=True, description="The value to assert on.")
    ]
    message: Annotated[
        Optional[str],
        Field(
            description="A message to display to the user if the assertion fails.",
            default=None,
        ),
    ]


class RewardType(str, Enum):
    DB = "DB"
    ENV_ASSERTION = "ENV_ASSERTION"
    NL_ASSERTION = "NL_ASSERTION"
    ACTION = "ACTION"
    COMMUNICATE = "COMMUNICATE"


class TaskIssueStatus(str, Enum):
    """Status of a task issue."""

    OPEN = "open"
    RESOLVED = "resolved"
    WONT_FIX = "wont_fix"


class TaskIssue(BaseModel):
    """
    An issue or discussion point about a task.
    Used to track potential problems, decisions made, and their resolutions.
    """

    id: str = Field(description="Unique identifier for the issue.")
    title: str = Field(description="Short summary of the issue.")
    description: Annotated[
        Optional[str],
        Field(
            description="Detailed description of the issue or discussion point.",
            default=None,
        ),
    ]
    status: Annotated[
        TaskIssueStatus,
        Field(
            description="Current status of the issue.",
            default=TaskIssueStatus.OPEN,
        ),
    ]
    resolution: Annotated[
        Optional[str],
        Field(
            description="Explanation of how/why the issue was resolved or won't be fixed.",
            default=None,
        ),
    ]
    created_at: Annotated[
        Optional[str],
        Field(
            description="ISO date (YYYY-MM-DD) when the issue was created.",
            default=None,
        ),
    ]
    resolved_at: Annotated[
        Optional[str],
        Field(
            description="ISO date (YYYY-MM-DD) when the issue was resolved.",
            default=None,
        ),
    ]
    author_email: Annotated[
        Optional[str],
        Field(
            description="Email of the person who raised this issue.",
            default=None,
        ),
    ]
    pr_link: Annotated[
        Optional[str],
        Field(
            description="Link to the PR that fixes this issue.",
            default=None,
        ),
    ]
    simulation_file: Annotated[
        Optional[str],
        Field(
            description="Relative path to a simulation result file demonstrating the issue (e.g., 'task_issues/task_0_issue_001.json').",
            default=None,
        ),
    ]

    def __str__(self) -> str:
        lines = []
        status_icon = {"open": "🔴", "resolved": "✅", "wont_fix": "⚪"}.get(
            self.status.value, ""
        )
        lines.append(f"{status_icon} [{self.id}] {self.title}")
        if self.description:
            lines.append(f"  Description: {self.description}")
        if self.resolution:
            lines.append(f"  Resolution: {self.resolution}")
        if self.created_at:
            lines.append(f"  Created: {self.created_at}")
        if self.resolved_at:
            lines.append(f"  Resolved: {self.resolved_at}")
        if self.author_email:
            lines.append(f"  Author: {self.author_email}")
        if self.pr_link:
            lines.append(f"  PR: {self.pr_link}")
        if self.simulation_file:
            lines.append(f"  Simulation: {self.simulation_file}")
        return "\n".join(lines)


class EvaluationCriteria(BaseModel):
    """
    Evaluation criteria for a particular task. This will be sent to the evaluator.
    """

    actions: Annotated[
        Optional[list[Action]],
        Field(
            description="The actions that the agent should take to complete the task.",
            default=None,
        ),
    ]

    env_assertions: Annotated[
        Optional[list[EnvAssertion]],
        Field(
            description="List of assertions on the agent or user environment.",
            default=None,
        ),
    ]

    communicate_info: Annotated[  # TODO: Deprecate this
        Optional[list[str]],
        Field(
            description="List of information that the agent should communicate to the user.",
            default=None,
        ),
    ]

    nl_assertions: Annotated[
        Optional[list[str]],
        Field(
            description="List of assertions for the task, in natural language.",
            default=None,
        ),
    ]

    reward_basis: Annotated[
        list[RewardType],
        Field(
            description="The basis of the reward. This will be used to determine the reward for the task.",
            default_factory=lambda: [RewardType.DB, RewardType.COMMUNICATE],
        ),
    ]

    def __str__(self) -> str:
        lines = []
        if self.actions is not None:
            lines.append("Actions:")
            lines.extend(
                [textwrap.indent(str(action), "\t") for action in self.actions]
            )
        if self.env_assertions is not None:
            lines.append("Env Assertions:")
            lines.extend(
                [
                    textwrap.indent(str(assertion), "\t")
                    for assertion in self.env_assertions
                ]
            )
        if self.communicate_info is not None:
            lines.append("Communicate Info:")
            lines.extend(
                [textwrap.indent(info, "\t") for info in self.communicate_info]
            )
        if self.nl_assertions is not None:
            lines.append("NL Assertions:")
            lines.extend(
                [textwrap.indent(assertion, "\t") for assertion in self.nl_assertions]
            )
        return "\n".join(lines)

    def info(self) -> dict:
        num_agent_actions = (
            len([action for action in self.actions if action.requestor == "assistant"])
            if self.actions is not None
            else 0
        )
        num_user_actions = (
            len([action for action in self.actions if action.requestor == "user"])
            if self.actions is not None
            else 0
        )
        num_env_assertions = (
            len(self.env_assertions) if self.env_assertions is not None else 0
        )
        num_nl_assertions = (
            len(self.nl_assertions) if self.nl_assertions is not None else 0
        )
        return {
            "num_agent_actions": num_agent_actions,
            "num_user_actions": num_user_actions,
            "num_env_assertions": num_env_assertions,
            "num_nl_assertions": num_nl_assertions,
        }


class InitializationData(BaseModel):
    """
    Updates default data for the agent and the user.
    """

    agent_data: Annotated[
        Optional[dict],
        Field(description="Agent env update data.", default=None),
    ]
    user_data: Annotated[
        Optional[dict],
        Field(description="User env update data.", default=None),
    ]


class InitialState(BaseModel):
    """
    Initial state of the task.
    This will be used to set the initial state of the environment and of the orchestrator.
    """

    initialization_data: Annotated[
        Optional[InitializationData],
        Field(description="Initial env update data.", default=None),
    ]
    initialization_actions: Annotated[
        Optional[list[EnvFunctionCall]],
        Field(
            description="Initial actions to be taken on the environment.", default=None
        ),
    ]
    message_history: Annotated[
        Optional[list[Message]],
        Field(
            default=None,
            description="Messages that have already been exchanged between the user, the agent and the environment. This will be used to set the initial state of the environment and of the orchestrator. Last messages must be from the user or the agent.",
        ),
    ]

    def __str__(self) -> str:
        lines = []
        if self.initialization_data is not None:
            lines.append("Initialization Data:")
            lines.extend(
                [
                    textwrap.indent(
                        self.initialization_data.model_dump_json(indent=2), "\t"
                    )
                ]
            )
        if self.initialization_actions is not None:
            lines.append("Initialization Actions:")
            lines.extend(
                [
                    textwrap.indent(str(action), "\t")
                    for action in self.initialization_actions
                ]
            )
        if self.message_history is not None:
            lines.append("Message History:")
            lines.extend(
                [
                    textwrap.indent(str(message), "\t")
                    for message in self.message_history
                ]
            )
        return "\n".join(lines)


class Task(BaseModel):
    """
    A task for a particular domain. This will be sent to the user simulator, the environment and the evaluator.
    """

    id: str = Field(description="The unique identifier for the task.")
    description: Annotated[
        Optional[Description],
        Field(
            description="Description of the task. This can be sent to the evaluator.",
            default=None,
        ),
    ]
    user_scenario: Annotated[
        UserScenario,
        Field(
            description="User scenario. This information will be sent to the user simulator."
        ),
    ]
    ticket: Annotated[
        Optional[str],
        Field(
            description="Task in ticket format for solo agent solving.",
            default=None,
        ),
    ]
    initial_state: Annotated[
        Optional[InitialState],
        Field(
            description="Initial state of the task. This will be used to set the initial state of the environment and of the orchestrator.",
            default=None,
        ),
    ]
    evaluation_criteria: Annotated[
        Optional[EvaluationCriteria],
        Field(
            description="Evaluation criteria for the task. This will be sent to the evaluator.",
            default=None,
        ),
    ]
    issues: Annotated[
        Optional[list[TaskIssue]],
        Field(
            description="List of issues, discussions, or notes about this task.",
            default=None,
        ),
    ]
    required_documents: Annotated[
        Optional[list[str]],
        Field(
            description="List of document titles required to solve the task (knowledge domain).",
            default=None,
        ),
    ]
    user_tools: Annotated[
        Optional[list[str]],
        Field(
            description="List of user tool names available to the user simulator for this task. "
            "If None, all domain user tools are available (backward compatible). "
            "If empty list, no user tools are available.",
            default=None,
        ),
    ]

    def __str__(self) -> str:
        lines = []
        lines.append(f"ID: {self.id}")
        if self.description is not None:
            lines.append("Description:")
            lines.append(textwrap.indent(str(self.description), "\t"))
        lines.append("User Scenario:")
        lines.append(textwrap.indent(str(self.user_scenario), "\t"))
        if self.initial_state is not None:
            lines.append("Initial State:")
            lines.append(textwrap.indent(str(self.initial_state), "\t"))
        if self.evaluation_criteria is not None:
            lines.append("Evaluation Criteria:")
            lines.append(textwrap.indent(str(self.evaluation_criteria), "\t"))
        if self.issues is not None and len(self.issues) > 0:
            lines.append("Issues:")
            lines.extend([textwrap.indent(str(issue), "\t") for issue in self.issues])
        return "\n".join(lines)


def make_task_id() -> str:
    """
    Make a task id.
    """
    return str(uuid.uuid4())


def make_task(
    user_instructions: str,
    eval_criteria: EvaluationCriteria,
    initialization_data: Optional[InitializationData] = None,
    initialization_actions: Optional[list[EnvFunctionCall]] = None,
    message_history: Optional[list[Message]] = None,
) -> Task:
    """
    Make a task from a user instruction, an evaluation criteria and a message history.
    """

    user_scenario = UserScenario(instructions=user_instructions)
    evaluation_criteria = eval_criteria
    initial_state = None
    if message_history is not None:
        # Patch to consider empty list of tool calls as None.
        for message in message_history:
            if (
                message.role == "assistant"
                and isinstance(message.tool_calls, list)
                and len(message.tool_calls) == 0
            ):
                message.tool_calls = None

        initial_state = InitialState(
            initialization_data=initialization_data,
            initialization_actions=initialization_actions,
            message_history=message_history,
        )
    return Task(
        id=make_task_id(),
        user_scenario=user_scenario,
        evaluation_criteria=evaluation_criteria,
        initial_state=initial_state,
    )
```

### `official/tau2_bench/src/tau2/domains/retail/data_model.py`

Source ref: `https://github.com/sierra-research/tau2-bench/blob/2be691669909439cf88dedc13decf94b7664d262/src/tau2/domains/retail/data_model.py`

```python
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field

from tau2.domains.retail.utils import RETAIL_DB_PATH
from tau2.environment.db import DB


class Variant(BaseModel):
    """Represents a specific variant of a product with its options, availability and price"""

    item_id: str = Field(description="Unique identifier for the variant")
    options: Dict[str, str] = Field(
        description="Dictionary of option names to values (e.g. {'color': 'blue', 'size': 'large'})"
    )
    available: bool = Field(description="Whether this variant is currently in stock")
    price: float = Field(description="Price of this variant")


class Product(BaseModel):
    """Represents a product with its variants"""

    name: str = Field(description="Name of the product")
    product_id: str = Field(description="Unique identifier for the product")
    variants: Dict[str, Variant] = Field(
        description="Dictionary of variants indexed by variant ID"
    )


class UserName(BaseModel):
    """Represents a user's full name"""

    first_name: str = Field(description="User's first name")
    last_name: str = Field(description="User's last name")


class UserAddress(BaseModel):
    """Represents a physical address"""

    address1: str = Field(description="Primary address line")
    address2: str = Field(description="Secondary address line")
    city: str = Field(description="City name")
    country: str = Field(description="Country name")
    state: str = Field(description="State or province name")
    zip: str = Field(description="Postal code")


class PaymentMethodBase(BaseModel):
    source: str = Field(description="Type of payment method")
    id: str = Field(description="Unique identifier for the payment method")


class CreditCard(PaymentMethodBase):
    source: Literal["credit_card"] = Field(
        description="Indicates this is a credit card payment method"
    )
    brand: str = Field(description="Credit card brand (e.g., visa, mastercard)")
    last_four: str = Field(description="Last four digits of the credit card")


class Paypal(PaymentMethodBase):
    source: Literal["paypal"] = Field(
        description="Indicates this is a paypal payment method"
    )


class GiftCard(PaymentMethodBase):
    source: Literal["gift_card"] = Field(
        description="Indicates this is a gift card payment method"
    )
    balance: float = Field(description="Gift card value amount")
    id: str = Field(description="Unique identifier for the gift card")


PaymentMethod = Union[CreditCard, GiftCard, Paypal]


class User(BaseModel):
    """Represents a user with their personal information, payment methods and order history"""

    user_id: str = Field(description="Unique identifier for the user")
    name: UserName = Field(description="User's full name")
    address: UserAddress = Field(description="User's primary address")
    email: str = Field(description="User's email address")
    payment_methods: Dict[str, PaymentMethod] = Field(
        description="Dictionary of payment methods indexed by payment method ID"
    )
    orders: List[str] = Field(description="List of order IDs associated with this user")


class OrderFullfilment(BaseModel):
    """Represents the fulfillment details for items in an order"""

    tracking_id: list[str] = Field(description="List of tracking IDs for shipments")
    item_ids: list[str] = Field(
        description="List of item IDs included in this fulfillment"
    )


class OrderItem(BaseModel):
    """Represents an item in an order"""

    name: str = Field(description="Name of the product")
    product_id: str = Field(description="ID of the product")
    item_id: str = Field(description="ID of the specific variant")
    price: float = Field(description="Price of the item at time of purchase")
    options: Dict[str, str] = Field(description="Options selected for this item")


OrderPaymentType = Literal["payment", "refund"]


class OrderPayment(BaseModel):
    """Represents a payment or refund transaction for an order"""

    transaction_type: OrderPaymentType = Field(
        description="Type of transaction (payment or refund)"
    )
    amount: float = Field(description="Amount of the transaction")
    payment_method_id: str = Field(description="ID of the payment method used")


OrderStatus = Literal[
    "processed",
    "pending",
    "pending (item modified)",
    "delivered",
    "cancelled",
    "exchange requested",
    "return requested",
]

CancelReason = Literal["no longer needed", "ordered by mistake"]


class BaseOrder(BaseModel):
    """Represents an order with its items, status, fulfillment and payment details"""

    order_id: str = Field(description="Unique identifier for the order")
    user_id: str = Field(description="Unique identifier for the user")
    address: UserAddress = Field(description="Address of the user")
    items: List[OrderItem] = Field(description="Items in the order")
    status: OrderStatus = Field(description="Status of the order")
    fulfillments: List[OrderFullfilment] = Field(
        description="Fulfillments of the order"
    )
    payment_history: List[OrderPayment] = Field(description="Payments of the order")
    cancel_reason: Optional[CancelReason] = Field(
        description="Reason for cancelling the order. Can'no longer needed' or 'ordered by mistake'",
        default=None,
    )
    exchange_items: Optional[List[str]] = Field(
        description="Items to be exchanged", default=None
    )
    exchange_new_items: Optional[List[str]] = Field(
        description="Items exchanged for", default=None
    )
    exchange_payment_method_id: Optional[str] = Field(
        description="Payment method ID for the exchange", default=None
    )
    exchange_price_difference: Optional[float] = Field(
        description="Price difference for the exchange", default=None
    )
    return_items: Optional[List[str]] = Field(
        description="Items to be returned", default=None
    )
    return_payment_method_id: Optional[str] = Field(
        description="Payment method ID for the return", default=None
    )


class Order(BaseModel):
    """Represents an order with its items, status, fulfillment and payment details"""

    order_id: str = Field(description="Unique identifier for the order")
    user_id: str = Field(description="Unique identifier for the user")
    address: UserAddress = Field(description="Address of the user")
    items: List[OrderItem] = Field(description="Items in the order")
    status: OrderStatus = Field(description="Status of the order")
    fulfillments: List[OrderFullfilment] = Field(
        description="Fulfillments of the order"
    )
    payment_history: List[OrderPayment] = Field(description="Payments of the order")
    cancel_reason: Optional[CancelReason] = Field(
        description="Reason for cancelling the order. Should be 'no longer needed' or 'ordered by mistake'",
        default=None,
    )
    exchange_items: Optional[List[str]] = Field(
        description="Items to be exchanged", default=None
    )
    exchange_new_items: Optional[List[str]] = Field(
        description="Items exchanged for", default=None
    )
    exchange_payment_method_id: Optional[str] = Field(
        description="Payment method ID for the exchange", default=None
    )
    exchange_price_difference: Optional[float] = Field(
        description="Price difference for the exchange", default=None
    )
    return_items: Optional[List[str]] = Field(
        description="Items to be returned", default=None
    )
    return_payment_method_id: Optional[str] = Field(
        description="Payment method ID for the return", default=None
    )


class RetailDB(DB):
    """Database containing all retail-related data including products, users and orders"""

    products: Dict[str, Product] = Field(
        description="Dictionary of all products indexed by product ID"
    )
    users: Dict[str, User] = Field(
        description="Dictionary of all users indexed by user ID"
    )
    orders: Dict[str, Order] = Field(
        description="Dictionary of all orders indexed by order ID"
    )

    def get_statistics(self) -> dict[str, Any]:
        """Get the statistics of the database."""
        num_products = len(self.products)
        num_users = len(self.users)
        num_orders = len(self.orders)
        total_num_items = sum(
            len(product.variants) for product in self.products.values()
        )
        return {
            "num_products": num_products,
            "num_users": num_users,
            "num_orders": num_orders,
            "total_num_items": total_num_items,
        }


def get_db():
    return RetailDB.load(RETAIL_DB_PATH)


if __name__ == "__main__":
    db = get_db()
    print(db.get_statistics())
```

### `derived/evaluator_bundle_manifest.json`

Source ref: `experiments/official_splits/tau2_bench_2be691669909439cf88dedc13decf94b7664d262/bundle_manifest.json`

```json
{
  "benchmark": "tau2-bench",
  "files": [
    {
      "path": "src/tau2/evaluator/evaluator.py",
      "sha256": "85a05cf75f19708bf855ac8f97cf34d8aef05c99332d57dc066725200ca59444"
    },
    {
      "path": "src/tau2/evaluator/evaluator_env.py",
      "sha256": "e932ea5f675d7a172557350f30b73d66474659d9b4d976ecd763ca2929017633"
    },
    {
      "path": "src/tau2/evaluator/evaluator_nl_assertions.py",
      "sha256": "cb6b3758cdceb02a726732b4ee1af618affcc08f8ab84b44f060146b8f3ad90a"
    },
    {
      "path": "src/tau2/data_model/tasks.py",
      "sha256": "a2feb565a5420223f96d565f05be546970e09aac82919a69301250c8f1883eb1"
    },
    {
      "path": "src/tau2/domains/retail/data_model.py",
      "sha256": "f5ad09590953855cc49d2ab2ad5c0594be408cae74d1500fb278e5a6bf2c50d6"
    }
  ],
  "git_commit": "2be691669909439cf88dedc13decf94b7664d262",
  "repository": "https://github.com/sierra-research/tau2-bench",
  "schema_version": "tau3_released_evaluator_source_bundle.v1"
}
```

### `derived/artifact_inventory.json`

Source ref: `experiments/evidence_contracts/artifact_inventories/tau3_retail_artifact_inventory.v1.json`

```json
{
  "artifact_classes": [
    {
      "authoritativeness": "released native evaluator output",
      "contents": [
        "released scalar reward",
        "reward_basis",
        "db_check.db_match and db_check.db_reward",
        "nl_assertions and their per-assertion judgments",
        "action_checks",
        "reward_breakdown",
        "termination_reason",
        "messages and ticks"
      ],
      "limitations": [
        "The released scalar label must be retained separately from the later evidence judgment.",
        "Action checks affect the native reward only when ACTION is present in reward_basis."
      ],
      "container_path": "simulations[*]",
      "selection_rule": "Select the unique simulations[*] entry whose task_id equals the case task_id. If no unique case-matching entry can be attributed to the scored run, native evidence is undecided rather than success or failure.",
      "field_paths": {
        "termination_reason": "simulations[*].termination_reason",
        "reward": "simulations[*].reward_info.reward",
        "reward_basis": "simulations[*].reward_info.reward_basis",
        "db_check": "simulations[*].reward_info.db_check",
        "nl_assertions": "simulations[*].reward_info.nl_assertions",
        "action_checks": "simulations[*].reward_info.action_checks",
        "reward_breakdown": "simulations[*].reward_info.reward_breakdown",
        "messages": "simulations[*].messages",
        "ticks": "simulations[*].ticks"
      },
      "serialized_values": {
        "normal_termination": [
          "agent_stop",
          "user_stop"
        ],
        "note": "These are the retained JSON string forms of TerminationReason.AGENT_STOP and TerminationReason.USER_STOP. Other retained termination_reason values do not pass the released evaluator's normal-termination gate."
      },
      "path_pattern": "adapter/native_run/results.json",
      "type": "native_evaluator_output"
    },
    {
      "authoritativeness": "artifact provenance and integrity metadata",
      "contents": [
        "artifact paths and types",
        "per-file sha256",
        "producer and evaluator metadata",
        "source-bundle and environment hashes"
      ],
      "limitations": [
        "The manifest describes evidence objects; it does not itself prove the task outcome."
      ],
      "path_pattern": "adapter/artifact_manifest.json",
      "type": "artifact_manifest"
    },
    {
      "authoritativeness": "official-runner conversation and tool record",
      "contents": [
        "conversation messages",
        "tool calls",
        "tool results",
        "runner logs"
      ],
      "limitations": [
        "Tool-returned entity views are partial observations and do not by themselves prove equality of the complete agent and user databases."
      ],
      "path_pattern": "adapter/native_run/artifacts/task_<task_id>/sim_<simulation_id>/task.log",
      "type": "tool_log"
    },
    {
      "authoritativeness": "simulation-selection status only",
      "contents": [
        "simulation status"
      ],
      "limitations": [
        "This file contains a status field only and is not a database snapshot."
      ],
      "path_pattern": "adapter/native_run/artifacts/task_<task_id>/sim_<simulation_id>/sim_status.json",
      "type": "post_state_status"
    },
    {
      "authoritativeness": "retained model/evaluator trace",
      "contents": [
        "agent response traces",
        "user-simulator response traces",
        "NL-assertion evaluator traces when produced"
      ],
      "limitations": [
        "A trace can support message, action, and evaluator-input claims, but it does not replace a missing full-database comparison."
      ],
      "path_pattern": "adapter/native_run/artifacts/task_<task_id>/sim_<simulation_id>/llm_debug/*.json",
      "type": "trace"
    },
    {
      "authoritativeness": "run configuration metadata",
      "contents": [
        "benchmark configuration hash",
        "job and machine identifiers",
        "runner workdir"
      ],
      "limitations": [
        "Configuration metadata is provenance, not outcome evidence."
      ],
      "path_pattern": "adapter/environment.json",
      "type": "environment_metadata"
    }
  ],
  "benchmark": "tau3_retail",
  "freeze_rule": "This inventory describes available evidence classes and their limitations without including any agent outcome, released reward value, or case-level evaluator result.",
  "frozen_before_evidence_scoring": true,
  "native_db_evidence_rule": "Native DB success is established by the released evaluator's complete predicted-agent-DB and predicted-user-DB hash comparison against the gold environment after replay of all reference actions. Partial entity observations alone are insufficient.",
  "run_namespace": "tau3-retail-remaining14-vps-20260716",
  "schema_version": "tau3_retail_artifact_inventory.v1"
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "88",
  "copied_files": [
    "derived/artifact_inventory.json",
    "derived/evaluator_bundle_manifest.json",
    "derived/task.json",
    "official/db.json",
    "official/policy.md",
    "official/split_tasks.json",
    "official/tasks.json",
    "official/tau2_bench/src/tau2/data_model/tasks.py",
    "official/tau2_bench/src/tau2/domains/retail/data_model.py",
    "official/tau2_bench/src/tau2/evaluator/evaluator.py",
    "official/tau2_bench/src/tau2/evaluator/evaluator_env.py",
    "official/tau2_bench/src/tau2/evaluator/evaluator_nl_assertions.py"
  ],
  "derived_files": [
    "derived/artifact_inventory.json",
    "derived/evaluator_bundle_manifest.json",
    "derived/task.json"
  ],
  "domain": "tau3_retail",
  "file_sources": {
    "derived/artifact_inventory.json": "experiments/evidence_contracts/artifact_inventories/tau3_retail_artifact_inventory.v1.json",
    "derived/evaluator_bundle_manifest.json": "experiments/official_splits/tau2_bench_2be691669909439cf88dedc13decf94b7664d262/bundle_manifest.json",
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/tau3_retail_tasks.json#id=88",
    "official/db.json": "<TAU2_BENCH_INSTALL_ROOT>/data/tau2/domains/retail/db.json",
    "official/policy.md": "<REPO_ROOT>/experiments/official_splits/tau3_retail_policy.md",
    "official/split_tasks.json": "<REPO_ROOT>/experiments/official_splits/tau3_retail_split_tasks.json",
    "official/tasks.json": "<REPO_ROOT>/experiments/official_splits/tau3_retail_tasks.json",
    "official/tau2_bench/src/tau2/data_model/tasks.py": "https://github.com/sierra-research/tau2-bench/blob/2be691669909439cf88dedc13decf94b7664d262/src/tau2/data_model/tasks.py",
    "official/tau2_bench/src/tau2/domains/retail/data_model.py": "https://github.com/sierra-research/tau2-bench/blob/2be691669909439cf88dedc13decf94b7664d262/src/tau2/domains/retail/data_model.py",
    "official/tau2_bench/src/tau2/evaluator/evaluator.py": "https://github.com/sierra-research/tau2-bench/blob/2be691669909439cf88dedc13decf94b7664d262/src/tau2/evaluator/evaluator.py",
    "official/tau2_bench/src/tau2/evaluator/evaluator_env.py": "https://github.com/sierra-research/tau2-bench/blob/2be691669909439cf88dedc13decf94b7664d262/src/tau2/evaluator/evaluator_env.py",
    "official/tau2_bench/src/tau2/evaluator/evaluator_nl_assertions.py": "https://github.com/sierra-research/tau2-bench/blob/2be691669909439cf88dedc13decf94b7664d262/src/tau2/evaluator/evaluator_nl_assertions.py"
  },
  "official_files": [
    "official/db.json",
    "official/policy.md",
    "official/split_tasks.json",
    "official/tasks.json",
    "official/tau2_bench/src/tau2/data_model/tasks.py",
    "official/tau2_bench/src/tau2/domains/retail/data_model.py",
    "official/tau2_bench/src/tau2/evaluator/evaluator.py",
    "official/tau2_bench/src/tau2/evaluator/evaluator_env.py",
    "official/tau2_bench/src/tau2/evaluator/evaluator_nl_assertions.py"
  ],
  "packet_files": [
    "derived/task.json",
    "official/policy.md",
    "official/split_tasks.json",
    "official/tau2_bench/src/tau2/evaluator/evaluator.py",
    "official/tau2_bench/src/tau2/evaluator/evaluator_env.py",
    "official/tau2_bench/src/tau2/evaluator/evaluator_nl_assertions.py",
    "official/tau2_bench/src/tau2/data_model/tasks.py",
    "official/tau2_bench/src/tau2/domains/retail/data_model.py",
    "derived/evaluator_bundle_manifest.json",
    "derived/artifact_inventory.json"
  ],
  "sha256_per_file": {
    "derived/artifact_inventory.json": "cebcdc019ec35eeee979ea0780f0a9355d4d270c7c01182daa213b9217ed9245",
    "derived/evaluator_bundle_manifest.json": "7818a461ef573c0eb000466c9f849b23f008187da250c63c9102e7e446d6cfa3",
    "derived/task.json": "a725bd0467ec76597daf974abf731137c5bc23a97f0ee2d726a285b8ab3b7476",
    "official/db.json": "413a65160adbdb5fde0ffc0015c49b6d70250b10c18128de169b597af7766765",
    "official/policy.md": "2c9652afbce57d6e087768d37cda64d31c53d50b3e3225cfdb791bac66466467",
    "official/split_tasks.json": "ed0580ec52575b63fbf76568af42490da6ee7783ecb4aa81af46961291358f20",
    "official/tasks.json": "8e03ebce7901bd6218e7a7dc3105faa9324091a68058f7fe61c65262868812e8",
    "official/tau2_bench/src/tau2/data_model/tasks.py": "a2feb565a5420223f96d565f05be546970e09aac82919a69301250c8f1883eb1",
    "official/tau2_bench/src/tau2/domains/retail/data_model.py": "f5ad09590953855cc49d2ab2ad5c0594be408cae74d1500fb278e5a6bf2c50d6",
    "official/tau2_bench/src/tau2/evaluator/evaluator.py": "85a05cf75f19708bf855ac8f97cf34d8aef05c99332d57dc066725200ca59444",
    "official/tau2_bench/src/tau2/evaluator/evaluator_env.py": "e932ea5f675d7a172557350f30b73d66474659d9b4d976ecd763ca2929017633",
    "official/tau2_bench/src/tau2/evaluator/evaluator_nl_assertions.py": "cb6b3758cdceb02a726732b4ee1af618affcc08f8ab84b44f060146b8f3ad90a"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/tau3_retail_tasks.json",
    "<REPO_ROOT>/experiments/official_splits/tau3_retail_policy.md",
    "<REPO_ROOT>/experiments/official_splits/tau3_retail_split_tasks.json",
    "<TAU2_BENCH_INSTALL_ROOT>/data/tau2/domains/retail/db.json",
    "https://github.com/sierra-research/tau2-bench/blob/2be691669909439cf88dedc13decf94b7664d262/src/tau2/evaluator/evaluator.py",
    "https://github.com/sierra-research/tau2-bench/blob/2be691669909439cf88dedc13decf94b7664d262/src/tau2/evaluator/evaluator_env.py",
    "https://github.com/sierra-research/tau2-bench/blob/2be691669909439cf88dedc13decf94b7664d262/src/tau2/evaluator/evaluator_nl_assertions.py",
    "https://github.com/sierra-research/tau2-bench/blob/2be691669909439cf88dedc13decf94b7664d262/src/tau2/data_model/tasks.py",
    "https://github.com/sierra-research/tau2-bench/blob/2be691669909439cf88dedc13decf94b7664d262/src/tau2/domains/retail/data_model.py",
    "experiments/official_splits/tau2_bench_2be691669909439cf88dedc13decf94b7664d262/bundle_manifest.json",
    "experiments/evidence_contracts/artifact_inventories/tau3_retail_artifact_inventory.v1.json"
  ],
  "task_id": "88"
}
```
